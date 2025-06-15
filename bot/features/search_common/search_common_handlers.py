from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.states.fsm_states import SearchStates
from bot.features.search_omdb.omdb_service import OMDbService
from bot.features.search_kp.kp_service import KpService
from bot.features.search_omdb.omdb_search_keyboards import get_search_results_keyboard
from bot.features.search_kp.kp_search_keyboards import get_search_results_keyboard_kp
from bot.states.fsm_states import MainMenuStates, SearchOmdbStates, SearchKpStates
from aiogram import Router
from bot.shared.other_keyboards import get_choose_type_search_keyboard
from aiogram import types
from bot.utils.strings import get_string
from database.models_db import UserDB
import re

search_common_router = Router()

MENU_STRINGS = [
    get_string("restart", "en"),
    get_string("list", "en"),
    get_string("profile", "en"),
    get_string("restart", "ru"),
    get_string("list", "ru"),
    get_string("profile", "ru"),
    "/restart",
    "/list",
    "/profile",
]


def is_cyrillic(text):
    return bool(re.search("[а-яА-ЯёЁ]", text))


@search_common_router.message(lambda m: m.text not in MENU_STRINGS)
async def handle_text(message: types.Message, state: FSMContext):

    user = UserDB.get_or_none(tg_id=message.from_user.id)
    lang = user.language if user else "en"
    current_state = await state.get_state()
    if current_state == MainMenuStates.waiting_for_query:
        await state.set_state(SearchStates.waiting_for_search_type)
        await message.answer(
            get_string("search_choose_question", lang),
            reply_markup=get_choose_type_search_keyboard(message.text, lang),
        )
    else:
        await message.answer(get_string("message_error", lang))


@search_common_router.callback_query(SearchStates.waiting_for_search_type)
async def handle_search_type(callback: CallbackQuery, state: FSMContext):
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    lang = user.language if user else "en"
    data = callback.data
    if data.startswith("search_global:"):
        query = data.split(":", 1)[1]
        page = 1

        # Проверяем язык запроса
        if is_cyrillic(query):
            # --- Поиск по вашему русскому API ---
            await callback.message.edit_text(get_string("searching_please_wait", lang))
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
                await state.set_state(MainMenuStates.waiting_for_query)
                await callback.answer()
            keyboard = get_search_results_keyboard_kp(
                results, query, page, total_results, lang=lang
            )
            await callback.message.edit_text(
                get_string("found_results", lang).format(
                    total_results=total_results, query=query
                ),
                reply_markup=keyboard,
            )
            await state.set_state(SearchKpStates.waiting_for_kp_selection)
            await callback.answer()
        else:
            # --- Поиск по OMDb (латиница) ---
            await callback.message.edit_text(get_string("searching_please_wait", lang))
            omdb_response = await OMDbService.search_movies_series(query, page)
            results = omdb_response.get("Search", [])
            try:
                total_results = int(omdb_response.get("totalResults", 0))
            except (ValueError, TypeError):
                total_results = 0
            if not results:
                await callback.message.edit_text(
                    get_string("nothing_found_query", lang).format(query=query)
                )
                await state.set_state(MainMenuStates.waiting_for_query)
                await callback.answer()
                return
            keyboard = get_search_results_keyboard(
                results, query, page, total_results, lang=lang
            )
            await callback.message.edit_text(
                get_string("found_results", lang).format(
                    total_results=total_results, query=query
                ),
                reply_markup=keyboard,
            )
            await state.set_state(SearchOmdbStates.waiting_for_omdb_selection)
            await callback.answer()
    elif data.startswith("search_local:"):
        await callback.answer(get_string("feature_developing", lang), show_alert=False)
        return
