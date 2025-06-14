def format_entity_details(
    entity,
    user_status=None,
    user_season=None,
    user_rating=None,
    user_comment=None,
    poster_url=None,
):
    """
    Формирует подробное описание фильма/сериала для Telegram.
    """
    # Заголовок
    title = entity.title
    year = getattr(entity, "year", "")
    entity_type = getattr(entity, "type", "")
    header = f"<b>{title} ({year}) | {entity_type.capitalize()}</b>"

    # User info
    user_info = f"<b>User status</b>: {user_status or '-'}"
    if user_season:
        user_info += f" | <b>Season</b>: {user_season}"
    if user_rating:
        user_info += f" | <b>User Rating</b>: {user_rating}"

    # Основная информация
    rating = getattr(entity, "rating", "-")
    runtime = getattr(entity, "runtime", "-")
    genre = getattr(entity, "genre", "-")
    directors = getattr(entity, "directors", "-")
    actors = getattr(entity, "actors", "-")
    country = getattr(entity, "country", "-")

    main_info = (
        f"rating {rating} | {runtime}\n{genre}\n{directors}\n{actors}\n{country}"
    )

    # Описание
    description = getattr(entity, "description", "-")
    description_block = f"\n\nDescription:\n{description}"

    # Комментарий пользователя
    comment_block = ""
    if user_comment:
        comment_block = f"\n\nComment:\n{user_comment}"

    # Собираем всё вместе
    text = f"{header}\n{user_info}\n\n{main_info}{description_block}{comment_block}"

    return text, poster_url
