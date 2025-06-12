from enum import Enum


class EntityType(Enum):
    MOVIE = "movie"
    SERIES = "series"
    GAME = "game"
    BOOK = "book"
    MIXED = "mixed"
    UNDEFINED = "undefined"


class StatusType(Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PLANNING = "planning"
    UNDEFINED = "undefined"
