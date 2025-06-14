from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from bot.features.user_list.user_list_keyboards import (
    get_user_list_keyboard,
    get_entity_detail_keyboard,
)
from database.models_db import UserEntityDB, UserDB
from models.enum_classes import StatusType
from bot.states.fsm_states import MainMenuStates, UserListStates
from bot.shared.other_keyboards import menu_keyboard
from bot.formater.entity_details_formater import format_entity_details
from database.models_db import UserEntityDB
from aiogram import Router, types
from models.factories import build_entity_from_db

user_list_router = Router()


async def show_user_list(
    callback: CallbackQuery | Message,
    page: int,
    status: StatusType = None,
    state: FSMContext = None,
) -> bool:
    """Показывает список фильмов пользователя

    Args:
        callback: объект callback или message
        page: номер страницы
        status: статус фильмов для фильтрации (опционально)
        state: объект FSMContext (опционально)

    Returns:
        bool: True если список показан, False если список пуст
    """
    # Получаем пользователя
    user_id = (
        callback.from_user.id
        if isinstance(callback, CallbackQuery)
        else callback.from_user.id
    )
    user = UserDB.get_or_none(tg_id=user_id)
    if not user:
        if isinstance(callback, CallbackQuery):
            await callback.message.edit_text("User not found")
        else:
            await callback.answer("User not found")
        return False

    # Получаем список фильмов пользователя
    query = (
        UserEntityDB.select()
        .where(UserEntityDB.user_id == user)
        .order_by(UserEntityDB.updated_db.desc())
    )
    if status:
        query = query.where(UserEntityDB.status == status)

    total_results = query.count()
    if not total_results:
        if isinstance(callback, CallbackQuery):
            await callback.message.edit_text(
                "Your list is empty"
                if not status
                else f"No {status.value} items in your list"
            )
        else:
            await callback.answer(
                "Your list is empty"
                if not status
                else f"No {status.value} items in your list"
            )
        if state:
            await state.set_state(MainMenuStates.waiting_for_query)
        return False

    # Получаем страницу результатов
    user_entities = query.paginate(page, 10)
    print(f"user_entities = {user_entities}")
    keyboard = get_user_list_keyboard(
        user_entities=user_entities,
        page=page,
        total_results=total_results,
        status=status,
    )

    # Проверяем тип callback и наличие фото
    if isinstance(callback, CallbackQuery):
        has_photo = getattr(callback.message, "photo", None) is not None
        if has_photo:
            await callback.message.delete()
            await callback.message.answer(
                f"Your list ({total_results} items):",
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        else:
            await callback.message.edit_text(
                f"Your list ({total_results} items):",
                reply_markup=keyboard,
            )
    else:
        # Если это Message, просто отправляем новое сообщение
        await callback.answer(
            f"Your list ({total_results} items):",
            reply_markup=keyboard,
        )

    return True


@user_list_router.message(lambda m: m.text == "List" or m.text == "/list")
async def handle_list(message: types.Message, state: FSMContext):
    # Показываем список фильмов пользователя
    success = await show_user_list(
        callback=message,  # передаем message как callback
        page=1,  # начинаем с первой страницы
        status=None,  # показываем все фильмы
        state=state,
    )

    if success:
        await state.set_state(UserListStates.waiting_for_list_selection)
    else:
        # Если список пуст, возвращаемся в главное меню
        await state.set_state(MainMenuStates.waiting_for_query)
        await message.answer(
            "Hi! Enter the name of the movie or TV series to search for:",
            reply_markup=menu_keyboard,
        )


@user_list_router.callback_query(lambda c: c.data.startswith("user_list_page:"))
async def handle_user_list_pagination(callback: CallbackQuery, state: FSMContext):
    try:
        # user_list_page:{page}:{status}
        _, page, status = callback.data.split(":", 2)
        page = int(page)
        status = StatusType(status) if status != "all" else None
    except (ValueError, IndexError):
        await callback.answer("Invalid callback data")
        return

    success = await show_user_list(callback, page, status, state)
    if success:
        await callback.answer()


@user_list_router.callback_query(lambda c: c.data.startswith("user_list_status:"))
async def handle_user_list_status_filter(callback: CallbackQuery, state: FSMContext):
    try:
        # user_list_status:{status}
        _, status = callback.data.split(":", 1)
        if status == "all":
            status = None
        else:
            status = StatusType(status)
    except (ValueError, IndexError):
        await callback.answer("Invalid callback data")
        return

    success = await show_user_list(callback, 1, status, state)
    if success:
        await callback.answer()


@user_list_router.callback_query(lambda c: c.data == "back_to_menu")
async def handle_back_to_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "Hi! Enter the name of the movie or TV series to search for:",
        reply_markup=menu_keyboard,
    )
    await state.set_state(MainMenuStates.waiting_for_query)
    await callback.answer()
    return


@user_list_router.callback_query(lambda c: c.data.startswith("user_entity_select:"))
async def handle_user_entity_select(callback: CallbackQuery, state: FSMContext):
    try:
        # user_entity_select:{user_entity_id}:{page}:{status}
        _, user_entity_id, page, status = callback.data.split(":", 3)
        user_entity_id = int(user_entity_id)
        page = int(page)
        status = None if status == "all" else status
    except (ValueError, IndexError):
        await callback.answer("Invalid callback data")
        return

    # Получаем user_entity и саму сущность
    user_entity = UserEntityDB.get_or_none(id=user_entity_id)
    if not user_entity:
        await callback.answer("Not found")
        return
    entity = user_entity.entity

    # Формируем текст и постер
    entity_full = build_entity_from_db(entity)
    text = format_entity_details(entity_full)

    # Используем готовую функцию для клавиатуры
    keyboard = get_entity_detail_keyboard(user_entity, page)

    # Показываем сообщение
    if entity.poster_url:
        await callback.message.delete()
        await callback.message.answer_photo(
            entity.poster_url, caption=text, reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
