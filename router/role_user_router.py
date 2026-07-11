from typing import List

from fastapi import APIRouter, Depends

from authentication.authentication import get_current_user, oauth2_scheme
from authentication.user_auth import require_admin
from config.jwt_config import JWT_CONFIG
from crud.role_user_crud import RoleUserCRUD
from crud.user_crud import UserCRUD
from model.result import Result
from model.user_model import User
from util.jwt_util import JwtUtil

router = APIRouter(prefix="/api/role_user", tags=["role_user"])

@router.post("/assign")
async def batch_assign_users_to_role(role_id: int, user_ids: List[int], admin: User = Depends(require_admin())):
    """批量为角色分配用户"""
    result = Result()

    # 删除user_ids中已经分配给角色的用户
    new_user_ids = []
    assigned_user_ids = RoleUserCRUD.get_users_by_role(role_id)
    for user_id in user_ids:
        if user_id not in assigned_user_ids:
            new_user_ids.append(user_id)

    res = RoleUserCRUD.batch_assign_users_to_role(role_id, new_user_ids)
    if not res:
        result.error("分配用户失败")
    return result.success("分配用户成功")

