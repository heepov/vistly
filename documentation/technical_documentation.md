# 🔧 ТЕХНИЧЕСКАЯ ДОКУМЕНТАЦИЯ: Vistly Bot

> **Архитектура, API и руководство по развертыванию**

## 🎯 Обзор

Vistly Bot - это Telegram-бот для управления списками фильмов и сериалов. Проект построен на современном стеке технологий с акцентом на простоту и надежность.

## 🏗 Архитектура

### Технологический стек
- **Backend:** Python 3.8+ + aiogram 3.x
- **База данных:** PostgreSQL + Peewee ORM
- **HTTP клиент:** aiohttp
- **Конфигурация:** environs + dataclasses
- **Логирование:** стандартная библиотека logging

### Структура проекта
```
vistly_bot/
├── main.py                      # Точка входа
├── config/                      # Конфигурация
├── bot/                        # Основная логика бота
│   ├── features/               # Функциональные модули
│   ├── formater/              # Форматирование сообщений
│   ├── shared/                # Общие компоненты
│   ├── states/                # FSM состояния
│   └── utils/                 # Утилиты и локализация
├── database/                  # Слой работы с БД
├── models/                    # Бизнес-модели
└── requirements.txt           # Зависимости
```

## 📊 База данных

### Основные таблицы

#### user_profile
```sql
CREATE TABLE user_profile (
    id SERIAL PRIMARY KEY,
    tg_id BIGINT UNIQUE,
    username VARCHAR(255),
    name VARCHAR(255),
    language VARCHAR(10) DEFAULT 'en',
    added_db TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### entity
```sql
CREATE TABLE entity (
    id SERIAL PRIMARY KEY,
    src_id VARCHAR(255),
    kp_id VARCHAR(255),
    title VARCHAR(500) NOT NULL,
    type VARCHAR(50) DEFAULT 'movie',
    description TEXT,
    poster_url VARCHAR(1000),
    duration INTEGER,
    genres TEXT[],
    actors TEXT[],
    release_date DATE,
    year_start INTEGER,
    total_season INTEGER,
    added_db TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### user_entity
```sql
CREATE TABLE user_entity (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user_profile(id),
    entity_id INTEGER REFERENCES entity(id),
    status VARCHAR(50) DEFAULT 'planning',
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 10),
    current_season INTEGER,
    added_db TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### rating
```sql
CREATE TABLE rating (
    entity_id INTEGER REFERENCES entity(id),
    source VARCHAR(100),
    value FLOAT,
    max_value INTEGER,
    percent BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (entity_id, source)
);
```

### Индексы
```sql
CREATE INDEX idx_user_profile_tg_id ON user_profile(tg_id);
CREATE INDEX idx_entity_title ON entity(title);
CREATE INDEX idx_user_entity_user_id ON user_entity(user_id);
CREATE INDEX idx_user_entity_status ON user_entity(status);
```

## 🌐 API интеграции

### Kinopoisk.dev API
- **Base URL:** `https://kinopoiskapiunofficial.tech/api/v2.1/films`
- **Authentication:** X-API-KEY header
- **Rate Limits:** 1000 requests/day (бесплатный план)

#### Основные эндпоинты
- `GET /search-by-keyword` - поиск по ключевому слову
- `GET /films/{id}` - получение информации о фильме
- `GET /films/{id}/seasons` - получение информации о сезонах

### OMDB API
- **Base URL:** `http://www.omdbapi.com/`
- **Authentication:** apikey parameter
- **Rate Limits:** 1000 requests/day (бесплатный план)

#### Основные эндпоинты
- `GET /?apikey={key}&s={search}` - поиск по названию
- `GET /?apikey={key}&i={imdb_id}` - получение информации по IMDb ID

### Автоматический выбор API
```python
def detect_language_and_choose_api(query: str) -> SourceApi:
    """Определяет язык запроса и выбирает подходящий API"""
    if any(ord(char) > 127 for char in query):
        return SourceApi.KP  # Kinopoisk для кириллицы
    return SourceApi.OMDB   # OMDB для латиницы
```

## 🔧 Основные компоненты

### 1. Роутеры
```python
router = Router()
router.include_router(search_router)      # Поиск
router.include_router(user_list_router)   # Списки
router.include_router(profile_router)     # Профиль
router.include_router(dl_router)          # Deep Links
```

### 2. Обработчики команд
```python
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    # Обработка команды /start
    # Парсинг deep link аргументов
    # Создание/получение пользователя
    # Отправка приветственного сообщения

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    # Отправка справки с изображениями

@router.message(Command("list"))
async def cmd_list(message: types.Message):
    # Отображение пользовательского списка

@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    # Отображение профиля пользователя
```

### 3. Сервисы
```python
class UserService:
    @staticmethod
    def get_or_create_user(user: types.User, language: str = "en") -> Tuple[UserDB, bool]:
        """Получить или создать пользователя"""
        return UserDB.get_or_create(
            tg_id=user.id,
            defaults={
                "username": user.username,
                "name": user.full_name,
                "language": language
            }
        )

class SearchService:
    async def search_content(self, query: str, api_source: SourceApi) -> List[dict]:
        """Поиск контента через выбранный API"""
        if api_source == SourceApi.KP:
            return await self.kp_service.search(query)
        else:
            return await self.omdb_service.search(query)
```

## 🔄 Состояния (FSM)

### Определение состояний
```python
class MainMenuStates(StatesGroup):
    waiting_for_query = State()

class UserListStates(StatesGroup):
    waiting_for_ls_select_entity = State()
    waiting_for_ls_action = State()
    waiting_for_ls_rating = State()
    waiting_for_ls_season = State()
    waiting_for_ls_status = State()
    waiting_for_ls_delete = State()

class DeepLinkStates(StatesGroup):
    waiting_for_dl_action_entity = State()

class ProfileStates(StatesGroup):
    waiting_for_profile_action = State()
```

### Управление состояниями
```python
# Установка состояния
await state.set_state(MainMenuStates.waiting_for_query)

# Получение данных состояния
state_data = await state.get_data()
lang = state_data.get("lang", "en")

# Обновление данных состояния
await state.update_data(lang=lang, query=query)

# Очистка состояния
await state.clear()
```

## ⚙️ Конфигурация

### Структура конфигурации
```python
@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig
    omdb: OmdbConfig
    kp: KpConfig

@dataclass
class TgBot:
    token: str
    admin_ids: list[int]

@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str
    port: int = 5432
```

### Переменные окружения
```env
# Telegram Bot
BOT_TOKEN=your_telegram_bot_token
ADMINS=123456789,987654321

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_db_user
DB_PASS=your_db_password
DB_NAME=vistly_bot

# API Keys
OMDB_API_KEY=your_omdb_api_key
KP_API_KEY=your_kinopoisk_api_key
```

### Загрузка конфигурации
```python
def load_config(path: str = None) -> Config:
    env = Env()
    env.read_env(path)
    
    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=list(map(int, env.list("ADMINS")))
        ),
        db=DbConfig(
            host=env.str("DB_HOST"),
            password=env.str("DB_PASS"),
            user=env.str("DB_USER"),
            database=env.str("DB_NAME"),
            port=env.int("DB_PORT", 5432),
        ),
        omdb=OmdbConfig(api_key=env.str("OMDB_API_KEY")),
        kp=KpConfig(api_key=env.str("KP_API_KEY")),
    )
```

## 📝 Логирование

### Настройка логирования
```python
def setup_logger():
    """Настройка структурированного логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/bot.log'),
            logging.StreamHandler()
        ]
    )
    
    # Настройка логгеров для внешних библиотек
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
```

### Логирование действий
```python
logger = logging.getLogger(__name__)

async def log_user_action(user_id: int, action: str, details: dict = None):
    """Логирование действий пользователей"""
    log_data = {
        "user_id": user_id,
        "action": action,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    logger.info(f"User action: {log_data}")
```

## 🛡️ Обработка ошибок

### Глобальная обработка исключений
```python
async def global_exception_handler(update: types.Update, exception: Exception):
    """Глобальный обработчик исключений"""
    logger.error(f"Exception while handling update {update}: {exception}")
    
    # Отправка сообщения пользователю
    if update.message:
        await update.message.answer(
            get_string("error_message", "en"),
            reply_markup=get_menu_keyboard("en")
        )
```

### Обработка ошибок API
```python
async def handle_api_error(api_name: str, error: Exception) -> dict:
    """Обработка ошибок внешних API"""
    if isinstance(error, aiohttp.ClientError):
        logger.warning(f"Network error in {api_name}: {error}")
        return {"error": "network_error", "message": "Network connection failed"}
    
    elif isinstance(error, aiohttp.ClientResponseError):
        if error.status == 429:
            logger.warning(f"Rate limit exceeded in {api_name}")
            return {"error": "rate_limit", "message": "Too many requests"}
    
    logger.error(f"Unexpected error in {api_name}: {error}")
    return {"error": "unknown", "message": "Unknown error occurred"}
```

### Валидация входных данных
```python
def validate_search_query(query: str) -> bool:
    """Валидация поискового запроса"""
    if not query or len(query.strip()) < 2:
        return False
    if len(query) > 100:
        return False
    return True

def validate_user_rating(rating: int) -> bool:
    """Валидация пользовательского рейтинга"""
    return isinstance(rating, int) and 1 <= rating <= 10
```

## 🚀 Развертывание

### Требования
- Python 3.8+
- PostgreSQL 12+
- API ключи для Kinopoisk и OMDB
- Telegram Bot Token

### Процесс развертывания

#### 1. Подготовка сервера
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python
sudo apt install python3 python3-pip python3-venv -y

# Установка PostgreSQL
sudo apt install postgresql postgresql-contrib -y
```

#### 2. Настройка базы данных
```bash
# Создание пользователя БД
sudo -u postgres createuser --interactive vistly_user

# Создание базы данных
sudo -u postgres createdb vistly_bot

# Установка пароля
sudo -u postgres psql -c "ALTER USER vistly_user PASSWORD 'your_password';"
```

#### 3. Настройка проекта
```bash
# Клонирование репозитория
git clone https://github.com/your-username/vistly_bot.git
cd vistly_bot

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Создание .env файла
cp .env.example .env
# Отредактируйте .env файл

# Создание папки для логов
mkdir logs
```

#### 4. Запуск бота
```bash
# Запуск в режиме разработки
python main.py

# Запуск в фоне (с nohup)
nohup python main.py > bot.log 2>&1 &

# Запуск с systemd (рекомендуется)
sudo systemctl enable vistly-bot
sudo systemctl start vistly-bot
```

### Docker развертывание (опционально)

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание пользователя
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Запуск приложения
CMD ["python", "main.py"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  bot:
    build: .
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_USER=${DB_USER}
      - DB_PASS=${DB_PASS}
      - DB_NAME=${DB_NAME}
      - OMDB_API_KEY=${OMDB_API_KEY}
      - KP_API_KEY=${KP_API_KEY}
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASS}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

## 🧪 Тестирование

### Unit тесты
```python
import pytest
from bot.shared.user_service import UserService

class TestUserService:
    def test_get_or_create_user_new(self):
        """Тест создания нового пользователя"""
        user = Mock(id=123456789, username="testuser", full_name="Test User")
        user_db, created = UserService.get_or_create_user(user, "en")
        
        assert created is True
        assert user_db.tg_id == 123456789
        assert user_db.language == "en"
```

### Интеграционные тесты
```python
import pytest
import aioresponses
from bot.features.search_kp.kp_service import KpService

class TestKinopoiskAPI:
    @pytest.mark.asyncio
    async def test_search_movies(self):
        """Тест поиска фильмов через Kinopoisk API"""
        with aioresponses() as m:
            m.get(
                "https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword?keyword=Матрица",
                payload={"films": [{"filmId": 301, "nameRu": "Матрица"}]},
                status=200
            )
            
            service = KpService(Mock(api_key="test_key"))
            results = await service.search("Матрица")
            
            assert len(results) == 1
            assert results[0]["nameRu"] == "Матрица"
```

### Настройка pytest
```ini
# pytest.ini
[tool:pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## 📊 Мониторинг

### Health Check
```python
async def health_check() -> dict:
    """Проверка состояния системы"""
    checks = {
        "database": await check_database_connection(),
        "kinopoisk_api": await check_kinopoisk_api(),
        "omdb_api": await check_omdb_api(),
        "telegram_api": await check_telegram_api()
    }
    
    overall_status = all(checks.values())
    return {
        "status": "healthy" if overall_status else "unhealthy",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }
```

### Метрики производительности
```python
import time
from functools import wraps

def track_performance(func_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"{func_name} executed in {execution_time:.2f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{func_name} failed after {execution_time:.2f}s: {e}")
                raise
        return wrapper
    return decorator
```

## 🔧 Обслуживание

### Резервное копирование
```bash
# Создание резервной копии БД
pg_dump -h localhost -U vistly_user vistly_bot > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление из резервной копии
psql -h localhost -U vistly_user vistly_bot < backup_20250108_120000.sql
```

### Обновление бота
```bash
# Остановка бота
sudo systemctl stop vistly-bot

# Обновление кода
git pull origin main

# Обновление зависимостей
source venv/bin/activate
pip install -r requirements.txt

# Запуск бота
sudo systemctl start vistly-bot
```

### Логи и отладка
```bash
# Просмотр логов
tail -f logs/bot.log

# Просмотр логов systemd
sudo journalctl -u vistly-bot -f

# Проверка статуса
sudo systemctl status vistly-bot
```
