from aiogram import Router, types
from aiogram.filters import Command
from bot.shared.other_keyboards import get_menu_keyboard, get_language_keyboard
from bot.shared.user_service import get_or_create_user
from aiogram.fsm.context import FSMContext
from bot.states.fsm_states import MainMenuStates
from database.models_db import UserDB
from bot.features.search_common.search_common_handlers import search_common_router
from bot.features.search_omdb.omdb_search_handlers import omdb_router
from bot.features.search_kp.kp_search_handlers import kp_router
from bot.features.user_list.user_list_handlers import user_list_router
from bot.features.profile.user_profile_handlers import profile_router
from bot.utils.strings import get_string

router = Router()
router.include_router(search_common_router)
router.include_router(omdb_router)
router.include_router(kp_router)
router.include_router(user_list_router)
router.include_router(profile_router)

MENU_STRINGS = [get_string(key, "en") for key in ["restart", "list", "profile"]]
MENU_COMMANDS = ["restart", "list", "profile"]

RESTART_COMMANDS = [
    get_string("restart", "en"),
    get_string("restart", "ru"),
    "/restart",
]


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    # Проверяем, существует ли пользователь
    user = UserDB.get_or_none(tg_id=message.from_user.id)
    lang = user.language if user else "en"

    if not user:
        # Если пользователь новый, показываем выбор языка
        await state.set_state(MainMenuStates.waiting_for_language)
        await message.answer(
            get_string("lang_choose"), reply_markup=get_language_keyboard()
        )
    else:
        # Если пользователь уже существует, переходим к обычному старту
        await state.set_state(MainMenuStates.waiting_for_query)
        await message.answer(
            get_string("start_message", lang),
            reply_markup=get_menu_keyboard(lang),
        )


@router.callback_query(MainMenuStates.waiting_for_language)
async def handle_language_selection(callback: types.CallbackQuery, state: FSMContext):
    # Получаем выбранный язык из callback_data
    lang = callback.data.split(":")[1]
    user, created = get_or_create_user(callback.from_user, lang)

    await callback.message.edit_text(get_string("start_message", lang))
    await state.set_state(MainMenuStates.waiting_for_query)
    await callback.answer()


@router.message(lambda m: m.text in RESTART_COMMANDS)
async def handle_cancel(message: types.Message, state: FSMContext):
    await cmd_start(message, state)


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    user = UserDB.get_or_none(tg_id=message.from_user.id)
    lang = user.language if user else "en"
    await message.answer(
        get_string("help_message", lang), reply_markup=get_menu_keyboard(lang)
    )


@router.message(lambda m: m.text.startswith("/") and m.text[1:] not in MENU_COMMANDS)
async def handle_all_commands(message: types.Message):
    user = UserDB.get_or_none(tg_id=message.from_user.id)
    lang = user.language if user else "en"
    await message.answer(f"{get_string('unknown_command', lang)}")
