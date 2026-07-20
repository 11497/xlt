from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

from ai.chat import ChatService
from ai.chroma_service import ChromaService
from ai.embedding import EmbeddingService
from authentication.user_auth import require_current_user
from config.ai_config import SYSTEM_MESSAGE
from crud.message_crud import MessageCRUD
from crud.session_crud import SessionCRUD
from crud.user_knowledge_base_crud import UserKnowledgeBaseCRUD
from model.message_model import Message
from model.result import Result
from model.user_model import User

router = APIRouter(prefix="/api/message", tags=["message"])

# 初始化服务
embedding_service = EmbeddingService()
chroma_service = ChromaService()
chat_service = ChatService()


def retrieve_context_from_knowledge_bases(user_id: int, query: str) -> str:
    """
    从用户可访问的知识库中检索相关上下文
    :param user_id: 用户ID
    :param query: 用户查询
    :return: 合并后的上下文文本
    """
    # 获取用户可访问的知识库列表
    knowledge_base_ids = UserKnowledgeBaseCRUD.get_knowledge_bases_by_user(user_id)
    
    if not knowledge_base_ids:
        return ""

    # 向量化查询
    query_embedding = embedding_service.embed_query(query)

    # 从所有知识库检索相似文档
    all_documents = []
    for kb_id in knowledge_base_ids:
        try:
            results = chroma_service.query_similar(kb_id, query_embedding)
            if results and "documents" in results and results["documents"]:
                all_documents.extend(results["documents"][0])
        except Exception as e:
            # 跳过访问失败的知识库
            continue

    # 合并文档内容，去重
    unique_docs = list(set(all_documents))
    return "\n\n".join(unique_docs)


@router.post("/chat")
async def chat(
        message: Message,
        user: User = Depends(require_current_user)
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
    MessageCRUD.create(message)
    
    # 构建完整对话历史
    # 添加系统提示词
    messages: List[BaseMessage] = [SystemMessage(content=SYSTEM_MESSAGE)]

    # 添加历史对话
    for msg in existing_messages:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            messages.append(AIMessage(content=msg.content))

    # RAG检索
    context = retrieve_context_from_knowledge_bases(user.id, message.content)

    # 添加当前用户消息（可能包含上下文）
    if context:
        current_content = f"<knowledge_base>\n{context}\n</knowledge_base>\n\n<user_query>\n{message.content}\n</user_query>"
    else:
        current_content = message.content
    messages.append(HumanMessage(content=current_content))

    # 调用AI模型获取响应
    response = chat_service.send_message(messages)
        
    # 流式响应结束后，保存AI回复到数据库
    ai_message = Message(
        session_id=message.session_id,
        role="assistant",
        content=response,
        create_time=datetime.now()
    )
    MessageCRUD.create(ai_message)
        
    # 如果是第一轮对话，总结对话并更新会话名称
    if is_first_round and session.name == "新建会话":
        messages = [HumanMessage(content=message.content), AIMessage(content=response)]
        summary = chat_service.summarize_conversation(messages)
        SessionCRUD.update_session_name(message.session_id, summary)

    # 更新会话更新时间
    SessionCRUD.update_session_update_time(message.session_id)

    return result.success(msg="对话成功", data=response)


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