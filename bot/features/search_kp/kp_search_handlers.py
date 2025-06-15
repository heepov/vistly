from aiogram import Router, types
from aiogram.types import CallbackQuery
from bot.shared.other_keyboards import get_menu_keyboard
from bot.features.search_omdb.omdb_search_keyboards import (
    get_entity_detail_keyboard,
    get_status_selection_keyboard,
)
from bot.features.search_kp.kp_search_keyboards import get_search_results_keyboard_kp
from bot.features.search_kp.kp_service import KpService
from database.models_db import EntityDB, RatingDB, UserEntityDB, UserDB
from models.enum_classes import EntityType, StatusType
from datetime import datetime, date
from aiogram.fsm.context import FSMContext
from bot.states.fsm_states import SearchKpStates, MainMenuStates, SearchStates
from bot.formater.message_formater import format_entity_details
from models.factories import build_entity_from_db
from bot.utils.strings import get_string

kp_router = Router()


def parse_dict(items: list[dict], key: str) -> list[str]:
    """Извлекает значения по ключу из списка словарей"""
    if not items:
        return []
    return [item.get(key, "") for item in items if key in item and item.get(key)]


def parse_seasons_count(seasons_info: list[dict]) -> int | None:
    """Возвращает максимальное значение поля 'number' из списка сезонов"""
    if not seasons_info:
        return None
    numbers = [
        season.get("number", 0)
        for season in seasons_info
        if isinstance(season.get("number", 0), int)
    ]
    return max(numbers) if numbers else None


def parse_person_names_by_profession(
    persons: list[dict], profession: str, name_key: str = "name"
) -> list[str]:
    result = []
    for person in persons:
        if person.get("enProfession") == profession:
            name = person.get(name_key) or person.get("enName") or person.get("name")
            if name:
                result.append(name)
            if len(result) == 5:
                break
    return result


def kp_details_to_db(details: dict) -> tuple[EntityDB, bool]:
    """Создает или обновляет запись в базе данных для сущности из Kp"""
    type = "series" if KpService.get_safe_value(details, "isSeries") else "movie"
    duration = None
    if KpService.get_safe_value(details, "movieLength"):
        duration = KpService.get_safe_value(details, "movieLength")
    elif KpService.get_safe_value(details, "seriesLength"):
        duration = KpService.get_safe_value(details, "seriesLength")

    entity, created = EntityDB.get_or_create(
        src_id=KpService.get_safe_value(details, "externalId.imdb"),
        kp_id=details.get("id"),
        defaults={
            "title": KpService.get_safe_value(details, "name") or "No title",
            "type": type or EntityType.UNDEFINED,
            "description": KpService.get_safe_value(details, "description"),
            "poster_url": KpService.get_safe_value(details, "poster.url"),
            "duration": duration,
            "genres": parse_dict(KpService.get_safe_value(details, "genres"), "name"),
            "authors": parse_person_names_by_profession(
                KpService.get_safe_value(details, "persons"), "director"
            ),
            "actors": parse_person_names_by_profession(
                KpService.get_safe_value(details, "persons"), "actor"
            ),
            "countries": parse_dict(
                KpService.get_safe_value(details, "countries"), "name"
            ),
            "release_date": datetime.strptime(
                f"01.01.{KpService.get_safe_value(details, "year")}", "%d.%m.%Y"
            ).date(),
            "year_start": KpService.get_safe_value(details, "year"),
            "year_end": KpService.get_safe_value(details, "releaseYears.end"),
            "total_season": parse_seasons_count(
                KpService.get_safe_value(details, "seasonsInfo")
            ),
        },
    )
    return entity, created


