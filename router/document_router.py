import json
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, Response, status as http_status

from authentication.user_auth import require_current_user, require_admin
from config.file_config import ALLOWED_FILE_TYPES, MAX_FILE_SIZE, EXPIRES
from crud.document_crud import DocumentCRUD
from crud.document_task_crud import DocumentTaskCRUD
from crud.knowledge_base_crud import KnowledgeBaseCRUD
from crud.user_knowledge_base_crud import UserKnowledgeBaseCRUD
from model.document_model import Document
from model.document_task_model import DocumentTask
from model.result import Result
from model.user_model import User
from util.db_util import get_connection
from util.oss_util import OSSUtil

router = APIRouter(prefix="/api/document", tags=["document"])


async def validate_file(file: UploadFile) -> Optional[str]:
    """
    验证文件类型和大小
    :param file: 上传的文件对象
    :return: 验证失败时返回错误信息，成功返回None
    """
    if not file.filename:
        return "文件名不能为空"

    # 获取文件扩展名
    file_ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""

    # 验证文件类型
    if file_ext not in ALLOWED_FILE_TYPES:
        return f"不支持的文件类型，仅支持：{', '.join(ALLOWED_FILE_TYPES.keys())}"

    # 验证文件大小
    content = await file.read()
    await file.seek(0)  # 重置文件指针

    if len(content) > MAX_FILE_SIZE:
        return f"文件大小超过限制，最大支持{MAX_FILE_SIZE // (1024 * 1024)}MB"

    if len(content) == 0:
        return "文件内容不能为空"

    return None


def _build_object_key(knowledge_base_id: int, filename: str) -> str:
    """
    生成 OSS 对象 key：UUID 保证唯一，避免同名覆盖；文件名仅用于控制台辨认。
    :param knowledge_base_id: 知识库ID
    :param filename: 原始文件名
    :return: OSS 对象 key
    """
    return f"knowledge_base/{knowledge_base_id}/{uuid4().hex}_{filename}"


def _create_document_and_task(
        knowledge_base_id: int,
        filename: str,
        object_key: str
) -> int:
    """
    原子创建文档记录（pending）和索引任务，单事务提交。
    :param knowledge_base_id: 知识库ID
    :param filename: 原始文件名
    :param object_key: OSS 对象 key
    :return: 文档ID
    :raises: 事务失败时抛出异常（由调用方补偿删除 OSS 对象）
    """
    payload = json.dumps({"object_key": object_key, "filename": filename}, ensure_ascii=False)
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO document (knowledge_base_id, filename, storage_path, status) "
                "VALUES (%s, %s, %s, 'pending')",
                (knowledge_base_id, filename, object_key)
            )
            document_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO document_task (task_type, document_id, knowledge_base_id, status, payload) "
                "VALUES ('index', %s, %s, 'pending', %s)",
                (document_id, knowledge_base_id, payload)
            )
            return document_id
        finally:
            cursor.close()


