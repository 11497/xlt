from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form

from authentication.user_auth import require_admin, require_current_user
from crud.document_crud import DocumentCRUD
from crud.knowledge_base_crud import KnowledgeBaseCRUD
from model.document_model import Document
from model.result import Result
from model.user_model import User
from util.oss_util import OSSUtil
from config.file_config import ALLOWED_FILE_TYPES, MAX_FILE_SIZE, EXPIRES

router = APIRouter(prefix="/api/document", tags=["document"])


async def validate_file(file: UploadFile) -> Optional[str]:
    """
    验证文件类型和大小
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


@router.post("/upload")
async def upload_document(
        knowledge_base_id: int = Form(...),
        file: UploadFile = File(...),
        _admin: User = Depends(require_admin)
):
    """上传文档"""
    result = Result()

    # 验证知识库是否存在
    knowledge_base = KnowledgeBaseCRUD.get_by_id(knowledge_base_id)
    if not knowledge_base:
        return result.error(msg="知识库不存在")

    # 验证文件
    error_msg = await validate_file(file)
    if error_msg:
        return result.error(msg=error_msg)

    # 生成OSS存储路径
    storage_path = f"knowledge_base/{knowledge_base_id}/{file.filename}"

    # 读取文件内容
    content = await file.read()

    # 上传到OSS
    try:
        async with OSSUtil() as oss_client:
            await oss_client.upload_file(storage_path, content)
    except Exception as e:
        return result.error(msg=f"文件上传失败：{str(e)}")

    # 获取当前时间
    from datetime import datetime
    now = datetime.now()

    # 保存到数据库
    document = Document(
        knowledge_base_id=knowledge_base_id,
        filename=file.filename,
        storage_path=storage_path,
        create_time=now,
        update_time=now
    )
    document_id = DocumentCRUD.create(document)

    return result.success(msg="上传成功", data={"id": document_id, "filename": file.filename})


@router.put("/update")
async def update_document(
        document_id: int = Form(...),
        file: UploadFile = File(...),
        _admin: User = Depends(require_admin)
):
    """修改文档"""
    result = Result()

    # 查询文档是否存在
    document = DocumentCRUD.get_by_id(document_id)
    if not document:
        return result.error(msg="文档不存在")

    # 验证文件
    error_msg = await validate_file(file)
    if error_msg:
        return result.error(msg=error_msg)

    # 生成新的OSS存储路径
    storage_path = f"knowledge_base/{document.knowledge_base_id}/{file.filename}"

    # 读取文件内容
    content = await file.read()

    # 上传到OSS（覆盖旧文件）
    try:
        async with OSSUtil() as oss_client:
            await oss_client.update_file(storage_path, content)
    except Exception as e:
        return result.error(msg=f"文件修改失败：{str(e)}")

    # 更新数据库记录
    DocumentCRUD.update_filename(document_id, file.filename)
    DocumentCRUD.update_storage_path(document_id, storage_path)

    return result.success(msg="修改成功", data={"id": document_id, "filename": file.filename})


@router.get("/download/{document_id}")
async def download_document(
        document_id: int,
        _user: User = Depends(require_current_user)
):
    """下载文档（生成预签名URL）"""
    result = Result()

    # 查询文档是否存在
    document = DocumentCRUD.get_by_id(document_id)
    if not document:
        return result.error(msg="文档不存在")

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


@router.delete("/{document_id}")
async def delete_document(
        document_id: int,
        _admin: User = Depends(require_admin)
):
    """删除文档"""
    result = Result()

    # 查询文档是否存在
    document = DocumentCRUD.get_by_id(document_id)
    if not document:
        return result.error(msg="文档不存在")

    # 从OSS删除文件
    try:
        async with OSSUtil() as oss_client:
            await oss_client.delete_file(document.storage_path)
    except Exception as e:
        return result.error(msg=f"文件删除失败：{str(e)}")

    # 从数据库删除记录
    delete_result = DocumentCRUD.delete(document_id)
    if not delete_result:
        return result.error(msg="数据库记录删除失败")

    return result.success(msg="删除成功")


@router.get("/knowledge_base/{knowledge_base_id}")
async def get_documents_by_knowledge_base(
        knowledge_base_id: int,
        _user: User = Depends(require_current_user)
):
    """根据知识库ID查询所有文档"""
    result = Result()

    # 验证知识库是否存在
    knowledge_base = KnowledgeBaseCRUD.get_by_id(knowledge_base_id)
    if not knowledge_base:
        return result.error(msg="知识库不存在")

    documents = DocumentCRUD.get_by_knowledge_base_id(knowledge_base_id)
    return result.success(msg="查询成功", data=documents)


@router.get("/{document_id}")
async def get_document_by_id(
        document_id: int,
        _user: User = Depends(require_current_user)
):
    """根据ID查询单个文档"""
    result = Result()

    document = DocumentCRUD.get_by_id(document_id)
    if not document:
        return result.error(msg="文档不存在")
    return result.success(msg="查询成功", data=document)