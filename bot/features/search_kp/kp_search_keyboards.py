from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict
from bot.utils.strings import get_string


def get_search_results_keyboard_kp(
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
        title = item.get("name", "No title")
        year = item.get("year", "?")
        type_ = "series" if item.get("isSeries", False) else "movie"
        kp_id = item.get("id", "?")
        btn_text = f"{title} ({year}) - {get_string(type_.lower(), lang)}"
        builder.row(
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"kp_select:{kp_id}:{query}:{page}:{entity_type}",
            )
        )
    # Пагинация
    total_pages = (total_results + 9) // 10
    pagination_row = []
    if page > 1:
        pagination_row.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"kp_page:{query}:{page-1}:{entity_type}",
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
                text="▶️", callback_data=f"kp_page:{query}:{page+1}:{entity_type}"
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
