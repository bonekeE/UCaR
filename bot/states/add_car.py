import logging
from datetime import datetime

from app import car_service
from keyboards.common import main_menu_keyboard

from aiogram import F, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)


class AddCarStates(StatesGroup):
    """Состояния для добавления машины"""
    brand = State()
    model = State()
    last_service_date = State()
    production_year = State()


async def cmd_add_car_callback(callback: CallbackQuery, state: FSMContext):
    """Начало процесса добавления машины"""
    await callback.message.delete()

    await callback.message.answer("Давайте добавим новую машину!")
    await callback.message.answer("Введите бренд машины:")
    await state.set_state(AddCarStates.brand)
    logger.info(f"User {callback.message.from_user.id} started adding a car")


async def cmd_add_car(message: Message, state: FSMContext):
    """Начало процесса добавления машины"""
    await message.delete()

    await message.answer("Давайте добавим новую машину!")
    await message.answer("Введите бренд машины:")
    await state.set_state(AddCarStates.brand)
    logger.info(f"User {message.from_user.id} started adding a car")


async def process_brand(message: Message, state: FSMContext):
    """Обработка бренда машины"""
    brand = message.text.strip()
    if not brand:
        await message.answer("Бренд не может быть пустым. Введите бренд машины:")
        return

    await state.update_data(brand=brand)
    await message.answer("Введите модель машины:")
    await state.set_state(AddCarStates.model)
    logger.info(f"User {message.from_user.id} entered brand: {brand}")


async def process_model(message: Message, state: FSMContext):
    """Обработка модели машины"""
    model = message.text.strip()
    if not model:
        await message.answer("Модель не может быть пустой. Введите модель машины:")
        return

    await state.update_data(model=model)
    await message.answer(
        "Введите дату последнего ТО (формат: ДД.ММ.ГГГГ, например: 15.03.2024):"
    )
    await state.set_state(AddCarStates.last_service_date)
    logger.info(f"User {message.from_user.id} entered model: {model}")


async def process_last_service_date(message: Message, state: FSMContext):
    """Обработка даты последнего ТО"""
    date_str = message.text.strip()

    try:
        service_date = datetime.strptime(date_str, "%d.%m.%Y")
        await state.update_data(last_service_date=service_date.strftime("%Y-%m-%d"))
        await message.answer("Введите год производства машины:")
        await state.set_state(AddCarStates.production_year)
        logger.info(f"User {message.from_user.id} entered service date: {date_str}")
    except ValueError:
        logger.error(f"User {message.from_user.id} entered service date: {date_str}")
        await message.answer(
            "Неверный формат даты. Используйте формат ДД.ММ.ГГГГ (например: 15.03.2024):"
        )


async def process_production_year(message: Message, state: FSMContext):
    """Обработка года производства и отправка данных на сервер"""
    year_str = message.text.strip()

    try:
        year = int(year_str)
        current_year = datetime.now().year
        if year < 1900 or year > current_year:
            await message.answer(
                f"Год должен быть между 1900 и {current_year}. Введите год производства:"
            )
            return

        logger.info(f"User {message.from_user.id} entered production year: {year_str}")
    except ValueError:
        logger.error(f"User {message.from_user.id} entered invalid production year: {year_str}")
        await message.answer("Год должен быть числом. Введите год производства:")
        return

    # Получение всех данных из состояния
    data = await state.get_data()
    user_id = message.from_user.id
    
    try:
        car_id = car_service.add_car(
            user_id=user_id,
            brand=data["brand"],
            model=data["model"],
            year_of_manufacture=year,
            last_service_time=data["last_service_date"],
        )

        await message.answer("Машина успешно добавлена!")
        await message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard(),
        )
        logger.info(f"Car {car_id} added successfully for user {user_id}")
    except Exception as e:
        error_msg = f"❌ Неожиданная ошибка"
        logger.error(f"Unexpected error when adding car for user {user_id}: {e}")
        await message.answer(error_msg)
    finally:
        await state.clear()


def register_add_car_handlers(dp: Dispatcher):
    """Регистрация всех хендлеров для добавления машины"""

    dp.callback_query.register(
        cmd_add_car_callback,
        F.data == "add_car",
    )
    dp.message.register(
        cmd_add_car,
        Command("add_car"),
    )
    dp.message.register(
        process_brand, 
        AddCarStates.brand
    )
    dp.message.register(
        process_model, 
        AddCarStates.model
    )
    dp.message.register(
        process_last_service_date, 
        AddCarStates.last_service_date
    )
    dp.message.register(
        process_production_year,
        AddCarStates.production_year
    )
