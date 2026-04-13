import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from dotenv import load_dotenv

from models import (
    User, UserLogin, Token, UserWithRole, UserRole, UserRegister
)
from security import (
    security_basic, auth_user_basic, hash_password, verify_password,
    create_jwt_token, get_current_user_from_jwt, fake_users_db,
    save_user_to_fake_db, get_user_from_fake_db, auth_user_advanced,
    security_bearer
)
from rbac import (
    get_current_user_with_role, require_role, require_permissions,
    ROLE_PERMISSIONS
)
from rate_limiter import setup_rate_limiter, register_limit, login_limit
from database import init_db, create_user, get_user_from_db

load_dotenv()

MODE = os.getenv("MODE", "DEV")
DOCS_USER = os.getenv("DOCS_USER", "admin")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD", "secret")


# ========== Настройка lifespan ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup: инициализация БД и rate limiter
    init_db()
    setup_rate_limiter(app)
    
    # Создаём тестовых пользователей для заданий
    if "testuser" not in fake_users_db:
        save_user_to_fake_db("testuser", hash_password("testpass"), "user")
    if "admin" not in fake_users_db:
        save_user_to_fake_db("admin", hash_password("adminpass"), "admin")
    if "guest" not in fake_users_db:
        save_user_to_fake_db("guest", hash_password("guestpass"), "guest")
    
    yield
    # Shutdown: здесь можно закрыть соединения при необходимости


# ========== Создание приложения с учётом MODE ==========
if MODE == "PROD":
    # PROD режим: документация полностью отключена
    app = FastAPI(
        title="KR3 API",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan
    )
else:
    # DEV режим: документация с базовой аутентификацией
    app = FastAPI(
        title="KR3 API",
        lifespan=lifespan
    )


# ========== Защита документации в DEV режиме ==========
def check_docs_auth(credentials: HTTPBasicCredentials = Depends(security_basic)):
    """Проверка аутентификации для доступа к документации"""
    import secrets
    correct_username = DOCS_USER
    correct_password = DOCS_PASSWORD
    
    username_match = secrets.compare_digest(credentials.username, correct_username)
    password_match = secrets.compare_digest(credentials.password, correct_password)
    
    if not (username_match and password_match):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


# Переопределяем эндпоинты документации для DEV режима
if MODE == "DEV":
    # /docs - требует аутентификации
    @app.get("/docs", include_in_schema=False)
    async def get_docs(request: Request, _=Depends(check_docs_auth)):
        from fastapi.openapi.docs import get_swagger_ui_html
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Swagger UI",
        )
    
    # /openapi.json - требует аутентификации
    @app.get(app.openapi_url, include_in_schema=False)
    async def get_openapi(_=Depends(check_docs_auth)):
        return app.openapi()
    
    # /redoc - полностью скрыт
    app.redoc_url = None


# ========== Задание 6.1: базовая аутентификация ==========
@app.get("/login_basic")
async def login_basic(user: dict = Depends(auth_user_basic)):
    """GET /login_basic - проверка базовой аутентификации"""
    return {"message": "You got my secret, welcome"}


# ========== Задание 6.2: регистрация и логин с хешированием ==========
@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: User):
    """POST /register - регистрация нового пользователя"""
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    
    hashed = hash_password(user.password)
    save_user_to_fake_db(user.username, hashed, "user")
    
    return {"message": "New user created"}


@app.get("/login")
async def login_advanced(user: dict = Depends(auth_user_advanced)):
    """GET /login - вход с хешированием пароля"""
    return {"message": f"Welcome, {user['username']}!"}


# ========== Задание 6.4: JWT аутентификация ==========
@app.post("/login_jwt", response_model=Token)
async def login_jwt(user: UserLogin):
    """POST /login_jwt - вход с получением JWT токена"""
    # Проверяем существование пользователя
    db_user = get_user_from_fake_db(user.username)
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Проверяем пароль
    if not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization failed"
        )
    
    # Генерируем токен
    access_token = create_jwt_token(data={"sub": user.username})
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/protected_resource")
async def protected_resource(username: str = Depends(get_current_user_from_jwt)):
    """GET /protected_resource - защищённый ресурс (требует JWT)"""
    return {"message": f"Access granted for user: {username}"}


# ========== Задание 6.5: расширенная JWT с rate limiting ==========
@app.post("/register_advanced", status_code=status.HTTP_201_CREATED)
@register_limit()
async def register_advanced(request: Request, user: User):
    """POST /register_advanced - регистрация с rate limiting"""
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    
    hashed = hash_password(user.password)
    save_user_to_fake_db(user.username, hashed, "user")
    
    return {"message": "New user created"}


