from fastapi import APIRouter, Depends

from authentication.user_auth import require_admin
from crud.role_crud import RoleCRUD
from model.result import Result
from model.role_model import Role
from model.user_model import User

router = APIRouter(prefix="/api/role", tags=["role"])

@router.post("")
async def create_role(role: Role, admin: User = Depends(require_admin)):
    """创建角色"""
    result = Result()

    role_id = RoleCRUD.create(role)
    if role_id is None:
        return result.error(msg="创建角色失败")
    return result.success(msg="创建角色成功")

@router.get("/all")
async def get_all_role(admin: User = Depends(require_admin)):
    """查询所有角色"""
    result = Result()

    roles = RoleCRUD.get_all()
    return result.success(msg="查询所有角色成功", data=roles)

@router.get("/{role_name}")
async def get_by_name(role_name: str, admin: User = Depends(require_admin)):
    """根据角色名查询角色"""
    result = Result()

    role = RoleCRUD.get_by_name(role_name)
    if role is None:
        return result.error(msg="角色不存在")
    return result.success(msg="查询角色成功", data=role)

@router.put("")
async def update(role: Role, admin: User = Depends(require_admin)):
    """更新角色名"""
    result = Result()

    update_result = RoleCRUD.update_name(role.id, role.name)
    if not update_result:
        return result.error(msg="更新角色名失败")
    return result.success(msg="更新角色名成功")

@router.delete("")
async def delete(id: int, admin: User = Depends(require_admin)):
    """删除角色"""
    result = Result()

    delete_result = RoleCRUD.delete(id)
    if not delete_result:
        return result.error(msg="删除角色失败")
    return result.success(msg="删除角色成功")
