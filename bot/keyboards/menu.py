from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Search"), KeyboardButton(text="List")],
        [KeyboardButton(text="Cancel"), KeyboardButton(text="Profile")],
    ],
    resize_keyboard=True,
)
