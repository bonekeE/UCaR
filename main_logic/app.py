"""
Основной модуль приложения для отслеживания состояния автомобилей.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from database import Database
from mistral import get_parts_lifetime


class CarTrackerApp:
    """Основной класс приложения для отслеживания автомобилей."""
    
    def __init__(self, db_file: str = "cars_db.json"):
        """
        Инициализация приложения.
        
        Args:
            db_file: Путь к файлу базы данных
        """
        self.db = Database(db_file)
    
    def add_user(self, user_name: str, user_id: int):
        """
        Добавляет пользователя в систему.
        
        Args:
            user_name: Имя пользователя
            user_id: Уникальный идентификатор пользователя (i64)
        """
        self.db.add_user_to_db(user_name, user_id)
    
    def add_car(self, user_id: int, brand: str, model: str, 
                last_service_time: str, year_of_manufacture: int) -> int:
        """
        Добавляет автомобиль пользователю и автоматически добавляет расходные материалы
        на основе данных автомобиля.
        
        Args:
            user_id: Идентификатор пользователя (i64)
            brand: Марка автомобиля
            model: Модель автомобиля
            last_service_time: Дата последнего обслуживания (формат: YYYY-MM-DD)
            year_of_manufacture: Год выпуска
        
        Returns:
            car_id: Уникальный идентификатор автомобиля (i64)
        """
        # Добавляем автомобиль в базу данных
        car_id = self.db.add_car_to_db(
            user_id, brand, model, last_service_time, year_of_manufacture
        )
        
        # Формируем название автомобиля для запроса к Mistral API
        car_name = f"{brand} {model} {year_of_manufacture}"
        
        try:
            # Получаем данные о сроке службы деталей
            parts_data = get_parts_lifetime(car_name)
            
            # Извлекаем словарь с деталями и их сроком службы в месяцах
            parts_lifetime = parts_data.get("parts_lifetime", {})
            
            # Добавляем каждую деталь как расходный материал
            # Конвертируем месяцы в дни (приблизительно 30 дней в месяце)
            for part_name, lifetime_months in parts_lifetime.items():
                if isinstance(lifetime_months, (int, float)) and lifetime_months > 0:
                    lifetime_days = int(lifetime_months * 30)  # Конвертируем месяцы в дни
                    try:
                        self.db.add_consumable_to_db(car_id, part_name, lifetime_days)
                    except Exception as e:
                        # Логируем ошибку, но продолжаем добавлять остальные детали
                        print(f"Ошибка при добавлении детали '{part_name}': {e}")
        except Exception as e:
            # Если не удалось получить данные о деталях, продолжаем без них
            print(f"Предупреждение: не удалось получить данные о расходных материалах для {car_name}: {e}")
            print("Автомобиль добавлен, но расходные материалы не были добавлены автоматически.")
        
        return car_id
    
    def get_cars(self, user_id: int) -> List[Dict]:
        """
        Получает список автомобилей пользователя.
        
        Args:
            user_id: Идентификатор пользователя (i64)
        
        Returns:
            Список словарей с информацией об автомобилях
        """
        return self.db.get_cars_from_db(user_id)
    
    def update_car(self, user_id: int, car_id: int) -> bool:
        """
        Обновляет дату последнего обслуживания автомобиля.
        
        Args:
            user_id: Идентификатор пользователя (i64)
            car_id: Идентификатор автомобиля (i64)
        
        Returns:
            True если обновление успешно, False в противном случае
        """
        return self.db.update_car_in_db(user_id, car_id)

