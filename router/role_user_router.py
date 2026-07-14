from typing import List

from fastapi import APIRouter, Depends

from authentication.user_auth import require_admin, require_current_user
from crud.role_user_crud import RoleUserCRUD
from model.result import Result
from model.user_model import User

router = APIRouter(prefix="/api/role_user", tags=["role_user"])

@router.post("/assign")
async def batch_assign_users_to_role(
        role_id: int,
        user_ids: List[int],
        _admin: User = Depends(require_admin)):
    """
    批量为角色分配用户
    :param role_id: 角色ID
    :param user_ids: 用户ID列表
    :param _admin: 管理员用户对象
    :return: 分配结果
    """
    result = Result()

    # 删除user_ids中已经分配给角色的用户
    new_user_ids = []
    assigned_user_ids = RoleUserCRUD.get_users_by_role(role_id)
    for user_id in user_ids:
        if user_id not in assigned_user_ids:
            new_user_ids.append(user_id)

    res = RoleUserCRUD.batch_assign_users_to_role(role_id, new_user_ids)
    if not res:
        result.error(msg="分配用户失败")
    return result.success(msg="分配用户成功")


@router.delete("/remove")
async def batch_remove_users_from_role(
        role_id: int,
        user_ids: List[int],
        _admin: User = Depends(require_admin)):
    """
    批量从指定角色中移除用户
    :param role_id: 角色ID
    :param user_ids: 用户ID列表
    :param _admin: 管理员用户对象
    :return: 移除结果
    """
    result = Result()
    res = RoleUserCRUD.batch_remove_users_from_role(role_id, user_ids)
    if not res:
        result.error(msg="移除用户失败")
    return result.success(msg="移除用户成功")


@router.get("/users_by_role/{role_id}")
async def get_users_by_role(
        role_id: int,
        _user: User = Depends(require_current_user)):
    """
    获取指定角色下的所有用户ID
    :param role_id: 角色ID
    :param _user: 当前用户对象
    :return: 用户ID列表
    """
    result = Result()
    user_ids = RoleUserCRUD.get_users_by_role(role_id)
    return result.success(data=user_ids)


@router.get("/roles_by_user/{user_id}")
async def get_roles_by_user(
        user_id: int,
        _admin: User = Depends(require_admin)):
    """
    获取指定用户的所有角色ID（管理员）
    :param user_id: 用户ID
    :param _admin: 管理员用户对象
    :return: 角色ID列表
    """
    result = Result()
    role_ids = RoleUserCRUD.get_roles_by_user(user_id)
    return result.success(data=role_ids)


@router.get("/my_roles")
async def get_my_roles(current_user: User = Depends(require_current_user)):
    """
    获取当前用户的所有角色ID（普通用户）
    :param current_user: 当前用户对象
    :return: 角色ID列表
    """
    result = Result()
    role_ids = RoleUserCRUD.get_roles_by_user(current_user.id)
    return result.success(data=role_ids)


@router.post("/assign_single")
async def assign_user_to_role(
        role_id: int,
        user_id: int,
        _admin: User = Depends(require_admin)):
    """
    分配单个用户到指定角色
    :param role_id: 角色ID
    :param user_id: 用户ID
    :param _admin: 管理员用户对象
    :return: 分配结果
    """
    result = Result()
    res = RoleUserCRUD.assign_user_to_role(role_id, user_id)
    if not res:
        result.error(msg="分配用户失败")
    return result.success(msg="分配用户成功")


@router.delete("/remove_single")
async def remove_user_from_role(
        role_id: int,
        user_id: int,
        _admin: User = Depends(require_admin)):
    """
    从指定角色中移除单个用户
    :param role_id: 角色ID
    :param user_id: 用户ID
    :param _admin: 管理员用户对象
    :return: 移除结果
    """
    result = Result()
    res = RoleUserCRUD.remove_user_from_role(role_id, user_id)
    if not res:
        result.error(msg="移除用户失败")
    return result.success(msg="移除用户成功")


@router.delete("/by_role/{role_id}")
async def delete_by_role(
        role_id: int,
        _admin: User = Depends(require_admin)):
    """
    删除指定角色的所有用户关联关系
    :param role_id: 角色ID
    :param _admin: 管理员用户对象
    :return: 删除结果
    """
    result = Result()
    res = RoleUserCRUD.delete_by_role(role_id)
    if not res:
        result.error(msg="删除角色关联关系失败")
    return result.success(msg="删除角色关联关系成功")


@router.delete("/by_user/{user_id}")
async def delete_by_user(
        user_id: int,
        _admin: User = Depends(require_admin)):
    """
    删除指定用户的所有角色关联关系
    :param user_id: 用户ID
    :param _admin: 管理员用户对象
    :return: 删除结果
    """
    result = Result()
    res = RoleUserCRUD.delete_by_user(user_id)
    if not res:
        result.error(msg="删除用户关联关系失败")
    return result.success(msg="删除用户关联关系成功")
