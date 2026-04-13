from pydantic import BaseModel, Field
from enum import Enum


# ========== Задание 6.2 ==========
class UserBase(BaseModel):
    """Базовая модель пользователя"""
    username: str = Field(..., min_length=3, max_length=50)


class User(UserBase):
    """Модель для регистрации (с открытым паролем)"""
    password: str = Field(..., min_length=4)


class UserInDB(UserBase):
    """Модель для хранения в БД (с хешем пароля)"""
    hashed_password: str


# ========== Задание 6.4, 6.5 ==========
class UserLogin(BaseModel):
    """Модель для входа"""
    username: str
    password: str


class Token(BaseModel):
    """Модель JWT токена"""
    access_token: str
    token_type: str = "bearer"


# ========== Задание 7.1 ==========
class UserRole(str, Enum):
    """Роли пользователей"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class UserWithRole(UserBase):
    """Модель пользователя с ролью"""
    role: UserRole = UserRole.USER


class UserInDBWithRole(UserWithRole):
    """Модель для хранения в БД с ролью и хешем пароля"""
    hashed_password: str


# ========== Задание 8.1 ==========
class UserRegister(BaseModel):
    """Модель для регистрации в SQLite"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4)