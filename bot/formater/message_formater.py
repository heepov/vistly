from models.models import Entity
from bot.utils.strings import get_string
from config.config import BOT_USERNAME

MAX_MESSAGE_LENGTH = 900


def format_entity_details(entity: Entity, lang: str = "en") -> str:
    """Формирует сообщение с деталями фильма/сериала"""
    # Собираем рейтинги для вывода
    rating_parts = []
    for rating in entity.ratings:
        if rating.value == 0:
            continue
        if rating.source in ["Internet Movie Database", "IMDB"]:
            rating_parts.append(f"IMDb - {rating.value}")
        elif rating.source == "Rotten Tomatoes":
            rating_parts.append(f"RT - {rating.value}")
        elif rating.source == "Metacritic":
            rating_parts.append(f"MC - {rating.value}")
        elif rating.source == "KP":
            rating_parts.append(f"KP - {rating.value}")

    rating_str = " | ".join(rating_parts) if rating_parts else None

    # Заголовок
    year_str = entity.year_start if entity.year_start else "?"
    if entity.year_end:
        year_str = f"{year_str} - {entity.year_end}"
    header = (
        f"<code>{entity.title}</code> ({year_str}) - {get_string(entity.type, lang)}"
    )

    # Quote-блок
    quote_lines = []
    if rating_str:
        quote_lines.append(f"<b>{get_string('rating', lang)}:</b> {rating_str}")
    if entity.duration:
        quote_lines.append(
            f"<b>{get_string('runtime', lang)}:</b> {entity.duration} {get_string('min', lang)}"
        )
    if entity.total_season:
        quote_lines.append(
            f"<b>{get_string('seasons', lang)}:</b> {entity.total_season}"
        )
    if entity.genres:
        quote_lines.append(
            f"<b>{get_string('genre', lang)}:</b> {', '.join(entity.genres)}"
        )
    if entity.countries:
        quote_lines.append(
            f"<b>{get_string('country', lang)}:</b> {', '.join(entity.countries)}"
        )
    if entity.authors:
        quote_lines.append(
            f"<b>{get_string('director', lang)}:</b> {', '.join(entity.authors)}"
        )
    if entity.actors:
        quote_lines.append(
            f"<b>{get_string('actors', lang)}:</b> {', '.join(entity.actors)}"
        )
    quote_block = (
        "<blockquote>" + "\n".join(quote_lines) + "</blockquote>" if quote_lines else ""
    )

    share_link = f"https://t.me/{BOT_USERNAME}?start=entity_{entity.id}"
    text_link = (
        f'<a href="{share_link}">{get_string("entity_share_link_text", lang)}</a>'
    )

    message_length = MAX_MESSAGE_LENGTH - len(
        f"{header}\n\n{quote_block}\n\n{text_link}"
    )

    description = entity.description if entity.description else ""
    if len(description) > message_length:
        description = description[: message_length - 3] + "..."

    # Собираем всё вместе (без лишних переносов)
    if quote_block and description:
        return f"{header}\n\n{quote_block}\n\n{description}\n\n{text_link}"
    elif quote_block:
        return f"{header}\n\n{quote_block}\n\n{text_link}"
    elif description:
        return f"{header}\n\n{description}\n\n{text_link}"
    else:
        return header
