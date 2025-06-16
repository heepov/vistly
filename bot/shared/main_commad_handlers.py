from aiogram import Router, types
from aiogram.filters import Command
from bot.shared.other_keyboards import get_menu_keyboard, get_language_keyboard
from bot.shared.user_service import get_or_create_user
from aiogram.fsm.context import FSMContext
from bot.states.fsm_states import (
    MainMenuStates,
    UserListStates,
    SearchStates,
    DeepLinkStates,
)
from database.models_db import UserDB
from bot.utils.strings import (
    get_string,
    get_restart_commands,
    get_list_commands,
    get_all_commands,
)
from bot.features.search.search_handlers import search_router
from bot.features.search.search_gs_handlers import gs_router
from bot.features.user_list.user_list_handlers import user_list_router, show_ls_list
from bot.features.profile.user_profile_handlers import profile_router
from models.enum_classes import EntityType, StatusType
from bot.features.deep_link.deep_link_handler import show_dl_entity, dl_router
import logging

logger = logging.getLogger(__name__)

router = Router()
router.include_router(search_router)
router.include_router(gs_router)
router.include_router(user_list_router)
router.include_router(profile_router)
router.include_router(dl_router)


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    parts = message.text.split(maxsplit=1)
    args = parts[1] if len(parts) > 1 else None
    if args:
        link_type, entity_id = args.split("_", 1)
        await state.update_data(link_type=link_type, entity_id=entity_id)

    # Проверяем, существует ли пользователь
    user = UserDB.get_or_none(tg_id=message.from_user.id)

    if not user:
        # Если пользователь новый, показываем выбор языка
        await state.set_state(MainMenuStates.waiting_for_language)
        await message.answer(
            get_string("lang_choose"), reply_markup=get_language_keyboard()
        )
    else:
        lang = user.language if user else "en"
        await state.update_data(lang=lang)
        if args:
            success = await show_dl_entity(
                msg=message,
                state=state,
                entity_id=entity_id,
            )

            if success:
                await state.set_state(DeepLinkStates.waiting_for_dl_action_entity)
            else:
                await state.clear()
                await message.answer(
                    get_string("start_message", lang),
                    reply_markup=get_menu_keyboard(lang),
                )
                await state.set_state(MainMenuStates.waiting_for_query)
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
    await state.update_data(lang=lang)
    state_data = await state.get_data()
    link_type = state_data.get("link_type")
    entity_id = state_data.get("entity_id")

    if entity_id:
        # Передаём callback.message (само сообщение с языком) в show_dl_entity
        success = await show_dl_entity(
            msg=callback.message,  # <--- передаём именно message!
            state=state,
            entity_id=entity_id,
        )

        if success:
            await state.set_state(DeepLinkStates.waiting_for_dl_action_entity)
        else:
            await state.clear()
            await callback.message.edit_text(
                get_string("start_message", lang), reply_markup=get_menu_keyboard(lang)
            )
            await state.set_state(MainMenuStates.waiting_for_query)
        await callback.answer()
    else:
        await callback.message.edit_text(
            get_string("start_message", lang), reply_markup=get_menu_keyboard(lang)
        )
        await state.set_state(MainMenuStates.waiting_for_query)
        await callback.answer()

@router.message(lambda m: m.text in get_restart_commands())
async def handle_cancel(message: types.Message, state: FSMContext):
    await cmd_start(message, state)


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    user = UserDB.get_or_none(tg_id=message.from_user.id)
    lang = user.language if user else "en"
    await message.answer(
        get_string("help_message", lang), reply_markup=get_menu_keyboard(lang)
    )


@router.message(lambda m: m.text in get_list_commands())
async def handle_list(message: types.Message, state: FSMContext):
    user = UserDB.get_or_none(tg_id=message.from_user.id)
    lang = user.language if user else "en"
    await state.clear()
    await state.update_data(
        query=None,
        entity_type_search=EntityType.ALL,
        lang=lang,
        status_type=StatusType.ALL,
    )

    success = await show_ls_list(
        callback=message,
        page=1,
        state=state,
    )

    if success:
        await state.set_state(UserListStates.waiting_for_ls_select_entity)
    else:
        await state.clear()
        await state.set_state(MainMenuStates.waiting_for_query)
        await message.answer(
            get_string("start_message", lang),
            reply_markup=get_menu_keyboard(lang),
        )


@router.message(lambda m: m.text.startswith("/") and m.text not in get_all_commands())
async def handle_all_commands(message: types.Message):
    user = UserDB.get_or_none(tg_id=message.from_user.id)
    lang = user.language if user else "en"
    await message.answer(f"{get_string('unknown_command', lang)}")
