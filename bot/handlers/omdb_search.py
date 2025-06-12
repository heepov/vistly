from aiogram import Router, types
from aiogram.types import CallbackQuery
from bot.keyboards.menu import menu_keyboard
from bot.keyboards.search import get_search_results_keyboard, get_entity_detail_keyboard
from services.omdb_service import OMDbService
from database.models_db import EntityDB, RatingDB
from models.enum_classes import EntityType, StatusType
from datetime import datetime, date

omdb_router = Router()


def parse_year_range(year_str: str) -> tuple[int | None, int | None]:
    if not year_str or year_str == "N/A":
        return None, None

    # Разделяем строку по дефису
    parts = year_str.split("–")

    try:
        year_start = int(parts[0])
        # Если есть вторая часть и она не пустая
        year_end = int(parts[1]) if len(parts) > 1 and parts[1].strip() else None
        return year_start, year_end
    except (ValueError, IndexError):
        return None, None


def parse_duration(duration_str: str) -> int | None:
    """Парсит строку длительности в минуты"""
    if not duration_str:
        return None
    try:
        return int(duration_str.split()[0])
    except (ValueError, IndexError):
        return None


def parse_list(value: str) -> list[str] | None:
    """Парсит строку со списком значений в список"""
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_date(date_str: str) -> date | None:
    """Парсит строку даты в объект date"""
    if not date_str or date_str == "N/A":
        return None
    try:
        return datetime.strptime(date_str, "%d %b %Y").date()
    except (ValueError, IndexError):
        return None


def parse_rating_value(value_str: str) -> tuple[float, int, bool] | None:
    """Парсит строку рейтинга в (значение, максимальное значение, процент)"""
    if not value_str or value_str == "N/A":
        return None

    try:
        if "%" in value_str:
            value = float(value_str.replace("%", ""))
            return value, 100, True
        elif "/" in value_str:
            left, right = value_str.split("/", 1)
            value = float(left)
            max_value = int(right)
            return value, max_value, False
        else:
            value = float(value_str)
            return value, 10, False
    except (ValueError, IndexError):
        return None


def omdb_details_to_db(details: dict) -> tuple[EntityDB, bool]:

    year_start, year_end = parse_year_range(OMDbService.get_safe_value(details, "Year"))

    total_season = None
    total_season_str = OMDbService.get_safe_value(details, "totalSeasons")
    if total_season_str:
        try:
            total_season = int(total_season_str)
        except ValueError:
            pass

    entity, created = EntityDB.get_or_create(
        src_id=details.get("imdbID"),
        defaults={
            "title": OMDbService.get_safe_value(details, "Title") or "No title",
            "type": OMDbService.get_safe_value(details, "Type") or EntityType.UNDEFINED,
            "description": OMDbService.get_safe_value(details, "Plot"),
            "poster_url": OMDbService.get_safe_value(details, "Poster"),
            "duration": parse_duration(OMDbService.get_safe_value(details, "Runtime")),
            "genres": parse_list(OMDbService.get_safe_value(details, "Genre")),
            "authors": parse_list(OMDbService.get_safe_value(details, "Director")),
            "actors": parse_list(OMDbService.get_safe_value(details, "Actors")),
            "countries": parse_list(OMDbService.get_safe_value(details, "Country")),
            "release_date": parse_date(OMDbService.get_safe_value(details, "Released")),
            "year_start": year_start,
            "year_end": year_end,
            "total_season": total_season,
        },
    )
    return entity, created


def omdb_ratings_to_db(entity: EntityDB, details: dict) -> list[RatingDB]:
    """Создает или обновляет рейтинги в базе данных из данных OMDB"""
    ratings = []
    ratings_data = OMDbService.get_safe_value(details, "Ratings")

    if not ratings_data:
        return ratings

    for rating_data in ratings_data:
        source = OMDbService.get_safe_value(rating_data, "Source")
        value_str = OMDbService.get_safe_value(rating_data, "Value")

        if not source or not value_str:
            continue

        value, max_value, percent = parse_rating_value(value_str)

        rating, _ = RatingDB.get_or_create(
            entity=entity,
            source=source,
            defaults={"value": value, "max_value": max_value, "percent": percent},
        )
        ratings.append(rating)

    return ratings


def format_entity_details(entity: EntityDB, ratings: list[RatingDB]) -> str:
    """Формирует сообщение с деталями фильма/сериала"""
    # Собираем рейтинги для вывода
    rating_parts = []
    for rating in ratings:
        if rating.source == "Internet Movie Database":
            rating_parts.append(f"IMDb - {rating.value}")
        elif rating.source == "Rotten Tomatoes":
            rating_parts.append(f"RT - {rating.value}")
        elif rating.source == "Metacritic":
            rating_parts.append(f"Meta - {rating.value}")
    rating_str = " | ".join(rating_parts) if rating_parts else None

    # Формируем сообщение
    message_parts = []

    # Заголовок
    if entity.release_date:
        release_date = entity.release_date.strftime("%d %b %Y")
    message_parts.append(
        f"<b>{entity.title}</b> | {release_date} | {entity.type.capitalize()}"
    )

    # Рейтинги
    if rating_str:
        message_parts.append(f"Rating: {rating_str}")

    # Длительность
    if entity.duration:
        message_parts.append(f"Runtime: {entity.duration} min")

    # Количество сезонов
    year_str = (
        f" ({entity.year_start}{f'-{entity.year_end}' if entity.year_end else ''})"
        if entity.year_start
        else ""
    )
    if entity.total_season:
        message_parts.append(f"Seasons: {entity.total_season} | {year_str}")

    # Жанры
    if entity.genres:
        message_parts.append(f"Genre: {', '.join(entity.genres)}")

    # Режиссер
    if entity.authors:
        message_parts.append(f"Director: {', '.join(entity.authors)}")

    # Актеры
    if entity.actors:
        message_parts.append(f"Actors: {', '.join(entity.actors)}")

    # Описание
    if entity.description:
        message_parts.append(f"\n{entity.description}")

    return "\n".join(message_parts)


