from fastapi import APIRouter, Depends, Query

from authentication.user_auth import require_current_user, require_admin
from crud.message_crud import MessageCRUD
from crud.session_crud import SessionCRUD
from model.result import Result
from model.session_model import Session
from model.user_model import User

router = APIRouter(prefix="/api/session", tags=["session"])


@router.post("")
async def create_session(
        session: Session,
        user: User = Depends(require_current_user)):
    """
    创建会话，需要获取当前用户id作为session_id
    :param session: 会话对象
    :param user: 当前用户对象
    :return: 会话对象
    """
    result = Result()
    
    # 设置session的用户ID为当前用户ID
    session.user_id = user.id
    
    session_id = SessionCRUD.create(session)
    created_session = SessionCRUD.get_by_id(session_id)
    
    return result.success(msg="会话创建成功", data=created_session)


@router.get("/all")
async def get_all_session(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数"),
        _admin: User = Depends(require_admin)
):
    """
    分页查询所有会话
    :param page: 页码，默认1
    :param page_size: 每页条数，默认10，最大100
    :param _admin: 管理员用户对象
    :return: 分页会话列表及总数
    """
    result = Result()

    sessions, total = SessionCRUD.get_page(page=page, page_size=page_size)
    return result.success(msg="查询成功", data={
        "list": sessions,
        "total": total,
        "page": page,
        "page_size": page_size
    })


@router.get("/user")
async def get_sessions_by_user_id(user_id: int, current_user: User = Depends(require_current_user)):
    """根据用户id获取会话列表"""
    result = Result()

    # 验证当前用户是否有权限访问该用户的会话列表
    if current_user.id != user_id and current_user.is_admin == 0:
        return result.error(msg="无权访问其他用户的会话列表")

    sessions = SessionCRUD.get_by_user_id(user_id)

    return result.success(msg="查询成功", data=sessions)


@router.get("/user/page")
async def get_user_session_page(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数"),
        user: User = Depends(require_current_user)
):
    """
    分页查询当前用户的会话
    :param page: 页码，默认1
    :param page_size: 每页条数，默认10，最大100
    :param user: 当前用户对象
    :return: 分页会话列表及总数
    """
    result = Result()

    sessions, total = SessionCRUD.get_page(page=page, page_size=page_size, user_id=user.id)
    return result.success(msg="查询成功", data={
        "list": sessions,
        "total": total,
        "page": page,
        "page_size": page_size
    })


@router.get("/{session_id}")
async def get_session(
        session_id: int,
        user: User = Depends(require_current_user)):
    """
    根据id查询单个会话
    :param session_id: 会话ID
    :param user: 当前用户对象
    :return: 会话对象
    """
    result = Result()
    
    session = SessionCRUD.get_by_id(session_id)
    
    # 验证该会话是否属于当前用户
    if not session or (session.user_id != user.id and user.is_admin == 0):
        return result.error(msg="会话不存在或无权访问")
    
    return result.success(msg="查询成功", data=session)


@router.delete("/{session_id}")
async def delete_session(
        session_id: int,
        user: User = Depends(require_current_user)):
    """
    根据id删除会话
    :param session_id: 会话ID
    :param user: 当前用户对象
    :return: 删除结果
    """
    result = Result()
    
    session = SessionCRUD.get_by_id(session_id)
    
    # 验证该会话是否属于当前用户
    if not session or (session.user_id != user.id and user.is_admin == 0):
        return result.error(msg="会话不存在或无权删除")

    # 删除会话下的所有消息
    MessageCRUD.delete_by_session_id(session_id)
    
    delete_result = SessionCRUD.delete(session_id)
    if not delete_result:
        return result.error(msg="删除失败")
    
    return result.success(msg="删除成功")


@router.put("/name")
async def update_session_name(
        session_id: int,
        name: str,
        user: User = Depends(require_current_user)):
    """
    更新会话名称
    :param session_id: 会话ID
    :param name: 会话名称
    :param user: 当前用户对象
    :return: 更新结果
    """
    result = Result()
    
    session = SessionCRUD.get_by_id(session_id)
    
    # 验证该会话是否属于当前用户
    if not session or (session.user_id != user.id and user.is_admin == 0):
        return result.error(msg="会话不存在或无权修改")
    
    update_result = SessionCRUD.update_session_name(session_id, name)
    if not update_result:
        return result.error(msg="更新失败")
    
    updated_session = SessionCRUD.get_by_id(session_id)
    
    return result.success(msg="更新成功", data=updated_session)
