from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.utils.strings import get_string


def get_profile_keyboard(
    lang: str = "en",
):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_string("change_language", lang),
            callback_data=f"profile_change_language",
        ),
        InlineKeyboardButton(
            text=get_string("share_list", lang),
            callback_data=f"profile_share_list",
        ),
        InlineKeyboardButton(
            text=get_string("cancel", lang),
            callback_data=f"profile_cancel",
        ),
    )
    return builder.as_markup()
