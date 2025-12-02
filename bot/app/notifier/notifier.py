import asyncio
import logging
from datetime import datetime
from typing import Dict

from app import user_service, car_service

from aiogram import Bot


logger = logging.getLogger(__name__)


async def check_all_cars(bot: Bot):
    """Проверяет все автомобили и их расходные материалы, отправляет уведомления при необходимости."""
    users_cars = user_service.get_all_users()
    
    notifications_sent = 0
    for user in users_cars:
        user_id, cars = user["user_id"], user.get("cars", [])
        if not cars:
            continue
        
        logger.info(f"user_id: {user_id}, cars: {cars}")

        main_message = ["Уведомления по вашим автомобилям:"]
        for car in cars:
            car_id, car_brand, car_model, car_year_of_manufacture = car.get("car_id"), car.get("brand"), car.get("model"), car.get("year_of_manufacture")

            car_info = f"\t- Автомобиль: {car_brand} {car_model} {car_year_of_manufacture}"

            consumables = car_service.get_car_consumables_with_remaining(
                user_id, car_id,
            )

            consumable_message = []
            for consumable in consumables:
                if consumable["months_remaining"] <= 1:
                    message = get_notification_message(consumable)
                    consumable_message.append(message)

            if consumable_message:
                main_message.append(car_info)
                main_message.extend(consumable_message)

        if len(main_message) == 1:
            continue
        
        notifications_sent += 1

        message = "\n".join(main_message)

        if len(message) < 4096:
            await bot.send_message(user_id, message)
            continue    

        iterations = 0  
        while len(message) > 4096:
            message_part = message[:4096]
            index = 0
            if iterations > 0:
                index = message_part.rfind("- Автомобиль:")
                if index == -1:
                    index = message_part.rfind("- Требуется замена:")
            else:
                index = message_part.rfind("- Требуется замена:")
                
            message_send = message_part[:index]

            await bot.send_message(user_id, message_send.strip())
            message = message[index:]

            iterations += 1

        if len(message) > 0:
            await bot.send_message(user_id, message)

    if notifications_sent > 0:
        logger.info(f"Проверка завершена. Отправлено уведомлений: {notifications_sent}")
    else:
        logger.info(f"Проверка завершена. Уведомлений не требуется.")


def get_notification_message(consumable: Dict):
    """
    Отправляет уведомление пользователю о необходимости замены расходного материала.
    
    Args:
        user_id: Идентификатор пользователя (i64)
        user_name: Имя пользователя
        car: Словарь с информацией об автомобиле
        consumable: Словарь с информацией о расходном материале
    """
    consumable_name = consumable["consumable_name"]
    last_replacement = consumable["last_service_time"]
    lifetime = consumable["lifetime_months"]
    days_since = calculate_days_since_service(last_replacement)

    message = (
        f"\t\t- Требуется замена: {consumable_name}\n"
        f"\t\t  Последняя замена: {last_replacement}\n"
        f"\t\t  Срок службы: {lifetime} месяцев\n"
        f"\t\t  Прошло дней: {days_since}\n"
    )

    return message


def calculate_days_since_service(last_service_time: datetime) -> int:
    """
    Вычисляет количество дней с последнего обслуживания.
    
    Args:
        last_service_time: Дата последнего обслуживания (формат: YYYY-MM-DD)
    
    Returns:
        Количество дней с последнего обслуживания
    """
    delta = datetime.date(datetime.today()) - last_service_time
    return delta.days
