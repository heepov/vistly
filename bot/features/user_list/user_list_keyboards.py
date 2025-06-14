from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models_db import UserEntityDB, EntityDB
from models.enum_classes import StatusType, EntityType

status_name_map = {
    StatusType.PLANNING: "Planing",
    StatusType.IN_PROGRESS: "In progress",
    StatusType.COMPLETED: "Completed",
}


def get_user_list_keyboard(
    user_entities: List[UserEntityDB],
    page: int,
    total_results: int,
    status: StatusType = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Кнопки с результатами (до 10)
    for user_entity in user_entities:
        entity = user_entity.entity
        # Безопасное получение статуса
        status_text = status_name_map.get(
            user_entity.status,
            str(user_entity.status).capitalize() if user_entity.status else "Undefined",
        )
        year = entity.release_date.year if entity.release_date else "?"
        btn_text = f"{entity.title} ({year}) | {status_text}"
        builder.row(
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"user_entity_select:{user_entity.id}:{page}:{status.value if status else 'all'}",
            )
        )

    # Пагинация
    total_pages = (total_results + 9) // 10
    pagination_row = []
    if page > 1:
        pagination_row.append(
            InlineKeyboardButton(
                text="previous",
                callback_data=f"user_list_page:{page-1}:{status.value if status else 'all'}",
            )
        )
    pagination_row.append(
        InlineKeyboardButton(text=f"Page {page} of {total_pages}", callback_data="noop")
    )
    if page < total_pages:
        pagination_row.append(
            InlineKeyboardButton(
                text="next",
                callback_data=f"user_list_page:{page+1}:{status.value if status else 'all'}",
            )
        )
    builder.row(*pagination_row)

    # Кнопки фильтрации по статусу + кнопка All
    status_buttons = []
    for status_type in StatusType:
        status_text = status_name_map.get(status_type, str(status_type).capitalize())
        status_buttons.append(
            InlineKeyboardButton(
                text=status_text,
                callback_data=f"user_list_status:{status_type.value}",
            )
        )
    builder.row(*status_buttons)

    # Кнопка возврата
    builder.row(
        InlineKeyboardButton(text="All", callback_data="user_list_status:all"),
        InlineKeyboardButton(text="Back to Menu", callback_data="back_to_menu"),
    )

    return builder.as_markup()


def get_entity_detail_keyboard(user_entity, page):
    user_entity_id = user_entity.id
    entity_type = user_entity.entity.type
    status = user_entity.status
    rating = user_entity.user_rating
    current_season = user_entity.current_season

    # Кнопка рейтинга
    rate_button_name = f"U rate: {rating}" if rating is not None else "Rate it"
    # Кнопка сезона (только для сериалов)
    current_season_button_name = (
        f"U season: {current_season}" if current_season is not None else "Set season"
    )
    # Кнопка статуса
    status_button_name = status_name_map.get(
        status, str(status).capitalize() if status else "Set status"
    )

    builder = InlineKeyboardBuilder()
    row_buttons = [
        InlineKeyboardButton(
            text=rate_button_name, callback_data=f"rate_entity:{user_entity_id}"
        ),
        InlineKeyboardButton(
            text=status_button_name, callback_data=f"status_entity:{user_entity_id}"
        ),
    ]
    if entity_type == EntityType.SERIES:
        row_buttons.append(
            InlineKeyboardButton(
                text=current_season_button_name,
                callback_data=f"season_entity:{user_entity_id}",
            )
        )
    builder.row(*row_buttons)
    builder.row(
        InlineKeyboardButton(
            text="Remove", callback_data=f"delete_entity:{user_entity_id}"
        ),
        InlineKeyboardButton(
            text="Share", callback_data=f"share_entity:{user_entity_id}"
        ),
        InlineKeyboardButton(
            text="Back",
            callback_data=f"user_list_page:{page}:{status if status else 'all'}",
        ),
    )
    return builder.as_markup()
