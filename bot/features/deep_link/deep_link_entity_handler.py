import logging
from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from bot.features.deep_link.deep_link_entity_keyboards import (
    get_deep_link_keyboard,
    get_dl_add_to_list_keyboard,
)
from bot.utils.strings import get_string
from bot.shared.main_commad_handlers import get_menu_keyboard
from database.models_db import UserDB, EntityDB, UserEntityDB
from models.factories import build_entity_from_db
from bot.formater.message_formater import format_entity_details
from bot.states.fsm_states import MainMenuStates, DeepLinkStates
from aiogram.exceptions import TelegramBadRequest
from models.enum_classes import StatusType
from bot.utils.strings import get_status_string


dl_router = Router()
logger = logging.getLogger(__name__)


async def show_dl_entity(
    msg: Message,  # теперь всегда объект Message!
    state: FSMContext,
    entity_id: int,
) -> bool:
    state_data = await state.get_data()
    lang = state_data.get("lang")
    user = UserDB.get_or_none(tg_id=msg.chat.id)
    entity = EntityDB.get_by_id(entity_id)

    if entity is None:
        await msg.edit_text(get_string("error_getting_entity", lang))
        await state.clear()
        await state.set_state(MainMenuStates.waiting_for_query)
        return False

    entity_full = build_entity_from_db(entity)
    message = format_entity_details(entity_full, lang)

    already_added = False
    if user:
        already_added = (
            UserEntityDB.select()
            .join(EntityDB)
            .where(
                (UserEntityDB.user_id == user)
                & (
                    (UserEntityDB.entity == entity)
                    | (
                        (EntityDB.src_id == entity.src_id)
                        & (EntityDB.src_id.is_null(False))
                    )
                )
            )
            .exists()
        )
    keyboard = get_deep_link_keyboard(
        entity_id=entity_full.id,
        lang=lang,
        already_added=already_added,
    )
    if entity_full.poster_url and entity_full.poster_url != "N/A":
        await msg.delete()  # удаляем сообщение с языком только сейчас!
        try:
            await msg.answer_photo(
                entity_full.poster_url, caption=message, reply_markup=keyboard
            )
        except TelegramBadRequest:
            await msg.answer(message, reply_markup=keyboard)
    else:
        await msg.edit_text(message, reply_markup=keyboard)
    await state.set_state(DeepLinkStates.waiting_for_dl_action_entity)
    return True


@dl_router.callback_query(DeepLinkStates.waiting_for_dl_action_entity)
async def handle_dl_action_entity(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("lang")
    data = callback.data

    if data == "dl_cancel":
        await callback.message.delete()
        await callback.message.answer(
            get_string("start_message", lang),
            reply_markup=get_menu_keyboard(lang),
        )
        await state.clear()
        await state.set_state(MainMenuStates.waiting_for_query)
        await callback.answer()
        return
    elif data == "noop":
        await callback.answer()
        return
    elif data.startswith("dl_add:"):
        try:
            _, entity_id = data.split(":", 2)
            entity_id = int(entity_id)
        except (ValueError, IndexError):
            await callback.answer("Invalid callback data")
            return

        # Получаем название сущности для отображения
        try:
            entity = EntityDB.get_by_id(entity_id)
            entity_name = entity.title
        except:
            entity_name = "Entity Name"

        # Проверяем, есть ли фото в сообщении
        has_photo = getattr(callback.message, "photo", None) is not None

        keyboard = get_dl_add_to_list_keyboard(
            entity_id=entity_id,
            lang=lang,
        )
        # Показываем меню выбора статуса
        if has_photo:
            # Если сообщение с фото, нужно удалить его и отправить новое
            await callback.message.delete()
            await callback.message.answer(
                get_string("select_status_type_for", lang).format(
                    entity_name=entity_name
                ),
                reply_markup=keyboard,
            )
        else:
            # Если обычное текстовое сообщение, можно просто отредактировать его
            await callback.message.edit_text(
                get_string("select_status_type_for", lang).format(
                    entity_name=entity_name
                ),
                reply_markup=keyboard,
            )

        # Переходим в состояние ожидания выбора статуса
        await state.set_state(DeepLinkStates.waiting_for_dl_add_to_list)
        await callback.answer()
        return


@dl_router.callback_query(DeepLinkStates.waiting_for_dl_add_to_list)
async def handle_dl_add_to_list_(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    lang = state_data.get("lang")
    data = callback.data
    user = UserDB.get_or_none(tg_id=callback.from_user.id)

    if data.startswith("dl_back:"):
        try:
            _, entity_id = data.split(":", 2)
            entity_id = int(entity_id)
        except (ValueError, IndexError):
            logger.error(f"Invalid callback data: {data}")
            await callback.answer("Invalid callback data")
            return

        success = await show_dl_entity(
            msg=callback.message,
            state=state,
            entity_id=entity_id,
        )
        if success:
            await callback.answer()
        return

    if data.startswith("dl_add_select:"):
        try:
            _, entity_id, status = data.split(":", 3)
            entity_id = int(entity_id)
            status = StatusType(status)
        except (ValueError, IndexError):
            logger.error(f"Invalid callback data: {data}")
            await callback.answer("Invalid callback data")
            return

        try:
            entity = EntityDB.get_by_id(entity_id)

            user_entity, created = UserEntityDB.get_or_create(
                user=user, entity=entity, defaults={"status": status}
            )

            if not created:
                user_entity.status = status
                user_entity.save()

            # Показываем сообщение об успехе
            success_message = get_string("entity_added_to_list", lang).format(
                entity_title=entity.title,
                status_type=get_status_string(status.value, lang),
            )
            await callback.message.delete()
            await callback.message.answer(success_message)
            await callback.message.answer(
                get_string("start_message", lang),
                reply_markup=get_menu_keyboard(lang),
            )
            await state.clear()
            await state.set_state(MainMenuStates.waiting_for_query)

        except Exception as e:
            # Обрабатываем ошибку
            logger.error(f"Error adding to list: {str(e)}")
            await callback.message.delete()
            await callback.message.answer(f"Error adding to list: {str(e)}")
            await state.clear()
            await state.set_state(MainMenuStates.waiting_for_query)
        await callback.answer()
        return
