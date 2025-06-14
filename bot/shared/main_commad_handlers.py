from aiogram import Router, types
from aiogram.filters import Command
from bot.shared.other_keyboards import menu_keyboard, get_language_keyboard
from bot.shared.user_service import get_or_create_user
from aiogram.fsm.context import FSMContext
from bot.states.fsm_states import MainMenuStates
from database.models_db import UserDB
from bot.features.search_common.search_common_handlers import search_common_router
from bot.features.search_omdb.omdb_search_handlers import omdb_router
from bot.features.user_list.user_list_handlers import user_list_router

router = Router()
router.include_router(omdb_router)
router.include_router(user_list_router)
router.include_router(search_common_router)

command_list = ["start", "restart", "help", "list", "profile"]


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


@router.message(lambda m: m.text == "Restart" or m.text == "/restart")
async def handle_cancel(message: types.Message, state: FSMContext):
    await cmd_start(message, state)


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Command help ran", reply_markup=menu_keyboard)


@router.message(
    lambda m: m.text and m.text.startswith("/") and m.text[1:] not in command_list
)
async def handle_all_commands(message: types.Message):
    command = message.text[1:].split()[0]  # получаем команду без /
    await message.answer(f"Получена команда: {command}")
