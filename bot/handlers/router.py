from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from bot.keyboards.menu import menu_keyboard
from services.user_service import get_or_create_user
from bot.keyboards.search import (
    get_choose_type_search_keyboard,
    get_search_results_keyboard,
    get_entity_detail_keyboard,
)
from services.omdb_service import OMDbService
from database.models_db import EntityDB, RatingDB
from peewee import DoesNotExist
from .omdb_search import omdb_router

router = Router()
router.include_router(omdb_router)

MENU_BUTTONS = {"Search", "List", "Cancel", "Profile"}


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    get_or_create_user(message.from_user)
    await message.answer("Command start ran", reply_markup=menu_keyboard)


@router.message(Command("help"))
async def cmd_start(message: types.Message):
    await message.answer("Command help ran", reply_markup=menu_keyboard)


@router.message()
async def handle_text(message: types.Message):
    if message.text in MENU_BUTTONS:
        return
    text = f"{message.text}"
    await message.answer(
        f"Where you want to search",
        reply_markup=get_choose_type_search_keyboard(text),
    )
