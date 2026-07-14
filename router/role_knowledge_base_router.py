from typing import List

from fastapi import APIRouter, Depends

from authentication.user_auth import require_admin
from crud.role_knowledge_base_crud import RoleKnowledgeBaseCRUD
from model.result import Result
from model.user_model import User

router = APIRouter(prefix="/api/role_knowledge_base", tags=["role_knowledge_base"])

@router.post("/assign")
async def batch_assign_role_to_knowledge_base(
        knowledge_base_id: int,
        role_ids: List[int],
        _admin: User = Depends(require_admin)):
    """
    批量为知识库分配角色
    :param knowledge_base_id: 知识库ID
    :param role_ids: 角色ID列表
    :param _admin: 管理员用户对象
    :return: 分配结果
    """
    result = Result()

    # 删除role_ids中已经分配给角色的用户
    new_role_ids = []
    assigned_role_ids = RoleKnowledgeBaseCRUD.get_roles_by_knowledge_base(knowledge_base_id)
    for role_id in role_ids:
        if role_id not in assigned_role_ids:
            new_role_ids.append(role_id)

    res = RoleKnowledgeBaseCRUD.batch_assign_roles_to_knowledge_base(knowledge_base_id, new_role_ids)
    if not res:
        result.error(msg="分配角色失败")
    return result.success(msg="分配角色成功")


@router.delete("/remove")
async def batch_remove_roles_from_knowledge_base(
        knowledge_base_id: int,
        role_ids: List[int],
        _admin: User = Depends(require_admin)):
    """
    批量从指定知识库中删除角色
    :param knowledge_base_id: 知识库ID
    :param role_ids: 角色ID列表
    :param _admin: 管理员用户对象
    :return: 删除结果
    """
    result = Result()
    res = RoleKnowledgeBaseCRUD.batch_remove_roles_from_knowledge_base(knowledge_base_id, role_ids)
    if not res:
        result.error(msg="删除角色失败")
    return result.success(msg="删除角色成功")


@router.get("/roles_by_knowledge_base/{knowledge_base_id}")
async def get_roles_by_knowledge_base(
        knowledge_base_id: int,
        _admin: User = Depends(require_admin)):
    """
    获取指定知识库的所有角色ID
    :param knowledge_base_id: 知识库ID
    :param _admin: 管理员用户对象
    :return: 角色ID列表
    """
    result = Result()
    role_ids = RoleKnowledgeBaseCRUD.get_roles_by_knowledge_base(knowledge_base_id)
    return result.success(data=role_ids)


@router.get("/knowledge_base_by_role/{role_id}")
async def get_knowledge_base_by_role(
        role_id: int,
        _admin: User = Depends(require_admin)):
    """
    获取指定角色的所有知识库ID
    :param role_id: 角色ID
    :param _admin: 管理员用户对象
    :return: 知识库ID列表
    """
    result = Result()
    knowledge_base_ids = RoleKnowledgeBaseCRUD.get_knowledge_base_by_role(role_id)
    return result.success(data=knowledge_base_ids)


@router.post("/assign_single")
async def assign_knowledge_base_to_role(
        role_id: int,
        knowledge_base_id: int,
        _admin: User = Depends(require_admin)):
    """
    为指定角色分配知识库
    :param role_id: 角色ID
    :param knowledge_base_id: 知识库ID
    :param _admin: 管理员用户对象
    :return: 分配结果
    """
    result = Result()
    res = RoleKnowledgeBaseCRUD.assign_knowledge_base_to_role(role_id, knowledge_base_id)
    if not res:
        result.error(msg="分配知识库失败")
    return result.success(msg="分配知识库成功")


@router.delete("/remove_single")
async def remove_knowledge_base_from_role(
        role_id: int,
        knowledge_base_id: int,
        _admin: User = Depends(require_admin)):
    """
    从指定角色中移除单个知识库
    :param role_id: 角色ID
    :param knowledge_base_id: 知识库ID
    :param _admin: 管理员用户对象
    :return: 移除结果
    """
    result = Result()
    res = RoleKnowledgeBaseCRUD.remove_knowledge_base_from_role(role_id, knowledge_base_id)
    if not res:
        result.error(msg="移除知识库失败")
    return result.success(msg="移除知识库成功")


@router.delete("/by_role/{role_id}")
async def delete_by_role(role_id: int, _admin: User = Depends(require_admin)):
    """
    删除指定角色的所有知识库关联关系
    :param role_id: 角色ID
    :param _admin: 管理员用户对象
    :return: 删除结果
    """
    result = Result()
    res = RoleKnowledgeBaseCRUD.delete_by_role(role_id)
    if not res:
        result.error(msg="删除角色关联关系失败")
    return result.success(msg="删除角色关联关系成功")


@router.delete("/by_knowledge_base/{knowledge_base_id}")
async def delete_by_knowledge_base(
        knowledge_base_id: int,
        _admin: User = Depends(require_admin)):
    """
    删除指定知识库的所有角色关联关系
    :param knowledge_base_id: 知识库ID
    :param _admin: 管理员用户对象
    :return: 删除结果
    """
    result = Result()
    res = RoleKnowledgeBaseCRUD.delete_by_knowledge_base(knowledge_base_id)
    if not res:
        result.error(msg="删除知识库关联关系失败")
    return result.success(msg="删除知识库关联关系成功")
