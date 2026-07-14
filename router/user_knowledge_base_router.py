from fastapi import APIRouter, Depends

from authentication.user_auth import require_current_user, require_admin
from crud.user_knowledge_base_crud import UserKnowledgeBaseCRUD
from model.result import Result
from model.user_model import User

router = APIRouter(prefix="/user_knowledge_base", tags=["user_knowledge_base"])


@router.get("/knowledge_bases")
async def get_knowledge_bases(user: User = Depends(require_current_user)):
    """
    查询当前用户所有可访问的知识库ID
    :param user: 当前用户对象
    :return: 知识库ID列表
    """
    result = Result()

    knowledge_bases = UserKnowledgeBaseCRUD.get_knowledge_bases_by_user(user.id)
    return result.success(msg="查询成功", data=knowledge_bases)

@router.get("/user/{user_id}")
async def get_knowledge_bases_by_user(
        user_id: int,
        _admin: User = Depends(require_admin)):
    """
    根据用户ID查询其所有可访问的知识库ID
    :param user_id: 用户ID
    :param _admin: 管理员用户对象
    :return: 知识库ID列表
    """
    result = Result()

    knowledge_bases = UserKnowledgeBaseCRUD.get_knowledge_bases_by_user(user_id)
    return result.success(msg="查询成功", data=knowledge_bases)

@router.get("/knowledge_bases/{knowledge_base_id}")
async def get_users_by_knowledge_base(
        knowledge_base_id: int,
        _admin: User = Depends(require_admin)):
    """
    根据知识库ID查询所有可访问该知识库的用户ID
    :param knowledge_base_id: 知识库ID
    :param _admin: 管理员用户对象
    :return: 用户ID列表
    """
    result = Result()

    users = UserKnowledgeBaseCRUD.get_users_by_knowledge_base(knowledge_base_id)
    return result.success(msg="查询成功", data=users)