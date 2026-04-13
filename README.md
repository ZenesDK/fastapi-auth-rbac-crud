# Контрольная работа №3 - FastAPI

## 📋 Описание

Реализация серверного приложения на FastAPI с аутентификацией, авторизацией (RBAC), работой с базой данных SQLite и защитой документации. Включает все задания контрольной работы №3.

## 🚀 Быстрый старт

### Требования
- Python 3.10+
- pip (менеджер пакетов)

### Установка и запуск

1. **Клонирование репозитория**
```bash
git clone <your-repo-url>
cd fastapi-auth-rbac-crud
```

2. **Создание виртуального окружения**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. **Установка зависимостей**
```bash
pip install -r requirements.txt
```

4. **Настройка окружения**
```bash
cp .env.example .env
# При необходимости отредактируйте .env файл
```

5. **Инициализация базы данных**
```bash
python init_db.py
```

6. **Запуск приложения**
```bash
uvicorn app:app --reload
```

Приложение будет доступно по адресу: http://localhost:8000

## 📚 Документация API

- **Swagger UI**: http://localhost:8000/docs (только в DEV режиме)
- **Логин для документации**: `admin` / `secret`

## 🧪 Тестирование эндпоинтов

### Задание 6.1 - Базовая аутентификация
```bash
# Успешный вход
curl -u admin:secret http://localhost:8000/login_basic

# Неверные данные (должен вернуть 401)
curl -u admin:wrongpass http://localhost:8000/login_basic
```
**Ожидаемый ответ (200 OK):**
```json
{"message": "You got my secret, welcome"}
```

### Задание 6.2 - Регистрация и логин с хешированием
```bash
# Регистрация нового пользователя
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","password":"newpass123"}'

# Логин (Basic Auth)
curl -u newuser:newpass123 http://localhost:8000/login
```
**Ожидаемые ответы:**
- Регистрация (201 Created): `{"message": "New user created"}`
- Логин (200 OK): `{"message": "Welcome, newuser!"}`

### Задание 6.4 - JWT аутентификация
```bash
# Получение JWT токена
curl -X POST http://localhost:8000/login_jwt \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}'

# Сохраните полученный токен: {"access_token": "eyJ...", "token_type": "bearer"}

# Доступ к защищённому ресурсу
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:8000/protected_resource
```
**Ожидаемые ответы:**
- Логин (200 OK): `{"access_token": "eyJ...", "token_type": "bearer"}`
- Защищённый ресурс (200 OK): `{"message": "Access granted for user: testuser"}`

### Задание 6.5 - Rate Limiting
```bash
# Регистрация с лимитом (1 запрос в минуту)
curl -X POST http://localhost:8000/register_advanced \
  -H "Content-Type: application/json" \
  -d '{"username":"limited_user","password":"pass123"}'

# Логин с лимитом (5 запросов в минуту)
curl -X POST http://localhost:8000/login_advanced \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}'
```
**Ожидаемый ответ при превышении лимита (429 Too Many Requests):**
```json
{"detail": "Rate limit exceeded: ..."}
```

### Задание 7.1 - RBAC (Управление доступом на основе ролей)

#### Доступные роли:
- **admin** (пароль: `adminpass`) - полные права
- **user** (пароль: `testpass`) - чтение и обновление
- **guest** (пароль: `guestpass`) - только чтение

#### Тестирование эндпоинтов:

```bash
# 1. Получите токен для нужной роли
curl -X POST http://localhost:8000/login_jwt \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"adminpass"}'

# 2. Используйте токен для доступа к эндпоинтам

# Только для администратора
curl -H "Authorization: Bearer ADMIN_TOKEN" \
  http://localhost:8000/admin_only

# Для администратора и пользователя
curl -H "Authorization: Bearer USER_TOKEN" \
  http://localhost:8000/user_only

# Публичный доступ (без токена)
curl http://localhost:8000/public_info

# Разрешения на основе ролей
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/read_resource        # ✅ есть у всех

curl -X POST -H "Authorization: Bearer ADMIN_TOKEN" \
  http://localhost:8000/create_resource      # ✅ только admin

curl -X PUT -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/update_resource      # ✅ admin и user

curl -X DELETE -H "Authorization: Bearer ADMIN_TOKEN" \
  http://localhost:8000/delete_resource      # ✅ только admin
```

