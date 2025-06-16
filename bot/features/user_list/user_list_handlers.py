import logging
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from bot.features.user_list.user_list_keyboards import (
    get_ls_results_keyboard,
    get_ls_detail_keyboard,
    get_rating_keyboard,
    get_status_keyboard,
    get_delete_confirm_keyboard,
    get_season_number_keyboard,
)
from database.models_db import UserEntityDB, UserDB
from models.enum_classes import StatusType, EntityType
from bot.states.fsm_states import MainMenuStates, UserListStates
from bot.shared.other_keyboards import get_menu_keyboard
from bot.formater.message_formater import format_entity_details
from database.models_db import UserEntityDB, EntityDB
from aiogram import Router, types
from models.factories import build_entity_from_db
from bot.utils.strings import get_string, get_status_string
from peewee import fn
from aiogram.exceptions import TelegramBadRequest
from config.config import BOT_USERNAME

logger = logging.getLogger(__name__)

user_list_router = Router()


async def show_ls_list(
    callback: CallbackQuery | Message,
    page: int,
    state: FSMContext = None,
) -> bool:
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    state_data = await state.get_data()
    query_text = state_data.get("query")
    entity_type_search = state_data.get("entity_type_search")
    status_type = state_data.get("status_type")
    lang = state_data.get("lang")

    if isinstance(callback, CallbackQuery):
        msg = callback.message
    else:
        msg = callback

    query = (
        UserEntityDB.select()
        .join(EntityDB)
        .where(UserEntityDB.user_id == user)
        .order_by(UserEntityDB.updated_db.desc())
    )

    if query_text and query_text != "":
        query = query.where(fn.LOWER(EntityDB.title).contains(query_text.lower()))

    total_results = query.count()

    if not total_results:
        await state.clear()
        await state.set_state(MainMenuStates.waiting_for_query)
        await msg.edit_text(
            f'{get_string("user_list_empty", lang)}\n{get_string("start_message", lang)}',
            reply_markup=get_menu_keyboard(lang),
        )
        return False

    if status_type != StatusType.ALL:
        query = query.where(UserEntityDB.status == status_type)
        total_results = query.count()

    user_entities = list(query.paginate(page, 10))
    keyboard = get_ls_results_keyboard(
        user_entities=user_entities,
        page=page,
        total_results=total_results,
        lang=lang,
    )

    title_text = (
        get_string("user_list_title", lang).format(
            status_text=get_status_string(status_type, lang),
            total_results=total_results,
        )
        if total_results
        else get_string("user_list_empty_status", lang).format(
            status=get_status_string(status_type, lang)
        )
    )

    if getattr(msg, "photo", None):
        await msg.delete()
        await msg.answer(
            title_text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    else:
        try:
            await msg.edit_text(
                title_text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except TelegramBadRequest:
            await msg.answer(
                title_text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

    await state.set_state(UserListStates.waiting_for_ls_select_entity)
    return True


async def show_ls_entity(
    callback: CallbackQuery | Message,
    page: int,
    state: FSMContext,
    user_entity_id: int,
) -> bool:
    state_data = await state.get_data()
    lang = state_data.get("lang")
    user_entity = UserEntityDB.get_or_none(id=user_entity_id)
    if not user_entity:
        await callback.answer("Not found")
        return

    entity = user_entity.entity
    entity_full = build_entity_from_db(entity)
    text = format_entity_details(entity_full, lang)
    keyboard = get_ls_detail_keyboard(
        user_entity=user_entity,
        page=page,
        lang=lang,
    )

    if entity.poster_url and entity.poster_url != "N/A":
        await callback.message.delete()
        try:
            await callback.message.answer_photo(
                entity.poster_url, caption=text, reply_markup=keyboard
            )
        except TelegramBadRequest:
            await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(UserListStates.waiting_for_ls_action_entity)
    await callback.answer()
    return True


@user_list_router.callback_query(UserListStates.waiting_for_ls_select_entity)
async def handle_ls_select_entity(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("lang")
    data = callback.data

    if data.startswith("ls_page:"):
        try:
            _, page = data.split(":", 2)
            page = int(page)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return
        success = await show_ls_list(callback, page, state)
        if success:
            await callback.answer()
    elif data.startswith("ls_status:"):
        try:
            _, status = data.split(":", 2)
            status = StatusType(status)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return
        await state.update_data(status_type=status)
        success = await show_ls_list(callback=callback, page=1, state=state)
        if success:
            await callback.answer()
    elif data == "cancel":
        await callback.message.delete()
        await callback.message.answer(
            get_string("start_message", lang),
            reply_markup=get_menu_keyboard(lang),
        )
        await state.clear()
        await state.set_state(MainMenuStates.waiting_for_query)
        await callback.answer()
        return
    elif data.startswith("ls_select:"):
        try:
            _, page, user_entity_id = data.split(":", 3)
            user_entity_id = int(user_entity_id)
            page = int(page)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return

        success = await show_ls_entity(
            callback=callback,
            page=page,
            state=state,
            user_entity_id=user_entity_id,
        )
        if success:
            await callback.answer()
        return


@user_list_router.callback_query(UserListStates.waiting_for_ls_action_entity)
async def handle_ls_action_entity(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("lang")
    data = callback.data
    title_text = keyboard = None

    if data.startswith("ls_select_rate:"):
        try:
            _, page, user_entity_id = callback.data.split(":", 3)
            user_entity_id = int(user_entity_id)
            page = int(page)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return

        user_entity = UserEntityDB.get_by_id(user_entity_id)
        entity = user_entity.entity

        await state.set_state(UserListStates.waiting_for_ls_entity_change_rating)
        title_text = get_string("ask_rating", lang).format(
            entity_type=entity.type, entity_name=entity.title
        )
        keyboard = get_rating_keyboard(user_entity_id, page, lang)
    elif data.startswith("ls_select_status:"):
        try:
            _, page, user_entity_id = callback.data.split(":", 3)
            user_entity_id = int(user_entity_id)
            page = int(page)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return

        user_entity = UserEntityDB.get_by_id(user_entity_id)
        entity = user_entity.entity

        await state.set_state(UserListStates.waiting_for_ls_entity_change_status)
        title_text = get_string("ask_status", lang).format(
            entity_type=entity.type, entity_name=entity.title
        )
        keyboard = get_status_keyboard(user_entity_id, page, lang)
    elif data.startswith("ls_select_season:"):
        try:
            _, page, user_entity_id = callback.data.split(":", 3)
            user_entity_id = int(user_entity_id)
            page = int(page)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return

        user_entity = UserEntityDB.get_by_id(user_entity_id)
        entity = user_entity.entity

        await state.set_state(UserListStates.waiting_for_ls_entity_change_season)
        title_text = get_string("ask_season", lang).format(
            entity_type=entity.type, entity_name=entity.title
        )
        keyboard = get_season_number_keyboard(
            user_entity_id=user_entity_id,
            season=user_entity.current_season or 1,
            lang=lang,
            page=page,
        )
    elif data.startswith("ls_select_delete"):
        try:
            _, page, user_entity_id = callback.data.split(":", 3)
            user_entity_id = int(user_entity_id)
            page = int(page)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return

        user_entity = UserEntityDB.get_by_id(user_entity_id)
        entity = user_entity.entity

        await state.set_state(UserListStates.waiting_for_ls_entity_delete_entity)
        title_text = get_string("ask_delete", lang).format(
            entity_type=get_string(entity.type, lang), entity_name=entity.title
        )
        keyboard = get_delete_confirm_keyboard(user_entity_id, lang, page)
    elif data.startswith("ls_back:"):
        try:
            _, page = callback.data.split(":", 2)
            page = int(page)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return
        success = await show_ls_list(callback, page, state)
        if success:
            await callback.answer()
            return
        return

    if getattr(callback.message, "photo", None):
        await callback.message.delete()
        await callback.message.answer(
            title_text,
            reply_markup=keyboard,
        )
    else:
        await callback.message.edit_text(
            title_text,
            reply_markup=keyboard,
        )
    await callback.answer()


@user_list_router.callback_query(UserListStates.waiting_for_ls_entity_change_rating)
async def handle_ls_set_rating(callback: CallbackQuery, state: FSMContext):
    page = user_entity_id = rating = None

    if callback.data.startswith("ls_set_rating:"):
        try:
            _, page, user_entity_id, rating = callback.data.split(":", 4)
            user_entity_id = int(user_entity_id)
            page = int(page)
            rating = int(rating)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return
        user_entity = UserEntityDB.get_by_id(user_entity_id)
        user_entity.user_rating = rating
        user_entity.save()
    elif callback.data.startswith("ls_back:"):
        try:
            _, page, user_entity_id = callback.data.split(":", 3)
            user_entity_id = int(user_entity_id)
            page = int(page)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return
    else:
        await callback.answer("Unknown action")
        return

    # Общая обработка результата
    success = await show_ls_entity(
        callback=callback,
        page=page,
        state=state,
        user_entity_id=user_entity_id,
    )
    if success:
        await callback.answer()


@user_list_router.callback_query(UserListStates.waiting_for_ls_entity_change_status)
async def handle_ls_set_status(callback: CallbackQuery, state: FSMContext):
    page = user_entity_id = status = None

    if callback.data.startswith("ls_set_status:"):
        try:
            _, page, user_entity_id, status = callback.data.split(":", 4)
            user_entity_id = int(user_entity_id)
            page = int(page)
            status = StatusType(status)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return
        user_entity = UserEntityDB.get_by_id(user_entity_id)
        user_entity.status = status
        user_entity.save()
    elif callback.data.startswith("ls_back:"):
        try:
            _, page, user_entity_id = callback.data.split(":", 3)
            user_entity_id = int(user_entity_id)
            page = int(page)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return
    else:
        await callback.answer("Unknown action")
        return

    # Общая обработка результата
    success = await show_ls_entity(
        callback=callback,
        page=page,
        state=state,
        user_entity_id=user_entity_id,
    )
    if success:
        await callback.answer()


@user_list_router.callback_query(UserListStates.waiting_for_ls_entity_change_season)
async def handle_ls_set_season(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang")
    page = user_entity_id = status = None

    if callback.data.startswith("ls_set_season_clean:"):
        try:
            _, page, user_entity_id = callback.data.split(":", 3)
            user_entity_id = int(user_entity_id)
            page = int(page)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return
        user_entity = UserEntityDB.get_by_id(user_entity_id)
        user_entity.current_season = None
        user_entity.save()
    elif callback.data.startswith("ls_set_season_confirm:"):
        try:
            _, page, user_entity_id, season = callback.data.split(":", 4)
            user_entity_id = int(user_entity_id)
            page = int(page)
            season = int(season)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return
        user_entity = UserEntityDB.get_by_id(user_entity_id)
        user_entity.current_season = season
        user_entity.save()
    elif callback.data.startswith("ls_set_season:"):
        try:
            _, page, user_entity_id, season = callback.data.split(":", 4)
            user_entity_id = int(user_entity_id)
            page = int(page)
            season = int(season)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return
        keyboard = get_season_number_keyboard(user_entity_id, season, lang, page)
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer()
        return
    else:
        await callback.answer("Unknown action")
        return

    # Общая обработка результата
    success = await show_ls_entity(
        callback=callback,
        page=page,
        state=state,
        user_entity_id=user_entity_id,
    )
    if success:
        await callback.answer()


@user_list_router.callback_query(UserListStates.waiting_for_ls_entity_delete_entity)
async def handle_ls_entity_delete(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("lang")
    page = user_entity_id = None

    if callback.data.startswith("ls_set_delete:"):
        try:
            _, page, user_entity_id, del_confirm = callback.data.split(":", 4)
            user_entity_id = int(user_entity_id)
            page = int(page)
            del_confirm = bool(del_confirm)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return
        if del_confirm:
            user_entity = UserEntityDB.get_by_id(user_entity_id)
            user_entity.delete_instance()

            await callback.message.delete()
            await callback.message.answer(
                get_string("entity_deleted", lang),
            )
            await callback.message.answer(
                get_string("start_message", lang),
                reply_markup=get_menu_keyboard(lang),
            )
            await state.clear()
            await state.set_state(MainMenuStates.waiting_for_query)
            await callback.answer()
            return
    elif callback.data.startswith("ls_back:"):
        try:
            _, page, user_entity_id = callback.data.split(":", 3)
            user_entity_id = int(user_entity_id)
            page = int(page)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return
    else:
        await callback.answer("Unknown action")
        return

    # Общая обработка результата
    success = await show_ls_entity(
        callback=callback,
        page=page,
        state=state,
        user_entity_id=user_entity_id,
    )
    if success:
        await callback.answer()
