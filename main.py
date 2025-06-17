import asyncio
import logging
from config.logger_config import setup_logger
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config.config import load_config
from bot.shared.main_commad_handlers import router
from database.connection import setup_database

logger = logging.getLogger(__name__)


async def main():
    setup_logger()
    config = load_config()

    # Инициализируем базу данных
    setup_database(config)

    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
