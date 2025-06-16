import logging
from aiogram import Router
from aiogram.types import CallbackQuery
from bot.shared.other_keyboards import get_menu_keyboard
from bot.features.search.search_gs_keyboards import (
    get_gs_results_keyboard,
    get_gs_entity_detail_keyboard,
    get_gs_add_to_list_keyboard,
)
from database.models_db import EntityDB, UserEntityDB, UserDB
from models.enum_classes import EntityType, StatusType, SourceApi
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


async def get_api_search_list(
    source_api: SourceApi, query: str, page: int
) -> tuple[list, int, bool]:
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
    if source_api == SourceApi.KP:
        return EntityDB.get_or_none(kp_id=api_id)
    elif source_api == SourceApi.OMDB:
        return EntityDB.get_or_none(src_id=api_id)


def add_entity_to_db(source_api: SourceApi, data: dict) -> EntityDB | None:
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


async def show_gs_list(
    callback: CallbackQuery,
    page: int,
    state: FSMContext,
) -> bool:
    state_data = await state.get_data()
    source_api = state_data.get("source_api")
    query = state_data.get("query")
    entity_type_search = state_data.get("entity_type_search")
    lang = state_data.get("lang")
    """Показывает результаты поиска по запросу"""
    results, total_results, success = await get_api_search_list(source_api, query, page)
    if not success:
        await callback.message.edit_text(get_string("error_getting_results", lang))
        await state.set_state(MainMenuStates.waiting_for_query)
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

    if getattr(callback.message, "photo", None):
        await callback.message.delete()
        await callback.message.answer(
            title_text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            title_text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    await state.set_state(SearchStates.waiting_for_gs_select_entity)
    return True


async def show_gs_entity(
    callback: CallbackQuery,
    page: int,
    state: FSMContext,
    entity_id: int = None,
    api_id: str = None,
) -> bool:
    state_data = await state.get_data()
    source_api = state_data.get("source_api")
    lang = state_data.get("lang")
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    entity = None

    if entity_id:
        entity = EntityDB.get_by_id(entity_id)
    elif api_id:
        data, success = await get_api_entity(source_api, api_id)
        if not success:
            await callback.message.edit_text(get_string("error_getting_entity", lang))
            await state.clear()
            await state.set_state(MainMenuStates.waiting_for_query)
            return False
        entity = add_entity_to_db(source_api, data)
        if not entity:
            await callback.message.edit_text(get_string("error_getting_entity", lang))
            await state.clear()
            await state.set_state(MainMenuStates.waiting_for_query)
            return False

    if entity is None:
        await callback.message.edit_text(get_string("error_getting_entity", lang))
        await state.clear()
        await state.set_state(MainMenuStates.waiting_for_query)
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
                & ((UserEntityDB.entity == entity) | (EntityDB.src_id == entity.src_id))
            )
            .exists()
        )

    if entity_full.poster_url and entity_full.poster_url != "N/A":
        await callback.message.delete()
        try:
            await callback.message.answer_photo(
                entity_full.poster_url,
                caption=message,
                reply_markup=get_gs_entity_detail_keyboard(
                    entity_id=entity_full.id,
                    page=page,
                    lang=lang,
                    already_added=already_added,
                ),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                message,
                reply_markup=get_gs_entity_detail_keyboard(
                    entity_id=entity_full.id,
                    page=page,
                    lang=lang,
                    already_added=already_added,
                ),
            )
    else:
        await callback.message.edit_text(
            message,
            reply_markup=get_gs_entity_detail_keyboard(
                entity_id=entity_full.id,
                page=page,
                lang=lang,
                already_added=already_added,
            ),
        )
    await state.set_state(SearchStates.waiting_for_gs_action_entity)
    await callback.answer()
    return True


