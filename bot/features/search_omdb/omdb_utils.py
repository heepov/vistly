from database.models_db import EntityDB, RatingDB
from models.enum_classes import EntityType
from datetime import datetime, date


def parse_year_range(year_str: str) -> tuple[int | None, int | None]:
    if not year_str or year_str == "N/A":
        return None, None

    # Разделяем строку по дефису
    parts = year_str.split("–")

    try:
        year_start = int(parts[0])
        # Если есть вторая часть и она не пустая
        year_end = int(parts[1]) if len(parts) > 1 and parts[1].strip() else None
        return year_start, year_end
    except (ValueError, IndexError):
        return None, None


def parse_duration(duration_str: str) -> int | None:
    """Парсит строку длительности в минуты"""
    if not duration_str:
        return None
    try:
        return int(duration_str.split()[0])
    except (ValueError, IndexError):
        return None


def parse_list(value: str) -> list[str] | None:
    """Парсит строку со списком значений в список"""
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_date(date_str: str) -> date | None:
    """Парсит строку даты в объект date"""
    if not date_str or date_str == "N/A":
        return None
    try:
        return datetime.strptime(date_str, "%d %b %Y").date()
    except (ValueError, IndexError):
        return None


def parse_rating_value(value_str: str) -> tuple[float, int, bool] | None:
    """Парсит строку рейтинга в (значение, максимальное значение, процент)"""
    if not value_str or value_str == "N/A":
        return None

    try:
        if "%" in value_str:
            value = float(value_str.replace("%", ""))
            return value, 100, True
        elif "/" in value_str:
            left, right = value_str.split("/", 1)
            value = float(left)
            max_value = int(right)
            return value, max_value, False
        else:
            value = float(value_str)
            return value, 10, False
    except (ValueError, IndexError):
        return None


def omdb_details_to_db(details: dict) -> tuple[EntityDB, bool]:
    year_start, year_end = parse_year_range(details.get("Year"))

    total_season = None
    total_season_str = details.get("totalSeasons")
    if total_season_str:
        try:
            total_season = int(total_season_str)
        except ValueError:
            pass

    entity, created = EntityDB.get_or_create(
        src_id=details.get("imdbID"),
        kp_id=None,
        defaults={
            "title": details.get("Title") or "No title",
            "type": details.get("Type") or EntityType.UNDEFINED,
            "description": details.get("Plot"),
            "poster_url": details.get("Poster"),
            "duration": parse_duration(details.get("Runtime")),
            "genres": parse_list(details.get("Genre")),
            "authors": parse_list(details.get("Director")),
            "actors": parse_list(details.get("Actors")),
            "countries": parse_list(details.get("Country")),
            "release_date": parse_date(details.get("Released")),
            "year_start": year_start,
            "year_end": year_end,
            "total_season": total_season,
        },
    )
    return entity, created


def omdb_ratings_to_db(entity: EntityDB, details: dict) -> list[RatingDB]:
    """Создает или обновляет рейтинги в базе данных из данных OMDB"""
    ratings = []
    ratings_data = details.get("Ratings")

    if not ratings_data:
        return ratings

    for rating_data in ratings_data:
        source = rating_data.get("Source")
        value_str = rating_data.get("Value")

        if not source or not value_str:
            continue

        value, max_value, percent = parse_rating_value(value_str)

        rating, _ = RatingDB.get_or_create(
            entity=entity,
            source=source,
            defaults={"value": value, "max_value": max_value, "percent": percent},
        )
        ratings.append(rating)

    return ratings
