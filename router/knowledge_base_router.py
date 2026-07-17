from fastapi import APIRouter, Depends

from ai.chroma_service import ChromaService
from authentication.user_auth import require_admin, require_current_user
from crud.knowledge_base_crud import KnowledgeBaseCRUD
from crud.role_knowledge_base_crud import RoleKnowledgeBaseCRUD
from model.result import Result
from model.knowledge_base_model import KnowledgeBase
from model.user_model import User

router = APIRouter(prefix="/api/knowledge_base", tags=["knowledge_base"])

@router.post("")
async def create_knowledge_base(knowledge_base: KnowledgeBase,
                                _admin: User = Depends(require_admin)):
    """
    创建知识库
    :param knowledge_base: 知识库对象
    :param _admin: 管理员用户对象
    :return: 创建结果和新知识库对象
    """
    result = Result()

    # 检查是否已存在同名知识库
    all_kbs = KnowledgeBaseCRUD.get_all()
    for kb in all_kbs:
        if kb.name == knowledge_base.name:
            return result.error(msg="已存在同名知识库")

    knowledge_base_id = KnowledgeBaseCRUD.create(knowledge_base)
    if knowledge_base_id is None:
        return result.error(msg="创建知识库失败")
    return result.success(msg="创建知识库成功", data={"id": knowledge_base_id})

@router.get("/all")
async def get_all_knowledge_bases(_admin: User = Depends(require_admin)):
    """
    查询所有知识库
    :param _admin: 管理员用户对象
    :return: 知识库列表
    """
    result = Result()

    knowledge_bases = KnowledgeBaseCRUD.get_all()
    return result.success(msg="查询所有知识库成功", data=knowledge_bases)

@router.put("")
async def update_knowledge_base(knowledge_base: KnowledgeBase,
                                _admin: User = Depends(require_admin)):
    """
    更新知识库
    :param knowledge_base: 知识库对象
    :param _admin: 管理员用户对象
    :return: 更新结果
    """
    result = Result()

    update_result = KnowledgeBaseCRUD.update(knowledge_base)
    if not update_result:
        return result.error(msg="更新知识库失败")
    return result.success(msg="更新知识库成功")

@router.delete("")
async def delete_knowledge_base(id: int, _admin: User = Depends(require_admin)):
    """
    删除知识库
    :param id: 知识库ID
    :param _admin: 管理员用户对象
    :return: 删除结果
    """
    result = Result()

    # 验证目标知识库是否有绑定的角色
    roles = RoleKnowledgeBaseCRUD.get_roles_by_knowledge_base(id)
    if roles:
        return result.error(msg="知识库下有绑定的角色，不能删除")

    delete_result = KnowledgeBaseCRUD.delete(id)
    if not delete_result:
        return result.error(msg="删除知识库失败")

    # 从chroma删除向量
    chroma_service = ChromaService()
    chroma_service.delete_knowledge_base(id)

    return result.success(msg="删除知识库成功")
