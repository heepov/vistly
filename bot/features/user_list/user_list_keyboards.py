from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models_db import UserEntityDB
from models.enum_classes import StatusType, EntityType
from bot.utils.strings import get_string, get_status_string


def get_ls_results_keyboard(
    user_entities: List[UserEntityDB],
    page: int,
    total_results: int,
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
                callback_data=f"ls_select:{page}:{user_entity.id}",
            )
        )

    # Пагинация
    total_pages = (total_results + 9) // 10
    pagination_row = []
    if page > 1:
        pagination_row.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"ls_page:{page-1}",
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
                callback_data=f"ls_page:{page+1}",
            )
        )
    builder.row(*pagination_row)

    builder.row(
        InlineKeyboardButton(
            text=get_status_string(StatusType.COMPLETED.value, lang),
            callback_data=f"ls_status:{StatusType.COMPLETED.value}",
        ),
        InlineKeyboardButton(
            text=get_status_string(StatusType.IN_PROGRESS.value, lang),
            callback_data=f"ls_status:{StatusType.IN_PROGRESS.value}",
        ),
        InlineKeyboardButton(
            text=get_status_string(StatusType.PLANNING.value, lang),
            callback_data=f"ls_status:{StatusType.PLANNING.value}",
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=get_status_string(StatusType.ALL.value, lang),
            callback_data=f"ls_status:{StatusType.ALL.value}",
        ),
        InlineKeyboardButton(text=get_string("cancel", lang), callback_data="cancel"),
    )

    return builder.as_markup()


def get_ls_detail_keyboard(user_entity, page, lang: str = "en"):
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
            callback_data=f"ls_select_rate:{page}:{user_entity_id}",
        ),
        InlineKeyboardButton(
            text=status_button_name,
            callback_data=f"ls_select_status:{page}:{user_entity_id}",
        ),
    ]
    if entity_type == EntityType.SERIES:
        row_buttons.append(
            InlineKeyboardButton(
                text=current_season_button_name,
                callback_data=f"ls_select_season:{page}:{user_entity_id}",
            )
        )
    builder.row(*row_buttons)
    builder.row(
        InlineKeyboardButton(
            text=get_string("delete", lang),
            callback_data=f"ls_select_delete:{page}:{user_entity_id}",
        ),
        # InlineKeyboardButton(
        #     text=get_string("share", lang),
        #     callback_data=f"ls_select_share:{page}:{user_entity_id}",
        # ),
        InlineKeyboardButton(
            text=get_string("back", lang),
            callback_data=f"ls_back:{page}",
        ),
    )
    return builder.as_markup()


def get_rating_keyboard(user_entity_id, page, lang: str = "en"):
    builder = InlineKeyboardBuilder()
    builder.row(
        *[
            InlineKeyboardButton(
                text=str(i),
                callback_data=f"ls_set_rating:{page}:{user_entity_id}:{i}",
            )
            for i in range(1, 6)
        ]
    )
    builder.row(
        InlineKeyboardButton(
            text=get_string("back", lang),
            callback_data=f"ls_back:{page}:{user_entity_id}",
        )
    )
    return builder.as_markup()


def get_status_keyboard(user_entity_id, page, lang: str = "en"):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_status_string(StatusType.COMPLETED.value, lang),
            callback_data=f"ls_set_status:{page}:{user_entity_id}:{StatusType.COMPLETED.value}",
        ),
        InlineKeyboardButton(
            text=get_status_string(StatusType.IN_PROGRESS.value, lang),
            callback_data=f"ls_set_status:{page}:{user_entity_id}:{StatusType.IN_PROGRESS.value}",
        ),
        InlineKeyboardButton(
            text=get_status_string(StatusType.PLANNING.value, lang),
            callback_data=f"ls_set_status:{page}:{user_entity_id}:{StatusType.PLANNING.value}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=get_string("back", lang),
            callback_data=f"ls_back:{page}:{user_entity_id}",
        )
    )
    return builder.as_markup()


def get_season_number_keyboard(
    user_entity_id,
    season: int = 1,
    lang: str = "en",
    page: int = 1,
):
    builder = InlineKeyboardBuilder()
    # Ряд 1: - | номер | +
    builder.row(
        InlineKeyboardButton(
            text="-",
            callback_data=f"ls_set_season:{page}:{user_entity_id}:{season-1 if season > 1 else 1}",
        ),
        InlineKeyboardButton(
            text=str(season),
            callback_data="noop",  # Просто отображение, без действия
        ),
        InlineKeyboardButton(
            text="+",
            callback_data=f"ls_set_season:{page}:{user_entity_id}:{season+1}",
        ),
    )
    # Ряд 2: Сброс | OK
    builder.row(
        InlineKeyboardButton(
            text=get_string("clean", lang),  # Например, "Сброс"
            callback_data=f"ls_set_season_clean:{page}:{user_entity_id}",
        ),
        InlineKeyboardButton(
            text=get_string("confirm", lang),  # Например, "OK"
            callback_data=f"ls_set_season_confirm:{page}:{user_entity_id}:{season}",
        ),
    )
    return builder.as_markup()


def get_delete_confirm_keyboard(
    user_entity_id,
    lang: str = "en",
    page: int = 1,
):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_string("yes", lang),
            callback_data=f"ls_set_delete:{page}:{user_entity_id}:{True}",
        ),
        InlineKeyboardButton(
            text=get_string("no", lang),
            callback_data=f"ls_back:{page}:{user_entity_id}",
        ),
    )
    return builder.as_markup()
