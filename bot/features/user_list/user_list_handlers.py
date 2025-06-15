from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from bot.features.user_list.user_list_keyboards import (
    get_user_list_keyboard,
    get_entity_detail_keyboard,
    get_rating_keyboard,
    get_status_keyboard,
    get_delete_confirm_keyboard,
    get_season_number_keyboard,
)
from database.models_db import UserEntityDB, UserDB
from models.enum_classes import StatusType
from bot.states.fsm_states import MainMenuStates, UserListStates
from bot.shared.other_keyboards import get_menu_keyboard
from bot.formater.message_formater import format_entity_details
from database.models_db import UserEntityDB
from aiogram import Router, types
from models.factories import build_entity_from_db
from bot.utils.strings import get_string, get_status_string

user_list_router = Router()

status_name_map = {
    StatusType.PLANNING: "planning",
    StatusType.IN_PROGRESS: "In progress",
    StatusType.COMPLETED: "Completed",
}

MENU_STRINGS = [
    get_string("list", "en"),
    get_string("list", "ru"),
    "/list",
]


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
    lang = user.language if user else "en"
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
                get_string("user_list_empty", lang)
                if not status
                else get_string("user_list_empty_status", lang).format(
                    status=status.value
                )
            )
        else:
            await callback.answer(
                get_string("user_list_empty", lang)
                if not status
                else get_string("user_list_empty_status", lang).format(
                    status=status.value
                )
            )
        if state:
            await state.set_state(MainMenuStates.waiting_for_query)
        return False

    # Получаем страницу результатов
    # user_entities = query.paginate(page, 10)
    user_entities = list(query.paginate(page, 10))
    keyboard = get_user_list_keyboard(
        user_entities=user_entities,
        page=page,
        total_results=total_results,
        status=status,
        lang=lang,
    )

    status_text = get_status_string(status, lang) if status else get_string("all", lang)
    # Проверяем тип callback и наличие фото
    if isinstance(callback, CallbackQuery):
        has_photo = getattr(callback.message, "photo", None) is not None
        if has_photo:
            await callback.message.delete()
            await callback.message.answer(
                get_string("user_list_title", lang).format(
                    status_text=status_text, total_results=total_results
                ),
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        else:
            await callback.message.edit_text(
                get_string("user_list_title", lang).format(
                    status_text=status_text, total_results=total_results
                ),
                reply_markup=keyboard,
                parse_mode="HTML",
            )
    else:
        # Если это Message, просто отправляем новое сообщение
        await callback.answer(
            get_string("user_list_title", lang).format(
                status_text=status_text, total_results=total_results
            ),
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    return True


@user_list_router.message(lambda m: m.text in MENU_STRINGS)
async def handle_list(message: types.Message, state: FSMContext):
    user = UserDB.get_or_none(tg_id=message.from_user.id)
    lang = user.language if user else "en"
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
            get_string("start_message", lang),
            reply_markup=get_menu_keyboard(lang),
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
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    lang = user.language if user else "en"
    await callback.message.delete()
    await callback.message.answer(
        get_string("start_message", lang),
        reply_markup=get_menu_keyboard(lang),
    )
    await state.set_state(MainMenuStates.waiting_for_query)
    await callback.answer()
    return


@user_list_router.callback_query(lambda c: c.data.startswith("user_entity_select:"))
async def handle_user_entity_select(callback: CallbackQuery, state: FSMContext):
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    lang = user.language if user else "en"
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
    text = format_entity_details(entity_full, lang)

    # Используем готовую функцию для клавиатуры
    keyboard = get_entity_detail_keyboard(user_entity, page, status, lang)

    # Показываем сообщение
    if entity.poster_url:
        await callback.message.delete()
        await callback.message.answer_photo(
            entity.poster_url, caption=text, reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@user_list_router.callback_query(lambda c: c.data.startswith("rate_entity:"))
async def ask_rating(callback: CallbackQuery, state: FSMContext):
    _, user_entity_id, page, status = callback.data.split(":")
    user_entity = UserEntityDB.get_by_id(int(user_entity_id))
    entity = user_entity.entity
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    lang = user.language if user else "en"
    await state.set_state(UserListStates.waiting_for_list_entity_change_rating)
    await state.update_data(user_entity_id=user_entity_id, page=page, status=status)
    if getattr(callback.message, "photo", None):
        await callback.message.delete()
        await callback.message.answer(
            get_string("ask_rating", lang).format(
                entity_type=entity.type, entity_name=entity.title
            ),
            reply_markup=get_rating_keyboard(user_entity_id, lang),
        )
    else:
        await callback.message.edit_text(
            get_string("ask_rating", lang).format(
                entity_type=entity.type, entity_name=entity.title
            ),
            reply_markup=get_rating_keyboard(user_entity_id, lang),
        )
    await callback.answer()


@user_list_router.callback_query(UserListStates.waiting_for_list_entity_change_rating)
async def set_rating(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith("set_rating:"):
        _, user_entity_id, rating = callback.data.split(":")
        user_entity = UserEntityDB.get_by_id(int(user_entity_id))
        user_entity.user_rating = int(rating)
        user_entity.save()
        # Вернуть к entity info
        await state.set_state(UserListStates.waiting_for_list_action_entity)
        await show_entity_info(callback, user_entity, state)
    elif callback.data.startswith("back_to_entity:"):
        _, user_entity_id = callback.data.split(":")
        user_entity = UserEntityDB.get_by_id(int(user_entity_id))
        await state.set_state(UserListStates.waiting_for_list_action_entity)
        await show_entity_info(callback, user_entity, state)
    await callback.answer()


@user_list_router.callback_query(lambda c: c.data.startswith("status_entity:"))
async def ask_status(callback: CallbackQuery, state: FSMContext):
    _, user_entity_id, page, status = callback.data.split(":")
    user_entity = UserEntityDB.get_by_id(int(user_entity_id))
    entity = user_entity.entity
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    lang = user.language if user else "en"
    await state.set_state(UserListStates.waiting_for_list_entity_change_status)
    await state.update_data(user_entity_id=user_entity_id, page=page, status=status)
    if getattr(callback.message, "photo", None):
        await callback.message.delete()
        await callback.message.answer(
            get_string("ask_status", lang).format(
                entity_type=entity.type, entity_name=entity.title
            ),
            reply_markup=get_status_keyboard(user_entity_id, lang),
        )
    else:
        await callback.message.edit_text(
            get_string("ask_status", lang).format(
                entity_type=entity.type, entity_name=entity.title
            ),
            reply_markup=get_status_keyboard(user_entity_id, lang),
        )
    await callback.answer()


@user_list_router.callback_query(UserListStates.waiting_for_list_entity_change_status)
async def set_status(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith("set_status:"):
        _, user_entity_id, status = callback.data.split(":")
        user_entity = UserEntityDB.get_by_id(int(user_entity_id))
        user_entity.status = status
        user_entity.save()
        await state.set_state(UserListStates.waiting_for_list_action_entity)
        await show_entity_info(callback, user_entity, state)
    elif callback.data.startswith("back_to_entity:"):
        _, user_entity_id = callback.data.split(":")
        user_entity = UserEntityDB.get_by_id(int(user_entity_id))
        await state.set_state(UserListStates.waiting_for_list_action_entity)
        await show_entity_info(callback, user_entity, state)
    await callback.answer()


@user_list_router.callback_query(lambda c: c.data.startswith("season_entity:"))
async def ask_season(callback: CallbackQuery, state: FSMContext):
    _, user_entity_id, page, status = callback.data.split(":")
    user_entity = UserEntityDB.get_by_id(int(user_entity_id))
    entity = user_entity.entity
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    lang = user.language if user else "en"
    season = user_entity.current_season or 1  # Если есть в базе — показываем, иначе 1
    await state.set_state(UserListStates.waiting_for_list_entity_change_season)
    await state.update_data(user_entity_id=user_entity_id, page=page, status=status)
    text = get_string("ask_season", lang).format(
        entity_type=entity.type, entity_name=entity.title
    )
    if getattr(callback.message, "photo", None):
        await callback.message.delete()
        await callback.message.answer(
            text, reply_markup=get_season_number_keyboard(user_entity_id, season, lang)
        )
    else:
        await callback.message.edit_text(
            text, reply_markup=get_season_number_keyboard(user_entity_id, season, lang)
        )
    await callback.answer()


@user_list_router.callback_query(lambda c: c.data.startswith("season_number:"))
async def change_season_number(callback: CallbackQuery, state: FSMContext):
    _, user_entity_id, value = callback.data.split(":")
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    lang = user.language if user else "en"

    if value == "clean":
        # Сбросить сезон (None)
        user_entity = UserEntityDB.get_by_id(int(user_entity_id))
        user_entity.current_season = None
        user_entity.save()
        await state.set_state(UserListStates.waiting_for_list_action_entity)
        await show_entity_info(callback, user_entity, state)
        return

    try:
        season = int(value)
        if season < 1:
            season = 1
    except ValueError:
        season = 1

    # Просто обновляем клавиатуру с новым значением
    await callback.message.edit_reply_markup(
        reply_markup=get_season_number_keyboard(user_entity_id, season, lang)
    )
    await callback.answer()


@user_list_router.callback_query(lambda c: c.data.startswith("set_season:"))
async def set_confirm_season(callback: CallbackQuery, state: FSMContext):
    _, user_entity_id, season = callback.data.split(":")
    user_entity = UserEntityDB.get_by_id(int(user_entity_id))
    user_entity.current_season = int(season)
    user_entity.save()
    await state.set_state(UserListStates.waiting_for_list_action_entity)
    await show_entity_info(callback, user_entity, state)
    await callback.answer()


@user_list_router.callback_query(lambda c: c.data.startswith("delete_entity:"))
async def ask_delete(callback: CallbackQuery, state: FSMContext):
    _, user_entity_id, page, status = callback.data.split(":")
    user_entity = UserEntityDB.get_by_id(int(user_entity_id))
    entity = user_entity.entity
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    lang = user.language if user else "en"
    await state.set_state(UserListStates.waiting_for_list_entity_delete_entity)
    await state.update_data(user_entity_id=user_entity_id, page=page, status=status)
    if getattr(callback.message, "photo", None):
        await callback.message.delete()
        await callback.message.answer(
            get_string("ask_delete", lang).format(
                entity_type=get_string(entity.type, lang), entity_name=entity.title
            ),
            reply_markup=get_delete_confirm_keyboard(user_entity_id, lang),
        )
    else:
        await callback.message.edit_text(
            get_string("ask_delete", lang).format(
                entity_type=get_string(entity.type, lang), entity_name=entity.title
            ),
            reply_markup=get_delete_confirm_keyboard(user_entity_id, lang),
        )
    await callback.answer()


@user_list_router.callback_query(UserListStates.waiting_for_list_entity_delete_entity)
async def confirm_delete(callback: CallbackQuery, state: FSMContext):
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    lang = user.language if user else "en"
    data = await state.get_data()
    page = int(data.get("page", 1))
    status = data.get("status", None)
    if callback.data.startswith("delete_confirm:"):
        _, user_entity_id, answer = callback.data.split(":")
        if answer == "yes":
            UserEntityDB.get_by_id(int(user_entity_id)).delete_instance()
            await callback.message.edit_text(
                get_string("entity_deleted", lang),
            )
            # Возврат к списку с теми же page и status
            await show_user_list(callback, page, status, state)
        else:
            user_entity = UserEntityDB.get_by_id(int(user_entity_id))
            await state.set_state(UserListStates.waiting_for_list_action_entity)
            await show_entity_info(callback, user_entity, state, page, status)
    elif callback.data.startswith("back_to_entity:"):
        _, user_entity_id = callback.data.split(":")
        user_entity = UserEntityDB.get_by_id(int(user_entity_id))
        await state.set_state(UserListStates.waiting_for_list_action_entity)
        await show_entity_info(callback, user_entity, state, page, status)
    await callback.answer()


async def show_entity_info(event, user_entity, state, page=1, status=None):
    """
    Показывает детальную информацию о фильме/сериале для user_entity.
    """
    user = UserDB.get_or_none(tg_id=event.from_user.id)
    lang = user.language if user else "en"
    entity = user_entity.entity
    entity_full = build_entity_from_db(entity)
    text = format_entity_details(entity_full, lang)
    keyboard = get_entity_detail_keyboard(user_entity, page, status, lang)

    if entity.poster_url:
        if hasattr(event, "message"):
            await event.message.delete()
            await event.message.answer_photo(
                entity.poster_url, caption=text, reply_markup=keyboard
            )
        else:
            await event.answer_photo(
                entity.poster_url, caption=text, reply_markup=keyboard
            )
    else:
        if hasattr(event, "message"):
            await event.message.edit_text(text, reply_markup=keyboard)
        else:
            await event.answer(text, reply_markup=keyboard)


@user_list_router.callback_query(lambda c: c.data.startswith("share_entity:"))
async def share_entity(callback: CallbackQuery, state: FSMContext):
    user = UserDB.get_or_none(tg_id=callback.from_user.id)
    lang = user.language if user else "en"
    await callback.answer(get_string("feature_developing", lang), show_alert=False)
    return
