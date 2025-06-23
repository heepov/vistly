import logging
from typing import Optional, Tuple, Union, Any
from aiogram import Router
from aiogram.types import CallbackQuery, Message
from bot.shared.other_keyboards import get_menu_keyboard
from bot.features.search.search_gs_keyboards import (
    get_gs_results_keyboard,
    get_gs_entity_detail_keyboard,
    get_gs_add_to_list_keyboard,
)
from database.models_db import EntityDB, UserEntityDB, UserDB
from models.enum_classes import StatusType, SourceApi
from aiogram.fsm.context import FSMContext
from bot.states.fsm_states import SearchStates, MainMenuStates
from bot.formater.message_formater import format_entity_details
from models.factories import build_entity_from_db
from bot.utils.strings import get_string, get_status_string
from bot.features.search_kp.kp_service import KpService
from bot.features.search_omdb.omdb_service import OMDbService
from bot.features.search_kp.kp_utils import kp_details_to_db, kp_ratings_to_db
from bot.features.search_omdb.omdb_utils import omdb_details_to_db, omdb_ratings_to_db
from aiogram.exceptions import TelegramBadRequest

gs_router = Router()
logger = logging.getLogger(__name__)


# Вспомогательные функции для уменьшения дублирования
def parse_callback_data(data: str, expected_parts: int) -> Optional[Tuple]:
    """Парсит callback данные с проверкой количества частей"""
    try:
        parts = data.split(":", expected_parts)
        if (
            len(parts) != expected_parts + 1
        ):  # +1 потому что split возвращает n+1 частей
            return None
        return tuple(parts[1:])  # Пропускаем префикс
    except (ValueError, IndexError):
        return None


def get_message_from_callback(callback: Union[CallbackQuery, Message]) -> Message:
    """Получает сообщение из callback или message"""
    return callback.message if isinstance(callback, CallbackQuery) else callback


async def safe_edit_or_send_message(
    message: Message, text: str, reply_markup=None, parse_mode: str = None
) -> None:
    """Безопасно редактирует или отправляет сообщение, обрабатывая фото"""
    if getattr(message, "photo", None):
        await message.delete()
        await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
    else:
        try:
            await message.edit_text(
                text, reply_markup=reply_markup, parse_mode=parse_mode
            )
        except TelegramBadRequest:
            await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)


async def safe_send_photo_or_text(
    message: Message, photo_url: str, caption: str, reply_markup=None
) -> None:
    """Безопасно отправляет фото или текст, обрабатывая ошибки"""
    if photo_url and photo_url != "N/A":
        await message.delete()
        try:
            await message.answer_photo(
                photo_url, caption=caption, reply_markup=reply_markup
            )
        except TelegramBadRequest:
            await message.answer(caption, reply_markup=reply_markup)
    else:
        await message.edit_text(caption, reply_markup=reply_markup)


def get_entity_safe(entity_id: int) -> Optional[EntityDB]:
    """Безопасно получает entity с обработкой ошибок"""
    try:
        return EntityDB.get_by_id(entity_id)
    except EntityDB.DoesNotExist:
        return None


async def handle_error_and_return_to_menu(
    callback: CallbackQuery, state: FSMContext, error_message: str, lang: str
) -> None:
    """Обрабатывает ошибку и возвращает в главное меню"""
    await callback.message.edit_text(error_message)
    await state.clear()
    await state.set_state(MainMenuStates.waiting_for_query)


async def handle_back_to_list(callback: CallbackQuery, state: FSMContext) -> bool:
    """Обрабатывает возврат к списку результатов"""
    success = await show_gs_list(callback=callback, state=state)
    if success:
        await callback.answer()
    return success


async def handle_back_to_entity(
    callback: CallbackQuery, state: FSMContext, entity_id: int
) -> bool:
    """Обрабатывает возврат к деталям entity"""
    success = await show_gs_entity(callback=callback, state=state, entity_id=entity_id)
    if success:
        await callback.answer()
    return success


# API функции
async def get_api_search_list(
    source_api: SourceApi, query: str, page: int
) -> tuple[list, int, bool]:
    """Получает список результатов поиска из API"""
    if source_api == SourceApi.KP:
        try:
            response = await KpService.search_movies_series(query, page)
            if response.get("Response") == "False":
                return [], 0, False
            return response.get("docs", []), int(response.get("total", 0)), True
        except Exception as e:
            logger.error(f"Error getting API response: {e}")
            return [], 0, False
    elif source_api == SourceApi.OMDB:
        try:
            response = await OMDbService.search_movies_series(query, page)
            if response.get("Response") == "False":
                return [], 0, False
            return (
                response.get("Search", []),
                int(response.get("totalResults", 0)),
                True,
            )
        except Exception as e:
            logger.error(f"Error getting API response: {e}")
            return [], 0, False


