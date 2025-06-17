import logging
from aiogram.fsm.context import FSMContext
from aiogram import Router
from aiogram import types
from bot.utils.strings import get_string, get_profile_commands
from database.models_db import UserDB
from bot.features.profile.user_profile_keyboards import get_profile_keyboard
from bot.states.fsm_states import ProfileStates, MainMenuStates
from aiogram.types import CallbackQuery
from bot.shared.other_keyboards import get_menu_keyboard

logger = logging.getLogger(__name__)

profile_router = Router()


@profile_router.message(lambda m: m.text in get_profile_commands())
async def handle_profile(message: types.Message, state: FSMContext):
    user = UserDB.get_or_none(tg_id=message.from_user.id)
    lang = user.language if user else "en"
    await state.update_data(lang=lang)

    await message.answer(
        text=get_string("profile_message", lang).format(
            user_name=user.name,
            entities_count=user.user_entities.count(),
        ),
        reply_markup=get_profile_keyboard(lang),
    )

    await state.set_state(ProfileStates.waiting_for_profile_action)


@profile_router.callback_query(ProfileStates.waiting_for_profile_action)
async def handle_profile_actions(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("lang")
    data = callback.data
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    if data == "profile_change_language":
        new_lang = "ru" if lang == "en" else "en"
        user.language = new_lang
        user.save()
        await state.update_data(lang=new_lang)
        await callback.message.edit_text(
            text=get_string("profile_message", new_lang).format(
                user_name=user.name,
                entities_count=user.user_entities.count(),
            ),
            reply_markup=get_profile_keyboard(new_lang),
        )
        await callback.answer()
        return
    elif data == "profile_share_list":
        await callback.answer(get_string("feature_developing", lang), show_alert=False)
        return
    elif data == "profile_cancel":
        await callback.message.delete()
        await callback.message.answer(
            get_string("start_message", lang),
            reply_markup=get_menu_keyboard(lang),
        )
        await state.clear()
        await state.set_state(MainMenuStates.waiting_for_query)
        await callback.answer()
        return
