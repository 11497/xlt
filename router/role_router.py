from fastapi import APIRouter, Depends

from authentication.authentication import get_current_user, oauth2_scheme
from config.jwt_config import JWT_CONFIG
from crud.role_crud import RoleCRUD
from crud.user_crud import UserCRUD
from model.result import Result
from model.role_model import Role
from util.jwt_util import JwtUtil

router = APIRouter(prefix="/api/role", tags=["role"])

jwt_util = JwtUtil(secret_key=JWT_CONFIG["secret_key"], algorithm=JWT_CONFIG["algorithm"],
                   access_token_expire_minutes=JWT_CONFIG["access_token_expire_minutes"])

@router.post("")
async def create_role(role: Role, token: str = Depends(oauth2_scheme)):
    """创建角色"""
    result = Result()
    current_user = get_current_user(token)
    user = UserCRUD.get_by_id(current_user["user_id"])
    if user.is_admin == 0 or user is None:
        return result.error(msg="您没有权限创建角色")

    role_id = RoleCRUD.create(role)
    if role_id is None:
        return result.error(msg="创建角色失败")
    return result.success(msg="创建角色成功")

@router.get("/all")
async def get_all_role(token: str = Depends(oauth2_scheme)):
    """查询所有角色"""
    result = Result()
    current_user = get_current_user(token)
    user = UserCRUD.get_by_id(current_user["user_id"])
    if user.is_admin == 0 or user is None:
        return result.error(msg="您没有权限查询所有角色")

    roles = RoleCRUD.get_all()
    return result.success(msg="查询所有角色成功", data=roles)

@router.get("/{role_name}")
async def get_by_name(role_name: str, token: str = Depends(oauth2_scheme)):
    """根据角色名查询角色"""
    result = Result()
    current_user = get_current_user(token)
    user = UserCRUD.get_by_id(current_user["user_id"])
    if user.is_admin == 0 or user is None:
        return result.error(msg="您没有权限查询角色")
    role = RoleCRUD.get_by_name(role_name)
    if role is None:
        return result.error(msg="角色不存在")
    return result.success(msg="查询角色成功", data=role)
