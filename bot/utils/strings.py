import json
from pathlib import Path

# Загружаем строки локализации
strings_file = Path(__file__).parent / "strings.json"
with open(strings_file, encoding="utf-8") as f:
    STRINGS = json.load(f)


def get_string(key, lang="en", **kwargs):
    """Получить строку по ключу и языку"""
    text = STRINGS.get(key, {}).get(lang, key)
    try:
        return text.format(**kwargs)
    except Exception:
        return text


def get_status_string(status: str, lang: str = "en") -> str:
    """Получить строку статуса (обратная совместимость)"""
    return get_string(f"status_{status}", lang)


def get_all_commands() -> list[str]:
    """Получить все команды (обратная совместимость)"""
    commands = []
    for lang in ["en", "ru"]:
        commands.extend(
            [
                get_string("restart", lang),
                get_string("list", lang),
                get_string("profile", lang),
            ]
        )
    commands.extend(["/restart", "/list", "/profile"])
    return commands


def get_restart_commands() -> list[str]:
    """Получить команды перезапуска (обратная совместимость)"""
    commands = [get_string("restart", lang) for lang in ["en", "ru"]]
    commands.append("/restart")
    return commands


def get_list_commands() -> list[str]:
    """Получить команды списка (обратная совместимость)"""
    commands = [get_string("list", lang) for lang in ["en", "ru"]]
    commands.append("/list")
    return commands


def get_profile_commands() -> list[str]:
    """Получить команды профиля (обратная совместимость)"""
    commands = [get_string("profile", lang) for lang in ["en", "ru"]]
    commands.append("/profile")
    return commands
