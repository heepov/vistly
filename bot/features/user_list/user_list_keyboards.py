from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models_db import UserEntityDB, EntityDB
from models.enum_classes import StatusType, EntityType
from bot.utils.strings import get_string, get_status_string


def get_user_list_keyboard(
    user_entities: List[UserEntityDB],
    page: int,
    total_results: int,
    status: StatusType = None,
    lang: str = "en",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Кнопки с результатами (до 10)
    for user_entity in user_entities:
        entity = user_entity.entity
        year = entity.release_date.year if entity.release_date else "?"
        btn_text = f"{entity.title} ({year}) | {get_string(user_entity.status, lang)}"
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
                text="◀️",
                callback_data=f"user_list_page:{page-1}:{status.value if status else 'all'}",
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
                callback_data=f"user_list_page:{page+1}:{status.value if status else 'all'}",
            )
        )
    builder.row(*pagination_row)

    builder.row(
        InlineKeyboardButton(
            text=get_string("completed", lang),
            callback_data=f"user_list_status:{StatusType.COMPLETED.value}",
        ),
        InlineKeyboardButton(
            text=get_string("in_progress", lang),
            callback_data=f"user_list_status:{StatusType.IN_PROGRESS.value}",
        ),
        InlineKeyboardButton(
            text=get_string("planning", lang),
            callback_data=f"user_list_status:{StatusType.PLANNING.value}",
        ),
    )

    # Кнопка возврата
    builder.row(
        InlineKeyboardButton(
            text=get_string("all", lang), callback_data="user_list_status:all"
        ),
        InlineKeyboardButton(
            text=get_string("cancel", lang), callback_data="back_to_menu"
        ),
    )

    return builder.as_markup()


def get_entity_detail_keyboard(user_entity, page, status, lang: str = "en"):
    user_entity_id = user_entity.id
    entity_type = user_entity.entity.type
    rating = user_entity.user_rating
    current_season = user_entity.current_season

    # Кнопка рейтинга
    rate_button_name = (
        get_string("user_rating", lang).format(rating=rating)
        if rating is not None
        else get_string("set_rating", lang)
    )
    # Кнопка сезона (только для сериалов)
    current_season_button_name = (
        get_string("user_season", lang).format(season=current_season)
        if current_season is not None
        else get_string("set_season", lang)
    )
    # Кнопка статуса
    status_button_name = get_status_string(user_entity.status, lang)

    builder = InlineKeyboardBuilder()
    row_buttons = [
        InlineKeyboardButton(
            text=rate_button_name,
            callback_data=f"rate_entity:{user_entity_id}:{page}:{status if status else 'all'}",
        ),
        InlineKeyboardButton(
            text=status_button_name,
            callback_data=f"status_entity:{user_entity_id}:{page}:{status if status else 'all'}",
        ),
    ]
    if entity_type == EntityType.SERIES:
        row_buttons.append(
            InlineKeyboardButton(
                text=current_season_button_name,
                callback_data=f"season_entity:{user_entity_id}:{page}:{status if status else 'all'}",
            )
        )
    builder.row(*row_buttons)
    builder.row(
        InlineKeyboardButton(
            text=get_string("delete", lang),
            callback_data=f"delete_entity:{user_entity_id}:{page}:{status if status else 'all'}",
        ),
        InlineKeyboardButton(
            text=get_string("share", lang),
            callback_data=f"share_entity:{user_entity_id}:{page}:{status if status else 'all'}",
        ),
        InlineKeyboardButton(
            text=get_string("back", lang),
            callback_data=f"user_list_page:{page}:{status if status else 'all'}",
        ),
    )
    return builder.as_markup()


def get_rating_keyboard(user_entity_id, lang: str = "en"):
    builder = InlineKeyboardBuilder()
    builder.row(
        *[
            InlineKeyboardButton(
                text=str(i), callback_data=f"set_rating:{user_entity_id}:{i}"
            )
            for i in range(1, 6)
        ]
    )
    builder.row(
        InlineKeyboardButton(
            text=get_string("back", lang),
            callback_data=f"back_to_entity:{user_entity_id}",
        )
    )
    return builder.as_markup()


def get_status_keyboard(user_entity_id, lang: str = "en"):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_string("completed", lang),
            callback_data=f"set_status:{user_entity_id}:completed",
        ),
        InlineKeyboardButton(
            text=get_string("in_progress", lang),
            callback_data=f"set_status:{user_entity_id}:in_progress",
        ),
        InlineKeyboardButton(
            text=get_string("planning", lang),
            callback_data=f"set_status:{user_entity_id}:planning",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=get_string("back", lang),
            callback_data=f"back_to_entity:{user_entity_id}",
        )
    )
    return builder.as_markup()


def get_delete_confirm_keyboard(user_entity_id, lang: str = "en"):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_string("yes", lang),
            callback_data=f"delete_confirm:{user_entity_id}:yes",
        ),
        InlineKeyboardButton(
            text=get_string("no", lang),
            callback_data=f"back_to_entity:{user_entity_id}",
        ),
    )
    return builder.as_markup()


def get_season_number_keyboard(user_entity_id, season: int = 1, lang: str = "en"):
    builder = InlineKeyboardBuilder()
    # Ряд 1: - | номер | +
    builder.row(
        InlineKeyboardButton(
            text="-",
            callback_data=f"season_number:{user_entity_id}:{season-1 if season > 1 else 1}",
        ),
        InlineKeyboardButton(
            text=str(season),
            callback_data="noop",  # Просто отображение, без действия
        ),
        InlineKeyboardButton(
            text="+",
            callback_data=f"season_number:{user_entity_id}:{season+1}",
        ),
    )
    # Ряд 2: Сброс | OK
    builder.row(
        InlineKeyboardButton(
            text=get_string("clean", lang),  # Например, "Сброс"
            callback_data=f"season_number:{user_entity_id}:clean",
        ),
        InlineKeyboardButton(
            text=get_string("confirm", lang),  # Например, "OK"
            callback_data=f"set_season:{user_entity_id}:{season}",
        ),
    )
    return builder.as_markup()
