from fastapi import APIRouter, Depends, Query, Body

from authentication.user_auth import require_admin, require_current_user
from config.jwt_config import JWT_CONFIG
from crud.role_user_crud import RoleUserCRUD
from crud.user_crud import UserCRUD
from model.result import Result
from model.user_model import User, UserRegistration
from util.jwt_util import JwtUtil
from util.password_util import PasswordUtil

router = APIRouter(prefix="/api/user", tags=["user"])

jwt_util = JwtUtil(secret_key=JWT_CONFIG["secret_key"], algorithm=JWT_CONFIG["algorithm"],
                   access_token_expire_minutes=JWT_CONFIG["access_token_expire_minutes"])


def user_to_response(user: User) -> dict:
    # BaseModel 使用 model_dump 导出数据；排除 password，避免任何用户信息接口泄露密码。
    return user.model_dump(exclude={"password"})


def valid_username(username: str):
    """
    验证用户名是否符合要求
    :param username: 用户名
    :return: 验证结果
    """
    # 用户名长度由 User.username 的 Field 约束自动校验；此处只处理数据库业务规则。
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
        if user is None or not PasswordUtil.verify_password(old_password, user.password):
            return "旧密码错误"
        if old_password == new_password:
            return "旧密码不能与新密码相同"
    # 密码长度由 User.password 或路由参数 Body 的声明自动校验。
    return None

def _create_user(user: User):
    result = Result()
    password_result = valid_password(user.password)
    if password_result is not None:
        return result.error(msg=password_result)

    username_result = valid_username(user.username)
    if username_result is not None:
        return result.error(msg=username_result)

    UserCRUD.create(user)
    return result.success(msg="注册成功")


@router.post("/register")
async def register(registration: UserRegistration):
    """
    普通用户注册
    :param registration: 注册信息
    :return: 注册结果
    """
    user = User(username=registration.username, password=registration.password, is_admin=0)
    return _create_user(user)


@router.post("/register-admin")
async def register_admin(user: User, _admin: User = Depends(require_admin)):
    """
    管理员创建用户
    :param user: 用户对象
    :param _admin: 管理员用户对象
    :return: 注册结果
    """
    return _create_user(user)

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
    if not PasswordUtil.verify_password(user.password, login_user.password):
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
        # 将每个 BaseModel 转为安全的字典后再作为 JSON 响应返回。
        "list": [user_to_response(user) for user in users],
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

    # 不修改 Depends 注入的 BaseModel 实例，直接导出不含密码的响应数据。
    return result.success(msg="查询成功", data=user_to_response(user))

@router.put("/username")
async def update_username(
        id: int = Body(..., alias="id"),
        # 独立 Body 参数不会经过 User 模型，故在此声明 Pydantic 的长度约束。
        username: str = Body(..., alias="username", min_length=4, max_length=15),
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
    update_result = UserCRUD.update_username(id, username)
    if not update_result:
        return result.error(msg="用户不存在")
    updated_user = UserCRUD.get_by_username(username)
    # 数据库查询结果同样是 User(BaseModel)，导出时排除敏感字段。
    return result.success(msg="更新成功", data=user_to_response(updated_user))

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
        old_password: str = Body(..., alias="oldPassword", min_length=6, max_length=20),
        # 独立 Body 参数不会经过 User 模型，故在此声明 Pydantic 的长度约束。
        new_password: str = Body(..., alias="newPassword", min_length=6, max_length=20),
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

    password_result = valid_password(new_password, old_password, user)
    if password_result is not None:
        return result.error(msg=password_result)

    res = UserCRUD.update_password(user.id, new_password)
    if not res:
        return result.error(msg="更新密码失败")
    return result.success(msg="更新成功")

@router.put("/reset_password/{id}")
async def reset_password(
        id: int,
        _admin: User = Depends(require_admin)
):
    """
    管理员重置用户密码
    :param id: 用户ID
    :param _admin: 管理员用户对象
    :return: 更新结果
    """
    result = Result()

    target_user = UserCRUD.get_by_id(id)
    if not target_user:
        return result.error(msg="用户不存在")

    # 重置密码为默认值（"123456"）
    default_password = "123456"
    if PasswordUtil.verify_password(default_password, target_user.password):
        return result.error(msg="重置密码失败，用户密码已是默认值")

    res = UserCRUD.update_password(id, default_password)
    if not res:
        return result.error(msg="重置密码失败")
    return result.success(msg="重置密码成功")



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
    # 数据库查询结果同样是 User(BaseModel)，导出时排除敏感字段。
    return result.success(msg="用户权限更新成功", data=user_to_response(updated_user))

@router.get("/search/{content}")
async def search_user(content: str, _admin: User = Depends(require_admin)):
    """
    管理员根据用户名或ID查询用户
    :param content: 搜索内容
    :param _admin: 管理员用户对象
    :return: 用户列表
    """
    result = Result()

    users = UserCRUD.search(content)
    # 列表中的元素也是 BaseModel，逐个导出为可 JSON 序列化的安全字典。
    return result.success(msg="查询成功", data=[user_to_response(user) for user in users])
