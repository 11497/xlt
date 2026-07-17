from fastapi import APIRouter, Depends, Query, Body

from authentication.user_auth import require_admin, require_current_user
from config.jwt_config import JWT_CONFIG
from crud.role_user_crud import RoleUserCRUD
from crud.user_crud import UserCRUD
from model.result import Result
from model.user_model import User
from util.jwt_util import JwtUtil

router = APIRouter(prefix="/api/user", tags=["user"])

jwt_util = JwtUtil(secret_key=JWT_CONFIG["secret_key"], algorithm=JWT_CONFIG["algorithm"],
                   access_token_expire_minutes=JWT_CONFIG["access_token_expire_minutes"])

def valid_username(username: str):
    """
    验证用户名是否符合要求
    :param username: 用户名
    :return: 验证结果
    """
    if len(username) < 4 or len(username) > 15:
        return "用户名长度必须在4到15位之间"
    user = UserCRUD.get_by_username(username)
    if user:
        return "用户名已存在"
    return None

def valid_password(
        new_password: str,
        old_password: str = "",
        user: User = None):
    """
    验证密码是否符合要求
    在传入old_password时必须同时传入user
    """
    if old_password != "":
        if old_password == new_password:
            return "旧密码不能与新密码相同"
        if user.password != old_password:
            return "旧密码错误"
    if len(new_password) < 6 or len(new_password) > 20:
        return "密码长度必须在6到20位之间"
    return None

@router.post("/register")
async def register(user: User):
    """
    用户注册
    :param user: 用户对象
    :return: 注册结果
    """
    result = Result()
    password_result = valid_password(user.password)
    if password_result is not None:
        return result.error(msg=password_result)

    username_result = valid_username(user.username)
    if username_result is not None:
        return result.error(msg=username_result)

    UserCRUD.create(user)
    return result.success(msg="注册成功")

@router.post("/login")
async def login(user: User):
    """
    用户登录
    :param user: 用户对象
    :return: 登录成功后的 JWT 令牌
    """
    result = Result()
    login_user = UserCRUD.get_by_username(user.username)
    if not login_user:
        return result.error(msg="用户名不存在")
    if login_user.password != user.password:
        return result.error(msg="密码错误")
    # 生成 JWT 令牌
    access_token = jwt_util.create_access_token(data={"user_id": login_user.id})
    return result.success(msg="登录成功", data=access_token)

@router.get("/all")
async def get_all_user(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数"),
        _admin: User = Depends(require_admin)
):
    """
    分页查询所有用户信息（管理员）
    :param page: 页码，默认1
    :param page_size: 每页条数，默认10，最大100
    :param _admin: 管理员用户对象
    :return: 分页用户列表及总数
    """
    result = Result()

    users, total = UserCRUD.get_page(page=page, page_size=page_size)
    return result.success(msg="查询成功", data={
        "list": users,
        "total": total,
        "page": page,
        "page_size": page_size
    })

@router.get("")
async def get_user(user: User = Depends(require_current_user)):
    """
    查询当前用户信息
    :param user: 当前用户对象
    :return: 用户信息
    """
    result = Result()

    # 返回去掉 password 字段的用户信息
    user.password = ""
    return result.success(msg="查询成功", data=user)

@router.put("/username")
async def update_username(
        id: int = Body(..., alias="id"),
        username: str = Body(..., alias="username"),
        _admin: User = Depends(require_admin)
):
    """
    管理员更新用户名
    :param id: 用户ID
    :param username: 新用户名
    :param _admin: 管理员用户对象
    :return: 更新结果
    """
    result = Result()

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
async def delete_user(id: int, _admin: User = Depends(require_admin)):
    """
    管理员删除用户
    :param id: 用户ID
    :param _admin: 管理员用户对象
    :return: 删除结果
    """
    result = Result()

    # 验证目标用户是否有绑定的角色
    roles = RoleUserCRUD.get_roles_by_user(id)
    if roles:
        return result.error(msg="用户下有绑定的角色，不能删除")

    delete_result = UserCRUD.delete(id)
    if not delete_result:
        return result.error(msg="用户不存在")
    return result.success(msg="删除成功")

@router.put("/password")
async def update_password(
        old_password: str = Body(..., alias="oldPassword"),
        new_password: str = Body(..., alias="newPassword"),
        user: User = Depends(require_current_user)
):
    """
    用户更新密码
    :param old_password: 旧密码
    :param new_password: 新密码
    :param user: 当前用户对象
    :return: 更新结果
    """
    result = Result()

    if user is None:
        return result.error(msg="用户不存在")
    password_result = valid_password(new_password, old_password, user)
    if password_result is not None:
        return result.error(msg=password_result)

    res = UserCRUD.update_password(user.id, new_password)
    if not res:
        return result.error(msg="更新密码失败")
    return result.success(msg="更新成功")


@router.put("/admin-status")
async def set_user_admin_status(
        id: int = Body(..., alias="id"),
        is_admin: int = Body(..., alias="isAdmin"),
        admin: User = Depends(require_admin)
):
    """
    管理员设置用户权限
    :param id: 用户ID
    :param is_admin: 管理员状态值（0：普通用户，1：管理员）
    :param admin: 管理员用户对象
    :return: 更新结果
    """
    result = Result()

    # 验证目标用户是否存在
    target_user = UserCRUD.get_by_id(id)
    if not target_user:
        return result.error(msg="目标用户不存在")

    # 确保 is_admin 值有效（0 或 1）
    if is_admin not in [0, 1]:
        return result.error(msg="管理员状态值无效，应为 0（普通用户）或 1（管理员）")

    # 防止管理员取消自己的管理员权限
    if admin.id == id and is_admin == 0:
        return result.error(msg="不能取消自己的管理员权限")
    update_result = UserCRUD.set_user_admin_status(id, is_admin)
    if not update_result:
        return result.error(msg="更新用户权限失败")

    updated_user = UserCRUD.get_by_id(id)
    return result.success(msg="用户权限更新成功", data=updated_user)