@router.post("/upload", status_code=http_status.HTTP_202_ACCEPTED)
async def upload_document(
        knowledge_base_id: int = Form(...),
        file: UploadFile = File(...),
        user: User = Depends(require_current_user)
):
    """
    上传文档到知识库（异步索引）
    :param knowledge_base_id: 知识库ID
    :param file: 上传的文件对象
    :param user: 当前用户对象
    :return: 上传结果，status 为 pending（待后台 Worker 索引）
    """
    result = Result()

    # 验证知识库是否存在
    knowledge_base = KnowledgeBaseCRUD.get_by_id(knowledge_base_id)
    if not knowledge_base:
        return result.error(msg="知识库不存在")
    if user.is_admin == 0 and not UserKnowledgeBaseCRUD.has_write_permission(user.id, knowledge_base_id):
        return result.error(msg="用户没有权限修改该知识库")

    # 验证文件
    error_msg = await validate_file(file)
    if error_msg:
        return result.error(msg=error_msg)

    # 生成 OSS 对象 key（UUID，避免同名覆盖）
    object_key = _build_object_key(knowledge_base_id, file.filename)

    # 读取文件内容并上传到 OSS
    content = await file.read()
    try:
        async with OSSUtil() as oss_client:
            await oss_client.upload_file(object_key, content)
    except Exception as e:
        return result.error(msg=f"文件上传失败：{str(e)}")

    # 原子创建文档记录 + 索引任务（单事务）
    try:
        document_id = _create_document_and_task(knowledge_base_id, file.filename, object_key)
    except Exception as e:
        # 事务失败：补偿删除刚上传的 OSS 对象，避免孤儿文件
        try:
            async with OSSUtil() as oss_client:
                await oss_client.delete_file(object_key)
        except Exception as cleanup_e:
            print(f"[ERROR] 清理孤儿 OSS 对象失败：{object_key} -> {cleanup_e}")
        return result.error(msg=f"保存文档记录失败：{str(e)}")

    return result.success(
        msg="上传成功，正在后台索引",
        data={
            "id": document_id,
            "filename": file.filename,
            "status": "pending"
        }
    )


@router.get("/download/{document_id}")
async def download_document(
        document_id: int,
        user: User = Depends(require_current_user)
):
    """
    下载文档（生成预签名URL）
    :param document_id: 文档ID
    :param user: 当前用户对象
    :return: 下载链接文档对象
    """
    result = Result()

    # 查询文档是否存在
    document = DocumentCRUD.get_by_id(document_id)
    if not document:
        return result.error(msg="文档不存在")

    # 验证用户是否有权限访问该知识库
    if user.is_admin == 0:
        if not UserKnowledgeBaseCRUD.has_read_permission(user.id, document.knowledge_base_id):
            return result.error(msg="用户没有权限访问该知识库")

    # 生成预签名URL用于下载
    try:
        async with OSSUtil() as oss_client:
            url_result = await oss_client.generate_presigned_url(document.storage_path, expires=EXPIRES)

            return result.success(
                msg="下载链接生成成功",
                data={
                    "filename": document.filename,
                    "download_url": url_result["url"],
                    "expires_in": url_result["expires"]
                }
            )
    except Exception as e:
        return result.error(msg=f"下载链接生成失败：{str(e)}")


@router.get("/status/{document_id}")
async def get_document_status(
        document_id: int,
        user: User = Depends(require_current_user)
):
    """
    查询文档索引状态（前端轮询用）
    :param document_id: 文档ID
    :param user: 当前用户对象
    :return: 文档状态信息
    """
    result = Result()

    document = DocumentCRUD.get_by_id(document_id)
    if not document:
        return result.error(msg="文档不存在")

    if user.is_admin == 0 and not UserKnowledgeBaseCRUD.has_read_permission(user.id, document.knowledge_base_id):
        return result.error(msg="用户没有权限访问该知识库")

    return result.success(msg="查询成功", data={
        "id": document.id,
        "status": document.status,
        "error_message": document.error_message,
        "retry_count": document.retry_count,
        "chunk_count": document.chunk_count
    })


@router.post("/reindex/{document_id}")
async def reindex_document(
        document_id: int,
        user: User = Depends(require_current_user)
):
    """
    重新索引文档（用于 failed 或需重建索引的文档）
    :param document_id: 文档ID
    :param user: 当前用户对象
    :return: 重新索引任务提交结果
    """
    result = Result()

    document = DocumentCRUD.get_by_id(document_id)
    if not document:
        return result.error(msg="文档不存在")
    if user.is_admin == 0 and not UserKnowledgeBaseCRUD.has_write_permission(user.id, document.knowledge_base_id):
        return result.error(msg="用户没有权限修改该知识库")

    # 检查是否有进行中的任务，避免重复入队
    existing = DocumentTaskCRUD.get_by_document_id(document_id, task_type="index")
    if existing and any(t.status in ("pending", "processing") for t in existing):
        return result.error(msg="该文档已有索引任务进行中，请稍后")

    # 重置文档状态并重新入队
    DocumentCRUD.update_status(
        document_id, "pending",
        error_message=None,
        retry_count=0,
        chunk_count=None
    )
    payload = json.dumps({"object_key": document.storage_path, "filename": document.filename}, ensure_ascii=False)
    task = DocumentTask(
        task_type="index",
        document_id=document_id,
        knowledge_base_id=document.knowledge_base_id,
        payload=payload
    )
    DocumentTaskCRUD.create(task)

    return result.success(msg="已重新提交索引任务", data={
        "id": document_id,
        "status": "pending"
    })


