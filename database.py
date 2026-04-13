import sqlite3
from contextlib import contextmanager

DB_NAME = "database.sqlite"


@contextmanager
def get_db_connection():
    """Контекстный менеджер для работы с БД"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Доступ по имени колонки
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Создание таблицы users (запускается один раз)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)
        print("Таблица users создана (или уже существует)")


def create_user(username: str, password: str) -> bool:
    """Создание пользователя в БД"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            return True
    except sqlite3.IntegrityError:
        return False  # Пользователь уже существует


def get_user_from_db(username: str):
    """Получение пользователя из БД по username"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None