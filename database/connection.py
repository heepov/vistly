from config.config import Config
import logging
from peewee import PostgresqlDatabase
from database.models import (
    User,
    Entity,
    Rating,
    UserEntity,
    Collection,
    CollectionEntity,
)

logger = logging.getLogger(__name__)

db = None


def setup_database(config: Config) -> None:
    try:
        global db
        db = PostgresqlDatabase(
            config.db.database,
            user=config.db.user,
            password=config.db.password,
            host=config.db.host,
            port=config.db.port,
        )

        # Устанавливаем базу данных для моделей
        models = [
            User,
            Entity,
            Rating,
            UserEntity,
            Collection,
            CollectionEntity,
        ]
        for model in models:
            model._meta.database = db

        db.connect()
        db.create_tables(models)
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
