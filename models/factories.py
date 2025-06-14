from models.models import Entity, Rating
from database.models_db import EntityDB


def build_entity_from_db(entity_db: EntityDB) -> Entity:
    # Собираем рейтинги
    ratings = [
        Rating(
            source=rating.source,
            value=rating.value,
            max_value=rating.max_value,
            percent=rating.percent,
        )
        for rating in entity_db.ratings
    ]
    return Entity(
        id=entity_db.id,
        title=entity_db.title,
        added_db=entity_db.added_db,
        updated_db=entity_db.updated_db,
        src_id=entity_db.src_id,
        type=entity_db.type,
        description=entity_db.description,
        poster_url=entity_db.poster_url,
        duration=entity_db.duration,
        genres=entity_db.genres,
        authors=entity_db.authors,
        actors=entity_db.actors,
        countries=entity_db.countries,
        release_date=entity_db.release_date,
        year_start=entity_db.year_start,
        year_end=entity_db.year_end,
        total_season=entity_db.total_season,
        ratings=ratings,
    )
