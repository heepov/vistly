from config.config import Config
import logging
from peewee import PostgresqlDatabase
from database.models_db import UserDB, EntityDB, RatingDB, UserEntityDB

logger = logging.getLogger(__name__)

db = None


def setup_database(config: Config) -> None:
    try:
        # Сначала пытаемся подключиться к целевой базе данных
        global db
        db = PostgresqlDatabase(
            config.db.database,
            user=config.db.user,
            password=config.db.password,
            host=config.db.host,
            port=config.db.port,
        )

        # Устанавливаем базу данных для моделей
        models = [UserDB, EntityDB, RatingDB, UserEntityDB]
        for model in models:
            model._meta.database = db

        try:
            # Пытаемся подключиться к целевой базе
            db.connect()
            logger.info(f"Connected to existing database: {config.db.database}")
        except Exception as connect_error:
            logger.info(f"Database {config.db.database} does not exist, creating it...")

            # Подключаемся к default базе для создания новой
            admin_db = PostgresqlDatabase(
                "postgres_db",  # default база данных
                user=config.db.user,
                password=config.db.password,
                host=config.db.host,
                port=config.db.port,
            )

            try:
                admin_db.connect()
                # Создаем базу данных
                admin_db.execute_sql(f"CREATE DATABASE {config.db.database};")
                logger.info(f"Database {config.db.database} created successfully")
                admin_db.close()

                # Теперь подключаемся к созданной базе
                db.connect()
                logger.info(
                    f"Connected to newly created database: {config.db.database}"
                )
            except Exception as create_error:
                logger.error(f"Failed to create database: {create_error}")
                admin_db.close()
                raise create_error

        # Создаем таблицы
        db.create_tables(models)
        logger.info("Database tables created successfully")
        logger.info("Database connection established")

    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
