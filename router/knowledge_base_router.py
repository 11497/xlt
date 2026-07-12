from fastapi import APIRouter, Depends

from authentication.user_auth import require_admin, require_current_user
from crud.knowledge_base_crud import KnowledgeBaseCRUD
from model.result import Result
from model.knowledge_base_model import KnowledgeBase
from model.user_model import User

router = APIRouter(prefix="/api/knowledge_base", tags=["knowledge_base"])

@router.post("")
async def create_knowledge_base(knowledge_base: KnowledgeBase, _admin: User = Depends(require_admin)):
    """创建知识库"""
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
async def get_all_knowledge_bases(_user: User = Depends(require_current_user)):
    """查询所有知识库（开放给所有用户）"""
    result = Result()

    knowledge_bases = KnowledgeBaseCRUD.get_all()
    return result.success(msg="查询所有知识库成功", data=knowledge_bases)

@router.put("")
async def update_knowledge_base(knowledge_base: KnowledgeBase, _admin: User = Depends(require_admin)):
    """更新知识库"""
    result = Result()

    update_result = KnowledgeBaseCRUD.update(knowledge_base)
    if not update_result:
        return result.error(msg="更新知识库失败")
    return result.success(msg="更新知识库成功")

@router.delete("")
async def delete_knowledge_base(id: int, _admin: User = Depends(require_admin)):
    """删除知识库"""
    # TODO 删除前验证kb对应的role_kb是否存在
    result = Result()

    delete_result = KnowledgeBaseCRUD.delete(id)
    if not delete_result:
        return result.error(msg="删除知识库失败")
    return result.success(msg="删除知识库成功")
