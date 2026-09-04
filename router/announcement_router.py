from fastapi import APIRouter, Depends, Query
from fastapi.params import Body

from authentication.user_auth import require_admin, require_current_user
from crud.announcement_crud import AnnouncementCRUD
from model.announcement_model import Announcement
from model.result import Result
from model.user_model import User

router = APIRouter(prefix="/api/announcement", tags=["announcement"])


@router.post("")
async def create_announcement(announcement: Announcement,
                              _admin: User = Depends(require_admin)):
    """
    新增公告
    :param announcement: 新公告对象
    :param _admin: 管理员用户对象
    :return: 新增结果
    """
    result = Result()

    announcement_id = AnnouncementCRUD.create(announcement)
    if announcement_id is None:
        return result.error(msg="新增公告失败")
    return result.success(msg="新增公告成功", data={"id": announcement_id})


@router.get("/all")
async def get_all_announcements(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数"),
        _user: User = Depends(require_current_user)
):
    """
    分页查询所有公告
    :param page: 页码，默认1
    :param page_size: 每页条数，默认10，最大100
    :param _user: 当前用户对象
    :return: 分页公告列表及总数
    """
    result = Result()

    announcements, total = AnnouncementCRUD.get_page(page=page, page_size=page_size)
    return result.success(msg="查询成功", data={
        "list": announcements,
        "total": total,
        "page": page,
        "page_size": page_size
    })


@router.get("/recent")
async def get_recent_announcements(
        limit: int = Query(5, ge=1, le=10, description="返回条数"),
        _admin: User = Depends(require_admin)
):
    """查询最近发布的公告及公告总数，供管理首页展示。"""
    announcements, total = AnnouncementCRUD.get_recent(limit=limit)
    return Result().success(msg="查询成功", data={
        "list": announcements,
        "total": total
    })


@router.get("/{id}")
async def get_announcement_by_id(id: int, _user: User = Depends(require_current_user)):
    """
    根据id查询单个公告
    :param id: 公告ID
    :param _user: 当前用户对象
    :return: 公告对象
    """
    result = Result()

    announcement = AnnouncementCRUD.get_by_id(id)
    if not announcement:
        return result.error(msg="公告不存在")
    return result.success(msg="查询成功", data=announcement)


@router.put("")
async def update_announcement(announcement: Announcement,
                              _admin: User = Depends(require_admin)):
    """
    修改公告
    :param announcement: 修改公告对象
    :param _admin: 管理员用户对象
    :return: 修改结果
    """
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
async def delete_announcements(ids: list[int] = Body(..., alias="ids"),
                              _admin: User = Depends(require_admin)):
    """
    批量删除公告（公告与附件同事务逻辑删除，OSS 对象保留）
    :param ids: 公告ID列表
    :param _admin: 管理员用户对象
    :return: 删除结果
    """
    result = Result()

    # 公告与附件仅逻辑删除，OSS 对象保留用于留存。
    delete_result = AnnouncementCRUD.batch_delete_with_attachments(ids)
    if not delete_result:
        return result.error(msg="批量删除公告失败")
    return result.success(msg="批量删除成功，公告及附件已进入逻辑删除状态，文件保留")
