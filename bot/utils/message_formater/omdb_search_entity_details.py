from database.models_db import EntityDB, RatingDB


def format_entity_details(entity: EntityDB, ratings: list[RatingDB]) -> str:
    """Формирует сообщение с деталями фильма/сериала"""
    # Собираем рейтинги для вывода
    rating_parts = []
    for rating in ratings:
        if rating.source == "Internet Movie Database":
            rating_parts.append(f"IMDb - {rating.value}")
        elif rating.source == "Rotten Tomatoes":
            rating_parts.append(f"RT - {rating.value}")
        elif rating.source == "Metacritic":
            rating_parts.append(f"Meta - {rating.value}")
    rating_str = " | ".join(rating_parts) if rating_parts else None

    # Формируем сообщение
    message_parts = []

    # Заголовок
    release_date_str = (
        f" | {entity.release_date.strftime('%d %b %Y')}" if entity.release_date else ""
    )
    message_parts.append(
        f"<b>{entity.title}</b>{release_date_str} | {entity.type.capitalize()}"
    )

    # Рейтинги
    if rating_str:
        message_parts.append(f"Rating: {rating_str}")

    # Длительность
    if entity.duration:
        message_parts.append(f"Runtime: {entity.duration} min")

    # Количество сезонов
    year_str = (
        f" ({entity.year_start}{f'-{entity.year_end}' if entity.year_end else ''})"
        if entity.year_start
        else ""
    )
    if entity.total_season:
        message_parts.append(f"Seasons: {entity.total_season} | {year_str}")

    # Жанры
    if entity.genres:
        message_parts.append(f"Genre: {', '.join(entity.genres)}")

    # Режиссер
    if entity.authors:
        message_parts.append(f"Director: {', '.join(entity.authors)}")

    # Актеры
    if entity.actors:
        message_parts.append(f"Actors: {', '.join(entity.actors)}")

    # Описание
    if entity.description:
        message_parts.append(f"\n{entity.description}")

    return "\n".join(message_parts)
