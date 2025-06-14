from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict


def get_search_results_keyboard(
    results: List[Dict],
    query: str,
    page: int,
    total_results: int,
    entity_type: str = "movie",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Кнопки с результатами (до 10)
    for item in results:
        title = item.get("Title", "No title")
        year = item.get("Year", "?")
        type_ = item.get("Type", "?")
        imdb_id = item.get("imdbID", "?")
        btn_text = f"{title} ({year}) - {type_.capitalize()}"
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
                text="previous",
                callback_data=f"omdb_page:{query}:{page-1}:{entity_type}",
            )
        )
    pagination_row.append(
        InlineKeyboardButton(text=f"Page {page} of {total_pages}", callback_data="noop")
    )
    if page < total_pages:
        pagination_row.append(
            InlineKeyboardButton(
                text="next", callback_data=f"omdb_page:{query}:{page+1}:{entity_type}"
            )
        )
    builder.row(*pagination_row)
    # Кнопки управления
    builder.row(
        InlineKeyboardButton(
            text="Change Entity type",
            callback_data="change_entity_type",
        ),
        InlineKeyboardButton(text="Cancel", callback_data="cancel_search"),
    )
    return builder.as_markup()


def get_entity_detail_keyboard(
    entity_id: int, query: str, page: int, entity_type: str = "movie"
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="add to list", callback_data=f"add_to_list:{entity_id}"
        ),
        InlineKeyboardButton(
            text="back to results",
            callback_data=f"back_to_results:{query}:{page}:{entity_type}",
        ),
    )
    return builder.as_markup()


def get_status_selection_keyboard(entity_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора статуса добавления в список"""
    builder = InlineKeyboardBuilder()

    # Первый ряд кнопок
    builder.row(
        InlineKeyboardButton(
            text="In progress", callback_data=f"add_status:{entity_id}:in_progress"
        ),
        InlineKeyboardButton(
            text="Complete", callback_data=f"add_status:{entity_id}:complete"
        ),
    )

    # Второй ряд кнопок
    builder.row(
        InlineKeyboardButton(
            text="Planing", callback_data=f"add_status:{entity_id}:planing"
        ),
        InlineKeyboardButton(text="Cancel", callback_data="cancel_add_to_list"),
    )

    return builder.as_markup()
