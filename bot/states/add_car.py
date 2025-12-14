import logging
from datetime import datetime

from app import car_service
from app.ai import CarNotFoundError
from keyboards import main_menu_keyboard, select_cancel

from aiogram import F, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)


class AddCarStates(StatesGroup):
    """Состояния для добавления машины"""
    brand = State()
    model = State()
    production_year = State()
    last_service_date = State()


async def cmd_add_car_callback(callback: CallbackQuery, state: FSMContext):
    """Начало процесса добавления машины"""
    await callback.message.delete()

    await callback.message.answer("Давайте добавим новую машину!")
    await callback.message.answer("Введите бренд машины:", reply_markup=select_cancel())
    await state.set_state(AddCarStates.brand)
    logger.info(f"User {callback.message.from_user.id} started adding a car")


async def cmd_add_car(message: Message, state: FSMContext):
    """Начало процесса добавления машины"""
    await message.delete()

    await message.answer("Давайте добавим новую машину!")
    await message.answer("Введите бренд машины:", reply_markup=select_cancel())
    await state.set_state(AddCarStates.brand)
    logger.info(f"User {message.from_user.id} started adding a car")


async def process_brand(message: Message, state: FSMContext):
    """Обработка бренда машины"""
    brand = message.text.strip()
    if brand.lower() == "cancel":
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
    
    if not brand:
        await message.answer("Бренд не может быть пустым. Введите бренд машины:")
        return

    await state.update_data(brand=brand)
    await message.answer("Введите модель машины:", reply_markup=select_cancel())
    await state.set_state(AddCarStates.model)
    logger.info(f"User {message.from_user.id} entered brand: {brand}")


async def process_model(message: Message, state: FSMContext):
    """Обработка модели машины"""
    model = message.text.strip()
    if model.lower() == "cancel":
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
    
    if not model:
        await message.answer(
            "Модель не может быть пустой. Введите модель машины:",
            reply_markup=select_cancel(),
        )
        return

    await state.update_data(model=model)
    await message.answer(
        "Введите год производства машины:",
        reply_markup=select_cancel(),
    )

    await state.set_state(AddCarStates.production_year)
    logger.info(f"User {message.from_user.id} entered model: {model}")


async def process_production_year(message: Message, state: FSMContext):
    """Обработка года производства"""
    year_str = message.text.strip()
    
    if year_str.lower() == "cancel":
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
        year = int(year_str)
        current_year = datetime.now().year
        if year < 1900 or year > current_year:
            await message.answer(
                f"Год должен быть между 1900 и {current_year}. Введите год производства:",
                reply_markup=select_cancel(),
            )
            return

        logger.info(f"User {message.from_user.id} entered production year: {year_str}")
        await state.update_data(production_year=year)
        await state.set_state(AddCarStates.last_service_date)
        await message.answer(
            "Введите дату последнего ТО (формат: ДД.ММ.ГГГГ, например: 15.03.2024):",
            reply_markup=select_cancel(),
        )
    except ValueError:
        logger.error(f"User {message.from_user.id} entered invalid production year: {year_str}")
        await message.answer("Год должен быть числом. Введите год производства:", reply_markup=select_cancel())


async def process_last_service_date(message: Message, state: FSMContext):
    """Обработка даты последнего ТО и отправка данных на сервер"""
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
        await state.update_data(last_service_date=service_date.strftime("%Y-%m-%d"))
        logger.info(f"User {message.from_user.id} entered service date: {date_str}")
    except ValueError:
        logger.error(f"User {message.from_user.id} entered service date: {date_str}")
        await message.answer(
            "Неверный формат даты. Используйте формат ДД.ММ.ГГГГ (например: 15.03.2024):",
            reply_markup=select_cancel(),
        )
        return

    data = await state.get_data()
    user_id = message.from_user.id
    
    try:
        car_id = car_service.add_car(
            user_id=user_id,
            brand=data["brand"],
            model=data["model"],
            year_of_manufacture=data["production_year"],
            last_service_time=data["last_service_date"],
        )

        await message.answer("✅ Машина успешно добавлена!")
        await message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard(),
        )
        logger.info(f"Car {car_id} added successfully for user {user_id}")
    except CarNotFoundError as e:
        # Специальная обработка случая, когда машина не найдена
        error_msg = f"❌ Расходные материалы не были загружены автоматически."
        logger.warning(f"Car not found by LLM for user {user_id}: {e.brand} {e.model} ({e.year_of_manufacture}) - {e}")
        await message.answer(error_msg)
        await message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard(),
        )
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
        process_production_year, 
        AddCarStates.production_year
    )
    dp.message.register(
        process_last_service_date,
        AddCarStates.last_service_date
    )
