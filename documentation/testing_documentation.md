# 🧪 ДОКУМЕНТАЦИЯ ПО ТЕСТИРОВАНИЮ: Vistly Bot

> **Стратегия и примеры тестирования для pet-проекта**

## 🎯 Обзор

Этот документ описывает подход к тестированию Vistly Bot. Поскольку это pet-проект, фокус делается на практичности и простоте, а не на корпоративных стандартах.

## 🏗 Стратегия тестирования

### Принципы
- **Практичность** - тестируем то, что важно
- **Простота** - минимум сложности
- **Эффективность** - максимум пользы при минимуме затрат
- **Надежность** - основные функции работают стабильно

### Пирамида тестирования
```
                    ┌─────────────────┐
                    │   Ручные тесты  │ ← 20%
                    │  (основные)     │
                    └─────────────────┘
                ┌─────────────────────┐
                │ Интеграционные      │ ← 30%
                │ (API, БД)           │
                └─────────────────────┘
            ┌─────────────────────────┐
            │   Unit тесты            │ ← 50%
            │ (функции, классы)       │
            └─────────────────────────┘
```

---

## 📊 Уровни тестирования

### 1. Unit тестирование (50%)
- **Объект:** Отдельные функции и классы
- **Инструменты:** pytest, unittest.mock
- **Цель:** Проверить логику компонентов

### 2. Интеграционное тестирование (30%)
- **Объект:** Взаимодействие компонентов
- **Инструменты:** pytest-asyncio, aioresponses
- **Цель:** Проверить работу API и БД

### 3. Ручное тестирование (20%)
- **Объект:** Пользовательские сценарии
- **Инструменты:** Telegram Bot
- **Цель:** Проверить UX и основные функции

---

## 🧪 Основные тестовые кейсы

### 1. Команды и навигация

#### TC-001: Команда /start
**Приоритет:** Критический  
**Описание:** Проверка корректной работы команды /start

**Шаги:**
1. Отправить `/start` новому пользователю
2. Отправить `/start` существующему пользователю
3. Отправить `/start` с deep link аргументами

**Ожидаемые результаты:**
- Новый пользователь получает приветственное сообщение с выбором языка
- Существующий пользователь получает главное меню
- Deep link корректно обрабатывается

#### TC-002: Команда /help
**Приоритет:** Высокий  
**Описание:** Проверка отображения справки

**Шаги:**
1. Отправить команду `/help`
2. Проверить отображение инструкций
3. Проверить наличие изображений

**Ожидаемые результаты:**
- Отображается текст справки на правильном языке
- Прикреплены изображения-инструкции
- Кнопки навигации работают корректно

### 2. Поиск контента

#### TC-003: Глобальный поиск (русский)
**Приоритет:** Критический  
**Описание:** Поиск русского контента через Kinopoisk API

**Шаги:**
1. Отправить русский поисковый запрос
2. Дождаться результатов
3. Проверить отображение результатов

**Ожидаемые результаты:**
- Поиск выполняется через Kinopoisk API
- Результаты отображаются корректно
- Время ответа не более 3 секунд

**Тестовые данные:**
```python
search_queries = ["Матрица", "Игра престолов", "Аватар"]
```

#### TC-004: Глобальный поиск (английский)
**Приоритет:** Критический  
**Описание:** Поиск английского контента через OMDB API

**Шаги:**
1. Отправить английский поисковый запрос
2. Дождаться результатов
3. Проверить отображение результатов

**Ожидаемые результаты:**
- Поиск выполняется через OMDB API
- Результаты отображаются корректно
- Время ответа не более 3 секунд

**Тестовые данные:**
```python
search_queries = ["The Matrix", "Game of Thrones", "Avatar"]
```

#### TC-005: Локальный поиск
**Приоритет:** Высокий  
**Описание:** Поиск в пользовательском списке

**Предусловия:**
- Пользователь имеет элементы в списке

**Шаги:**
1. Выбрать "Поиск в моем списке"
2. Ввести поисковый запрос
3. Проверить результаты

**Ожидаемые результаты:**
- Поиск выполняется в базе данных
- Отображаются только элементы пользователя
- Результаты релевантны запросу

### 3. Управление списками

#### TC-006: Добавление в список
**Приоритет:** Критический  
**Описание:** Добавление элемента в пользовательский список

**Предусловия:**
- Выполнен поиск и найден элемент

**Шаги:**
1. Выбрать элемент из результатов поиска
2. Нажать "Добавить в список"
3. Выбрать статус (смотрю/посмотрел/хочу)
4. Подтвердить добавление

**Ожидаемые результаты:**
- Элемент добавляется в базу данных
- Отображается подтверждение
- Элемент появляется в списке пользователя

