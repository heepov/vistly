# logger_config.py
import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger():
    # Создаем директорию для логов если её нет
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Настраиваем формат логов
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # Настраиваем хендлер для файла с ротацией
    file_handler = RotatingFileHandler(
        "logs/bot.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 5MB
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Настраиваем хендлер для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Настраиваем основной логгер
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
