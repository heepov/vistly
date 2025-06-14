from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.states.fsm_states import SearchStates
from bot.features.search_omdb.omdb_service import OMDbService
from bot.features.search_omdb.omdb_search_keyboards import get_search_results_keyboard
from bot.states.fsm_states import MainMenuStates, SearchOmdbStates
from aiogram import Router
from bot.shared.other_keyboards import get_choose_type_search_keyboard
from aiogram import types


search_common_router = Router()

MENU_BUTTONS = {"List", "Cancel", "Profile"}


@search_common_router.message()
async def handle_text(message: types.Message, state: FSMContext):
    if message.text in MENU_BUTTONS:
        return
    current_state = await state.get_state()
    if current_state == MainMenuStates.waiting_for_query:
        await state.set_state(SearchStates.waiting_for_search_type)
        await message.answer(
            "Where you want to search",
            reply_markup=get_choose_type_search_keyboard(message.text),
        )
    else:
        await message.answer(
            "You are not in the main menu. Use /start to start the bot"
        )


@search_common_router.callback_query(SearchStates.waiting_for_search_type)
async def handle_search_type(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    if data.startswith("search_global:"):
        query = data.split(":", 1)[1]
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
            await state.set_state(MainMenuStates.waiting_for_query)
            await callback.answer()
            return
        keyboard = get_search_results_keyboard(results, query, page, total_results)
        await callback.message.edit_text(
            f"Found {total_results} for: <b>{query}</b>", reply_markup=keyboard
        )
        await state.set_state(SearchOmdbStates.waiting_for_omdb_selection)
        await callback.answer()
    # Можно добавить обработку других типов поиска (например, search_local)
