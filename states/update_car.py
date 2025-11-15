import logging
from datetime import datetime

from keyboards.common import car_inline_keyboard, main_menu_keyboard

from aiogram import F, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)


class UpdateCarStates(StatesGroup):
    """Состояния для обновления последнего ТО машины"""
    car_id = State()
    brand = State()
    model = State()
    last_service_date = State()
    production_year = State()


async def cmd_update_car(callback: CallbackQuery, state: FSMContext):
    """Начало процесса обновления машины - запрос списка машин с сервера"""
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

        if not cars or len(cars) == 0:
            await callback.message.answer(
                "У вас пока нет машин для обновления.\n"
                "Используйте /add_car для добавления машины."
            )
            await state.clear()
            return
        
        await state.update_data(cars=cars)
        await state.set_state(UpdateCarStates.car_id)
        
        await callback.message.answer(
            "Выберите машину для обновления:",
            reply_markup=car_inline_keyboard(cars),
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

    await callback.message.answer(f"Введенный бренд машины: {selected_car['brand']}. Введите новый бренд машины:")
    await state.set_state(UpdateCarStates.brand)


async def process_brand(message: Message, state: FSMContext):
    """Обработка бренда машины"""
    brand = message.text.strip()
    if not brand:
        await message.answer("Бренд не может быть пустым. Введите бренд машины:")
        return

    data = await state.get_data()
    data["updated_car"]["brand"] = brand
    
    model = data["updated_car"]["model"]
    
    await state.update_data(updated_car=data["updated_car"])
    await message.answer(f"Введенный бренд машины: {model}. Введите новую модель машины:")
    await state.set_state(UpdateCarStates.model)
    logger.info(f"User {message.from_user.id} entered brand: {brand}")


async def process_model(message: Message, state: FSMContext):
    """Обработка модели машины"""
    model = message.text.strip()
    if not model:
        await message.answer("Модель не может быть пустой. Введите модель машины:")
        return

    data = await state.get_data()
    data["updated_car"]["model"] = model
    
    last_service_date = data["updated_car"]["last_service_date"]
    
    await state.update_data(updated_car=data["updated_car"])
    await message.answer(
        f"Введенный бренд машины: {last_service_date}. "
        "Введите дату последнего ТО (формат: ДД.ММ.ГГГГ, например: 15.03.2024):"
    )
    await state.set_state(UpdateCarStates.last_service_date)
    logger.info(f"User {message.from_user.id} entered model: {model}")


async def process_last_service_date(message: Message, state: FSMContext):
    """Обработка даты последнего ТО"""
    date_str = message.text.strip()

    try:
        service_date = datetime.strptime(date_str, "%d.%m.%Y")
        last_service_date = service_date.strftime("%Y-%m-%d")
        
        data = await state.get_data()
        production_year = data["updated_car"]["production_year"]
        
        data["updated_car"]["last_service_date"] = last_service_date

        await state.update_data(updated_car=data["updated_car"])
        await message.answer(f"Введенный год производства машины: {production_year}. Введите год производства машины:")
        await state.set_state(UpdateCarStates.production_year)
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

        logger.info(f"User {message.from_user.id} entered service date: {year_str}")
    except ValueError:
        logger.error(f"User {message.from_user.id} entered service date: {year_str}")
        await message.answer("Год должен быть числом. Введите год производства:")
        return

    # Получение всех данных из состояния
    data = await state.get_data()
    car_data = {
        "user_id": message.from_user.id,
        "brand": data["updated_car"]["brand"],
        "model": data["updated_car"]["model"],
        "last_service_date": data["updated_car"]["last_service_date"],
        "production_year": year,
    }
    
    try:
        # await add_car(car_data)
        print(car_data)

        await message.answer("Машина успешно обновлена!")
        await message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard(),
        )
    except Exception as e:
        error_msg = f"❌ Неожиданная ошибка"
        logger.error(f"Unexpected error when adding car for user {message.from_user.id}: {e}")
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
    dp.message.register(process_brand, UpdateCarStates.brand)
    dp.message.register(process_model, UpdateCarStates.model)
    dp.message.register(process_last_service_date, UpdateCarStates.last_service_date)
    dp.message.register(process_production_year, UpdateCarStates.production_year)
