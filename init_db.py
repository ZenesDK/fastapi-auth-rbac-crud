"""Запустите этот файл один раз для создания таблицы users"""

from database import init_db

if __name__ == "__main__":
    init_db()
    print("База данных готова к работе!")