from fastapi import APIRouter, Depends

from authentication.user_auth import require_admin, require_current_user
from crud.announcement_crud import AnnouncementCRUD
from model.announcement_model import Announcement
from model.result import Result
from model.user_model import User

router = APIRouter(prefix="/api/announcement", tags=["announcement"])


@router.post("")
def create_announcement(announcement: Announcement, _admin: User = Depends(require_admin)):
    """新增公告"""
    result = Result()

    announcement_id = AnnouncementCRUD.create(announcement)
    if announcement_id is None:
        return result.error(msg="新增公告失败")
    return result.success(msg="新增公告成功", data={"id": announcement_id})


@router.get("/all")
def get_all_announcements(_user: User = Depends(require_current_user)):
    """查看所有公告"""
    result = Result()

    announcements = AnnouncementCRUD.get_all()
    return result.success(msg="查询所有公告成功", data=announcements)


@router.get("/{id}")
def get_announcement_by_id(id: int, _user: User = Depends(require_current_user)):
    """根据id查询单个公告"""
    result = Result()

    announcement = AnnouncementCRUD.get_by_id(id)
    if not announcement:
        return result.error(msg="公告不存在")
    return result.success(msg="查询成功", data=announcement)


@router.put("")
def update_announcement(announcement: Announcement, _admin: User = Depends(require_admin)):
    """修改公告"""
    result = Result()

    update_result = AnnouncementCRUD.update(
        announcement_id=announcement.id,
        title=announcement.title,
        content=announcement.content,
        is_top=announcement.is_top
    )
    if not update_result:
        return result.error(msg="修改公告失败")
    return result.success(msg="修改公告成功")


@router.delete("")
def delete_announcements(ids: list[int], _admin: User = Depends(require_admin)):
    """批量删除公告"""
    result = Result()

    delete_result = AnnouncementCRUD.batch_delete(ids)
    if not delete_result:
        return result.error(msg="批量删除公告失败")
    return result.success(msg="批量删除成功")