import pymysql
from fastapi import APIRouter, Depends, Query

from authentication.user_auth import require_admin, require_current_user
from crud.knowledge_base_crud import KnowledgeBaseCRUD
from crud.user_knowledge_base_crud import UserKnowledgeBaseCRUD
from model.knowledge_base_model import KnowledgeBase
from model.result import Result
from model.user_model import User
from util.db_util import get_connection
from util.soft_delete_name import tombstone_unique_name

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
async def get_all_knowledge_bases(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数"),
        _admin: User = Depends(require_admin)
):
    """
    分页查询所有知识库
    :param page: 页码，默认1
    :param page_size: 每页条数，默认10，最大100
    :param _admin: 管理员用户对象
    :return: 分页知识库列表及总数
    """
    result = Result()

    knowledge_bases, total = KnowledgeBaseCRUD.get_page(page=page, page_size=page_size)
    return result.success(msg="查询成功", data={
        "list": knowledge_bases,
        "total": total,
        "page": page,
        "page_size": page_size
    })

@router.get("/search/{content}")
async def search_knowledge_base(
        content: str,
        _admin: User = Depends(require_admin),
):
    """
    管理员根据ID或名字查询知识库
    :param content: 查询内容
    :param _admin: 管理员用户对象
    :return: 查询结果
    """
    result = Result()

    knowledge_bases = KnowledgeBaseCRUD.search(content)
    return result.success(msg="查询成功", data=knowledge_bases)

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
    删除知识库（异步：Chroma/ES 索引清理由 Worker 执行，MySQL 逻辑删除，OSS 保留）
    :param id: 知识库ID
    :param _admin: 管理员用户对象
    :return: 删除结果
    """
    result = Result()

    # 异步删除：入队 delete_kb 任务；Worker 清理 Chroma/ES 后统一逻辑删除文档和知识库。
    from crud.document_task_crud import DocumentTaskCRUD
    from model.document_task_model import DocumentTask
    import json

    payload = json.dumps({"kb_id": id}, ensure_ascii=False)
    task = DocumentTask(
        task_type="delete_kb",
        document_id=0,  # 无具体文档，占位
        knowledge_base_id=id,
        payload=payload
    )

    # 提交任务时先锁定知识库并进入逻辑删除态，阻止并发上传/删除文档；
    # Worker 清理 Chroma/ES 成功后再统一将文档置为最终逻辑删除。
    try:
        with get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            try:
                cursor.execute(
                    "SELECT id, name FROM knowledge_base WHERE id = %s AND is_deleted = 0 FOR UPDATE",
                    (id,)
                )
                knowledge_base_row = cursor.fetchone()
                if knowledge_base_row is None:
                    return result.error(msg="知识库不存在或已有删除任务")
                cursor.execute(
                    "SELECT rkb.role_id FROM role_knowledge_base rkb "
                    "JOIN role r ON r.id = rkb.role_id AND r.is_deleted = 0 "
                    "WHERE rkb.knowledge_base_id = %s AND rkb.is_deleted = 0 FOR UPDATE",
                    (id,),
                )
                if cursor.fetchone() is not None:
                    return result.error(msg="知识库下有绑定的角色，不能删除")
                cursor.execute(
                    "SELECT id, status FROM document WHERE knowledge_base_id = %s AND is_deleted = 0 FOR UPDATE",
                    (id,)
                )
                documents = cursor.fetchall()
                if any(document["status"] == "deleting" for document in documents):
                    return result.error(msg="知识库下仍有文档删除任务进行中，请稍后再删除")
                cursor.execute(
                    "SELECT id, status, task_type FROM document_task WHERE knowledge_base_id = %s FOR UPDATE",
                    (id,)
                )
                tasks = cursor.fetchall()
                if any(task["status"] in ("pending", "processing") and task["task_type"] != "delete_kb" for task in tasks):
                    return result.error(msg="该知识库下仍有文档任务进行中，请稍后再删除")
                cursor.execute(
                    "SELECT id FROM document_task WHERE knowledge_base_id = %s AND task_type = 'delete_kb' AND status IN ('pending', 'processing') FOR UPDATE",
                    (id,)
                )
                if cursor.fetchone() is not None:
                    return result.error(msg="该知识库已有删除任务进行中")
                cursor.execute(
                    "UPDATE document SET status = 'deleting', update_time = NOW() "
                    "WHERE knowledge_base_id = %s AND is_deleted = 0 AND status <> 'deleting'",
                    (id,)
                )
                cursor.execute(
                    "UPDATE knowledge_base SET name = %s, is_deleted = 1, deleted_at = NOW() "
                    "WHERE id = %s AND is_deleted = 0",
                    (tombstone_unique_name(knowledge_base_row["name"]), id),
                )
                cursor.execute(
                    "INSERT INTO document_task (task_type, document_id, knowledge_base_id, status, payload) "
                    "VALUES ('delete_kb', %s, %s, 'pending', %s)",
                    (task.document_id, task.knowledge_base_id, task.payload)
                )
            finally:
                cursor.close()
    except Exception as e:
        return result.error(msg=f"提交删除任务失败：{str(e)}")

    return result.success(msg="删除任务已提交，正在清理知识库检索数据；文件将保留")

@router.get("/{id}")
async def get_by_id(id: int, user: User = Depends(require_current_user)):
    """
    根据ID查询知识库
    :param id: 知识库ID
    :param user: 当前用户对象
    :return: 知识库对象
    """
    result = Result()

    # 检查知识库是否存在
    knowledge_base = KnowledgeBaseCRUD.get_by_id(id)
    if not knowledge_base:
        return result.error(msg="知识库不存在")

    # 检查当前用户是否有访问权限
    if user.is_admin == 0:
        if not UserKnowledgeBaseCRUD.has_read_permission(user.id, knowledge_base.id):
            return result.error(msg="您没有权限访问该知识库")

    return result.success(msg="查询成功", data=knowledge_base)
