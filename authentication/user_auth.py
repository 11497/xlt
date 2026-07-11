from fastapi import Depends, HTTPException, status

from authentication.authentication import get_current_user, oauth2_scheme
from crud.user_crud import UserCRUD


def require_admin(token: str = Depends(oauth2_scheme)):
    """
    依赖函数：验证当前用户是否为管理员
    :return: 执行操作的管理员
    """
    current_user_data = get_current_user(token)
    admin = UserCRUD.get_by_id(current_user_data["user_id"])

    if not admin or admin.is_admin == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可以执行此操作，您没有权限执行此操作"
        )

    return admin


def require_current_user(token: str = Depends(oauth2_scheme)):
    """
    依赖函数：获取当前登录用户
    :return: 当前登录用户
    """
    current_user_data = get_current_user(token)
    user = UserCRUD.get_by_id(current_user_data["user_id"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户未登录或不存在"
        )

    return user
