from datetime import datetime
from models.enum_classes import EntityType, StatusType
from typing import Optional, List, Dict, Any, Union


class User:
    def __init__(
        self,
        id: int,
        added_db: datetime,
        tg_id: Optional[int] = None,
        username: Optional[str] = None,
        name: Optional[str] = None,
        info: Optional[str] = None,
    ):
        self.id = id
        self.added_db = added_db
        self.tg_id = tg_id
        self.username = username
        self.name = name
        self.info = info


class Rating:
    def __init__(
        self,
        source: Optional[str] = None,
        value: Optional[float] = None,
        max_value: Optional[int] = None,
        percent: Optional[bool] = None,
    ):
        self.source = source
        self.value = value
        self.max_value = max_value
        self.percent = percent


class Entity:
    def __init__(
        self,
        id: int,
        title: str,
        added_db: datetime,
        updated_db: datetime,
        src_id: Optional[str] = None,
        type: Optional[EntityType] = None,
        description: Optional[str] = None,
        poster_url: Optional[str] = None,
        duration: Optional[int] = None,
        genres: Optional[List[str]] = None,
        authors: Optional[List[str]] = None,
        actors: Optional[List[str]] = None,
        countries: Optional[List[str]] = None,
        release_date: Optional[datetime] = None,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        total_season: Optional[int] = None,
        ratings: Optional[List[Rating]] = None,
    ):
        self.id = id
        self.src_id = src_id
        self.title = title
        self.type = type
        self.description = description
        self.poster_url = poster_url
        self.duration = duration
        self.genres = genres
        self.authors = authors
        self.actors = actors
        self.countries = countries
        self.release_date = release_date
        self.year_start = year_start
        self.year_end = year_end
        self.total_season = total_season
        self.added_db = added_db
        self.updated_db = updated_db
        self.ratings = ratings


class UserEntity:
    def __init__(
        self,
        id: int,
        user: User,
        entity: Entity,
        status: StatusType,
        added_db: datetime,
        updated_db: datetime,
        user_rating: Optional[int] = None,
        comment: Optional[str] = None,
        current_season: Optional[int] = None,
    ):
        self.id = id
        self.user = user
        self.entity = entity
        self.status = status
        self.user_rating = user_rating
        self.comment = comment
        self.current_season = current_season
        self.added_db = added_db
        self.updated_db = updated_db
