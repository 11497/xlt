from fastapi import APIRouter, Depends, Query

from authentication.user_auth import require_admin, require_current_user
from crud.role_crud import RoleCRUD
from crud.role_knowledge_base_crud import RoleKnowledgeBaseCRUD
from crud.role_user_crud import RoleUserCRUD
from model.result import Result
from model.role_model import Role
from model.user_model import User

router = APIRouter(prefix="/api/role", tags=["role"])

@router.post("")
async def create_role(role: Role, _admin: User = Depends(require_admin)):
    """
    创建角色
    :param role: 角色对象
    :param _admin: 管理员用户对象
    :return: 创建结果
    """
    result = Result()

    # 检查是否已存在同名角色
    role_exists = RoleCRUD.get_by_name(role.name)
    if role_exists is not None:
        return result.error(msg="已存在同名角色")

    role_id = RoleCRUD.create(role)
    if role_id is None:
        return result.error(msg="创建角色失败")
    return result.success(msg="创建角色成功")

@router.get("/all")
async def get_all_role(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数"),
        _admin: User = Depends(require_admin)
):
    """
    分页查询所有角色
    :param _admin: 管理员用户对象
    :param page: 页码，默认1
    :param page_size: 每页条数，默认10，最大100
    :return: 分页角色列表及总数
    """
    result = Result()

    roles, total = RoleCRUD.get_page(page=page, page_size=page_size)
    return result.success(msg="查询成功", data={
        "list": roles,
        "total": total,
        "page": page,
        "page_size": page_size
    })

@router.get("/name/{role_name}")
async def get_by_name(role_name: str, _admin: User = Depends(require_admin)):
    """
    根据角色名查询角色
    :param role_name: 角色名
    :param _admin: 管理员用户对象
    :return: 角色对象
    """
    result = Result()

    role = RoleCRUD.get_by_name(role_name)
    if role is None:
        return result.error(msg="角色不存在")
    return result.success(msg="查询角色成功", data=role)

@router.get("/id/{role_id}")
async def get_by_id(role_id: int, user: User = Depends(require_current_user)):
    """
    根据角色ID查询角色
    :param role_id: 角色ID
    :param user: 用户对象
    :return: 角色对象
    """
    result = Result()

    # 校验用户是否有权限查询该角色
    if user.is_admin == 0:
        roles = RoleUserCRUD.get_roles_by_user(user.id)
        if role_id not in roles:
            return result.error(msg="用户没有权限查询该角色")

    role = RoleCRUD.get_by_id(role_id)
    return result.success(msg="查询角色成功", data=role)

@router.get("/search/{content}")
async def search_role(content: str, _admin: User = Depends(require_admin)):
    """
    搜索角色
    :param content: 搜索内容（角色名或ID）
    :param _admin: 管理员用户对象
    :return: 角色对象列表
    """
    result = Result()

    roles = RoleCRUD.search(content)
    return result.success(msg="查询成功", data=roles)

@router.put("")
async def update(role: Role, _admin: User = Depends(require_admin)):
    """
    更新角色名
    :param role: 角色对象
    :param _admin: 管理员用户对象
    :return: 更新结果
    """
    result = Result()

    update_result = RoleCRUD.update_name(role.id, role.name)
    if not update_result:
        return result.error(msg="更新角色名失败")
    return result.success(msg="更新角色名成功")

@router.delete("")
async def delete(id: int, _admin: User = Depends(require_admin)):
    """
    删除角色
    :param id: 角色ID
    :param _admin: 管理员用户对象
    :return: 删除结果
    """
    result = Result()

    # 验证目标角色是否有绑定的用户和知识库
    users = RoleUserCRUD.get_users_by_role(id)
    if users:
        return result.error(msg="角色下有绑定的用户，不能删除")
    knowledge_bases = RoleKnowledgeBaseCRUD.get_knowledge_base_by_role(id)
    if knowledge_bases:
        return result.error(msg="角色下有绑定的知识库，不能删除")

    delete_result = RoleCRUD.delete(id)
    if not delete_result:
        return result.error(msg="删除角色失败")
    return result.success(msg="删除角色成功")