@gs_router.callback_query(SearchStates.waiting_for_gs_select_entity)
async def handle_gs_select_entity(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    source_api = state_data.get("source_api")
    lang = state_data.get("lang")
    data = callback.data

    if data.startswith("gs_page:"):
        try:
            _, page = data.split(":", 1)
            page = int(page)
        except (ValueError, IndexError):
            logger.error(f"Invalid callback data: {data}")
            await callback.answer("Invalid callback data")
            return

        success = await show_gs_list(
            callback=callback,
            page=page,
            state=state,
        )
        if success:
            await callback.answer()
            return
        return

    elif data.startswith("gs_select:"):
        try:
            _, page, api_id = data.split(":", 3)
            page = int(page)
        except (ValueError, IndexError):
            logger.error(f"Invalid callback data: {data}")
            await callback.answer("Invalid callback data")
            return

        success = await show_gs_entity(
            callback=callback,
            page=page,
            state=state,
            api_id=api_id,
        )
        if success:
            await callback.answer()
        return

    elif data.startswith("gs_filter:"):
        await callback.answer(get_string("feature_developing", lang), show_alert=False)
        return

    elif data == "gs_cancel":
        await callback.message.delete()
        await callback.message.answer(
            get_string("start_message", lang),
            reply_markup=get_menu_keyboard(lang),
        )
        await state.clear()
        await state.set_state(MainMenuStates.waiting_for_query)
        await callback.answer()
        return

    elif data == "noop":
        await callback.answer()
        return


@gs_router.callback_query(SearchStates.waiting_for_gs_action_entity)
async def handle_gs_action_entity(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    source_api = state_data.get("source_api")
    lang = state_data.get("lang")
    data = callback.data

    if data.startswith("gs_back:"):
        try:
            _, page = data.split(":", 2)
            page = int(page)
        except (ValueError, IndexError):
            logger.error(f"Invalid callback data: {data}")
            await callback.answer("Invalid callback data")
            return

        success = await show_gs_list(
            callback=callback,
            page=page,
            state=state,
        )
        if success:
            await state.set_state(SearchStates.waiting_for_gs_select_entity)
            await callback.answer()
            return

    elif data.startswith("gs_add:"):
        try:
            _, page, entity_id = data.split(":", 3)
            page = int(page)
            entity_id = int(entity_id)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return

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
                reply_markup=get_gs_add_to_list_keyboard(
                    entity_id=entity_id,
                    page=page,
                    lang=lang,
                ),
            )
        else:
            # Если обычное текстовое сообщение, можно просто отредактировать его
            await callback.message.edit_text(
                get_string("select_status_type_for", lang).format(
                    entity_name=entity_name
                ),
                reply_markup=get_gs_add_to_list_keyboard(
                    entity_id=entity_id,
                    page=page,
                    lang=lang,
                ),
            )

        # Переходим в состояние ожидания выбора статуса
        await state.set_state(SearchStates.waiting_for_gs_add_to_list)
        await callback.answer()
        return


@gs_router.callback_query(SearchStates.waiting_for_gs_add_to_list)
async def handle_gs_add_to_list_(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("lang")
    data = callback.data
    user = UserDB.get_or_none(tg_id=callback.from_user.id)

    if data.startswith("gs_back:"):
        try:
            _, page, entity_id = data.split(":", 3)
            page = int(page)
            entity_id = int(entity_id)
        except (ValueError, IndexError):
            logger.error(f"Invalid callback data: {data}")
            await callback.answer("Invalid callback data")
            return

        success = await show_gs_entity(
            callback=callback,
            page=page,
            state=state,
            entity_id=entity_id,
        )
        if success:
            await callback.answer()
        return

    if data.startswith("gs_add_select:"):
        try:
            _, page, entity_id, status = data.split(":", 7)
            page = int(page)
            entity_id = int(entity_id)
            status = StatusType(status)
        except (ValueError, IndexError):
            logger.error(f"Invalid callback data: {data}")
            await callback.answer("Invalid callback data")
            return

        try:
            entity = EntityDB.get_by_id(entity_id)

            user_entity, created = UserEntityDB.get_or_create(
                user=user, entity=entity, defaults={"status": status}
            )

            if not created:
                user_entity.status = status
                user_entity.save()

            # Показываем сообщение об успехе
            success_message = get_string("entity_added_to_list", lang).format(
                entity_title=entity.title,
                status_type=get_status_string(status.value, lang),
            )
            await callback.message.delete()
            await callback.message.answer(success_message)
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
        return
