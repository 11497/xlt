import json
from datetime import datetime
from functools import lru_cache
from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

from ai.chat import ChatService
from ai.hybrid_search_service import HybridSearchService
from authentication.user_auth import require_current_user
from config.ai_config import SYSTEM_MESSAGE, TOPK, TOPN
from crud.message_crud import MessageCRUD
from crud.session_crud import SessionCRUD
from crud.user_knowledge_base_crud import UserKnowledgeBaseCRUD
from model.message_model import Message
from model.result import Result
from model.user_model import User

router = APIRouter(prefix="/api/message", tags=["message"])


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


def retrieve_context_from_knowledge_bases(
        user_id: int,
        query: str,
        search_service: HybridSearchService
) -> str:
    """
    从用户可访问的知识库中检索相关上下文（使用混合检索 + Rerank）
    :param user_id: 用户ID
    :param query: 用户查询
    :return: 合并后的上下文文本
    """
    # 获取用户可访问的知识库列表
    knowledge_base_ids = UserKnowledgeBaseCRUD.get_knowledge_bases_by_user(user_id)

    if not knowledge_base_ids:
        return ""

    all_documents = []

    # 在每个知识库中执行混合检索
    for kb_id in knowledge_base_ids:
        try:
            # 调用混合检索，返回已重排序的文档列表
            results = search_service.search(
                knowledge_base_id=kb_id,
                query=query,
                top_k=TOPK,      # 最终返回数量（重排后）
                top_n=TOPN       # 精排数量（可根据需要调整）
            )
            if results:
                # 提取文档内容
                docs = [item["content"] for item in results if item.get("content")]
                all_documents.extend(docs)
        except Exception as e:
            # 跳过访问失败或检索失败的知识库，记录日志（可选）
            print(f"检索知识库 {kb_id} 失败: {e}")
            continue

    # 去重并合并
    unique_docs = list(set(all_documents))
    return "\n\n".join(unique_docs)


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
            yield encode_stream_event({"type": "start", "user_message_id": message_id})
            yield encode_stream_event({"type": "delta", "content": ai_message.content})
            yield encode_stream_event({"type": "done", "assistant_message_id": ai_message_id})

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
    context = retrieve_context_from_knowledge_bases(user.id, rewritten_query, search_service)

    # 添加当前用户消息（可能包含上下文）
    if context:
        current_content = f"<knowledge_base>\n{context}\n</knowledge_base>\n\n<user_query>\n{rewritten_query}\n</user_query>"
    else:
        current_content = rewritten_query
    messages.append(HumanMessage(content=current_content))

    async def generate_response():
        response_parts = []
        yield encode_stream_event({"type": "start", "user_message_id": message_id})

        try:
            async for chunk in chat_service.stream_message(messages):
                response_parts.append(chunk)
                yield encode_stream_event({"type": "delta", "content": chunk})

            response = "".join(response_parts)
            if not response.strip():
                raise RuntimeError("AI returned an empty response")

            # 只持久化完整的回复，取消或失败的流必须保持对话历史的完整性。
            ai_message = Message(
                session_id=message.session_id,
                role="assistant",
                content=response,
                rewritten_content=None,
                create_time=datetime.now()
            )
            ai_message_id = MessageCRUD.create(ai_message)

            try:
                if is_first_round and session.name == "新建会话":
                    conversation = [HumanMessage(content=message.content), AIMessage(content=response)]
                    summary = await chat_service.summarize_conversation(conversation)
                    SessionCRUD.update_session_name(message.session_id, summary)

                SessionCRUD.update_session_update_time(message.session_id)
            except Exception as exc:
                # 回复已完整持久化，所以可选的会话元更新必须保持成功。
                print(f"更新会话信息失败: {exc}")

            yield encode_stream_event({"type": "done", "assistant_message_id": ai_message_id})
        except Exception as exc:
            print(f"生成 AI 回复失败: {exc}")
            yield encode_stream_event({"type": "error", "message": "AI 回复生成失败，请稍后重试"})

    return StreamingResponse(
        generate_response(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
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

    return result.success(msg="查询成功", data=messages)


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

    return result.success(msg="查询成功", data=message)


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
