from aiogram.fsm.context import FSMContext
from aiogram import Router
from aiogram import types
from bot.utils.strings import get_string, get_profile_commands
from database.models_db import UserDB

profile_router = Router()


@profile_router.message(lambda m: m.text in get_profile_commands())
async def handle_profile(message: types.Message, state: FSMContext):
    user = UserDB.get_or_none(tg_id=message.from_user.id)
    lang = user.language if user else "en"
    await message.answer(get_string("feature_developing", lang))
    return
