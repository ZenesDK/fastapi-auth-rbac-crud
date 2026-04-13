import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

# ========== Настройки ==========
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "mysecretkey")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

# Passlib для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Basic для заданий 6.1, 6.2
security_basic = HTTPBasic()

# HTTP Bearer для JWT (задания 6.4, 6.5)
security_bearer = HTTPBearer(auto_error=False)


# ========== Хеширование паролей ==========
def hash_password(password: str) -> str:
    """Хеширование пароля с помощью bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


# ========== JWT функции ==========
def create_jwt_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_jwt_token(token: str) -> dict:
    """Декодирование и проверка JWT токена"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_from_jwt(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> str:
    """Получение username из JWT токена (зависимость)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_jwt_token(token)
    username = payload.get("sub")
    
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    return username


# ========== Задание 6.1: базовая аутентификация ==========
def auth_user_basic(credentials: HTTPBasicCredentials = Depends(security_basic)) -> dict:
    """
    Проверка базовой аутентификации (задание 6.1)
    Возвращает словарь с данными пользователя при успехе
    """
    correct_username = "admin"
    correct_password = "secret"
    
    # secrets.compare_digest защищает от тайминг-атак
    username_match = secrets.compare_digest(credentials.username, correct_username)
    password_match = secrets.compare_digest(credentials.password, correct_password)
    
    if not (username_match and password_match):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return {"username": credentials.username}


# ========== Задание 6.2: расширенная аутентификация ==========
# In-memory база данных для заданий 6.2, 6.4, 6.5, 7.1
fake_users_db: dict[str, dict] = {}


def get_user_from_fake_db(username: str) -> Optional[dict]:
    """Поиск пользователя в in-memory БД"""
    return fake_users_db.get(username)


def save_user_to_fake_db(username: str, hashed_password: str, role: str = "user") -> None:
    """Сохранение пользователя в in-memory БД"""
    fake_users_db[username] = {
        "username": username,
        "hashed_password": hashed_password,
        "role": role,
    }


def auth_user_advanced(credentials: HTTPBasicCredentials = Depends(security_basic)) -> dict:
    """
    Расширенная аутентификация (задание 6.2)
    - Поиск пользователя в БД
    - Проверка хеша пароля
    - Защита от тайминг-атак
    """
    user = get_user_from_fake_db(credentials.username)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # secrets.compare_digest для username (хотя тут и так сравнение)
    if not secrets.compare_digest(credentials.username, user["username"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # Проверка пароля через passlib
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return user