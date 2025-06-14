from aiogram import Router, types
from aiogram.filters import Command
from bot.keyboards.other_keyboards import menu_keyboard, get_language_keyboard
from services.user_service import get_or_create_user
from bot.keyboards.other_keyboards import get_choose_type_search_keyboard
from aiogram.fsm.context import FSMContext
from bot.states.fsm_states import MainMenuStates, SearchStates, UserListStates
from database.models_db import UserDB
from bot.handlers.user_list_handlers import show_user_list

from .omdb_search_handlers import omdb_router
from .user_list_handlers import usrl_list_router

router = Router()
router.include_router(omdb_router)
router.include_router(usrl_list_router)

MENU_BUTTONS = {"List", "Cancel", "Profile"}


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    # Проверяем, существует ли пользователь
    user = UserDB.get_or_none(tg_id=message.from_user.id)

    if not user:
        # Если пользователь новый, показываем выбор языка
        await state.set_state(MainMenuStates.waiting_for_language)
        await message.answer(
            "Выберите язык / Choose language:", reply_markup=get_language_keyboard()
        )
    else:
        # Если пользователь уже существует, переходим к обычному старту
        await state.set_state(MainMenuStates.waiting_for_query)
        await message.answer(
            "Hi! Enter the name of the movie or TV series to search for:",
            reply_markup=menu_keyboard,
        )


@router.callback_query(MainMenuStates.waiting_for_language)
async def handle_language_selection(callback: types.CallbackQuery, state: FSMContext):
    # Получаем выбранный язык из callback_data
    lang = callback.data.split(":")[1]
    user, created = get_or_create_user(callback.from_user, lang)

    # Отправляем приветственное сообщение на выбранном языке
    welcome_message = (
        "Hi! Enter the name of the movie or TV series to search for:"
        if lang == "en"
        else "Привет! Введите название фильма или сериала для поиска:"
    )

    await callback.message.edit_text(welcome_message)
    await state.set_state(MainMenuStates.waiting_for_query)
    await callback.answer()


@router.message(lambda m: m.text == "Cancel")
async def handle_cancel(message: types.Message, state: FSMContext):
    await cmd_start(message, state)


@router.message(lambda m: m.text == "List")
async def handle_list(message: types.Message, state: FSMContext):
    # Показываем список фильмов пользователя
    success = await show_user_list(
        callback=message,  # передаем message как callback
        page=1,  # начинаем с первой страницы
        status=None,  # показываем все фильмы
        state=state,
    )

    if success:
        await state.set_state(UserListStates.waiting_for_list_selection)
    else:
        # Если список пуст, возвращаемся в главное меню
        await state.set_state(MainMenuStates.waiting_for_query)
        await message.answer(
            "Hi! Enter the name of the movie or TV series to search for:",
            reply_markup=menu_keyboard,
        )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Command help ran", reply_markup=menu_keyboard)


@router.message(lambda m: m.text and m.text.startswith("/"))
async def handle_all_commands(message: types.Message):
    command = message.text[1:].split()[0]  # получаем команду без /
    await message.answer(f"Получена команда: {command}")


@router.message()
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
