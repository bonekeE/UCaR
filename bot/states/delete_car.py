import logging

from app import car_service
from keyboards import (
    car_inline_keyboard,
    main_menu_keyboard,
)

from aiogram import F, Dispatcher
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


logger = logging.getLogger(__name__)


class DeleteCarStates(StatesGroup):
    """Состояния для удаления машины"""
    car_id = State()


async def cmd_delete_car(callback: CallbackQuery, state: FSMContext):
    """Начало процесса удаления машины - запрос списка машин"""
    await callback.message.delete()
    user_id = callback.from_user.id

    try:
        cars = car_service.get_user_cars(user_id)

        if not cars or len(cars) == 0:
            await callback.message.answer(
                "У вас пока нет машин для удаления.\n"
                "Используйте /add_car для добавления машины."
            )
            await callback.message.answer(
                "Выберите действие:",
                reply_markup=main_menu_keyboard(),
            )
            await state.clear()
            return
        
        cars_for_keyboard = [
            {
                'id': car['car_id'],
                'brand': car['brand'],
                'model': car['model'],
                'last_service_date': car['last_service_time'],
                'production_year': car['year_of_manufacture'],
            }
            for car in cars
        ]
        
        await state.update_data(cars=cars_for_keyboard)
        await state.set_state(DeleteCarStates.car_id)
        
        await callback.message.answer(
            "Выберите машину для удаления:",
            reply_markup=car_inline_keyboard(cars_for_keyboard),
        )
        logger.info(f"User {user_id} requested car list for deletion, found {len(cars)} cars")
                
    except Exception as e:
        error_msg = f"❌ Неожиданная ошибка"
        logger.error(f"Unexpected error when getting cars for deletion for user {user_id}: {e}")
        await callback.message.answer(error_msg)
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard(),
        )
        await state.clear()


async def process_car_deletion(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора машины из списка и удаление"""
    await callback.message.delete()

    car_id = int(callback.data)
    if car_id == -1:
        await callback.message.answer(
            "Действие отменено",
        )
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard(),
        )
        await state.clear()
        return

    # Получение данных о машине из состояния
    data = await state.get_data()
    cars = data.get("cars", [])

    # Поиск выбранной машины
    selected_car = None
    for car in cars:
        if car.get('id') == car_id:
            selected_car = car
            break

    if not selected_car:
        await callback.answer("Машина не найдена", show_alert=True)
        await state.clear()
        return

    user_id = callback.from_user.id

    try:
        success = car_service.delete_user_car(
            user_id=user_id,
            car_id=car_id,
        )

        if success:
            car_info = f"{selected_car['brand']} {selected_car['model']} ({selected_car['production_year']})"
            await callback.message.answer(f"✅ Машина {car_info} успешно удалена!")
            logger.info(f"Car {car_id} deleted successfully for user {user_id}")
        else:
            await callback.message.answer("❌ Не удалось удалить машину. Проверьте правильность данных.")
            logger.warning(f"Failed to delete car {car_id} for user {user_id}")
        
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard(),
        )
    except Exception as e:
        error_msg = f"❌ Неожиданная ошибка"
        logger.error(f"Unexpected error when deleting car for user {user_id}: {e}")
        await callback.message.answer(error_msg)
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard(),
        )
    finally:
        await state.clear()


def register_delete_car_handlers(dp: Dispatcher):
    """Регистрация всех хендлеров для удаления машины"""

    dp.callback_query.register(
        cmd_delete_car,
        F.data == "delete_car",
    )
    dp.callback_query.register(
        process_car_deletion,
        DeleteCarStates.car_id,
    )
