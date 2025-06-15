from aiogram.fsm.context import FSMContext
from aiogram import Router
from aiogram import types
from bot.utils.strings import get_string
from database.models_db import UserDB

profile_router = Router()

MENU_STRINGS = [
    get_string("profile", "en"),
    get_string("profile", "ru"),
    "/profile",
]


@profile_router.message(lambda m: m.text in MENU_STRINGS)
async def handle_profile(message: types.Message, state: FSMContext):
    user = UserDB.get_or_none(tg_id=message.from_user.id)
    lang = user.language if user else "en"
    await message.answer(get_string("feature_developing", lang))
    return
