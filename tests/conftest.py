from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from authentication.authentication import get_current_user
from model.user_model import User
from router import message_router, session_router


class StubChatService:
    async def is_malicious(self, _messages: list[Any]) -> bool:
        return False

    async def rewrite_question(self, _history: list[Any], question: str) -> str:
        return question

    async def stream_message(self, _messages: list[Any]) -> AsyncIterator[str]:
        yield "校园"
        yield "回答"

    async def summarize_conversation(self, _messages: list[Any]) -> str:
        return "问答标题"


class StubSearchService:
    def search(self, **_kwargs: Any) -> list[dict[str, Any]]:
        return []


@pytest.fixture
def current_user() -> User:
    return User(id=1, username="student", password="secret1", is_admin=0)


@pytest.fixture
def admin_user() -> User:
    return User(id=2, username="admin1", password="secret1", is_admin=1)


@pytest.fixture
def app_client_factory():
    clients: list[TestClient] = []

    def create_client(
            user: User | None = None,
            chat_service: Any | None = None,
            search_service: Any | None = None
    ) -> TestClient:
        app = FastAPI()
        app.include_router(session_router.router)
        app.include_router(message_router.router)

        if user is not None:
            app.dependency_overrides[get_current_user] = lambda: user

        app.dependency_overrides[message_router.get_chat_service] = (
            lambda: chat_service or StubChatService()
        )
        app.dependency_overrides[message_router.get_hybrid_search_service] = (
            lambda: search_service or StubSearchService()
        )

        client = TestClient(app)
        clients.append(client)
        return client

    yield create_client

    for client in clients:
        client.close()
