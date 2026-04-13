from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Создаём limiter с определением клиента по IP
limiter = Limiter(key_func=get_remote_address, default_limits=[])


def setup_rate_limiter(app: FastAPI):
    """Настройка rate limiter для приложения"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Функции-декораторы для удобного использования в эндпоинтах
def register_limit():
    """Лимит для регистрации: 1 запрос в минуту"""
    return limiter.limit("1/minute")


def login_limit():
    """Лимит для логина: 5 запросов в минуту"""
    return limiter.limit("5/minute")