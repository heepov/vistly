from database.models_db import UserDB


def get_or_create_user(tg_user) -> tuple[UserDB, bool]:
    """
    Получить или создать пользователя по данным Telegram.
    :param tg_user: объект message.from_user
    :return: (User, created)
    """
    user, created = UserDB.get_or_create(
        tg_id=tg_user.id,
        defaults={
            "username": tg_user.username,
            "name": tg_user.full_name,
        },
    )
    return user, created
