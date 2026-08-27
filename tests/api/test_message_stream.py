import asyncio
import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from crud.message_crud import MessageCRUD
from crud.session_crud import SessionCRUD
from crud.user_knowledge_base_crud import UserKnowledgeBaseCRUD
from model.message_model import Message
from model.session_model import Session
from router import message_router


def message_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "session_id": 7,
        "role": "user",
        "content": "请假有什么要求？",
        "create_time": datetime.now().isoformat()
    }
    payload.update(overrides)
    return payload


def parse_events(response) -> list[dict[str, Any]]:
    return [json.loads(line) for line in response.text.splitlines() if line]


def prepare_owned_session(monkeypatch, current_user) -> None:
    session = Session(
        id=7,
        user_id=current_user.id,
        name="新建会话",
        create_time=datetime.now(),
        update_time=datetime.now()
    )
    monkeypatch.setattr(SessionCRUD, "get_by_id", lambda _session_id: session)
    monkeypatch.setattr(MessageCRUD, "get_by_session_id", lambda _session_id: [])
    monkeypatch.setattr(
        UserKnowledgeBaseCRUD,
        "get_knowledge_bases_by_user",
        lambda _user_id: []
    )
    monkeypatch.setattr(SessionCRUD, "update_session_name", lambda *_args: True)
    monkeypatch.setattr(SessionCRUD, "update_session_update_time", lambda *_args: True)


def test_chat_requires_authentication(app_client_factory):
    client = app_client_factory()

    response = client.post("/api/message/chat", json=message_payload())

    assert response.status_code == 401


def test_chat_rejects_session_owned_by_another_user(
        monkeypatch,
        app_client_factory,
        current_user
):
    other_session = Session(id=7, user_id=99, name="其他用户会话")
    monkeypatch.setattr(SessionCRUD, "get_by_id", lambda _session_id: other_session)

    def fail_if_created(_message):
        raise AssertionError("无权访问时不应保存消息")

    monkeypatch.setattr(MessageCRUD, "create", fail_if_created)
    client = app_client_factory(user=current_user)

    response = client.post("/api/message/chat", json=message_payload())

    assert response.status_code == 200
    assert response.json()["code"] == 0
    assert "无权访问" in response.json()["msg"]


def test_chat_streams_events_and_persists_complete_reply(
        monkeypatch,
        app_client_factory,
        current_user
):
    prepare_owned_session(monkeypatch, current_user)
    created_messages = []

    def create_message(message):
        created_messages.append(message)
        return 100 + len(created_messages)

    monkeypatch.setattr(MessageCRUD, "create", create_message)
    client = app_client_factory(user=current_user)

    response = client.post("/api/message/chat", json=message_payload())
    events = parse_events(response)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    assert [event["type"] for event in events] == ["start", "delta", "delta", "done"]
    assert events[0]["user_message_id"] == 101
    assert events[-1]["assistant_message_id"] == 102
    assert [message.role for message in created_messages] == ["user", "assistant"]
    assert created_messages[-1].content == "校园回答"


def test_chat_failure_does_not_persist_partial_assistant_reply(
        monkeypatch,
        app_client_factory,
        current_user
):
    class FailingChatService:
        async def is_malicious(self, _messages):
            return False

        async def rewrite_question(self, _history, question):
            return question

        async def stream_message(self, _messages):
            yield "未完成"
            raise RuntimeError("模型连接中断")

    prepare_owned_session(monkeypatch, current_user)
    created_messages = []

    def create_message(message):
        created_messages.append(message)
        return 100 + len(created_messages)

    monkeypatch.setattr(MessageCRUD, "create", create_message)
    client = app_client_factory(user=current_user, chat_service=FailingChatService())

    response = client.post("/api/message/chat", json=message_payload())
    events = parse_events(response)

    assert [event["type"] for event in events] == ["start", "delta", "error"]
    assert [message.role for message in created_messages] == ["user"]
    assert events[-1]["message"] == "AI 回复生成失败，请稍后重试"


