from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.utils.strings import get_string


def get_menu_keyboard(lang="en"):
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_string("profile", lang)),
                KeyboardButton(text=get_string("restart", lang)),
                KeyboardButton(text=get_string("list", lang)),
            ],
        ],
        resize_keyboard=True,
    )


def get_language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
    )
    return builder.as_markup()


def get_choose_type_search_keyboard(lang="en") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_string("global", lang), callback_data=f"search_global"
        ),
        InlineKeyboardButton(
            text=get_string("local", lang), callback_data=f"search_local"
        ),
    )
    return builder.as_markup()
