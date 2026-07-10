from fastapi import APIRouter

from crud.user_crud import UserCRUD
from model.user_model import User

router = APIRouter(prefix="/api/user", tags=["user"])


@router.post("/regisster")
async def register(user: User):
    """用户注册"""
    if len(user.password) < 6:
        return {"code": 1, "msg": "密码长度不能小于6位", "data": None}
    if len(user.username) < 4 or len(user.username) > 15:
        return {"code": 1, "msg": "用户名长度必须在4到15位之间", "data": None}
    user_exist = UserCRUD.get_by_username(user.username)
    if user_exist:
        return {"code": 1, "msg": "用户名已存在", "data": None}
    UserCRUD.create(user)
    return {"code": 0, "msg": "注册成功", "data": None}

@router.post("/login")
async def login(username: str, password: str):
    login_user = UserCRUD.get_by_username(username)
    if not login_user:
        return {"code": 1, "msg": "用户名不存在", "data": None}
    if login_user.password != password:
        return {"code": 1, "msg": "密码错误", "data": None}
    # 返回去掉 password 字段的用户信息
    login_user.password = ""
    return {"code": 0, "msg": "登录成功", "data": login_user.to_dict()}