def test_chat_cancellation_does_not_persist_partial_assistant_reply(
        monkeypatch,
        current_user
):
    class CancellingChatService:
        async def is_malicious(self, _messages):
            return False

        async def rewrite_question(self, _history, question):
            return question

        async def stream_message(self, _messages):
            yield "未完成"
            raise asyncio.CancelledError()

    prepare_owned_session(monkeypatch, current_user)
    created_messages = []

    def create_message(message):
        created_messages.append(message)
        return 100 + len(created_messages)

    monkeypatch.setattr(MessageCRUD, "create", create_message)
    message = Message.model_validate(message_payload())
    response = asyncio.run(message_router.chat(
        message,
        current_user,
        CancellingChatService(),
        object()
    ))
    received_chunks = []

    async def consume_stream():
        async for chunk in response.body_iterator:
            received_chunks.append(chunk)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(consume_stream())

    events = [json.loads(chunk) for chunk in received_chunks]
    assert [event["type"] for event in events] == ["start", "delta"]
    assert [message.role for message in created_messages] == ["user"]


def test_explicit_stop_persists_truncated_assistant_reply(
        monkeypatch,
        current_user
):
    class StoppableChatService:
        def __init__(self):
            self.summary_messages = None

        async def is_malicious(self, _messages):
            return False

        async def rewrite_question(self, _history, question):
            return question

        async def stream_message(self, _messages):
            yield "第一段"
            yield "不应保存的第二段"

        async def summarize_conversation(self, messages):
            self.summary_messages = messages
            return "截断回答标题"

    prepare_owned_session(monkeypatch, current_user)
    created_messages = []
    renamed_sessions = []
    chat_service = StoppableChatService()

    def create_message(message):
        created_messages.append(message)
        return 100 + len(created_messages)

    monkeypatch.setattr(MessageCRUD, "create", create_message)
    monkeypatch.setattr(
        SessionCRUD,
        "update_session_name",
        lambda session_id, name: renamed_sessions.append((session_id, name)) or True
    )
    message = Message.model_validate(message_payload())

    async def run_stoppable_stream():
        response = await message_router.chat(
            message,
            current_user,
            chat_service,
            object()
        )
        events = []

        async for chunk in response.body_iterator:
            event = json.loads(chunk)
            events.append(event)
            if event["type"] == "delta":
                stop_result = await message_router.stop_chat(
                    UUID(events[0]["request_id"]),
                    current_user
                )
                assert stop_result["code"] == 1

        return events

    events = asyncio.run(run_stoppable_stream())

    assert [event["type"] for event in events] == ["start", "delta", "stopped"]
    assert events[-1]["assistant_message_id"] == 102
    assert [message.role for message in created_messages] == ["user", "assistant"]
    assert created_messages[-1].content == "第一段"
    assert renamed_sessions == [(7, "截断回答标题")]
    assert chat_service.summary_messages[1].content == "第一段"
    assert message_router.active_chat_requests == {}


def test_user_cannot_stop_another_users_generation(current_user):
    request_id = uuid4()
    stop_event = asyncio.Event()
    message_router.active_chat_requests[request_id] = message_router.ActiveChatRequest(
        user_id=99,
        session_id=7,
        stop_event=stop_event
    )

    try:
        result = asyncio.run(message_router.stop_chat(request_id, current_user))

        assert result["code"] == 0
        assert "无权" in result["msg"]
        assert not stop_event.is_set()
    finally:
        message_router.active_chat_requests.pop(request_id, None)


def test_chat_rejects_invalid_message_role(
        monkeypatch,
        app_client_factory,
        current_user
):
    def fail_if_created(_message):
        raise AssertionError("请求校验失败时不应保存消息")

    monkeypatch.setattr(MessageCRUD, "create", fail_if_created)
    client = app_client_factory(user=current_user)

    response = client.post(
        "/api/message/chat",
        json=message_payload(role="system")
    )

    assert response.status_code == 422
