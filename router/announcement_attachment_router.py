from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import Response
from typing import Optional
import urllib.parse

from authentication.user_auth import require_admin, require_current_user
from crud.announcement_attachment_crud import AnnouncementAttachmentCRUD
from crud.announcement_crud import AnnouncementCRUD
from model.announcement_attachment_model import AnnouncementAttachment
from model.result import Result
from model.user_model import User
from util.oss_util import OSSUtil

router = APIRouter(prefix="/api/announcement_attachment", tags=["announcement_attachment"])

# 支持的文件类型和最大文件大小（10MB）
ALLOWED_FILE_TYPES = {
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


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
async def upload_attachment(
    announcement_id: int = Form(...),
    file: UploadFile = File(...),
    _admin: User = Depends(require_admin)
):
    """上传公告附件"""
    result = Result()
    
    # 验证公告是否存在
    announcement = AnnouncementCRUD.get_by_id(announcement_id)
    if not announcement:
        return result.error(msg="公告不存在")
    
    # 验证文件
    error_msg = await validate_file(file)
    if error_msg:
        return result.error(msg=error_msg)
    
    # 生成OSS存储路径
    storage_path = f"announcement/{announcement_id}/{file.filename}"
    
    # 读取文件内容
    content = await file.read()
    
    # 上传到OSS
    try:
        async with OSSUtil() as oss_client:
            await oss_client.upload_file(storage_path, content)
    except Exception as e:
        return result.error(msg=f"文件上传失败：{str(e)}")
    
    # 保存到数据库
    attachment = AnnouncementAttachment(
        announcement_id=announcement_id,
        filename=file.filename,
        storage_path=storage_path
    )
    attachment_id = AnnouncementAttachmentCRUD.create(attachment)
    
    return result.success(msg="上传成功", data={"id": attachment_id, "filename": file.filename})


@router.put("/update")
async def update_attachment(
    attachment_id: int = Form(...),
    file: UploadFile = File(...),
    _admin: User = Depends(require_admin)
):
    """修改公告附件"""
    result = Result()
    
    # 查询附件是否存在
    attachment = AnnouncementAttachmentCRUD.get_by_id(attachment_id)
    if not attachment:
        return result.error(msg="附件不存在")
    
    # 验证文件
    error_msg = await validate_file(file)
    if error_msg:
        return result.error(msg=error_msg)
    
    # 生成新的OSS存储路径
    storage_path = f"announcement/{attachment.announcement_id}/{file.filename}"
    
    # 读取文件内容
    content = await file.read()
    
    # 上传到OSS（覆盖旧文件）
    try:
        async with OSSUtil() as oss_client:
            await oss_client.update_file(storage_path, content)
    except Exception as e:
        return result.error(msg=f"文件修改失败：{str(e)}")
    
    # 更新数据库记录
    AnnouncementAttachmentCRUD.update_filename(attachment_id, file.filename)
    
    # 更新存储路径
    from db.db_connection import get_cursor
    with get_cursor() as cursor:
        cursor.execute(
            "UPDATE announcement_attachment SET storage_path = %s WHERE id = %s",
            (storage_path, attachment_id)
        )
    
    return result.success(msg="修改成功", data={"id": attachment_id, "filename": file.filename})


@router.get("/download/{attachment_id}")
async def download_attachment(
        attachment_id: int,
        _user: User = Depends(require_current_user)
):
    """下载公告附件（生成预签名URL）"""
    result = Result()

    # 查询附件是否存在
    attachment = AnnouncementAttachmentCRUD.get_by_id(attachment_id)
    if not attachment:
        return result.error(msg="附件不存在")

    # 生成预签名URL用于下载
    try:
        async with OSSUtil() as oss_client:
            url_result = await oss_client.generate_presigned_url(attachment.storage_path, expires=3600)

            return result.success(
                msg="下载链接生成成功",
                data={
                    "filename": attachment.filename,
                    "download_url": url_result["url"],
                    "expires_in": url_result["expires"]
                }
            )
    except Exception as e:
        return result.error(msg=f"下载链接生成失败：{str(e)}")


@router.get("/preview/{attachment_id}")
async def preview_attachment(
    attachment_id: int,
    _user: User = Depends(require_current_user)
):
    """预览公告附件（生成预签名URL）"""
    result = Result()
    
    # 查询附件是否存在
    attachment = AnnouncementAttachmentCRUD.get_by_id(attachment_id)
    if not attachment:
        return result.error(msg="附件不存在")
    
    # 生成预签名URL
    try:
        async with OSSUtil() as oss_client:
            url_result = await oss_client.generate_presigned_url(attachment.storage_path, expires=3600)
            
            return result.success(
                msg="预览链接生成成功",
                data={
                    "filename": attachment.filename,
                    "preview_url": url_result["url"],
                    "expires_in": url_result["expires"]
                }
            )
    except Exception as e:
        return result.error(msg=f"预览链接生成失败：{str(e)}")


@router.delete("/{attachment_id}")
async def delete_attachment(
    attachment_id: int,
    _admin: User = Depends(require_admin)
):
    """删除公告附件"""
    result = Result()
    
    # 查询附件是否存在
    attachment = AnnouncementAttachmentCRUD.get_by_id(attachment_id)
    if not attachment:
        return result.error(msg="附件不存在")
    
    # 从OSS删除文件
    try:
        async with OSSUtil() as oss_client:
            await oss_client.delete_file(attachment.storage_path)
    except Exception as e:
        return result.error(msg=f"文件删除失败：{str(e)}")
    
    # 从数据库删除记录
    delete_result = AnnouncementAttachmentCRUD.delete(attachment_id)
    if not delete_result:
        return result.error(msg="数据库记录删除失败")
    
    return result.success(msg="删除成功")


@router.get("/announcement/{announcement_id}")
async def get_attachments_by_announcement(
    announcement_id: int,
    _user: User = Depends(require_current_user)
):
    """根据公告ID查询所有附件"""
    result = Result()
    
    # 验证公告是否存在
    announcement = AnnouncementCRUD.get_by_id(announcement_id)
    if not announcement:
        return result.error(msg="公告不存在")
    
    attachments = AnnouncementAttachmentCRUD.get_by_announcement_id(announcement_id)
    return result.success(msg="查询成功", data=attachments)


@router.get("/{attachment_id}")
async def get_attachment_by_id(
    attachment_id: int,
    _user: User = Depends(require_current_user)
):
    """根据ID查询单个附件"""
    result = Result()
    
    attachment = AnnouncementAttachmentCRUD.get_by_id(attachment_id)
    if not attachment:
        return result.error(msg="附件不存在")
    return result.success(msg="查询成功", data=attachment)