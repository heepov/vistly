import logging
from typing import Optional, Tuple, Union, Any
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
from models.enum_classes import StatusType
from bot.states.fsm_states import MainMenuStates, UserListStates
from bot.shared.other_keyboards import get_menu_keyboard
from bot.formater.message_formater import format_entity_details
from database.models_db import UserEntityDB, EntityDB
from aiogram import Router
from models.factories import build_entity_from_db
from bot.utils.strings import get_string, get_status_string
from peewee import fn
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)

user_list_router = Router()


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


def get_user_entity_safe(user_entity_id: int) -> Optional[UserEntityDB]:
    """Безопасно получает user_entity с обработкой ошибок"""
    try:
        return UserEntityDB.get_by_id(user_entity_id)
    except UserEntityDB.DoesNotExist:
        return None


async def handle_back_to_entity(
    callback: CallbackQuery, state: FSMContext, user_entity_id: int
) -> bool:
    """Обрабатывает возврат к деталям entity"""
    success = await show_ls_entity(
        callback=callback,
        state=state,
        user_entity_id=user_entity_id,
    )
    if success:
        await callback.answer()
    return success


async def handle_back_to_list(
    callback: CallbackQuery, state: FSMContext, page: int = None
) -> bool:
    """Обрабатывает возврат к списку"""
    if page is not None:
        await state.update_data(page=page)

    success = await show_ls_list(callback, state)
    if success:
        await callback.answer()
    return success


