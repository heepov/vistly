from enum import Enum


class EntityType(str, Enum):
    MOVIE = "movie"
    SERIES = "series"
    GAME = "game"
    BOOK = "book"
    MIXED = "mixed"
    ALL = "all"
    UNDEFINED = "undefined"


class StatusType(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PLANNING = "planning"
    ALL = "all"


class LanguageType(str, Enum):
    RU = "ru"
    EN = "en"


class SourceApi(str, Enum):
    OMDB = "omdb"
    KP = "kp"
