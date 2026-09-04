from fastapi import status

from authentication.authentication import jwt_util
from crud.user_crud import UserCRUD


def test_deleted_user_cannot_use_old_jwt(monkeypatch, app_client_factory):
    token = jwt_util.create_access_token(data={"user_id": 7})
    monkeypatch.setattr(UserCRUD, "get_by_id", lambda _user_id: None)
    client = app_client_factory(user=None)

    response = client.get("/api/session/all", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "用户未登录或不存在"


def test_deleted_user_cannot_login(monkeypatch, app_client_factory):
    monkeypatch.setattr(UserCRUD, "get_by_username", lambda _username: None)
    client = app_client_factory(user=None)

    login_response = client.post("/api/user/login", json={"username": "deleted", "password": "123456"})
    auth_response = client.post("/api/auth", data={"username": "deleted", "password": "123456"})

    assert login_response.status_code == status.HTTP_200_OK
    assert login_response.json()["code"] == 0
    assert auth_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert auth_response.json()["detail"] == "用户名或密码错误"
