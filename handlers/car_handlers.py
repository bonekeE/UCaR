import logging

from states import register_add_car_handlers, register_update_car_handlers
from keyboards.common import main_menu_keyboard

from aiogram import F, Dispatcher
from aiogram.types import CallbackQuery

logger = logging.getLogger(__name__)


async def cmd_get_cars(callback: CallbackQuery):
    """Получение списка машин пользователя"""
    await callback.message.delete()
    user_id = callback.message.from_user.id
    
    try:
        # cars = await get_cars(user_id)
        cars = [
            {'id': 1, 'brand': 'Toyota', 'model': 'Camry', 'last_service_date': '2023-12-01', 'production_year': 2018},
            {'id': 2, 'brand': 'Honda', 'model': 'Civic', 'last_service_date': '2024-01-15', 'production_year': 2020},
            {'id': 3, 'brand': 'Ford', 'model': 'Focus', 'last_service_date': '2023-11-20', 'production_year': 2017},
            {'id': 4, 'brand': 'Chevrolet', 'model': 'Malibu', 'last_service_date': '2024-02-10', 'production_year': 2019},
        ]

        if len(cars) == 0:
            await callback.message.answer("У вас пока нет машин. Используйте /add_car для добавления.")   
            return

        response_text = "Список ваших машин:\n\n"
        for idx, car in enumerate(cars, 1):
            response_text += f"Машина #{idx}:\n"
            response_text += f"Бренд: {car.get('brand')}\n"
            response_text += f"Модель: {car.get('model')}\n"
            response_text += f"Дата последнего ТО: {car.get('last_service_date')}\n"
            response_text += f"Год производства: {car.get('production_year')}\n\n"
                    
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
