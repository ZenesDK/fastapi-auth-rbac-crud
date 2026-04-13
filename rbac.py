from functools import wraps
from typing import List

from fastapi import HTTPException, status, Depends
from security import get_current_user_from_jwt, fake_users_db, get_user_from_fake_db


# Определение разрешений для ролей
ROLE_PERMISSIONS = {
    "admin": ["create", "read", "update", "delete"],
    "user": ["read", "update"],
    "guest": ["read"],
}


def get_current_user_with_role(username: str = Depends(get_current_user_from_jwt)) -> dict:
    """Получение текущего пользователя с его ролью"""
    user = get_user_from_fake_db(username)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


def require_permissions(required_permissions: List[str]):
    """
    Декоратор для проверки разрешений пользователя (на основе роли)
    
    Использование:
        @require_permissions(["read", "update"])
        async def my_endpoint(...)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Ищем current_user в kwargs (передаётся через Depends)
            current_user = kwargs.get("current_user")
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authentication required",
                )
            
            user_role = current_user.get("role", "guest")
            user_permissions = ROLE_PERMISSIONS.get(user_role, [])
            
            # Проверка наличия всех требуемых разрешений
            has_permissions = all(
                perm in user_permissions for perm in required_permissions
            )
            
            if not has_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {required_permissions}, User role: {user_role}",
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(allowed_roles: List[str]):
    """
    Декоратор для проверки роли пользователя (упрощённая версия)
    
    Использование:
        @require_role(["admin"])
        async def admin_only_endpoint(...)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authentication required",
                )
            
            user_role = current_user.get("role", "guest")
            
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {allowed_roles}, Your role: {user_role}",
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator