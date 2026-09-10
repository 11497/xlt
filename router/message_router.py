import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

from ai.chat import ChatService
from ai.hybrid_search_service import HybridSearchService
from authentication.user_auth import require_current_user
from config.ai_config import SYSTEM_MESSAGE, TOPK, TOPN
from crud.message_crud import MessageCRUD
from crud.message_source_crud import (
    build_message_sources,
    create_assistant_message_with_sources,
    get_sources_by_message_ids,
    get_sources_grouped_by_message_ids,
)
from crud.session_crud import SessionCRUD
from crud.user_knowledge_base_crud import UserKnowledgeBaseCRUD
from model.message_model import Message
from model.result import Result
from model.session_model import DEFAULT_SESSION_NAME, normalize_session_name
from model.user_model import User

router = APIRouter(prefix="/api/message", tags=["message"])

# 与 system.md 中的固定无依据回复保持完全一致。
NO_SOURCE_RESPONSE = "知识库中没有找到"


@dataclass
class ActiveChatRequest:
    user_id: int
    session_id: int
    stop_event: asyncio.Event


active_chat_requests: dict[UUID, ActiveChatRequest] = {}


@lru_cache
def get_hybrid_search_service() -> HybridSearchService:
    """获取复用的混合检索服务实例。"""
    return HybridSearchService()


@lru_cache
def get_chat_service() -> ChatService:
    """获取复用的聊天服务实例。"""
    return ChatService()


def encode_stream_event(event: dict) -> str:
    """
    编码一个流式 NDJSON 事件，不转义中文文本
    """
    return json.dumps(event, ensure_ascii=False) + "\n"


def retrieve_chunks_from_knowledge_bases(
        user_id: int,
        query: str,
        search_service: HybridSearchService
) -> list[dict]:
    """
    从用户可访问的知识库中检索结构化切片。
    :param user_id: 用户ID
    :param query: 用户查询
    :param search_service: 混合检索服务
    :return: 带 id、正文和元数据的切片列表
    """
    knowledge_base_ids = UserKnowledgeBaseCRUD.get_knowledge_bases_by_user(user_id)
    if not knowledge_base_ids:
        return []

    all_chunks = []

    for kb_id in knowledge_base_ids:
        try:
            results = search_service.search(
                knowledge_base_id=kb_id,
                query=query,
                top_k=TOPK,
                top_n=TOPN
            )
            for item in results:
                metadata = item.get("metadata", {})
                chunk_id = str(item.get("id", "")).strip()
                content = item.get("content", "")
                if not chunk_id or not content:
                    continue

                # 注入和判定使用同一份处理后正文，避免标签替换导致来源快照不一致。
                content = content.replace("</source>", "[/source]")
                all_chunks.append({
                    "id": chunk_id,
                    "content": content,
                    "metadata": {
                        "document_id": metadata.get("document_id"),
                        "knowledge_base_id": metadata.get("knowledge_base_id", kb_id),
                        "chunk_index": metadata.get("chunk_index"),
                    },
                    "source": item.get("source"),
                    "rerank_score": item.get("rerank_score"),
                })
        except Exception as exc:
            print(f"检索知识库 {kb_id} 失败: {exc}")
            continue

    seen_ids = set()
    chunks = []
    for chunk in all_chunks:
        if chunk["id"] in seen_ids:
            continue
        seen_ids.add(chunk["id"])
        chunks.append(chunk)

    return chunks


def format_source_blocks(chunks: list[dict]) -> str:
    """将结构化切片格式化为带稳定 ID 的注入文本。"""
    return "\n\n".join(
        f"<source id=\"{chunk['id']}\" "
        f"document_id=\"{chunk['metadata']['document_id']}\" "
        f"chunk_index=\"{chunk['metadata']['chunk_index']}\">\n"
        f"{chunk['content']}\n"
        f"</source>"
        for chunk in chunks
    )