@router.delete("/{document_id}")
async def delete_document(
        document_id: int,
        user: User = Depends(require_current_user)
):
    """
    删除文档（异步：OSS/Chroma/ES/MySQL 四端清理由 Worker 执行）
    :param document_id: 文档ID
    :param user: 当前用户对象
    :return: 删除结果（异步提交）
    """
    result = Result()

    # 查询文档是否存在
    document = DocumentCRUD.get_by_id(document_id)
    if not document:
        return result.error(msg="文档不存在")
    if user.is_admin == 0 and not UserKnowledgeBaseCRUD.has_write_permission(user.id, document.knowledge_base_id):
        return result.error(msg="用户没有权限修改该知识库")

    # 若已在删除中，避免重复入队
    if document.status == "deleting":
        return result.error(msg="该文档正在删除中，请稍后")

    # 原子：标记文档 deleting + 入队删除任务
    payload = json.dumps({"object_key": document.storage_path, "filename": document.filename}, ensure_ascii=False)
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE document SET status = 'deleting', update_time = NOW() WHERE id = %s",
                    (document_id,)
                )
                cursor.execute(
                    "INSERT INTO document_task (task_type, document_id, knowledge_base_id, status, payload) "
                    "VALUES ('delete', %s, %s, 'pending', %s)",
                    (document_id, document.knowledge_base_id, payload)
                )
            finally:
                cursor.close()
    except Exception as e:
        return result.error(msg=f"提交删除任务失败：{str(e)}")

    return result.success(msg="删除任务已提交，正在清理", data={
        "id": document_id,
        "status": "deleting"
    })


@router.get("/knowledge_base/{knowledge_base_id}")
async def get_documents_by_knowledge_base(
        knowledge_base_id: int,
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数"),
        user: User = Depends(require_current_user)
):
    """
    按知识库分页查询文档
    :param knowledge_base_id: 知识库ID
    :param page: 页码，默认1
    :param page_size: 每页条数，默认10，最大100
    :param user: 当前用户对象
    :return: 分页文档列表及总数
    """
    result = Result()

    if not KnowledgeBaseCRUD.get_by_id(knowledge_base_id):
        return result.error(msg="知识库不存在")
    if user.is_admin == 0 and not UserKnowledgeBaseCRUD.has_read_permission(user.id, knowledge_base_id):
        return result.error(msg="用户没有权限访问该知识库")

    documents, total = DocumentCRUD.get_page_by_knowledge_base(
        knowledge_base_id=knowledge_base_id,
        page=page,
        page_size=page_size
    )
    return result.success(msg="查询成功", data={
        "list": documents,
        "total": total,
        "page": page,
        "page_size": page_size
    })


@router.get("/{document_id}")
async def get_document_by_id(
        document_id: int,
        user: User = Depends(require_current_user)
):
    """
    根据ID查询单个文档
    :param document_id: 文档ID
    :param user: 当前用户对象
    :return: 文档对象
    """
    result = Result()

    # 验证文档是否存在
    document = DocumentCRUD.get_by_id(document_id)
    if not document:
        return result.error(msg="文档不存在")

    if user.is_admin == 0 and not UserKnowledgeBaseCRUD.has_read_permission(user.id, document.knowledge_base_id):
        return result.error(msg="用户没有权限访问该知识库")
    return result.success(msg="查询成功", data=document)
