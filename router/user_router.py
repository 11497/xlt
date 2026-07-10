from fastapi import APIRouter, Depends

from authentication.authentication import get_current_user, oauth2_scheme
from config.jwt_config import JWT_CONFIG
from crud.user_crud import UserCRUD
from model.result import Result
from model.user_model import User
from util.jwt_util import JwtUtil

router = APIRouter(prefix="/api/user", tags=["user"])

jwt_util = JwtUtil(secret_key=JWT_CONFIG["secret_key"], algorithm=JWT_CONFIG["algorithm"],
                   access_token_expire_minutes=JWT_CONFIG["access_token_expire_minutes"])

@router.post("/register")
async def register(user: User):
    """用户注册"""
    result = Result()
    if len(user.password) < 6:
        return result.error(msg="密码长度不能小于6位")
    if len(user.username) < 4 or len(user.username) > 15:
        return result.error(msg="用户名长度必须在4到15位之间")
    user_exist = UserCRUD.get_by_username(user.username)
    if user_exist:
        return result.error(msg="用户名已存在")

    UserCRUD.create(user)
    return result.success(msg="注册成功")

@router.post("/login")
async def login(username: str, password: str):
    """用户登录"""
    result = Result()
    login_user = UserCRUD.get_by_username(username)
    if not login_user:
        return result.error(msg="用户名不存在")
    if login_user.password != password:
        return result.error(msg="密码错误")
    # 生成 JWT 令牌
    access_token = jwt_util.create_access_token(data={"user_id": login_user.id})
    return result.success(msg="登录成功", data=access_token)

@router.get("/all")
async def get_all_user(token: str = Depends(oauth2_scheme)):
    result = Result()
    current_user = get_current_user(token)
    user = UserCRUD.get_by_id(current_user["user_id"])
    if user.is_admin == 0 or user is None:
        return result.error(msg="您没有权限查询所有用户")

    users = UserCRUD.get_all()
    return result.success(msg="查询成功", data=[user for user in users])

@router.get("")
async def get_user(token: str = Depends(oauth2_scheme)):
    """查询当前用户信息"""
    result = Result()
    current_user = get_current_user(token)
    user = UserCRUD.get_by_id(current_user["user_id"])

    # 返回去掉 password 字段的用户信息
    user.password = ""
    return result.success(msg="查询成功", data=user)

@router.put("/username")
async def update_username(id: int, username: str, token: str = Depends(oauth2_scheme)):
    """管理员更新用户名"""
    result = Result()
    current_user = get_current_user(token)
    admin_user = UserCRUD.get_by_id(current_user["user_id"])

    if admin_user.is_admin == 0 or admin_user is None:
        return result.error(msg="您没有权限更新用户名")

    user_exist = UserCRUD.get_by_username(username)
    if user_exist:
        return result.error(msg="用户名已存在")
    if len(username) < 4 or len(username) > 15:
        return result.error(msg="用户名长度必须在4到15位之间")

    update_result = UserCRUD.update_username(id, username)
    if not update_result:
        return result.error(msg="用户不存在")
    updated_user = UserCRUD.get_by_username(username)
    return result.success(msg="更新成功", data=updated_user)

@router.delete("/{id}")
async def delete_user(id: int, token: str = Depends(oauth2_scheme)):
    """管理员删除用户"""
    result = Result()
    current_user = get_current_user(token)
    admin_user = UserCRUD.get_by_id(current_user["user_id"])
    if admin_user.is_admin == 0 or admin_user is None:
        return result.error(msg="您没有权限删除用户")
    delete_result = UserCRUD.delete(id)
    if not delete_result:
        return result.error(msg="用户不存在")
    return result.success(msg="删除成功")

@router.post("/password")
async def update_password(old_password: str, new_password: str, token: str = Depends(oauth2_scheme)):
    """用户更新密码"""
    result = Result()
    current_user = get_current_user(token)
    user = UserCRUD.get_by_id(current_user["user_id"])
    if user is None:
        return result.error(msg="用户不存在")

    if len(new_password) < 6 or len(old_password) < 6:
        return result.error(msg="密码长度不能小于6位")
    if old_password == new_password:
        return result.error(msg="新密码不能与旧密码相同")

    user_exist = UserCRUD.get_by_id(user.id)
    if not user_exist:
        return result.error(msg="用户不存在")

    # 密码校验
    if user_exist.password != old_password:
        return result.error(msg="旧密码错误")
    res = UserCRUD.update_password(user.id, new_password)
    if not res:
        return result.error(msg="更新密码失败")
    return result.success(msg="更新成功")
