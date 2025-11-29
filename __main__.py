import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import register_start_handler, register_car_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def main():
    """
    Основная функция для запуска бота
    """
    logger.info("Starting bot...")
    
    # Создание экземпляров бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация всех хендлеров
    logger.info("Registering handlers...")
    register_start_handler(dp)
    register_car_handlers(dp)
    
    # Запуск polling
    logger.info("Bot started successfully!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error occurred: {e}")
