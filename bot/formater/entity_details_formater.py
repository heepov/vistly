from models.models import Entity


def format_entity_details(entity: Entity) -> str:
    """Формирует сообщение с деталями фильма/сериала"""
    # Собираем рейтинги для вывода
    rating_parts = []
    for rating in entity.ratings:
        if rating.source == "Internet Movie Database":
            rating_parts.append(f"IMDb - {rating.value}")
        elif rating.source == "Rotten Tomatoes":
            rating_parts.append(f"RT - {rating.value}")
        elif rating.source == "Metacritic":
            rating_parts.append(f"Meta - {rating.value}")
    rating_str = " | ".join(rating_parts) if rating_parts else None

    # Заголовок
    year_str = entity.year_start if entity.year_start else "?"
    if entity.year_end:
        year_str = f"{year_str} - {entity.year_end}"
    header = f"<code>{entity.title} ({year_str})</code> - {entity.type.capitalize()}"

    # Quote-блок (одна строка с \n внутри)
    quote_lines = []
    if rating_str:
        quote_lines.append(f"<b>Rating:</b> {rating_str}")
    if entity.duration:
        quote_lines.append(f"<b>Runtime:</b> {entity.duration} min")
    if entity.total_season:
        quote_lines.append(f"<b>Seasons:</b> {entity.total_season}")
    if entity.genres:
        quote_lines.append(f"<b>Genre:</b> {', '.join(entity.genres)}")
    if entity.countries:
        quote_lines.append(f"<b>Country:</b> {', '.join(entity.countries)}")
    if entity.authors:
        quote_lines.append(f"<b>Director:</b> {', '.join(entity.authors)}")
    if entity.actors:
        quote_lines.append(f"<b>Actors:</b> {', '.join(entity.actors)}")
    quote_block = (
        "<blockquote>" + "\n".join(quote_lines) + "</blockquote>" if quote_lines else ""
    )

    # Описание
    description = entity.description if entity.description else ""

    # Собираем всё вместе (без лишних переносов)
    if quote_block and description:
        return f"{header}\n\n{quote_block}\n\n{description}"
    elif quote_block:
        return f"{header}\n\n{quote_block}"
    elif description:
        return f"{header}\n\n{description}"
    else:
        return header