async def get_api_entity(source_api: SourceApi, api_id: str) -> tuple[dict, bool]:
    """Получает детали entity из API"""
    if source_api == SourceApi.KP:
        try:
            response = await KpService.get_item_details(api_id)
            if response.get("Response") == "False":
                return {}, False
            return response, True
        except Exception as e:
            logger.error(f"Error getting entity details: {e}")
            return {}, False
    elif source_api == SourceApi.OMDB:
        try:
            response = await OMDbService.get_item_details(api_id)
            if response.get("Response") == "False":
                return {}, False
            return response, True
        except Exception as e:
            logger.error(f"Error getting entity details: {e}")
            return {}, False


def get_entity_from_db(source_api: SourceApi, api_id: str) -> EntityDB:
    """Получает entity из базы данных по API ID"""
    if source_api == SourceApi.KP:
        return EntityDB.get_or_none(kp_id=api_id)
    elif source_api == SourceApi.OMDB:
        return EntityDB.get_or_none(src_id=api_id)


def add_entity_to_db(source_api: SourceApi, data: dict) -> EntityDB | None:
    """Добавляет entity в базу данных"""
    if source_api == SourceApi.KP:
        try:
            entity, created = kp_details_to_db(data)
        except Exception as e:
            logger.error(f"Error adding entity to database: {e}")
            return None
        try:
            ratings = kp_ratings_to_db(entity, data)
        except Exception as e:
            logger.error(f"Error adding ratings to database: {e}")
            return None
        return entity
    elif source_api == SourceApi.OMDB:
        try:
            entity, created = omdb_details_to_db(data)
        except Exception as e:
            logger.error(f"Error adding entity to database: {e}")
            return None
        try:
            ratings = omdb_ratings_to_db(entity, data)
        except Exception as e:
            logger.error(f"Error adding ratings to database: {e}")
            return None
        return entity
    return None


# Основные функции отображения
async def show_gs_list(
    callback: CallbackQuery,
    state: FSMContext,
) -> bool:
    """Показывает результаты поиска по запросу"""
    state_data = await state.get_data()
    source_api = state_data.get("source_api")
    query = state_data.get("query")
    lang = state_data.get("lang")
    page = state_data.get("page", 1)

    results, total_results, success = await get_api_search_list(source_api, query, page)
    if not success:
        await handle_error_and_return_to_menu(
            callback, state, get_string("error_getting_results", lang), lang
        )
        return False

    if not results:
        await callback.message.edit_text(
            get_string("nothing_found_query", lang).format(query=query)
        )
        await state.clear()
        await state.set_state(MainMenuStates.waiting_for_query)
        return False

    keyboard = get_gs_results_keyboard(
        results=results,
        source_api=source_api,
        page=page,
        total_results=total_results,
        lang=lang,
    )

    title_text = get_string("found_results", lang).format(
        total_results=total_results, query=query
    )

    await safe_edit_or_send_message(
        callback.message, title_text, keyboard, parse_mode="HTML"
    )
    await state.set_state(SearchStates.waiting_for_gs_select_entity)
    return True


async def show_gs_entity(
    callback: CallbackQuery,
    state: FSMContext,
    entity_id: int = None,
    api_id: str = None,
) -> bool:
    """Показывает детали entity"""
    state_data = await state.get_data()
    source_api = state_data.get("source_api")
    lang = state_data.get("lang")
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    entity = None

    if entity_id:
        entity = get_entity_safe(entity_id)
        # Сохраняем entity_id в state для возможности возврата
        await state.update_data(current_entity_id=entity_id)
    elif api_id:
        data, success = await get_api_entity(source_api, api_id)
        if not success:
            await handle_error_and_return_to_menu(
                callback, state, get_string("error_getting_entity", lang), lang
            )
            return False
        entity = add_entity_to_db(source_api, data)
        if not entity:
            await handle_error_and_return_to_menu(
                callback, state, get_string("error_getting_entity", lang), lang
            )
            return False
        # Сохраняем entity_id в state для возможности возврата
        await state.update_data(current_entity_id=entity.id)

    if entity is None:
        await handle_error_and_return_to_menu(
            callback, state, get_string("error_getting_entity", lang), lang
        )
        return False

    entity_full = build_entity_from_db(entity)
    message = format_entity_details(entity_full, lang)

    already_added = False
    if user:
        already_added = (
            UserEntityDB.select()
            .join(EntityDB)
            .where(
                (UserEntityDB.user_id == user)
                & (
                    (UserEntityDB.entity == entity)
                    | (
                        (EntityDB.src_id == entity.src_id)
                        & (EntityDB.src_id.is_null(False))
                    )
                )
            )
            .exists()
        )

    keyboard = get_gs_entity_detail_keyboard(
        entity_id=entity_full.id,
        lang=lang,
        already_added=already_added,
    )

    await safe_send_photo_or_text(
        callback.message, entity_full.poster_url, message, keyboard
    )
    await state.set_state(SearchStates.waiting_for_gs_action_entity)
    await callback.answer()
    return True


