import asyncio
import logging
import os
from datetime import time
from zoneinfo import ZoneInfo

from app.notifier import check_all_cars
from handlers import (
    register_start_handler,
    register_car_handlers,
    register_handlers_cancel_action,
    register_periodic_task_handler,
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
SEND_TOP_TIME = time(hour=12, minute=0, tzinfo=ZoneInfo("Europe/Moscow"))


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
    register_handlers_cancel_action(dp)
    register_periodic_task_handler(dp)
    
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(
        check_all_cars,
        trigger="cron",
        hour=12,
        minute=0,
        coalesce=True,
        misfire_grace_time=3600,
        args=(bot,),
    )
    scheduler.start()
    
    logger.info("Bot started successfully!")
    try:
        await dp.start_polling(bot)
    finally:
        await dp.storage.close()

        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error occurred: {e}")