@app.post("/login_advanced", response_model=Token)
@login_limit()
async def login_advanced_jwt(request: Request, user: UserLogin):
    """POST /login_advanced - вход с JWT и rate limiting"""
    db_user = get_user_from_fake_db(user.username)
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization failed"
        )
    
    access_token = create_jwt_token(data={"sub": user.username})
    
    return {"access_token": access_token, "token_type": "bearer"}


# ========== Задание 7.1: RBAC (управление доступом на основе ролей) ==========
@app.get("/admin_only")
@require_role(["admin"])
async def admin_only_endpoint(current_user: dict = Depends(get_current_user_with_role)):
    """Только для администраторов"""
    return {
        "message": f"Welcome admin {current_user['username']}!",
        "your_permissions": ROLE_PERMISSIONS.get("admin", [])
    }


@app.get("/user_only")
@require_role(["admin", "user"])
async def user_only_endpoint(current_user: dict = Depends(get_current_user_with_role)):
    """Для администраторов и обычных пользователей"""
    return {
        "message": f"Welcome {current_user['username']}!",
        "your_role": current_user.get("role", "unknown"),
        "your_permissions": ROLE_PERMISSIONS.get(current_user.get("role", "guest"), [])
    }


@app.get("/public_info")
async def public_info():
    """Общедоступный эндпоинт (без аутентификации)"""
    return {"message": "This is public information for everyone!"}


@app.get("/read_resource")
@require_permissions(["read"])
async def read_resource(current_user: dict = Depends(get_current_user_with_role)):
    """Требует разрешение на чтение (есть у всех ролей)"""
    return {
        "message": f"{current_user['username']} is reading the resource",
        "role": current_user.get("role"),
        "permissions": ROLE_PERMISSIONS.get(current_user.get("role", "guest"), [])
    }


@app.post("/create_resource")
@require_permissions(["create"])
async def create_resource(current_user: dict = Depends(get_current_user_with_role)):
    """Требует разрешение на создание (только у admin)"""
    return {
        "message": f"{current_user['username']} created a new resource!",
        "role": current_user.get("role")
    }


@app.put("/update_resource")
@require_permissions(["update"])
async def update_resource(current_user: dict = Depends(get_current_user_with_role)):
    """Требует разрешение на обновление (admin и user)"""
    return {
        "message": f"{current_user['username']} updated the resource!",
        "role": current_user.get("role")
    }


@app.delete("/delete_resource")
@require_permissions(["delete"])
async def delete_resource(current_user: dict = Depends(get_current_user_with_role)):
    """Требует разрешение на удаление (только у admin)"""
    return {
        "message": f"{current_user['username']} deleted the resource!",
        "role": current_user.get("role")
    }


# ========== Задание 8.1: SQLite база данных ==========
@app.post("/register_sqlite", status_code=status.HTTP_201_CREATED)
async def register_sqlite(user: UserRegister):
    """POST /register_sqlite - регистрация в SQLite БД"""
    # Проверяем, существует ли пользователь
    existing_user = get_user_from_db(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    
    # Сохраняем пользователя (пока пароль в открытом виде, как требует задание)
    success = create_user(user.username, user.password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    
    return {"message": "User registered successfully!"}


@app.get("/users_sqlite")
async def get_all_users_sqlite():
    """Получение всех пользователей из SQLite (для проверки)"""
    from database import get_db_connection
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users")
        rows = cursor.fetchall()
        users = [dict(row) for row in rows]
    
    return {"users": users}


# ========== Корневой эндпоинт ==========
@app.get("/")
async def root():
    return {
        "message": "KR3 API",
        "mode": MODE,
        "available_endpoints": [
            "/login_basic (GET)",
            "/register (POST)",
            "/login (GET)",
            "/login_jwt (POST)",
            "/protected_resource (GET)",
            "/register_advanced (POST) - with rate limit",
            "/login_advanced (POST) - with rate limit",
            "/admin_only (GET) - RBAC",
            "/user_only (GET) - RBAC",
            "/public_info (GET)",
            "/read_resource (GET)",
            "/create_resource (POST)",
            "/update_resource (PUT)",
            "/delete_resource (DELETE)",
            "/register_sqlite (POST)",
            "/users_sqlite (GET)",
        ]
    }


# ========== Запуск ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)