# Обработчики callback
@gs_router.callback_query(SearchStates.waiting_for_gs_select_entity)
async def handle_gs_select_entity(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("lang")
    data = callback.data

    if data == "gs_page_prev":
        current_page = state_data.get("page", 1)
        if current_page > 1:
            await state.update_data(page=current_page - 1)
            await handle_back_to_list(callback, state)

    elif data == "gs_page_next":
        current_page = state_data.get("page", 1)
        await state.update_data(page=current_page + 1)
        await handle_back_to_list(callback, state)

    elif data.startswith("gs_select:"):
        parsed = parse_callback_data(data, 1)
        if not parsed:
            await callback.answer("Invalid callback data")
            return
        api_id = parsed[0]

        success = await show_gs_entity(
            callback=callback,
            state=state,
            api_id=api_id,
        )
        if success:
            await callback.answer()

    elif data == "gs_filter":
        await callback.answer(get_string("feature_developing", lang), show_alert=False)

    elif data == "gs_cancel":
        await callback.message.delete()
        await callback.message.answer(
            get_string("start_message", lang),
            reply_markup=get_menu_keyboard(lang),
        )
        await state.clear()
        await state.set_state(MainMenuStates.waiting_for_query)
        await callback.answer()

    elif data == "noop":
        await callback.answer()


@gs_router.callback_query(SearchStates.waiting_for_gs_action_entity)
async def handle_gs_action_entity(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("lang")
    data = callback.data

    if data == "gs_back":
        await handle_back_to_list(callback, state)

    elif data.startswith("gs_add:"):
        parsed = parse_callback_data(data, 1)
        if not parsed:
            await callback.answer("Invalid callback data")
            return
        entity_id = int(parsed[0])

        # Получаем название сущности для отображения
        entity = get_entity_safe(entity_id)
        entity_name = entity.title if entity else "Entity Name"

        title_text = get_string("select_status_type_for", lang).format(
            entity_name=entity_name
        )
        keyboard = get_gs_add_to_list_keyboard(entity_id=entity_id, lang=lang)

        await safe_edit_or_send_message(
            callback.message, title_text, keyboard, parse_mode="HTML"
        )

        # Переходим в состояние ожидания выбора статуса
        await state.set_state(SearchStates.waiting_for_gs_add_to_list)
        await callback.answer()


@gs_router.callback_query(SearchStates.waiting_for_gs_add_to_list)
async def handle_gs_add_to_list(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("lang")
    data = callback.data
    user = UserDB.get_or_none(tg_id=callback.from_user.id)

    if data == "gs_back":
        # Возвращаемся к деталям entity
        entity_id = state_data.get("current_entity_id")
        if entity_id:
            success = await show_gs_entity(
                callback=callback,
                state=state,
                entity_id=entity_id,
            )
            if success:
                await state.set_state(SearchStates.waiting_for_gs_action_entity)
                await callback.answer()
        else:
            await handle_back_to_list(callback, state)

    elif data.startswith("gs_add_select:"):
        parsed = parse_callback_data(data, 2)
        if not parsed:
            await callback.answer("Invalid callback data")
            return
        entity_id, status = int(parsed[0]), parsed[1]

        try:
            status = StatusType(status)
        except ValueError:
            await callback.answer("Invalid status")
            return

        try:
            entity = get_entity_safe(entity_id)
            if not entity:
                await callback.answer("Entity not found")
                return

            user_entity, created = UserEntityDB.get_or_create(
                user=user, entity=entity, defaults={"status": status}
            )

            if not created:
                user_entity.status = status
                user_entity.save()

            # Показываем сообщение об успехе
            success_message = f"{get_string('entity_added_to_list', lang).format(
                entity_title=entity.title,
                status_type=get_status_string(status.value, lang),
            )}\n\n{get_string('start_message', lang)}"
            await callback.message.delete()
            await callback.message.answer(
                success_message,
                reply_markup=get_menu_keyboard(lang),
            )
            await state.clear()
            await state.set_state(MainMenuStates.waiting_for_query)

        except Exception as e:
            # Обрабатываем ошибку
            logger.error(f"Error adding to list: {str(e)}")
            await callback.message.delete()
            await callback.message.answer(f"Error adding to list: {str(e)}")
            await state.clear()
            await state.set_state(MainMenuStates.waiting_for_query)
        await callback.answer()
