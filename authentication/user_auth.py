from fastapi import Depends, HTTPException, status

from authentication.authentication import get_current_user
from model.user_model import User


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    依赖函数：验证当前用户是否为管理员
    :return: 执行操作的管理员
    """
    if current_user.is_admin == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可以执行此操作，您没有权限执行此操作"
        )

    return current_user


def require_current_user(current_user: User = Depends(get_current_user)) -> User:
    """
    依赖函数：获取当前登录用户
    :return: 当前登录用户
    """
    return current_user
