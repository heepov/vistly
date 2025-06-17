from database.models_db import UserDB


def get_or_create_user(tg_user, lang) -> tuple[UserDB, bool]:
    """
    Получить или создать пользователя по данным Telegram.
    :param tg_user: объект message.from_user
    :return: (User, created)
    """
    full_name = ""
    if tg_user.first_name:
        full_name += tg_user.first_name
    if tg_user.last_name:
        full_name += " " + tg_user.last_name
    if full_name == "":
        full_name = None

    user, created = UserDB.get_or_create(
        tg_id=tg_user.id,
        defaults={
            "username": tg_user.username,
            "name": full_name,
            "language": lang,
        },
    )
    return user, created
