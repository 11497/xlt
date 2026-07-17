from typing import List

from fastapi import APIRouter, Depends, Query

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


@router.get("/role/{role_id}/knowledge_bases")
async def get_knowledge_base_by_role(
        role_id: int,
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数")
):
    """
    按角色分页查询关联的知识库
    :param role_id: 角色ID
    :param page: 页码，默认1
    :param page_size: 每页条数，默认10，最大100
    :return: 分页知识库列表及总数
    """
    result = Result()

    knowledge_bases, total = RoleKnowledgeBaseCRUD.get_page_knowledge_base_by_role(
        role_id=role_id,
        page=page,
        page_size=page_size
    )
    return result.success(msg="查询成功", data={
        "list": knowledge_bases,
        "total": total,
        "page": page,
        "page_size": page_size
    })


@router.get("/knowledge_base/{knowledge_base_id}/roles")
async def get_roles_by_knowledge_base(
        knowledge_base_id: int,
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数")
):
    """
    按知识库分页查询关联的角色
    :param knowledge_base_id: 知识库ID
    :param page: 页码，默认1
    :param page_size: 每页条数，默认10，最大100
    :return: 分页角色列表及总数
    """
    result = Result()

    roles, total = RoleKnowledgeBaseCRUD.get_page_roles_by_knowledge_base(
        knowledge_base_id=knowledge_base_id,
        page=page,
        page_size=page_size
    )
    return result.success(msg="查询成功", data={
        "list": roles,
        "total": total,
        "page": page,
        "page_size": page_size
    })


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
