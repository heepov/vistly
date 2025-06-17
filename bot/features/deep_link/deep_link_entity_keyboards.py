import logging
from bot.utils.strings import get_string
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from models.enum_classes import StatusType

logger = logging.getLogger(__name__)


def get_deep_link_keyboard(
    entity_id: int,
    lang: str = "en",
    already_added: bool = False,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if already_added:
        builder.row(
            InlineKeyboardButton(
                text=get_string("already_added", lang),
                callback_data="noop",
            ),
            InlineKeyboardButton(
                text=get_string("cancel", lang),
                callback_data=f"dl_cancel",
            ),
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text=get_string("add_to_list", lang),
                callback_data=f"dl_add:{entity_id}",
            ),
            InlineKeyboardButton(
                text=get_string("cancel", lang),
                callback_data=f"dl_cancel",
            ),
        )
    return builder.as_markup()


def get_dl_add_to_list_keyboard(
    entity_id: int,
    lang: str = "en",
) -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора статуса добавления в список"""
    builder = InlineKeyboardBuilder()

    # Первый ряд кнопок
    builder.row(
        InlineKeyboardButton(
            text=get_string("in_progress", lang),
            callback_data=f"dl_add_select:{entity_id}:{StatusType.IN_PROGRESS.value}",
        ),
        InlineKeyboardButton(
            text=get_string("completed", lang),
            callback_data=f"dl_add_select:{entity_id}:{StatusType.COMPLETED.value}",
        ),
    )

    # Второй ряд кнопок
    builder.row(
        InlineKeyboardButton(
            text=get_string("planning", lang),
            callback_data=f"dl_add_select:{entity_id}:{StatusType.PLANNING.value}",
        ),
        InlineKeyboardButton(
            text=get_string("back", lang),
            callback_data=f"dl_back:{entity_id}",
        ),
    )

    return builder.as_markup()
