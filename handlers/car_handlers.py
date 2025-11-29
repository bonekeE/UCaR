import logging

from states import register_add_car_handlers, register_update_car_handlers
from keyboards.common import main_menu_keyboard

from aiogram import F, Dispatcher
from aiogram.types import CallbackQuery
from app import car_service

logger = logging.getLogger(__name__)


async def cmd_get_cars(callback: CallbackQuery):
    """Получение списка машин пользователя"""
    await callback.message.delete()
    user_id = callback.message.from_user.id
    
    try:
        cars = car_service.get_user_cars(user_id)

        if len(cars) == 0:
            await callback.message.answer("У вас пока нет машин")
            await callback.message.answer(
                "Выберите действие:",
                reply_markup=main_menu_keyboard(),
            )
            return

        response_text = "Список ваших машин:\n\n"
        for idx, car in enumerate(cars, 1):
            response_text += f"Машина #{idx}:\n"
            response_text += f"Бренд: {car.get('brand')}\n"
            response_text += f"Модель: {car.get('model')}\n"
            response_text += f"Дата последнего ТО: {car.get('last_service_time')}\n"
            response_text += f"Год производства: {car.get('year_of_manufacture')}\n\n"
                    
        await callback.message.answer(response_text)
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard(),
        )
    except Exception as e:
        await callback.message.answer(f"❌ Неожиданная ошибка")
        logger.error(f"Unexpected error when getting cars for user {user_id}: {e}")


def register_car_handlers(dp: Dispatcher):
    """Регистрация всех хендлеров для работы с машинами"""

    dp.callback_query.register(
        cmd_get_cars,
        F.data == "get_cars",
    )
    register_add_car_handlers(dp)
    register_update_car_handlers(dp)