async def show_ls_list(
    callback: CallbackQuery | Message,
    state: FSMContext = None,
) -> bool:
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    state_data = await state.get_data()
    query_text = state_data.get("query")
    entity_type_search = state_data.get("entity_type_search")
    status_type = state_data.get("status_type")
    lang = state_data.get("lang")
    page = state_data.get("page", 1)

    msg = get_message_from_callback(callback)

    query = (
        UserEntityDB.select()
        .join(EntityDB)
        .where(UserEntityDB.user_id == user)
        .order_by(UserEntityDB.updated_db.desc())
    )

    if query_text and query_text != "":
        query = query.where(fn.LOWER(EntityDB.title).contains(query_text.lower()))

    total_results = query.count()

    if total_results == 0 or total_results is None:
        await state.clear()
        await state.set_state(MainMenuStates.waiting_for_query)
        await msg.answer(
            f'{get_string("user_list_empty", lang)}',
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

    await safe_edit_or_send_message(msg, title_text, keyboard, parse_mode="HTML")

    await state.set_state(UserListStates.waiting_for_ls_select_entity)
    return True


async def show_ls_entity(
    callback: CallbackQuery | Message,
    state: FSMContext,
    user_entity_id: int,
) -> bool:
    state_data = await state.get_data()
    lang = state_data.get("lang")
    page = state_data.get("page", 1)
    user_entity = UserEntityDB.get_or_none(id=user_entity_id)
    if not user_entity:
        await callback.answer("Not found")
        return False

    entity = user_entity.entity
    entity_full = build_entity_from_db(entity)
    text = format_entity_details(entity_full, lang)
    keyboard = get_ls_detail_keyboard(
        user_entity=user_entity,
        lang=lang,
    )

    msg = get_message_from_callback(callback)

    if entity.poster_url and entity.poster_url != "N/A":
        await msg.delete()
        try:
            await msg.answer_photo(
                entity.poster_url, caption=text, reply_markup=keyboard
            )
        except TelegramBadRequest:
            await msg.edit_text(text, reply_markup=keyboard)
    else:
        await msg.edit_text(text, reply_markup=keyboard)

    await state.set_state(UserListStates.waiting_for_ls_action_entity)
    await callback.answer()
    return True


@user_list_router.callback_query(UserListStates.waiting_for_ls_select_entity)
async def handle_ls_select_entity(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("lang")
    data = callback.data

    if data.startswith("ls_page:"):
        parsed = parse_callback_data(data, 1)
        if not parsed:
            await callback.answer("Invalid callback data")
            return
        page = int(parsed[0])
        await handle_back_to_list(callback, state, page)

    elif data.startswith("ls_status:"):
        parsed = parse_callback_data(data, 1)
        if not parsed:
            await callback.answer("Invalid callback data")
            return

        try:
            status = StatusType(parsed[0])
        except ValueError:
            await callback.answer("Invalid callback data")
            return

        # Проверяем, изменился ли статус
        current_status = state_data.get("status_type")
        if current_status == status:
            await callback.answer()
            return

        # Обновляем статус и сбрасываем на первую страницу
        await state.update_data(status_type=status)
        await handle_back_to_list(callback, state, page=1)

    elif data == "cancel":
        await callback.message.delete()
        await callback.message.answer(
            get_string("start_message", lang),
            reply_markup=get_menu_keyboard(lang),
        )
        await state.clear()
        await state.set_state(MainMenuStates.waiting_for_query)
        await callback.answer()

    elif data.startswith("ls_select:"):
        parsed = parse_callback_data(data, 1)
        if not parsed:
            await callback.answer("Invalid callback data")
            return

        user_entity_id = int(parsed[0])
        success = await show_ls_entity(
            callback=callback,
            state=state,
            user_entity_id=user_entity_id,
        )
        if success:
            await callback.answer()


@user_list_router.callback_query(UserListStates.waiting_for_ls_action_entity)
async def handle_ls_action_entity(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("lang")
    page = state_data.get("page", 1)
    data = callback.data
    title_text = keyboard = None

    if data.startswith("ls_select_rate:"):
        parsed = parse_callback_data(data, 1)
        if not parsed:
            await callback.answer("Invalid callback data")
            return

        user_entity_id = int(parsed[0])
        user_entity = get_user_entity_safe(user_entity_id)
        if not user_entity:
            await callback.answer("Entity not found")
            return

        entity = user_entity.entity
        await state.set_state(UserListStates.waiting_for_ls_entity_change_rating)
        title_text = get_string("ask_rating", lang).format(
            entity_type=entity.type, entity_name=entity.title
        )
        keyboard = get_rating_keyboard(user_entity_id, lang)

    elif data.startswith("ls_select_status:"):
        parsed = parse_callback_data(data, 1)
        if not parsed:
            await callback.answer("Invalid callback data")
            return

        user_entity_id = int(parsed[0])
        user_entity = get_user_entity_safe(user_entity_id)
        if not user_entity:
            await callback.answer("Entity not found")
            return

        entity = user_entity.entity
        await state.set_state(UserListStates.waiting_for_ls_entity_change_status)
        title_text = get_string("ask_status", lang).format(
            entity_type=entity.type, entity_name=entity.title
        )
        keyboard = get_status_keyboard(user_entity_id, lang)

    elif data.startswith("ls_select_season:"):
        parsed = parse_callback_data(data, 1)
        if not parsed:
            await callback.answer("Invalid callback data")
            return

        user_entity_id = int(parsed[0])
        user_entity = get_user_entity_safe(user_entity_id)
        if not user_entity:
            await callback.answer("Entity not found")
            return

        entity = user_entity.entity
        await state.set_state(UserListStates.waiting_for_ls_entity_change_season)
        title_text = get_string("ask_season", lang).format(
            entity_type=entity.type, entity_name=entity.title
        )
        keyboard = get_season_number_keyboard(
            user_entity_id=user_entity_id,
            season=user_entity.current_season or 1,
            lang=lang,
        )

    elif data.startswith("ls_select_delete"):
        parsed = parse_callback_data(data, 1)
        if not parsed:
            await callback.answer("Invalid callback data")
            return

        user_entity_id = int(parsed[0])
        user_entity = get_user_entity_safe(user_entity_id)
        if not user_entity:
            await callback.answer("Entity not found")
            return

        entity = user_entity.entity
        await state.set_state(UserListStates.waiting_for_ls_entity_delete_entity)
        title_text = get_string("ask_delete", lang).format(
            entity_type=get_string(entity.type, lang), entity_name=entity.title
        )
        keyboard = get_delete_confirm_keyboard(user_entity_id, lang)

    elif data.startswith("ls_back:"):
        await handle_back_to_list(callback, state)
        return

    if title_text and keyboard:
        await safe_edit_or_send_message(
            callback.message, title_text, keyboard, parse_mode="HTML"
        )
    await callback.answer()


@user_list_router.callback_query(UserListStates.waiting_for_ls_entity_change_rating)
async def handle_ls_set_rating(callback: CallbackQuery, state: FSMContext):
    user_entity_id = None

    if callback.data.startswith("ls_set_rating:"):
        parsed = parse_callback_data(callback.data, 2)
        if not parsed:
            await callback.answer("Invalid callback data")
            return

        user_entity_id, rating = int(parsed[0]), int(parsed[1])
        user_entity = get_user_entity_safe(user_entity_id)
        if user_entity:
            user_entity.user_rating = rating
            user_entity.save()

    elif callback.data.startswith("ls_back:"):
        parsed = parse_callback_data(callback.data, 1)
        if not parsed:
            await callback.answer("Invalid callback data")
            return

        user_entity_id = int(parsed[0])
    else:
        await callback.answer("Unknown action")
        return

    await handle_back_to_entity(callback, state, user_entity_id)


@user_list_router.callback_query(UserListStates.waiting_for_ls_entity_change_status)
async def handle_ls_set_status(callback: CallbackQuery, state: FSMContext):
    user_entity_id = None

    if callback.data.startswith("ls_set_status:"):
        parsed = parse_callback_data(callback.data, 2)
        if not parsed:
            await callback.answer("Invalid callback data")
            return

        user_entity_id, status = int(parsed[0]), parsed[1]
        try:
            status = StatusType(status)
        except ValueError:
            await callback.answer("Invalid status")
            return

        user_entity = get_user_entity_safe(user_entity_id)
        if user_entity:
            user_entity.status = status
            user_entity.save()

    elif callback.data.startswith("ls_back:"):
        parsed = parse_callback_data(callback.data, 1)
        if not parsed:
            await callback.answer("Invalid callback data")
            return

        user_entity_id = int(parsed[0])
    else:
        await callback.answer("Unknown action")
        return

    await handle_back_to_entity(callback, state, user_entity_id)


@user_list_router.callback_query(UserListStates.waiting_for_ls_entity_change_season)
async def handle_ls_set_season(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang")
    page = data.get("page", 1)
    user_entity_id = None

    if callback.data.startswith("ls_set_season_clean:"):
        parsed = parse_callback_data(callback.data, 1)
        if not parsed:
            await callback.answer("Invalid callback data")
            return

        user_entity_id = int(parsed[0])
        user_entity = get_user_entity_safe(user_entity_id)
        if user_entity:
            user_entity.current_season = None
            user_entity.save()

    elif callback.data.startswith("ls_set_season_confirm:"):
        parsed = parse_callback_data(callback.data, 2)
        if not parsed:
            await callback.answer("Invalid callback data")
            return

        user_entity_id, season = int(parsed[0]), int(parsed[1])
        user_entity = get_user_entity_safe(user_entity_id)
        if user_entity:
            user_entity.current_season = season
            user_entity.save()

    elif callback.data.startswith("ls_set_season:"):
        parsed = parse_callback_data(callback.data, 2)
        if not parsed:
            await callback.answer("Invalid callback data")
            return

        user_entity_id, season = int(parsed[0]), int(parsed[1])
        keyboard = get_season_number_keyboard(user_entity_id, season, lang)
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer()
        return
    else:
        await callback.answer("Unknown action")
        return

    await handle_back_to_entity(callback, state, user_entity_id)


@user_list_router.callback_query(UserListStates.waiting_for_ls_entity_delete_entity)
async def handle_ls_entity_delete(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("lang")
    user_entity_id = None

    if callback.data.startswith("ls_set_delete:"):
        parsed = parse_callback_data(callback.data, 2)
        if not parsed:
            await callback.answer("Invalid callback data")
            return

        user_entity_id, del_confirm = int(parsed[0]), bool(parsed[1])
        if del_confirm:
            user_entity = get_user_entity_safe(user_entity_id)
            if user_entity:
                user_entity.delete_instance()

            await handle_back_to_list(callback, state, page=1)
            return

    elif callback.data.startswith("ls_back:"):
        parsed = parse_callback_data(callback.data, 1)
        if not parsed:
            await callback.answer("Invalid callback data")
            return

        user_entity_id = int(parsed[0])
    else:
        await callback.answer("Unknown action")
        return

    await handle_back_to_entity(callback, state, user_entity_id)