#### TC-007: Изменение статуса
**Приоритет:** Высокий  
**Описание:** Изменение статуса элемента в списке

**Предусловия:**
- Элемент есть в списке пользователя

**Шаги:**
1. Открыть элемент в списке
2. Нажать "Изменить статус"
3. Выбрать новый статус
4. Подтвердить изменение

**Ожидаемые результаты:**
- Статус обновляется в базе данных
- Отображается подтверждение
- Элемент перемещается в соответствующую категорию

#### TC-008: Установка рейтинга
**Приоритет:** Высокий  
**Описание:** Установка пользовательского рейтинга

**Шаги:**
1. Открыть элемент в списке
2. Нажать "Оценить"
3. Выбрать рейтинг от 1 до 10
4. Подтвердить оценку

**Ожидаемые результаты:**
- Рейтинг сохраняется в базе данных
- Отображается подтверждение
- Рейтинг отображается в деталях элемента

### 4. Deep Links

#### TC-009: Deep link для фильма
**Приоритет:** Высокий  
**Описание:** Обработка deep link для фильма

**Шаги:**
1. Перейти по ссылке `/start movie_12345`
2. Проверить отображение информации о фильме
3. Добавить в список

**Ожидаемые результаты:**
- Отображается информация о фильме
- Можно добавить в список
- Работает навигация

#### TC-010: Некорректный deep link
**Приоритет:** Средний  
**Описание:** Обработка некорректных deep link

**Шаги:**
1. Перейти по ссылке `/start invalid_123`
2. Перейти по ссылке `/start`

**Ожидаемые результаты:**
- Отображается сообщение об ошибке
- Бот не падает
- Предлагается начать заново

### 5. Многоязычность

#### TC-011: Переключение языка
**Приоритет:** Высокий  
**Описание:** Переключение между русским и английским

**Шаги:**
1. Открыть профиль
2. Нажать "Сменить язык"
3. Выбрать русский
4. Проверить интерфейс
5. Сменить на английский
6. Проверить интерфейс

**Ожидаемые результаты:**
- Интерфейс переключается на выбранный язык
- Все элементы переведены
- Настройки сохраняются

#### TC-012: Автоматическое определение языка
**Приоритет:** Высокий  
**Описание:** Автоматическое определение языка запроса

**Шаги:**
1. Отправить русский запрос
2. Отправить английский запрос
3. Отправить смешанный запрос

**Ожидаемые результаты:**
- Русские запросы обрабатываются через Kinopoisk
- Английские запросы обрабатываются через OMDB
- Смешанные запросы обрабатываются корректно

---

## 🤖 Автоматизированное тестирование

### Структура тестов
```
tests/
├── unit/                    # Unit тесты
│   ├── test_models.py      # Тесты моделей
│   ├── test_services.py    # Тесты сервисов
│   └── test_utils.py       # Тесты утилит
├── integration/            # Интеграционные тесты
│   ├── test_api.py         # Тесты API
│   ├── test_database.py    # Тесты БД
│   └── test_bot.py         # Тесты бота
├── fixtures/               # Фикстуры
│   ├── users.py           # Пользователи
│   ├── entities.py        # Сущности
│   └── api_responses.py   # Ответы API
└── conftest.py            # Конфигурация pytest
```

### Примеры unit тестов

#### Тест модели пользователя
```python
import pytest
from database.models_db import UserDB
from models.enum_classes import LanguageType

class TestUserDB:
    def test_create_user(self):
        """Тест создания пользователя"""
        user = UserDB.create(
            tg_id=123456789,
            username="testuser",
            name="Test User",
            language=LanguageType.EN.value
        )
        
        assert user.tg_id == 123456789
        assert user.username == "testuser"
        assert user.language == LanguageType.EN.value
    
    def test_user_language_default(self):
        """Тест языка по умолчанию"""
        user = UserDB.create(
            tg_id=987654321,
            username="testuser2",
            name="Test User 2"
        )
        
        assert user.language == LanguageType.EN.value
```

#### Тест сервиса поиска
```python
import pytest
from unittest.mock import Mock, patch
from bot.features.search.search_gs_handlers import perform_global_search
from models.enum_classes import SourceApi

class TestSearchService:
    @pytest.mark.asyncio
    async def test_cyrillic_detection(self):
        """Тест определения кириллицы"""
        from bot.features.search.search_handlers import is_cyrillic
        
        assert is_cyrillic("Матрица") == True
        assert is_cyrillic("The Matrix") == False
        assert is_cyrillic("Matrix 2024") == False
    
    @pytest.mark.asyncio
    async def test_api_selection(self):
        """Тест выбора API"""
        from bot.features.search.search_handlers import is_cyrillic
        from models.enum_classes import SourceApi
        
        def get_api_source(query: str) -> SourceApi:
            return SourceApi.KP if is_cyrillic(query) else SourceApi.OMDB
        
        assert get_api_source("Матрица") == SourceApi.KP
        assert get_api_source("The Matrix") == SourceApi.OMDB
```