@router.post("/chat")
async def chat(
        message: Message,
        user: User = Depends(require_current_user),
        chat_service: ChatService = Depends(get_chat_service),
        search_service: HybridSearchService = Depends(get_hybrid_search_service)
):
    """
    对话接口，第一轮对话后自动总结并修改会话名，非第一轮对话则合并历史对话
    :param message: 消息对象
    :param user: 当前用户对象
    :return: 流式响应
    """
    result = Result()

    # 验证会话是否存在且属于当前用户
    session = SessionCRUD.get_by_id(message.session_id)
    if not session or (session.user_id != user.id and user.is_admin == 0):
        return result.error(msg="会话不存在或无权访问")

    # 获取当前会话的所有历史消息（判断是否是第一轮对话）
    existing_messages = MessageCRUD.get_by_session_id(message.session_id)
    is_first_round = len(existing_messages) == 0

    # 保存用户消息
    message.create_time = datetime.now()
    message_id = MessageCRUD.create(message)

    # 判断对话是否为恶意或敏感内容
    if await chat_service.is_malicious([HumanMessage(content=message.content)]):
        # AI回复：对话包含恶意或敏感内容
        ai_message = Message(
            session_id=message.session_id,
            role="assistant",
            content="对话包含恶意或敏感内容",
            rewritten_content=None,
            create_time=datetime.now()
        )
        ai_message_id = MessageCRUD.create(ai_message)

        async def malicious_response():
            yield encode_stream_event({
                "type": "start",
                "user_message_id": message_id,
                "request_id": None
            })
            yield encode_stream_event({"type": "delta", "content": ai_message.content})
            yield encode_stream_event({
                "type": "done",
                "assistant_message_id": ai_message_id,
                "sources": []
            })

        return StreamingResponse(
            malicious_response(),
            media_type="application/x-ndjson",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        )
    
    # 构建历史对话消息（用于重写问题）
    history_messages: List[BaseMessage] = []
    for msg in existing_messages:
        if msg.role == "user":
            # 如果有重写后的内容，使用重写后的；否则使用原始内容
            query_content = msg.rewritten_content if msg.rewritten_content else msg.content
            history_messages.append(HumanMessage(content=query_content))
        elif msg.role == "assistant":
            history_messages.append(AIMessage(content=msg.content))
    
    # 重写用户问题（结合历史对话）
    rewritten_query = await chat_service.rewrite_question(history_messages, message.content)
    
    # 更新数据库中的重写后内容
    if rewritten_query != message.content and rewritten_query != "" and rewritten_query is not None:
        MessageCRUD.update_rewritten_content(message_id, rewritten_query)
    
    # 构建完整对话历史
    # 添加系统提示词
    messages: List[BaseMessage] = [SystemMessage(content=SYSTEM_MESSAGE)]

    # 添加历史对话
    messages.extend(history_messages)

    # RAG检索（使用重写后的问题）
    chunks = retrieve_chunks_from_knowledge_bases(user.id, rewritten_query, search_service)

    # 添加当前用户消息（可能包含上下文）
    if chunks:
        current_content = f"<knowledge_base>\n{format_source_blocks(chunks)}\n</knowledge_base>\n\n<user_query>\n{rewritten_query}\n</user_query>"
    else:
        current_content = rewritten_query
    messages.append(HumanMessage(content=current_content))

    request_id = uuid4()
    stop_event = asyncio.Event()
    active_chat_requests[request_id] = ActiveChatRequest(
        user_id=user.id,
        session_id=message.session_id,
        stop_event=stop_event
    )

    async def generate_response():
        response_parts = []

        try:
            yield encode_stream_event({
                "type": "start",
                "user_message_id": message_id,
                "request_id": str(request_id)
            })

            async for chunk in chat_service.stream_message(messages):
                if stop_event.is_set():
                    break
                response_parts.append(chunk)
                yield encode_stream_event({"type": "delta", "content": chunk})

            response = "".join(response_parts)
            was_stopped = stop_event.is_set()
            if not response.strip() and not was_stopped:
                raise RuntimeError("AI returned an empty response")

            ai_message_id = None
            source_payload = []
            if response.strip():
                selected_chunks = []
                # 显式停止也对已生成片段做来源判定；取消连接/失败仍不落库。
                if chunks and response.strip() != NO_SOURCE_RESPONSE:
                    try:
                        selected_ids = await chat_service.select_source_ids(
                            format_source_blocks(chunks),
                            rewritten_query,
                            response
                        )
                        candidate_by_id = {chunk["id"]: chunk for chunk in chunks}
                        selected_chunks = [
                            candidate_by_id[source_id]
                            for source_id in selected_ids
                            if source_id in candidate_by_id
                        ]
                    except Exception as exc:
                        # 判定失败不影响完整回答落库；来源按无来源处理。
                        print(f"stage=source_select message=相关性判定失败 error={exc}")

                ai_message = Message(
                    session_id=message.session_id,
                    role="assistant",
                    content=response,
                    rewritten_content=None,
                    create_time=datetime.now()
                )

                if selected_chunks:
                    sources = build_message_sources(message.session_id, selected_chunks)
                    ai_message_id = create_assistant_message_with_sources(ai_message, sources)
                    source_payload = [
                        {
                            "chunk_id": source.chunk_id,
                            "chunk_index": source.chunk_index,
                            "document_id": source.document_id,
                            "filename": source.filename,
                            "knowledge_base_id": source.knowledge_base_id,
                            "content": source.content,
                            "rerank_score": source.rerank_score,
                            "recall_source": source.recall_source,
                            "sort_order": source.sort_order,
                        }
                        for source in sources
                    ]
                else:
                    ai_message_id = MessageCRUD.create(ai_message)

            try:
                if response.strip() and is_first_round and session.name == DEFAULT_SESSION_NAME:
                    conversation = [HumanMessage(content=message.content), AIMessage(content=response)]
                    summary = await chat_service.summarize_conversation(conversation)
                    normalized_summary = normalize_session_name(summary)
                    SessionCRUD.update_session_name(message.session_id, normalized_summary)

                SessionCRUD.update_session_update_time(message.session_id)
            except Exception as exc:
                # 回复已持久化，可选的会话元更新失败不影响流的终止事件。
                print(f"更新会话信息失败: {exc}")

            terminal_type = "stopped" if was_stopped else "done"
            terminal_event = {
                "type": terminal_type,
                "assistant_message_id": ai_message_id,
                "sources": source_payload
            }
            yield encode_stream_event(terminal_event)
        except asyncio.CancelledError:
            # 断网或页面离开仍视为连接中断，不保存部分回复。
            raise
        except Exception as exc:
            print(f"生成 AI 回复失败: {exc}")
            yield encode_stream_event({"type": "error", "message": "AI 回复生成失败，请稍后重试"})
        finally:
            active_chat_requests.pop(request_id, None)

    return StreamingResponse(
        generate_response(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.post("/chat/stop/{request_id}")
async def stop_chat(
        request_id: UUID,
        user: User = Depends(require_current_user)
):
    """停止当前用户的活动生成，并保存已生成的非空回复。"""
    result = Result()
    active_request = active_chat_requests.get(request_id)

    if not active_request:
        return result.error(msg="生成请求不存在或已结束")
    if active_request.user_id != user.id:
        return result.error(msg="无权停止该生成请求")

    active_request.stop_event.set()
    return result.success(
        msg="已请求停止生成",
        data={"request_id": str(request_id)}
    )


@router.get("/session/{session_id}")
async def get_messages_by_session_id(
        session_id: int,
        user: User = Depends(require_current_user)
):
    """
    根据会话ID查询消息列表
    :param session_id: 会话ID
    :param user: 当前用户对象
    :return: 消息列表
    """
    result = Result()

    # 验证会话是否存在且属于当前用户
    session = SessionCRUD.get_by_id(session_id)
    if not session or (session.user_id != user.id and user.is_admin == 0):
        return result.error(msg="会话不存在或无权访问")

    messages = MessageCRUD.get_by_session_id(session_id)
    sources_by_message_id = get_sources_grouped_by_message_ids([
        item.id for item in messages if item.role == "assistant" and item.id is not None
    ])

    message_data = []
    for item in messages:
        data = item.to_dict()
        data["sources"] = sources_by_message_id.get(item.id, [])
        message_data.append(data)

    return result.success(msg="查询成功", data=message_data)


@router.get("/{message_id}")
async def get_message(
        message_id: int,
        user: User = Depends(require_current_user)
):
    """
    根据消息ID查询单个消息
    :param message_id: 消息ID
    :param user: 当前用户对象
    :return: 消息对象
    """
    result = Result()

    message = MessageCRUD.get_by_id(message_id)
    if not message:
        return result.error(msg="消息不存在")

    # 验证消息所属会话是否属于当前用户
    session = SessionCRUD.get_by_id(message.session_id)
    if not session or (session.user_id != user.id and user.is_admin == 0):
        return result.error(msg="无权访问该消息")

    sources = get_sources_by_message_ids([message.id]) if message.role == "assistant" else []
    message_data = message.to_dict()
    message_data["sources"] = sources

    return result.success(msg="查询成功", data=message_data)


@router.delete("/session/{session_id}")
async def delete_messages_by_session_id(
        session_id: int,
        user: User = Depends(require_current_user)
):
    """
    根据会话ID删除该会话下的所有消息
    :param session_id: 会话ID
    :param user: 当前用户对象
    :return: 删除结果
    """
    result = Result()

    # 验证会话是否存在且属于当前用户
    session = SessionCRUD.get_by_id(session_id)
    if not session or (session.user_id != user.id and user.is_admin == 0):
        return result.error(msg="会话不存在或无权删除")

    delete_result = MessageCRUD.delete_by_session_id(session_id)
    if not delete_result:
        return result.error(msg="删除失败")

    return result.success(msg="删除成功")


@router.delete("/after")
async def delete_messages_after(
        session_id: int,
        message_id: int,
        user: User = Depends(require_current_user)
):
    """
    删除会话内指定消息ID之后的所有消息
    :param session_id: 会话ID
    :param message_id: 消息ID
    :param user: 当前用户对象
    :return: 删除结果
    """
    result = Result()

    # 验证会话是否存在且属于当前用户
    session = SessionCRUD.get_by_id(session_id)
    if not session or (session.user_id != user.id and user.is_admin == 0):
        return result.error(msg="会话不存在或无权操作")

    # 验证消息是否存在且属于该会话
    message = MessageCRUD.get_by_id(message_id)
    if not message or message.session_id != session_id:
        return result.error(msg="消息不存在或不属于该会话")

    delete_result = MessageCRUD.delete_message_with_after(session_id, message_id)
    if not delete_result:
        return result.error(msg="删除失败")

    return result.success(msg="删除成功")
