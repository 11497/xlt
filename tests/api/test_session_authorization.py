from datetime import datetime

from crud.session_crud import SessionCRUD
from model.session_model import Session


def make_session(user_id: int) -> Session:
    return Session(
        id=7,
        user_id=user_id,
        name="测试会话",
        create_time=datetime.now(),
        update_time=datetime.now()
    )


def test_regular_user_cannot_read_another_users_session(
        monkeypatch,
        app_client_factory,
        current_user
):
    monkeypatch.setattr(SessionCRUD, "get_by_id", lambda _session_id: make_session(99))
    client = app_client_factory(user=current_user)

    response = client.get("/api/session/7")

    assert response.status_code == 200
    assert response.json()["code"] == 0
    assert "无权访问" in response.json()["msg"]


def test_regular_user_cannot_list_all_sessions(app_client_factory, current_user):
    client = app_client_factory(user=current_user)

    response = client.get("/api/session/all")

    assert response.status_code == 403


def test_admin_can_list_all_sessions(monkeypatch, app_client_factory, admin_user):
    sessions = [make_session(admin_user.id)]
    monkeypatch.setattr(SessionCRUD, "get_page", lambda **_kwargs: (sessions, 1))
    client = app_client_factory(user=admin_user)

    response = client.get("/api/session/all?page=1&page_size=10")

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 1
    assert body["data"]["total"] == 1
    assert body["data"]["list"][0]["user_id"] == admin_user.id
