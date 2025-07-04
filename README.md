# Vistly Bot

Telegram-бот для поиска, отслеживания и организации фильмов и сериалов. Бот позволяет пользователям искать контент через API Kinopoisk и OMDB, добавлять его в персональные списки с различными статусами и делиться ссылками на контент.

## 🎯 Основные возможности

### 🔍 Поиск контента
- **Поиск фильмов и сериалов** по названию
- **Интеграция с двумя API**: Kinopoisk.dev (для русского контента) и OMDB (для международного)
- **Автоматический выбор API** на основе языка запроса
- **Детальная информация**: рейтинги, описание, постеры, актеры, режиссеры
- **Пагинация результатов** для удобного просмотра

### 📋 Управление списками
- **Персональные списки** для каждого пользователя
- **Статусы просмотра**:
  - 🎬 **Смотрю** (In Progress)
  - ✅ **Посмотрел** (Completed) 
  - 📝 **Хочу посмотреть** (Planning)
- **Фильтрация** по статусам
- **Пользовательские рейтинги** (1-10)
- **Отслеживание сезонов** для сериалов
- **Поиск по названию** в своем списке

### 👤 Профиль пользователя
- **Многоязычность**: русский и английский
- **Статистика**: количество тайтлов в списке
- **Смена языка** интерфейса
- **Профиль с информацией** о пользователе

### 🔗 Deep Links
- **Прямые ссылки** на фильмы/сериалы
- **Быстрое добавление** в список через ссылки
- **Возможность делиться** контентом с друзьями

## 🛠 Технологии

### Backend
- **Python 3.8+** - основной язык разработки
- **aiogram 3.x** - современный фреймворк для Telegram ботов
- **PostgreSQL** - основная база данных
- **Peewee ORM** - для работы с базой данных
- **aiohttp** - для асинхронных HTTP запросов к API

### API интеграции
- **Kinopoisk.dev API** - для поиска русского контента
- **OMDB API** - для международного контента

### Конфигурация
- **environs** - управление переменными окружения
- **Структурированная конфигурация** через dataclasses

## 📁 Структура проекта

```
vistly_bot/
├── bot/                          # Основная логика бота
│   ├── features/                 # Функциональные модули
│   │   ├── deep_link/           # Deep links функциональность
│   │   ├── profile/             # Профиль пользователя
│   │   ├── search/              # Поиск контента
│   │   ├── search_kp/           # Интеграция с Kinopoisk API
│   │   ├── search_omdb/         # Интеграция с OMDB API
│   │   └── user_list/           # Управление списками
│   ├── formater/                # Форматирование сообщений
│   ├── shared/                  # Общие компоненты
│   ├── states/                  # FSM состояния
│   └── utils/                   # Утилиты и строки
├── config/                      # Конфигурация
├── database/                    # Модели базы данных
├── models/                      # Бизнес-модели
├── logs/                        # Логи
├── main.py                      # Точка входа
└── requirements.txt             # Зависимости
```

## 🚀 Установка и запуск

### Предварительные требования
- Python 3.8 или выше
- PostgreSQL база данных
- API ключи для Kinopoisk.dev и OMDB

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd vistly_bot
```

### 2. Создание виртуального окружения
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка базы данных
Создайте PostgreSQL базу данных и выполните миграции (если необходимо).

### 5. Создание файла конфигурации
Создайте файл `.env` в корне проекта:

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

### 6. Запуск бота
```bash
python main.py
```

## 📋 Получение API ключей

### Telegram Bot Token
1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен

### OMDB API Key
1. Перейдите на [OMDB API](http://www.omdbapi.com/apikey.aspx)
2. Зарегистрируйтесь и получите бесплатный API ключ

### Kinopoisk.dev API Key
1. Перейдите на [Kinopoisk.dev](https://kinopoisk.dev/)
2. Зарегистрируйтесь и получите API ключ

## 🎮 Использование

### Основные команды
- `/start` - запуск бота
- `/help` - показать инструкции
- `/list` - открыть ваш список
- `/profile` - профиль пользователя
- `/restart` - перезапуск бота

### Поиск контента
1. Отправьте название фильма или сериала
2. Выберите нужный результат из списка
3. Просмотрите детальную информацию
4. Добавьте в свой список с выбранным статусом

### Управление списком
- **Фильтрация**: используйте кнопки статусов для фильтрации
- **Изменение статуса**: нажмите на статус элемента
- **Добавление рейтинга**: оцените контент от 1 до 10
- **Отслеживание сезонов**: для сериалов можно указать текущий сезон
- **Удаление**: удалите элемент из списка

### Профиль
- **Смена языка**: переключение между русским и английским
- **Статистика**: количество тайтлов в списке
- **Настройки**: управление профилем

## 🔧 Разработка

### Структура кода
Проект использует модульную архитектуру с четким разделением ответственности:

- **Features** - основные функциональные модули
- **Shared** - общие компоненты и утилиты
- **Models** - бизнес-логика и модели данных
- **Database** - слой работы с базой данных

### Добавление новых функций
1. Создайте новый модуль в `bot/features/`
2. Добавьте роутер в `bot/shared/main_commad_handlers.py`
3. Создайте необходимые состояния в `bot/states/fsm_states.py`
4. Добавьте строки в `bot/utils/strings.json`

### Логирование
Бот использует структурированное логирование. Логи сохраняются в папке `logs/`.

## 📊 База данных

### Основные таблицы
- **user_profile** - профили пользователей
- **entity** - информация о фильмах/сериалах
- **rating** - рейтинги от различных источников
- **user_entity** - связь пользователей с контентом

### Связи
- Пользователи могут иметь множество элементов в списке
- Каждый элемент может иметь множество рейтингов
- Поддержка как IMDb, так и Kinopoisk ID

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT.

## 🆘 Поддержка

Если у вас возникли вопросы или проблемы:
1. Проверьте раздел [Issues](../../issues)
2. Создайте новое issue с подробным описанием проблемы
3. Убедитесь, что проблема не была описана ранее

---

**Vistly Bot** - ваш персональный помощник для организации просмотра фильмов и сериалов! 🎬✨
