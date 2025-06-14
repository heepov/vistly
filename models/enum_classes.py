from enum import Enum


class EntityType(str, Enum):
    MOVIE = "movie"
    SERIES = "series"
    GAME = "game"
    BOOK = "book"
    MIXED = "mixed"
    UNDEFINED = "undefined"


class StatusType(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PLANNING = "planning"


class LanguageType(str, Enum):
    RU = "ru"
    EN = "en"