**Ожидаемые ответы:**
- Доступ разрешён (200 OK): Информационное сообщение
- Доступ запрещён (403 Forbidden): `{"detail": "Insufficient permissions..."}`

### Задание 8.1 - SQLite база данных

```bash
# Регистрация пользователя в SQLite
curl -X POST http://localhost:8000/register_sqlite \
  -H "Content-Type: application/json" \
  -d '{"username":"sql_user","password":"sqlpass"}'

# Просмотр всех пользователей (пароли не отображаются)
curl http://localhost:8000/users_sqlite

# Попытка регистрации существующего пользователя
curl -X POST http://localhost:8000/register_sqlite \
  -H "Content-Type: application/json" \
  -d '{"username":"sql_user","password":"anotherpass"}'
```
**Ожидаемые ответы:**
- Успешная регистрация (201 Created): `{"message": "User registered successfully!"}`
- Список пользователей (200 OK): `{"users": [{"id": 1, "username": "sql_user"}]}`
- Конфликт (409 Conflict): `{"detail": "User already exists"}`

## 🗄️ Хранилища данных

В приложении используются два типа хранилищ:

### 1. In-memory база данных (`fake_users_db`)
- **Используется в заданиях:** 6.2, 6.4, 6.5, 7.1
- **Хранение:** Оперативная память (данные теряются при перезапуске)
- **Эндпоинты:** `/register`, `/login_jwt`, `/register_advanced`, `/login_advanced`, RBAC-эндпоинты

### 2. SQLite база данных (`database.sqlite`)
- **Используется в заданиях:** 8.1
- **Хранение:** Файл (данные сохраняются)
- **Эндпоинты:** `/register_sqlite`, `/users_sqlite`

### Тестовые пользователи (создаются автоматически при запуске)

| Username | Password | Role  |
|----------|----------|-------|
| admin    | adminpass| admin |
| testuser | testpass | user  |
| guest    | guestpass| guest |

## 🔧 Переменные окружения

Создайте файл `.env` на основе `.env.example`:

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `MODE` | Режим работы (DEV/PROD) | DEV |
| `DOCS_USER` | Логин для доступа к документации | admin |
| `DOCS_PASSWORD` | Пароль для доступа к документации | secret |
| `JWT_SECRET_KEY` | Секретный ключ для JWT | mysecretkey... |
| `JWT_ALGORITHM` | Алгоритм JWT | HS256 |
| `JWT_EXPIRE_MINUTES` | Время жизни токена (минуты) | 30 |

## 🐛 Отладка

### Просмотр всех in-memory пользователей
```bash
curl http://localhost:8000/debug/users
```

### Прямой доступ к SQLite
```bash
sqlite3 database.sqlite
.tables
SELECT * FROM users;
.quit
```

## 📁 Структура проекта

```
fastapi-auth-rbac-crud/
├── app.py                 # Основное приложение FastAPI
├── models.py              # Pydantic модели
├── database.py            # Работа с SQLite
├── security.py            # JWT, хеширование, аутентификация
├── rbac.py                # RBAC декораторы
├── rate_limiter.py        # Rate limiting
├── init_db.py             # Инициализация SQLite
├── requirements.txt       # Зависимости
├── .env.example           # Пример переменных окружения
├── .gitignore             # Игнорируемые файлы
├── README.md              # Этот файл
└── database.sqlite        # SQLite БД (создаётся автоматически)
```

## ✅ Выполненные задания

- [x] **Задание 6.1** - Базовая аутентификация
- [x] **Задание 6.2** - Регистрация и логин с хешированием паролей
- [x] **Задание 6.3** - Управление документацией (DEV/PROD режимы)
- [x] **Задание 6.4** - JWT аутентификация
- [x] **Задание 6.5** - Rate limiting (ограничение запросов)
- [x] **Задание 7.1** - RBAC (управление доступом на основе ролей)
- [x] **Задание 8.1** - SQLite база данных

## ⚠️ Примечания

1. **Безопасность**: В учебных целях пароли в SQLite хранятся в открытом виде (согласно условию задания 8.1). В реальных проектах нужно всегда использовать хеширование.

2. **JWT токены**: Срок жизни токена - 30 минут (настраивается через `.env`).

3. **Rate Limiting**: 
   - `/register_advanced`: 1 запрос в минуту
   - `/login_advanced`: 5 запросов в минуту

4. **PROD режим**: При установке `MODE=PROD` документация API полностью отключается.