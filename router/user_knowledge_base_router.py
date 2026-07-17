from fastapi import APIRouter, Depends, Query

from authentication.user_auth import require_current_user, require_admin
from crud.user_knowledge_base_crud import UserKnowledgeBaseCRUD
from model.result import Result
from model.user_model import User

router = APIRouter(prefix="/user_knowledge_base", tags=["user_knowledge_base"])


@router.get("/knowledge_bases")
async def get_knowledge_bases(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数"),
        user: User = Depends(require_current_user)):
    """
    分页查询当前用户所有可访问的知识库ID
    :param page: 页码
    :param page_size: 每页条数
    :param user: 当前用户对象
    :return: 分页结果
    """
    result = Result()

    data = UserKnowledgeBaseCRUD.get_knowledge_bases_by_user_paged(user.id, page, page_size)
    return result.success(msg="查询成功", data=data)


@router.get("/user/{user_id}")
async def get_knowledge_bases_by_user(
        user_id: int,
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数"),
        _admin: User = Depends(require_admin)):
    """
    根据用户ID分页查询其所有可访问的知识库ID
    :param user_id: 用户ID
    :param page: 页码
    :param page_size: 每页条数
    :param _admin: 管理员用户对象
    :return: 分页结果
    """
    result = Result()

    data = UserKnowledgeBaseCRUD.get_knowledge_bases_by_user_paged(user_id, page, page_size)
    return result.success(msg="查询成功", data=data)


@router.get("/knowledge_bases/{knowledge_base_id}")
async def get_users_by_knowledge_base(
        knowledge_base_id: int,
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数"),
        _admin: User = Depends(require_admin)):
    """
    根据知识库ID分页查询所有可访问该知识库的用户ID
    :param knowledge_base_id: 知识库ID
    :param page: 页码
    :param page_size: 每页条数
    :param _admin: 管理员用户对象
    :return: 分页结果
    """
    result = Result()

    data = UserKnowledgeBaseCRUD.get_users_by_knowledge_base_paged(knowledge_base_id, page, page_size)
    return result.success(msg="查询成功", data=data)