import logging
from aiogram.types import CallbackQuery
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

logger = logging.getLogger(__name__)

search_router = Router()


def is_cyrillic(text):
    return bool(re.search("[а-яА-ЯёЁ]", text))


@search_router.callback_query(MainMenuStates.waiting_for_query)
@search_router.message(lambda m: m.text not in get_all_commands())
async def handle_text(message: types.Message, state: FSMContext):
    logger.info(f"handle_text: {message.text}")
    user = UserDB.get_or_none(tg_id=message.from_user.id)
    lang = user.language if user else "en"
    await state.clear()
    await state.set_state(SearchStates.waiting_for_search_type)
    await state.update_data(
        query=message.text, entity_type_search=EntityType.ALL, lang=lang
    )
    await message.answer(
        get_string("search_choose_question", lang),
        reply_markup=get_choose_type_search_keyboard(lang),
    )


@search_router.callback_query(SearchStates.waiting_for_search_type)
async def handle_search_type(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    state_data = await state.get_data()
    query = state_data.get("query")
    lang = state_data.get("lang")
    page = 1

    if data == "search_global":
        if is_cyrillic(query):
            await state.update_data(source_api=SourceApi.KP)
            await callback.message.edit_text(get_string("searching_please_wait", lang))
            success = await show_gs_list(
                callback=callback,
                page=page,
                state=state,
            )
            if success:
                await callback.answer()
                return
            else:
                await state.clear()
                await state.set_state(MainMenuStates.waiting_for_query)
        else:
            await state.update_data(source_api=SourceApi.OMDB)
            await callback.message.edit_text(get_string("searching_please_wait", lang))
            success = await show_gs_list(
                callback=callback,
                page=page,
                state=state,
            )
            if success:
                await callback.answer()
                return
            else:
                await state.clear()
                await state.set_state(MainMenuStates.waiting_for_query)
    elif data == "search_local":
        await state.update_data(status_type=StatusType.ALL)
        await callback.message.edit_text(get_string("searching_please_wait", lang))
        success = await show_ls_list(
            callback=callback,
            page=page,
            state=state,
        )

        if success:
            await state.set_state(UserListStates.waiting_for_ls_select_entity)
            await callback.answer()
            return
        else:
            await state.clear()
            await state.set_state(MainMenuStates.waiting_for_query)
            await callback.message.answer(
                get_string("start_message", lang),
                reply_markup=get_menu_keyboard(lang),
            )
            await callback.answer()
            return