@omdb_router.callback_query()
async def handle_callback(callback: CallbackQuery):
    data = callback.data
    # 1. Кнопка Global — показать "Searching please wait", потом результаты
    if data.startswith("search_global:"):
        try:
            query = data.split(":", 1)[1]
        except IndexError:
            await callback.answer("Invalid callback data")
            return

        page = 1
        await callback.message.edit_text("Searching please wait...")

        omdb_response = await OMDbService.search_movies_series(query, page)
        results = omdb_response.get("Search", [])
        try:
            total_results = int(omdb_response.get("totalResults", 0))
        except (ValueError, TypeError):
            total_results = 0
        if not results:
            await callback.message.edit_text(
                f"Nothing was found for the query: <b>{query}</b>"
            )
            await callback.answer()
            return
        keyboard = get_search_results_keyboard(results, query, page, total_results)
        await callback.message.edit_text(
            f"Found {total_results} for: <b>{query}</b>", reply_markup=keyboard
        )
        await callback.answer()
        return
    # 2. Кнопка Change Entity type
    if data == "change_entity_type":
        await callback.answer("Feature is developing", show_alert=False)
        return
    # 3. Кнопка Page X of Y (noop)
    if data == "noop":
        await callback.answer()
        return
    # 4. Кнопка Cancel
    if data == "cancel_search":
        await callback.message.delete()
        await callback.message.answer("Command start ran", reply_markup=menu_keyboard)
        await callback.answer()
        return
    # 5. Кнопка next (omdb_page)
    if data.startswith("omdb_page:"):
        try:
            # omdb_page:{query}:{page}:{entity_type}
            _, query, page, entity_type = data.split(":", 3)
            page = int(page)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return
        omdb_response = await OMDbService.search_movies_series(query, page)
        results = omdb_response.get("Search", [])
        total_results = int(omdb_response.get("totalResults", 0))
        if not results:
            await callback.message.edit_text(
                f"Nothing was found for the query: <b>{query}</b>"
            )
            await callback.answer()
            return
        keyboard = get_search_results_keyboard(
            results, query, page, total_results, entity_type
        )
        await callback.message.edit_text(
            f"Found {total_results} results for: <b>{query}</b>", reply_markup=keyboard
        )
        await callback.answer()
        return
    # 6. Кнопка выбора фильма (omdb_select)
    if data.startswith("omdb_select:"):
        try:
            # omdb_select:{imdb_id}:{query}:{page}:{entity_type}
            _, imdb_id, query, page, entity_type = data.split(":", 4)
            page = int(page)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return
        # Получить детали фильма
        details = await OMDbService.get_item_details(imdb_id)
        # --- Добавить в базу ---
        entity, created = omdb_details_to_db(details)
        # Сохраняем рейтинги
        ratings = omdb_ratings_to_db(entity, details)
        # --- Формируем сообщение ---
        message = format_entity_details(entity, ratings)
        # --- Отправляем сообщение ---
        poster = OMDbService.get_safe_value(details, "Poster")
        if poster and poster != "N/A":
            await callback.message.delete()
            await callback.message.answer_photo(
                poster,
                caption=message,
                reply_markup=get_entity_detail_keyboard(
                    entity.id, query, page, entity_type
                ),
            )
        else:
            await callback.message.edit_text(
                message,
                reply_markup=get_entity_detail_keyboard(
                    entity.id, query, page, entity_type
                ),
            )
        await callback.answer()
        return
    # 7. Кнопка back to results
    if data.startswith("back_to_results:"):
        try:
            # back_to_results:{query}:{page}:{entity_type}
            _, query, page, entity_type = data.split(":", 3)
            page = int(page)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return
        omdb_response = await OMDbService.search_movies_series(query, page)
        results = omdb_response.get("Search", [])
        total_results = int(omdb_response.get("totalResults", 0))
        if not results:
            await callback.message.edit_text(
                f"Nothing was found for the query: <b>{query}</b>"
            )
            await callback.answer()
            return
        keyboard = get_search_results_keyboard(
            results, query, page, total_results, entity_type
        )
        # Фикс: если сообщение с фото, удаляем и отправляем новое текстовое сообщение
        if getattr(callback.message, "photo", None):
            await callback.message.delete()
            await callback.message.answer(
                f"Found {total_results} results for: <b>{query}</b>",
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        else:
            await callback.message.edit_text(
                f"Found {total_results} results for: <b>{query}</b>",
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        await callback.answer()
        return
