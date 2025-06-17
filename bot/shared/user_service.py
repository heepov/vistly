from database.models_db import UserDB
from aiogram.types import Message, CallbackQuery
from typing import Union, Tuple, Optional
from bot.utils.strings import get_string
from bot.shared.other_keyboards import get_language_keyboard
from bot.states.fsm_states import MainMenuStates
from aiogram.fsm.context import FSMContext
import logging

logger = logging.getLogger(__name__)


def get_or_create_user(tg_user, lang) -> tuple[UserDB, bool]:
    """
    Получить или создать пользователя по данным Telegram.
    :param tg_user: объект message.from_user
    :return: (User, created)
    """
    full_name = ""
    if tg_user.first_name:
        full_name += tg_user.first_name
    if tg_user.last_name:
        full_name += " " + tg_user.last_name
    if full_name == "":
        full_name = None

    user, created = UserDB.get_or_create(
        tg_id=tg_user.id,
        defaults={
            "username": tg_user.username,
            "name": full_name,
            "language": lang,
        },
    )
    return user, created


async def ensure_user_exists(
    update: Union[Message, CallbackQuery], state: FSMContext
) -> bool:
    """
    Проверить, существует ли пользователь в базе данных.
    Если нет - показать выбор языка и вернуть False.
    Если есть - вернуть True.

    :param update: Message или CallbackQuery объект
    :param state: FSMContext для управления состоянием
    :return: True если пользователь существует, False если показан выбор языка
    """

    user = UserDB.get_or_none(tg_id=update.from_user.id)
    if not user:
        await state.set_state(MainMenuStates.waiting_for_language)
        if isinstance(update, CallbackQuery):
            await update.message.answer(
                get_string("lang_choose"), reply_markup=get_language_keyboard()
            )
            await update.answer()
        else:  # Message
            await update.answer(
                get_string("lang_choose"), reply_markup=get_language_keyboard()
            )
        return False

    return True
