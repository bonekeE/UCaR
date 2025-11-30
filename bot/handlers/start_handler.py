import logging

from keyboards.common import main_menu_keyboard

from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from app import user_service

logger = logging.getLogger(__name__)


GREET_MESSAGE = (
    "Приветствуем на нашем сервисе!\n"
    "На нем вы можете добавить информацию о своем автомобиле и отслеживать "
    "жизненный цикл запчастей. Сервис будет напоминать вам о замене расходников, "
    "когда будет подходить срок их износа."
)

async def cmd_start(message: Message):
    """
    Обработчик команды /start для получения данных пользователя и отправки запроса на сервер
    """
    user = message.from_user
    
    user_id = user.id
    
    try:
        user_service.register_user(user.id, user.username)
        logger.info(f"User {user.id} {user.username} registered successfully")

        await message.answer(GREET_MESSAGE)
        await message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard(),
        )
    except Exception as e:
        error_msg = f"❌ Неожиданная ошибка"
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(error_msg)


def register_start_handler(dp: Dispatcher):
    """Регистрация хендлера команды /start"""
    dp.message.register(cmd_start, Command("start"))
