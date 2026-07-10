from fastapi import APIRouter

from crud.user_crud import UserCRUD
from model.user_model import User

router = APIRouter(prefix="/api/user", tags=["user"])


@router.post("/regisster")
async def register(user: User):
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
