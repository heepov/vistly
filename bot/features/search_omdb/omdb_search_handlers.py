from aiogram import Router, types
from aiogram.types import CallbackQuery
from bot.shared.other_keyboards import menu_keyboard
from bot.features.search_omdb.omdb_search_keyboards import (
    get_search_results_keyboard,
    get_entity_detail_keyboard,
    get_status_selection_keyboard,
)
from bot.features.search_omdb.omdb_service import OMDbService
from database.models_db import EntityDB, RatingDB, UserEntityDB, UserDB
from models.enum_classes import EntityType, StatusType
from datetime import datetime, date
from aiogram.fsm.context import FSMContext
from bot.states.fsm_states import SearchOmdbStates, MainMenuStates, SearchStates
from bot.formater.message_formater import format_entity_details
from models.factories import build_entity_from_db

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


async def show_search_results(
    callback: CallbackQuery,
    query: str,
    page: int,
    entity_type: str,
    state: FSMContext = None,
) -> bool:
    """Показывает результаты поиска по запросу

    Args:
        callback: объект callback
        query: поисковый запрос
        page: номер страницы
        entity_type: тип сущности (movie, series и т.д.)
        state: объект FSMContext (опционально)

    Returns:
        bool: True если результаты найдены и показаны, False если результаты не найдены
    """
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
        if state:
            await state.set_state(MainMenuStates.waiting_for_query)
        return False

    keyboard = get_search_results_keyboard(
        results, query, page, total_results, entity_type
    )

    # Проверяем, есть ли фото в сообщении
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
        )

    return True


@omdb_router.callback_query(SearchOmdbStates.waiting_for_omdb_selection)
async def handle_omdb_search_selection(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    if data.startswith("omdb_page:"):
        try:
            _, query, page, entity_type = data.split(":", 3)
            page = int(page)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return

        success = await show_search_results(callback, query, page, entity_type, state)
        if success:
            await callback.answer()
            return

    # Обработка выбора фильма
    elif data.startswith("omdb_select:"):
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
        entity_full = build_entity_from_db(entity)
        message = format_entity_details(entity_full)

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
        await state.set_state(SearchOmdbStates.waiting_for_omdb_action_entity)
        await callback.answer()

    if data == "noop":
        await callback.answer()
        return

    if data == "cancel_search":
        await callback.message.delete()
        await callback.message.answer(
            "Hi! Enter the name of the movie or TV series to search for:",
            reply_markup=menu_keyboard,
        )
        await state.set_state(MainMenuStates.waiting_for_query)
        await callback.answer()
        return

    if data == "change_entity_type":
        await callback.answer("Feature is developing", show_alert=False)
        return


@omdb_router.callback_query(SearchOmdbStates.waiting_for_omdb_action_entity)
async def handle_omdb_entity_actions(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    if data.startswith("back_to_results:"):
        try:
            # back_to_results:{query}:{page}:{entity_type}
            _, query, page, entity_type = data.split(":", 3)
            page = int(page)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return

        success = await show_search_results(callback, query, page, entity_type)
        if success:
            await state.set_state(SearchOmdbStates.waiting_for_omdb_selection)
            await callback.answer()
            return

    elif data.startswith("add_to_list:"):
        try:
            # add_to_list:{entity_id}
            _, entity_id = data.split(":", 1)
            entity_id = int(entity_id)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return

        # Сохраняем entity_id в state для использования в следующем шаге
        await state.update_data(entity_id=entity_id)

        # Получаем название сущности для отображения
        try:
            entity = EntityDB.get_by_id(entity_id)
            entity_name = entity.title
        except:
            entity_name = "Entity Name"

        # Проверяем, есть ли фото в сообщении
        has_photo = getattr(callback.message, "photo", None) is not None

        # Показываем меню выбора статуса
        if has_photo:
            # Если сообщение с фото, нужно удалить его и отправить новое
            await callback.message.delete()
            await callback.message.answer(
                f"Select Status type for {entity_name}",
                reply_markup=get_status_selection_keyboard(entity_id),
            )
        else:
            # Если обычное текстовое сообщение, можно просто отредактировать его
            await callback.message.edit_text(
                f"Select Status type for {entity_name}",
                reply_markup=get_status_selection_keyboard(entity_id),
            )

        # Переходим в состояние ожидания выбора статуса
        await state.set_state(SearchOmdbStates.waiting_for_omdb_entity_add_to_list)
        await callback.answer()
        return


@omdb_router.callback_query(SearchOmdbStates.waiting_for_omdb_entity_add_to_list)
async def handle_add_to_list_status_selection(
    callback: CallbackQuery, state: FSMContext
):
    data = callback.data

    # Обработка отмены
    if data == "cancel_add_to_list":
        await callback.message.delete()
        await callback.message.answer(
            "Hi! Enter the name of the movie or TV series to search for:",
            reply_markup=menu_keyboard,
        )
        await state.set_state(MainMenuStates.waiting_for_query)
        await callback.answer()
        return

    # Обработка выбора статуса
    if data.startswith("add_status:"):
        try:
            # add_status:{entity_id}:{status}
            _, entity_id, status = data.split(":", 2)
            entity_id = int(entity_id)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return

        # Получаем пользователя из callback
        user_id = UserDB.get_or_none(tg_id=callback.from_user.id)
        if not user_id:
            await callback.answer("User not found")
            return

        # Определяем статус
        status_map = {
            "in_progress": StatusType.IN_PROGRESS,
            "complete": StatusType.COMPLETED,
            "planing": StatusType.PLANNING,
        }
        status_type = status_map.get(status, StatusType.PLANNING)

        try:
            # Получаем сущность
            entity = EntityDB.get_by_id(entity_id)

            # Создаем или обновляем запись в user_entity
            user_entity, created = UserEntityDB.get_or_create(
                user_id=user_id, entity=entity, defaults={"status": status_type}
            )

            if not created:
                user_entity.status = status_type
                user_entity.save()

            # Показываем сообщение об успехе
            success_message = f"{entity.title} has been successfully added with {status_type.name} status"
            await callback.message.delete()
            await callback.message.answer(success_message)
            await state.set_state(MainMenuStates.waiting_for_query)

        except Exception as e:
            # Обрабатываем ошибку
            error_message = f"Error adding to list: {str(e)}"
            await callback.message.delete()
            await callback.message.answer(error_message)
            await state.set_state(MainMenuStates.waiting_for_query)

        await callback.answer()
        return
