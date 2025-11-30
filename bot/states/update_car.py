import logging
from datetime import datetime

from app import car_service
from keyboards import (
    car_inline_keyboard,
    main_menu_keyboard,
    select_cancel,
)

from aiogram import F, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove


logger = logging.getLogger(__name__)


class UpdateCarStates(StatesGroup):
    """Состояния для обновления последнего ТО машины"""
    car_id = State()
    last_service_date = State()


async def cmd_update_car(callback: CallbackQuery, state: FSMContext):
    """Начало процесса обновления машины - запрос списка машин с сервера"""
    await callback.message.delete()
    user_id = callback.from_user.id

    try:
        cars = car_service.get_user_cars(user_id)

        if not cars or len(cars) == 0:
            await callback.message.answer(
                "У вас пока нет машин для обновления.\n"
                "Используйте /add_car для добавления машины."
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
        await state.set_state(UpdateCarStates.car_id)
        
        await callback.message.answer(
            "Выберите машину для обновления:",
            reply_markup=car_inline_keyboard(cars_for_keyboard),
        )
        logger.info(f"User {user_id} requested car list for update, found {len(cars)} cars")
                
    except Exception as e:
        error_msg = f"❌ Неожиданная ошибка"
        logger.error(f"Unexpected error when getting cars for update for user {user_id}: {e}")
        await callback.message.answer(error_msg)
        await state.clear()


async def process_car_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора машины из списка и отправка запроса на обновление на сервер"""
    await callback.message.delete()

    car_id = int(callback.data)
    if car_id == -1:
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard(),
        )
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

    await state.update_data(updated_car=selected_car)

    await callback.message.answer(
        "Введите новую дату последнего ТО (формат: ДД.ММ.ГГГГ, например: 15.03.2024):",
        reply_markup=select_cancel(),
    )
    await state.set_state(UpdateCarStates.last_service_date)


async def process_last_service_date(message: Message, state: FSMContext):
    """Обработка даты последнего ТО"""
    date_str = message.text.strip()
    
    if date_str.lower() == "cancel":
        await message.answer(
            "Действие отменено",
            reply_markup=ReplyKeyboardRemove(),
        )

        await state.clear()
        await message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard(),
        )
        return

    try:
        service_date = datetime.strptime(date_str, "%d.%m.%Y")
        last_service_date = service_date.strftime("%Y-%m-%d")
        
        data = await state.get_data()
        data["updated_car"]["last_service_date"] = last_service_date

        await state.update_data(updated_car=data["updated_car"])
        logger.info(f"User {message.from_user.id} entered service date: {date_str}")
    except ValueError:
        logger.error(f"User {message.from_user.id} entered service date: {date_str}")
        await message.answer(
            "Неверный формат даты. Используйте формат ДД.ММ.ГГГГ (например: 15.03.2024):",
            reply_markup=select_cancel(),
        )

        return

    data = await state.get_data()
    updated_car = data["updated_car"]
    car_id = updated_car.get('id')
    user_id = message.from_user.id

    try:
        success = car_service.update_car_service_time(
            user_id=user_id,
            car_id=car_id,
            last_service_time=updated_car["last_service_date"],
        )

        if success:
            await message.answer("Машина успешно обновлена!")
        else:
            await message.answer("❌ Не удалось обновить машину. Проверьте правильность данных.")
        
        await message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard(),
        )
        logger.info(f"Car {car_id} updated successfully for user {user_id}")
    except Exception as e:
        error_msg = f"❌ Неожиданная ошибка"
        logger.error(f"Unexpected error when updating car for user {user_id}: {e}")
        await message.answer(error_msg)
    finally:
        await state.clear()


def register_update_car_handlers(dp: Dispatcher):
    """Регистрация всех хендлеров для обновления машины"""

    dp.callback_query.register(
        cmd_update_car,
        F.data == "update_car",
    )
    dp.callback_query.register(
        process_car_selection,
        UpdateCarStates.car_id,
    )
    dp.message.register(
        process_last_service_date,
        UpdateCarStates.last_service_date,
    )
