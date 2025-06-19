import logging
from typing import Optional, Union
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from models.enum_classes import SourceApi, EntityType, StatusType
from bot.features.search.search_gs_handlers import show_gs_list
from bot.states.fsm_states import MainMenuStates, SearchStates, UserListStates
from aiogram import Router, types
from bot.shared.other_keyboards import (
    get_choose_type_search_keyboard,
    get_menu_keyboard,
)
from bot.utils.strings import get_string, get_all_commands
from database.models_db import UserDB
import re
from bot.features.user_list.user_list_handlers import show_ls_list
from bot.shared.user_service import ensure_user_exists

logger = logging.getLogger(__name__)

search_router = Router()


# Вспомогательные функции
def is_cyrillic(text: str) -> bool:
    """Проверяет, содержит ли текст кириллические символы"""
    return bool(re.search("[а-яА-ЯёЁ]", text))


def get_user_language(user_id: int) -> str:
    """Получает язык пользователя"""
    user = UserDB.get_or_none(tg_id=user_id)
    return user.language if user else "en"


async def handle_search_failure(
    callback: CallbackQuery, state: FSMContext, lang: str
) -> None:
    """Обрабатывает неудачный поиск"""
    await state.clear()
    await state.set_state(MainMenuStates.waiting_for_query)
    # Не удаляем сообщение, так как оно может быть уже изменено или удалено
    await callback.message.answer(
        get_string("start_message", lang),
        reply_markup=get_menu_keyboard(lang),
    )
    await callback.answer()


async def safe_delete_message(message):
    """Безопасно удаляет сообщение с обработкой ошибок"""
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Failed to delete message: {e}")


async def perform_global_search(
    callback: CallbackQuery, state: FSMContext, query: str, lang: str
) -> bool:
    """Выполняет глобальный поиск"""
    page = 1

    # Определяем API на основе языка запроса
    source_api = SourceApi.KP if is_cyrillic(query) else SourceApi.OMDB
    await state.update_data(source_api=source_api)

    await callback.message.edit_text(get_string("searching_please_wait", lang))

    success = await show_gs_list(
        callback=callback,
        state=state,
    )

    if success:
        await callback.answer()
        return True
    else:
        await handle_search_failure(callback, state, lang)
        return False


async def perform_local_search(
    callback: CallbackQuery, state: FSMContext, lang: str
) -> bool:
    """Выполняет локальный поиск"""
    page = 1
    await state.update_data(status_type=StatusType.ALL)

    await callback.message.edit_text(get_string("searching_please_wait", lang))

    success = await show_ls_list(
        callback=callback,
        state=state,
    )

    if success:
        await safe_delete_message(callback.message)
        await state.set_state(UserListStates.waiting_for_ls_select_entity)
        await callback.answer()
        return True
    else:
        await handle_search_failure(callback, state, lang)
        return False


# Обработчики
@search_router.callback_query(MainMenuStates.waiting_for_query)
@search_router.message(lambda m: m.text and m.text not in get_all_commands())
async def handle_search_text(
    message: Union[types.Message, CallbackQuery], state: FSMContext
):
    """Обрабатывает текстовый поисковый запрос"""
    if not await ensure_user_exists(message, state):
        return

    current_state = await state.get_state()
    lang = get_user_language(message.from_user.id)

    if current_state != MainMenuStates.waiting_for_query.state:
        await message.answer(
            get_string("error_message", lang),
            reply_markup=get_menu_keyboard(lang),
        )
        return

    await state.clear()
    await state.set_state(SearchStates.waiting_for_search_type)
    await state.update_data(
        query=message.text,
        entity_type_search=EntityType.ALL,
        lang=lang,
        page=1,  # Инициализируем страницу
    )

    await message.answer(
        get_string("search_choose_question", lang),
        reply_markup=get_choose_type_search_keyboard(lang),
    )


@search_router.callback_query(SearchStates.waiting_for_search_type)
async def handle_search_type(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор типа поиска"""
    data = callback.data
    state_data = await state.get_data()
    query = state_data.get("query")
    lang = state_data.get("lang")

    if data == "search_global":
        await perform_global_search(callback, state, query, lang)
    elif data == "search_local":
        await perform_local_search(callback, state, lang)