def kp_ratings_to_db(entity: EntityDB, details: dict) -> list[RatingDB]:
    """Создает или обновляет рейтинги в базе данных только для 'kp' и 'imdb'"""
    ratings = []
    ratings_data = KpService.get_safe_value(details, "rating")

    if not ratings_data or not isinstance(ratings_data, dict):
        return ratings

    for source in ("kp", "imdb"):
        value = ratings_data.get(source)
        if value is not None:
            rating, _ = RatingDB.get_or_create(
                entity=entity,
                source=source.upper(),  # 'KP' или 'IMDB'
                defaults={"value": value, "max_value": 10, "percent": False},
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
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    lang = user.language if user else "en"
    kp_response = await KpService.search_movies_series(query, page)
    results = kp_response.get("docs", [])

    try:
        total_results = int(kp_response.get("total", 0))
    except (ValueError, TypeError):
        total_results = 0

    if not results:
        await callback.message.edit_text(
            get_string("nothing_found_query", lang).format(query=query)
        )
        if state:
            await state.set_state(MainMenuStates.waiting_for_query)
        return False
    keyboard = get_search_results_keyboard_kp(
        results, query, page, total_results, entity_type, lang
    )

    # Проверяем, есть ли фото в сообщении
    if getattr(callback.message, "photo", None):
        await callback.message.delete()
        await callback.message.answer(
            get_string("found_results", lang).format(
                total_results=total_results, query=query
            ),
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            get_string("found_results", lang).format(
                total_results=total_results, query=query
            ),
            reply_markup=keyboard,
        )

    return True


@kp_router.callback_query(SearchKpStates.waiting_for_kp_selection)
async def handle_kp_search_selection(callback: CallbackQuery, state: FSMContext):
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    lang = user.language if user else "en"
    data = callback.data
    if data.startswith("kp_page:"):
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
    elif data.startswith("kp_select:"):
        try:
            # kp_select:{kp_id}:{query}:{page}:{entity_type}
            _, kp_id, query, page, entity_type = data.split(":", 4)
            page = int(page)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return

        # Получить детали фильма
        details = await KpService.get_item_details(kp_id)
        # --- Добавить в базу ---
        entity, created = kp_details_to_db(details)
        # Сохраняем рейтинги
        ratings = kp_ratings_to_db(entity, details)
        # --- Формируем сообщение ---
        entity_full = build_entity_from_db(entity)
        message = format_entity_details(entity_full, lang)

        # --- Отправляем сообщение ---

        already_added = False
        if user:
            already_added = (
                UserEntityDB.select()
                .where((UserEntityDB.user_id == user) & (UserEntityDB.entity == entity))
                .exists()
            )
        if entity_full.poster_url and entity_full.poster_url != "N/A":
            await callback.message.delete()
            await callback.message.answer_photo(
                entity_full.poster_url,
                caption=message,
                reply_markup=get_entity_detail_keyboard(
                    entity.id,
                    query,
                    page,
                    entity_type,
                    lang,
                    already_added=already_added,
                ),
            )
        else:
            await callback.message.edit_text(
                message,
                reply_markup=get_entity_detail_keyboard(
                    entity.id,
                    query,
                    page,
                    entity_type,
                    lang,
                    already_added=already_added,
                ),
            )
        await state.set_state(SearchKpStates.waiting_for_kp_action_entity)
        await callback.answer()

    if data == "noop":
        await callback.answer()
        return

    if data == "cancel_search":
        await callback.message.delete()
        await callback.message.answer(
            get_string("start_message", lang),
            reply_markup=get_menu_keyboard(lang),
        )
        await state.set_state(MainMenuStates.waiting_for_query)
        await callback.answer()
        return

    if data == "change_entity_type":
        await callback.answer(get_string("feature_developing", lang), show_alert=False)
        return


@kp_router.callback_query(SearchKpStates.waiting_for_kp_action_entity)
async def handle_kp_entity_actions(callback: CallbackQuery, state: FSMContext):
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    lang = user.language if user else "en"
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
            await state.set_state(SearchKpStates.waiting_for_kp_selection)
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
                get_string("select_status_type_for", lang).format(
                    entity_name=entity_name
                ),
                reply_markup=get_status_selection_keyboard(entity_id, lang),
            )
        else:
            # Если обычное текстовое сообщение, можно просто отредактировать его
            await callback.message.edit_text(
                get_string("select_status_type_for", lang).format(
                    entity_name=entity_name
                ),
                reply_markup=get_status_selection_keyboard(entity_id, lang),
            )

        # Переходим в состояние ожидания выбора статуса
        await state.set_state(SearchKpStates.waiting_for_kp_entity_add_to_list)
        await callback.answer()
        return


@kp_router.callback_query(SearchKpStates.waiting_for_kp_entity_add_to_list)
async def handle_add_to_list_status_selection(
    callback: CallbackQuery, state: FSMContext
):
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    lang = user.language if user else "en"
    data = callback.data

    # Обработка отмены
    if data == "cancel_add_to_list":
        await callback.message.delete()
        await callback.message.answer(
            get_string("start_message", lang),
            reply_markup=get_menu_keyboard(lang),
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
            "completed": StatusType.COMPLETED,
            "planning": StatusType.PLANNING,
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
            success_message = get_string("entity_added_to_list", lang).format(
                entity_title=entity.title, status_type=status_type.name
            )
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
