STRINGS = {
    "en": {
        "welcome": "Welcome!",
        "list_empty": "Your list is empty.",
    },
    "ru": {
        "welcome": "Добро пожаловать!",
        "list_empty": "Ваш список пуст.",
    }
}

def get_string(key, lang="en"):
    return STRINGS.get(lang, STRINGS["en"]).get(key, key)


# Выберите язык / Choose language:
# Hi! Enter the name of the movie or TV series to search for: