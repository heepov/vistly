from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from models.enum_classes import EntityType, StatusType, LanguageType


@dataclass
class User:
    id: int
    added_db: datetime
    tg_id: Optional[int] = None
    username: Optional[str] = None
    name: Optional[str] = None
    info: Optional[str] = None
    language: LanguageType = LanguageType.EN


@dataclass
class Rating:
    source: Optional[str] = None
    value: Optional[float] = None
    max_value: Optional[int] = None
    percent: Optional[bool] = None


@dataclass
class Entity:
    id: int
    title: str
    added_db: datetime
    updated_db: datetime
    src_id: Optional[str] = None
    kp_id: Optional[str] = None
    type: Optional[EntityType] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None
    duration: Optional[int] = None
    genres: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    actors: Optional[List[str]] = None
    countries: Optional[List[str]] = None
    release_date: Optional[datetime] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    total_season: Optional[int] = None
    ratings: List[Rating] = field(default_factory=list)


@dataclass
class UserEntity:
    id: int
    user: User
    entity: Entity
    status: StatusType
    added_db: datetime
    updated_db: datetime
    user_rating: Optional[int] = None
    current_season: Optional[int] = None
