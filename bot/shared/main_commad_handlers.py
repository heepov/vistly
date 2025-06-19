from aiogram import Router, types
from aiogram.filters import Command
from bot.shared.other_keyboards import (
    get_menu_keyboard,
    get_language_keyboard,
)
from bot.shared.user_service import get_or_create_user, ensure_user_exists
from aiogram.fsm.context import FSMContext
from bot.states.fsm_states import (
    MainMenuStates,
    UserListStates,
    DeepLinkStates,
    ProfileStates,
)
from database.models_db import UserDB
from bot.utils.strings import (
    get_string,
    get_restart_commands,
    get_list_commands,
    get_all_commands,
    get_profile_commands,
)
from bot.features.search.search_handlers import search_router
from bot.features.search.search_gs_handlers import gs_router
from bot.features.user_list.user_list_handlers import user_list_router, show_ls_list
from bot.features.profile.user_profile_handlers import profile_router
from bot.features.profile.user_profile_keyboards import get_profile_keyboard
from models.enum_classes import EntityType, StatusType
from bot.features.deep_link.deep_link_entity_handler import show_dl_entity, dl_router
from aiogram.types import FSInputFile, InputMediaPhoto
import logging

logger = logging.getLogger(__name__)

router = Router()
router.include_router(search_router)
router.include_router(gs_router)
router.include_router(user_list_router)
router.include_router(profile_router)
router.include_router(dl_router)


# Вспомогательные функции
async def get_user_and_lang(message: types.Message) -> tuple[UserDB, str]:
    """Получить пользователя и язык"""
    user = UserDB.get_or_none(tg_id=message.from_user.id)
    lang = user.language if user else "en"
    return user, lang


async def send_start_message(message: types.Message, lang: str):
    """Отправить стартовое сообщение"""
    await message.answer(
        get_string("start_message", lang),
        reply_markup=get_menu_keyboard(lang),
    )


async def handle_deep_link_start(
    message: types.Message, state: FSMContext, entity_id: str, lang: str
):
    """Обработать старт с deep link"""
    success = await show_dl_entity(
        msg=message,
        state=state,
        entity_id=entity_id,
    )

    if success:
        await state.set_state(DeepLinkStates.waiting_for_dl_action_entity)
    else:
        await state.clear()
        await send_start_message(message, lang)
        await state.set_state(MainMenuStates.waiting_for_query)


def parse_start_args(message_text: str) -> tuple[str | None, str | None]:
    """Парсить аргументы команды /start"""
    parts = message_text.split(maxsplit=1)
    if len(parts) <= 1:
        return None, None

    args = parts[1]
    try:
        link_type, entity_id = args.split("_", 1)
        return link_type, entity_id
    except ValueError:
        return None, None


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    # Очистка состояния если нет deep link
    state_data = await state.get_data()
    if not state_data.get("entity_id"):
        await state.clear()

    # Парсинг аргументов
    link_type, entity_id = parse_start_args(message.text)
    logger.info(f"link_type: {link_type}, entity_id: {entity_id}")
    if entity_id:
        await state.update_data(link_type=link_type, entity_id=entity_id)
    # Проверка пользователя
    if not await ensure_user_exists(message, state):
        return

    # Получение пользователя и языка
    user, lang = await get_user_and_lang(message)
    await state.update_data(lang=lang)

    # Обработка deep link или обычного старта
    if entity_id:
        await state.update_data(link_type=link_type, entity_id=entity_id)
        await handle_deep_link_start(message, state, entity_id, lang)
    else:
        await state.set_state(MainMenuStates.waiting_for_query)
        await send_start_message(message, lang)


@router.callback_query(MainMenuStates.waiting_for_language)
async def handle_language_selection(callback: types.CallbackQuery, state: FSMContext):
    # Получение языка
    lang = callback.data.split(":")[1]
    # user, created = get_or_create_user(callback.from_user, lang)
    await state.update_data(lang=lang)

    # Проверка deep link
    state_data = await state.get_data()
    entity_id = state_data.get("entity_id")
    logger.info(f"entity_id: {entity_id}")

    if entity_id:
        # Обработка deep link после выбора языка
        success = await show_dl_entity(
            msg=callback.message,
            state=state,
            entity_id=entity_id,
        )

        if success:
            await state.set_state(DeepLinkStates.waiting_for_dl_action_entity)
        else:
            await state.clear()
            await callback.message.delete()
            await send_start_message(callback.message, lang)
            await state.set_state(MainMenuStates.waiting_for_query)
    else:
        # Обычный старт после выбора языка
        await callback.message.delete()
        await send_start_message(callback.message, lang)
        await state.set_state(MainMenuStates.waiting_for_query)

    await callback.answer()


@router.message(lambda m: m.text and m.text in get_restart_commands())
async def handle_cancel(message: types.Message, state: FSMContext):
    if not await ensure_user_exists(message, state):
        return
    await message.delete()  # Удаляем команду пользователя
    await cmd_start(message, state)


@router.message(Command("help"))
async def cmd_help(message: types.Message, state: FSMContext):
    if not await ensure_user_exists(message, state):
        return

    await message.delete()  # Удаляем команду пользователя
    user, lang = await get_user_and_lang(message)

    media = [
        InputMediaPhoto(
            media=FSInputFile("bot/img/instruction_en_001.png"),
            caption=get_string("help_message", lang),
            parse_mode="HTML",
        ),
        InputMediaPhoto(media=FSInputFile("bot/img/instruction_en_002.png")),
    ]
    await message.answer_media_group(media)


@router.message(lambda m: m.text and m.text in get_list_commands())
async def handle_list(message: types.Message, state: FSMContext):
    if not await ensure_user_exists(message, state):
        return

    await message.delete()  # Удаляем команду пользователя
    user, lang = await get_user_and_lang(message)

    await state.clear()
    await state.update_data(
        query=None,
        entity_type_search=EntityType.ALL,
        lang=lang,
        status_type=StatusType.ALL,
    )

    success = await show_ls_list(
        callback=message,
        state=state,
    )

    if success:
        await state.set_state(UserListStates.waiting_for_ls_select_entity)
    else:
        await state.clear()
        await state.set_state(MainMenuStates.waiting_for_query)
        await send_start_message(message, lang)


@router.message(lambda m: m.text and m.text in get_profile_commands())
async def handle_profile(message: types.Message, state: FSMContext):
    if not await ensure_user_exists(message, state):
        return

    await message.delete()  # Удаляем команду пользователя
    user, lang = await get_user_and_lang(message)
    await state.update_data(lang=lang)

    await message.answer(
        text=get_string("profile_message", lang).format(
            user_name=user.name,
            entities_count=user.user_entities.count(),
        ),
        reply_markup=get_profile_keyboard(lang),
    )

    await state.set_state(ProfileStates.waiting_for_profile_action)


@router.message(
    lambda m: m.text and m.text.startswith("/") and m.text not in get_all_commands()
)
async def handle_all_commands(message: types.Message, state: FSMContext):
    if not await ensure_user_exists(message, state):
        return

    await message.delete()  # Удаляем неизвестную команду
    user, lang = await get_user_and_lang(message)
    await message.answer(get_string("unknown_command", lang))


@router.message(lambda m: m.content_type != "text")
async def handle_non_text_content(message: types.Message, state: FSMContext):
    """Обработчик для всех типов контента кроме текста (фото, видео, документы и т.д.)"""
    if not await ensure_user_exists(message, state):
        return

    await message.delete()  # Удаляем не-текстовый контент
    user, lang = await get_user_and_lang(message)
    await message.answer(get_string("message_error", lang))
