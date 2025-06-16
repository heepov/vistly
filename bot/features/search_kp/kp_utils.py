from database.models_db import EntityDB, RatingDB
from models.enum_classes import EntityType
from datetime import datetime
from bot.features.search_kp.kp_service import KpService


def parse_dict(items: list[dict], key: str) -> list[str]:
    """Извлекает значения по ключу из списка словарей"""
    if not items:
        return []
    return [item.get(key, "") for item in items if key in item and item.get(key)]


def parse_seasons_count(seasons_info: list[dict]) -> int | None:
    """Возвращает максимальное значение поля 'number' из списка сезонов"""
    if not seasons_info:
        return None
    numbers = [
        season.get("number", 0)
        for season in seasons_info
        if isinstance(season.get("number", 0), int)
    ]
    return max(numbers) if numbers else None


def parse_person_names_by_profession(
    persons: list[dict], profession: str, name_key: str = "name"
) -> list[str]:
    result = []
    for person in persons:
        if person.get("enProfession") == profession:
            name = person.get(name_key) or person.get("enName") or person.get("name")
            if name:
                result.append(name)
            if len(result) == 5:
                break
    return result


def kp_details_to_db(details: dict) -> tuple[EntityDB, bool]:
    """Создает или обновляет запись в базе данных для сущности из Kp"""
    type = "series" if KpService.get_safe_value(details, "isSeries") else "movie"
    duration = None
    if KpService.get_safe_value(details, "movieLength"):
        duration = KpService.get_safe_value(details, "movieLength")
    elif KpService.get_safe_value(details, "seriesLength"):
        duration = KpService.get_safe_value(details, "seriesLength")

    entity, created = EntityDB.get_or_create(
        src_id=KpService.get_safe_value(details, "externalId.imdb"),
        kp_id=KpService.get_safe_value(details, "id"),
        defaults={
            "title": KpService.get_safe_value(details, "name") or "No title",
            "type": type or EntityType.UNDEFINED,
            "description": KpService.get_safe_value(details, "description"),
            "poster_url": KpService.get_safe_value(details, "poster.url"),
            "duration": duration,
            "genres": parse_dict(
                KpService.get_safe_value(details, "genres", []), "name"
            ),
            "authors": parse_person_names_by_profession(
                KpService.get_safe_value(details, "persons", []), "director"
            ),
            "actors": parse_person_names_by_profession(
                KpService.get_safe_value(details, "persons", []), "actor"
            ),
            "countries": parse_dict(
                KpService.get_safe_value(details, "countries", []), "name"
            ),
            "release_date": datetime.strptime(
                f"01.01.{KpService.get_safe_value(details, 'year')}", "%d.%m.%Y"
            ).date(),
            "year_start": KpService.get_safe_value(details, "year"),
            "year_end": KpService.get_safe_value(details, "releaseYears.end"),
            "total_season": parse_seasons_count(
                KpService.get_safe_value(details, "seasonsInfo", [])
            ),
        },
    )
    return entity, created


def kp_ratings_to_db(entity: EntityDB, details: dict) -> list[RatingDB]:
    """Создает или обновляет рейтинги в базе данных только для 'kp' и 'imdb'"""
    ratings = []
    ratings_data = details.get("rating")

    if not ratings_data or not isinstance(ratings_data, dict):
        return ratings

    for source in ("kp", "imdb"):
        value = ratings_data.get(source)
        if value is not None:
            rating, _ = RatingDB.get_or_create(
                entity=entity,
                source=source.upper(),  # 'KP' или 'IMDB'
                defaults={"value": value, "max_value": 10, "percent": False},
            )
            ratings.append(rating)

    return ratings