### Примеры интеграционных тестов

#### Тест API интеграции
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
                payload={
                    "films": [
                        {
                            "filmId": 301,
                            "nameRu": "Матрица",
                            "nameEn": "The Matrix",
                            "year": "1999"
                        }
                    ]
                },
                status=200
            )
            
            service = KpService(Mock(api_key="test_key"))
            results = await service.search("Матрица")
            
            assert len(results) == 1
            assert results[0]["nameRu"] == "Матрица"
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Тест обработки ошибок API"""
        with aioresponses() as m:
            m.get(
                "https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword?keyword=test",
                status=429
            )
            
            service = KpService(Mock(api_key="test_key"))
            results = await service.search("test")
            
            assert results == []
```

#### Тест базы данных
```python
import pytest
from database.models_db import UserDB, EntityDB, UserEntityDB
from models.enum_classes import StatusType, EntityType

class TestDatabase:
    def test_user_entity_relationship(self):
        """Тест связей между пользователем и сущностями"""
        # Создаем пользователя
        user = UserDB.create(
            tg_id=123456789,
            username="testuser",
            name="Test User"
        )
        
        # Создаем сущность
        entity = EntityDB.create(
            title="Test Movie",
            type=EntityType.MOVIE.value
        )
        
        # Создаем связь
        user_entity = UserEntityDB.create(
            user=user,
            entity=entity,
            status=StatusType.PLANNING.value
        )
        
        # Проверяем связи
        assert user_entity.user == user
        assert user_entity.entity == entity
        assert user.user_entities.count() == 1
        assert entity.user_entities.count() == 1
```

### Настройка pytest
```python
# pytest.ini
[tool:pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    api: API tests
    database: Database tests
```

---

## 👨‍💻 Ручное тестирование

### Чек-лист для ручного тестирования

#### Основные функции
- [ ] Команда `/start` работает для новых пользователей
- [ ] Команда `/start` работает для существующих пользователей
- [ ] Команда `/help` отображает справку
- [ ] Команда `/list` показывает список пользователя
- [ ] Команда `/profile` показывает профиль

#### Поиск
- [ ] Поиск на русском языке работает
- [ ] Поиск на английском языке работает
- [ ] Результаты поиска отображаются корректно
- [ ] Пагинация работает
- [ ] Поиск в списке работает

#### Управление списками
- [ ] Добавление в список работает
- [ ] Изменение статуса работает
- [ ] Установка рейтинга работает
- [ ] Установка сезона работает для сериалов
- [ ] Удаление из списка работает
- [ ] Фильтрация по статусам работает

#### Deep Links
- [ ] Deep link для фильмов работает
- [ ] Deep link для сериалов работает
- [ ] Некорректные deep links обрабатываются

#### Многоязычность
- [ ] Переключение языка работает
- [ ] Автоматическое определение языка работает
- [ ] Все элементы интерфейса переведены

### Сценарии тестирования

#### Сценарий 1: Новый пользователь
1. Отправить `/start`
2. Выбрать язык (русский)
3. Выполнить поиск "Матрица"
4. Добавить фильм в список со статусом "Хочу посмотреть"
5. Открыть список и проверить элемент
6. Изменить статус на "Смотрю"
7. Установить рейтинг 9
8. Проверить профиль

#### Сценарий 2: Поиск и добавление
1. Выполнить поиск "Game of Thrones"
2. Выбрать сериал из результатов
3. Добавить в список со статусом "Смотрю"
4. Установить текущий сезон 3
5. Проверить в списке
6. Изменить статус на "Посмотрел"

#### Сценарий 3: Deep Links
1. Создать deep link для фильма
2. Перейти по ссылке
3. Добавить в список
4. Проверить в профиле

---

## ⚡ Тестирование производительности

### Метрики производительности
- **Время отклика** - не более 3 секунд для поиска
- **Пропускная способность** - 100 запросов в минуту
- **Использование памяти** - не более 512MB
- **Использование CPU** - не более 80%

### Простые тесты производительности
```python
import time
import asyncio

async def test_search_performance():
    """Тест производительности поиска"""
    start_time = time.time()
    
    # Выполняем 10 поисковых запросов
    for i in range(10):
        await perform_search(f"test query {i}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Проверяем, что среднее время не превышает 3 секунды
    avg_time = total_time / 10
    assert avg_time < 3.0, f"Average search time {avg_time:.2f}s exceeds 3s"
```

---

## 🔒 Тестирование безопасности

### Области тестирования безопасности
1. **Валидация входных данных**
2. **Защита API ключей**
3. **SQL-инъекции**
4. **XSS атаки**

### Тестовые сценарии безопасности

#### SQL-инъекция
```python
malicious_inputs = [
    "'; DROP TABLE users; --",
    "' OR 1=1; --",
    "'; INSERT INTO users VALUES (1, 'hacker'); --"
]

def test_sql_injection():
    for input_data in malicious_inputs:
        # Попытка использовать вредоносный ввод
        result = search_database(input_data)
        # Проверяем, что вредоносный код не выполнился
        assert "error" in result or result == []
```

#### XSS атака
```python
xss_payloads = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "javascript:alert('XSS')"
]

def test_xss_protection():
    for payload in xss_payloads:
        # Попытка внедрить XSS
        result = process_user_input(payload)
        # Проверяем, что HTML экранирован
        assert "<script>" not in result
        assert "javascript:" not in result
```

---

## 🛠 Инструменты тестирования

### Основные инструменты
- **pytest** - основной фреймворк тестирования
- **pytest-asyncio** - поддержка асинхронных тестов
- **pytest-mock** - мокирование
- **aioresponses** - мокирование HTTP запросов
- **factory-boy** - создание тестовых данных

### Дополнительные инструменты
- **coverage** - измерение покрытия кода
- **black** - форматирование кода
- **flake8** - линтинг
- **mypy** - проверка типов

### Конфигурация инструментов

#### coverage.ini
```ini
[run]
source = bot,database,models
omit = 
    */tests/*
    */venv/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

#### .flake8
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    venv,
    .venv
```

---

## 📋 Процесс тестирования

### Этапы тестирования

#### 1. Планирование
- Определение объема тестирования
- Выбор тестовых сценариев
- Подготовка тестовых данных

#### 2. Выполнение
- Запуск автоматизированных тестов
- Выполнение ручного тестирования
- Документирование результатов

#### 3. Анализ
- Анализ результатов тестирования
- Выявление дефектов
- Оценка качества

#### 4. Отчетность
- Создание отчетов о тестировании
- Документирование дефектов
- Рекомендации по улучшению

### Критерии готовности к релизу
- [ ] Все критические тесты пройдены
- [ ] Покрытие кода не менее 70%
- [ ] Нет критических дефектов
- [ ] Производительность соответствует требованиям
- [ ] Безопасность проверена

### Автоматизация CI/CD
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests
      env:
        DB_HOST: localhost
        DB_PORT: 5432
        DB_USER: postgres
        DB_PASS: postgres
        DB_NAME: test_db
        OMDB_API_KEY: test_key
        KP_API_KEY: test_key
      run: |
        pytest --cov=bot --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
```

---

## 📊 Метрики качества

### Ключевые показатели
- **Покрытие кода** - 70%+
- **Время выполнения тестов** - < 5 минут
- **Количество дефектов** - 0 критических
- **Время отклика** - < 3 секунды
- **Доступность** - 99.9%

### Отслеживание метрик
```python
# metrics.py
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

---

## 🔄 Обновление тестов

### Политика обновления
- Тесты обновляются при изменении функциональности
- Новые тесты добавляются для новых функций
- Устаревшие тесты удаляются
- Покрытие кода поддерживается на уровне 70%+

### Процесс обновления
1. **Анализ изменений** - определение затронутых компонентов
2. **Обновление тестов** - модификация существующих тестов
3. **Добавление тестов** - создание тестов для новой функциональности
4. **Валидация** - проверка корректности тестов
5. **Документирование** - обновление документации

---

## 💡 Рекомендации для pet-проекта

### Приоритеты тестирования
1. **Критические функции** - поиск, добавление в список, основные команды
2. **Интеграции** - API Kinopoisk и OMDB
3. **Пользовательский опыт** - навигация, интерфейс
4. **Безопасность** - базовая защита от уязвимостей

### Практические советы
- **Начните с ручного тестирования** - быстро выявите основные проблемы
- **Автоматизируйте критичные тесты** - поиск и API интеграции
- **Используйте простые инструменты** - pytest, coverage
- **Фокусируйтесь на качестве, а не количестве** - лучше меньше, да лучше

### Для дальнейшего развития
- **Расширяйте покрытие** по мере роста проекта
- **Добавляйте интеграционные тесты** для новых API
- **Внедряйте CI/CD** для автоматизации
- **Мониторьте производительность** при росте пользователей
