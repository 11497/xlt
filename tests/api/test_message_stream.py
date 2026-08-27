import json
from datetime import datetime
from typing import Any

from crud.message_crud import MessageCRUD
from crud.session_crud import SessionCRUD
from crud.user_knowledge_base_crud import UserKnowledgeBaseCRUD
from model.session_model import Session


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
