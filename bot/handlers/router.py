from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from bot.keyboards.menu import menu_keyboard
from services.user_service import get_or_create_user
from bot.keyboards.search import get_choose_type_search_keyboard
from aiogram.fsm.context import FSMContext
from bot.states.fsm_states import MainMenuStates, OmdbSearchStates

from .omdb_search import omdb_router

router = Router()
router.include_router(omdb_router)

MENU_BUTTONS = {"Search", "List", "Cancel", "Profile"}


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    get_or_create_user(message.from_user)
    await state.set_state(MainMenuStates.awaiting_query)
    await message.answer(
        "Hi! Enter the name of the movie or TV series to search for:",
        reply_markup=menu_keyboard,
    )


@router.message(lambda m: m.text == "Cancel")
async def handle_cancel(message: types.Message, state: FSMContext):
    await cmd_start(message, state)


@router.message(Command("help"))
async def cmd_start(message: types.Message):
    await message.answer("Command help ran", reply_markup=menu_keyboard)


@router.message()
async def handle_text(message: types.Message, state: FSMContext):
    if message.text in MENU_BUTTONS:
        return
    current_state = await state.get_state()
    if current_state == MainMenuStates.awaiting_query:
        await state.set_state(OmdbSearchStates.waiting_for_search_type)
        await message.answer(
            "Where you want to search",
            reply_markup=get_choose_type_search_keyboard(message.text),
        )
    else:
        await message.answer(
            "You are not in the main menu. Use /start to start the bot"
        )
