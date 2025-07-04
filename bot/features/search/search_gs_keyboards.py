import logging

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict
from bot.utils.strings import get_string
from models.enum_classes import SourceApi, StatusType

logger = logging.getLogger(__name__)


def get_gs_kp_list_keyboard(
    results: List[Dict],
    lang: str = "en",
) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for item in results:
        title = item.get("name", "No title")
        year = item.get("year", "?")
        type = "series" if item.get("isSeries", False) else "movie"
        kp_id = item.get("id", "?")
        btn_text = f"{title} ({year}) - {get_string(type.lower(), lang)}"
        builder.row(
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"gs_select:{kp_id}",
            )
        )
    return builder


def get_gs_omdb_list_keyboard(
    results: List[Dict],
    lang: str = "en",
) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for item in results:
        title = item.get("Title", "No title")
        year = item.get("Year", "?")
        type = item.get("Type", "?")
        imdb_id = item.get("imdbID", "?")
        btn_text = f"{title} ({year}) - {get_string(type.lower(), lang)}"
        builder.row(
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"gs_select:{imdb_id}",
            )
        )
    return builder


def get_gs_results_keyboard(
    results: List[Dict],
    source_api: SourceApi,
    page: int,
    total_results: int,
    lang: str = "en",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Кнопки с результатами
    if source_api == SourceApi.KP:
        builder = get_gs_kp_list_keyboard(
            results=results,
            lang=lang,
        )
    elif source_api == SourceApi.OMDB:
        builder = get_gs_omdb_list_keyboard(
            results=results,
            lang=lang,
        )

    # Пагинация
    total_pages = (total_results + 9) // 10
    pagination_row = []
    if page > 1:
        pagination_row.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data="gs_page_prev",
            )
        )
    pagination_row.append(
        InlineKeyboardButton(
            text=get_string("page_of_total_pages", lang).format(
                page=page, total_pages=total_pages
            ),
            callback_data="noop",
        )
    )
    if page < total_pages:
        pagination_row.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data="gs_page_next",
            )
        )
    builder.row(*pagination_row)
    # Кнопки управления
    builder.row(
        InlineKeyboardButton(
            text=get_string("change_entity_type", lang),
            callback_data="gs_filter",
        ),
        InlineKeyboardButton(
            text=get_string("cancel", lang), callback_data="gs_cancel"
        ),
    )
    return builder.as_markup()


def get_gs_entity_detail_keyboard(
    entity_id: int,
    lang: str = "en",
    already_added: bool = False,
    is_deep_link: bool = False,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if is_deep_link:
        back_btn = InlineKeyboardButton(
            text=get_string("cancel", lang),
            callback_data="gs_cancel",
        )
    else:
        back_btn = InlineKeyboardButton(
            text=get_string("back", lang),
            callback_data="gs_back",
        )
    if already_added:
        builder.row(
            InlineKeyboardButton(
                text=get_string("already_added", lang),
                callback_data="noop",
            ),
            back_btn,
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text=get_string("add_to_list", lang),
                callback_data=f"gs_add:{entity_id}",
            ),
            back_btn,
        )
    return builder.as_markup()


def get_gs_add_to_list_keyboard(
    entity_id: int,
    lang: str = "en",
) -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора статуса добавления в список"""
    builder = InlineKeyboardBuilder()

    # Первый ряд кнопок
    builder.row(
        InlineKeyboardButton(
            text=get_string("in_progress", lang),
            callback_data=f"gs_add_select:{entity_id}:{StatusType.IN_PROGRESS.value}",
        ),
        InlineKeyboardButton(
            text=get_string("completed", lang),
            callback_data=f"gs_add_select:{entity_id}:{StatusType.COMPLETED.value}",
        ),
    )

    # Второй ряд кнопок
    builder.row(
        InlineKeyboardButton(
            text=get_string("planning", lang),
            callback_data=f"gs_add_select:{entity_id}:{StatusType.PLANNING.value}",
        ),
        InlineKeyboardButton(
            text=get_string("back", lang),
            callback_data="gs_back",
        ),
    )

    return builder.as_markup()
