from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict
from bot.utils.strings import get_string


def get_search_results_keyboard(
    results: List[Dict],
    query: str,
    page: int,
    total_results: int,
    entity_type: str = "movie",
    lang: str = "en",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Кнопки с результатами (до 10)
    for item in results:
        title = item.get("Title", "No title")
        year = item.get("Year", "?")
        type_ = item.get("Type", "?")
        imdb_id = item.get("imdbID", "?")
        btn_text = f"{title} ({year}) - {get_string(type_.lower(), lang)}"
        builder.row(
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"omdb_select:{imdb_id}:{query}:{page}:{entity_type}",
            )
        )
    # Пагинация
    total_pages = (total_results + 9) // 10
    pagination_row = []
    if page > 1:
        pagination_row.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"omdb_page:{query}:{page-1}:{entity_type}",
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
                text="▶️", callback_data=f"omdb_page:{query}:{page+1}:{entity_type}"
            )
        )
    builder.row(*pagination_row)
    # Кнопки управления
    builder.row(
        InlineKeyboardButton(
            text=get_string("change_entity_type", lang),
            callback_data="change_entity_type",
        ),
        InlineKeyboardButton(
            text=get_string("cancel", lang), callback_data="cancel_search"
        ),
    )
    return builder.as_markup()


def get_entity_detail_keyboard(
    entity_id: int,
    query: str,
    page: int,
    entity_type: str = "movie",
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
                text=get_string("back", lang),
                callback_data=f"back_to_results:{query}:{page}:{entity_type}",
            ),
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text=get_string("add_to_list", lang),
                callback_data=f"add_to_list:{entity_id}",
            ),
            InlineKeyboardButton(
                text=get_string("back", lang),
                callback_data=f"back_to_results:{query}:{page}:{entity_type}",
            ),
        )
    return builder.as_markup()


def get_status_selection_keyboard(
    entity_id: int, lang: str = "en"
) -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора статуса добавления в список"""
    builder = InlineKeyboardBuilder()

    # Первый ряд кнопок
    builder.row(
        InlineKeyboardButton(
            text=get_string("in_progress", lang),
            callback_data=f"add_status:{entity_id}:in_progress",
        ),
        InlineKeyboardButton(
            text=get_string("completed", lang),
            callback_data=f"add_status:{entity_id}:completed",
        ),
    )

    # Второй ряд кнопок
    builder.row(
        InlineKeyboardButton(
            text=get_string("planning", lang),
            callback_data=f"add_status:{entity_id}:planning",
        ),
        InlineKeyboardButton(
            text=get_string("cancel", lang), callback_data="cancel_add_to_list"
        ),
    )

    return builder.as_markup()
