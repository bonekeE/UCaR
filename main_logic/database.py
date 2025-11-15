"""
Модуль для работы с базой данных автомобилей и пользователей.
"""
from datetime import datetime
from typing import List, Dict, Optional
import json
import os


class Database:
    """Класс для работы с базой данных."""
    
    def __init__(self, db_file: str = "cars_db.json"):
        """
        Инициализация базы данных.
        
        Args:
            db_file: Путь к файлу базы данных (JSON)
        """
        self.db_file = db_file
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Создает файл базы данных, если его нет."""
        if not os.path.exists(self.db_file):
            self._write_db({"users": {}, "cars": {}, "consumables": {}})
    
    def _read_db(self) -> Dict:
        """Читает данные из базы данных."""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"users": {}, "cars": {}, "consumables": {}}
    
    def _write_db(self, data: Dict):
        """Записывает данные в базу данных."""
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_user_to_db(self, user_name: str, user_id: int):
        """
        Добавляет пользователя в базу данных.
        
        Args:
            user_name: Имя пользователя
            user_id: Уникальный идентификатор пользователя (i64)
        """
        db = self._read_db()
        # В JSON ключи словарей должны быть строками
        db["users"][str(user_id)] = {
            "user_name": user_name,
            "user_id": user_id
        }
        self._write_db(db)
    
    def add_car_to_db(self, user_id: int, brand: str, model: str, 
                     last_service_time: str, year_of_manufacture: int) -> int:
        """
        Добавляет автомобиль в базу данных.
        
        Args:
            user_id: Идентификатор пользователя (i64)
            brand: Марка автомобиля
            model: Модель автомобиля
            last_service_time: Дата последнего обслуживания (формат: YYYY-MM-DD)
            year_of_manufacture: Год выпуска
        
        Returns:
            car_id: Уникальный идентификатор автомобиля (i64)
        """
        db = self._read_db()
        
        # Генерируем car_id как число
        if "cars" not in db:
            db["cars"] = {}
        
        # Генерируем уникальный car_id на основе количества существующих машин
        car_id = len(db["cars"]) + 1
        
        # В JSON ключи словарей должны быть строками
        db["cars"][str(car_id)] = {
            "car_id": car_id,
            "user_id": user_id,
            "brand": brand,
            "model": model,
            "last_service_time": last_service_time,
            "year_of_manufacture": year_of_manufacture
        }
        
        self._write_db(db)
        return car_id
    
    def get_cars_from_db(self, user_id: int) -> List[Dict]:
        """
        Получает список автомобилей пользователя.
        
        Args:
            user_id: Идентификатор пользователя (i64)
        
        Returns:
            Список словарей с информацией об автомобилях
        """
        db = self._read_db()
        cars = []
        
        if "cars" in db:
            for car_id_key, car_data in db["cars"].items():
                # Конвертируем user_id из JSON в int для сравнения
                car_user_id = car_data.get("user_id")
                if isinstance(car_user_id, str):
                    car_user_id = int(car_user_id)
                if car_user_id == user_id:
                    car_copy = car_data.copy()
                    # Убеждаемся, что car_id является int
                    if isinstance(car_copy.get("car_id"), str):
                        car_copy["car_id"] = int(car_copy["car_id"])
                    cars.append(car_copy)
        
        return cars
    
    def update_car_in_db(self, user_id: int, car_id: int):
        """
        Обновляет дату последнего обслуживания автомобиля.
        При обновлении также обновляется дата замены всех расходных материалов автомобиля.
        
        Args:
            user_id: Идентификатор пользователя (i64)
            car_id: Идентификатор автомобиля (i64)
        """
        db = self._read_db()
        
        # В JSON ключи словарей должны быть строками
        car_id_str = str(car_id)
        if "cars" in db and car_id_str in db["cars"]:
            car = db["cars"][car_id_str]
            # Конвертируем user_id из JSON в int для сравнения
            car_user_id = car.get("user_id")
            if isinstance(car_user_id, str):
                car_user_id = int(car_user_id)
            if car_user_id == user_id:
                # Обновляем дату последнего обслуживания на текущую
                current_date = datetime.now().strftime("%Y-%m-%d")
                car["last_service_time"] = current_date
                
                # Обновляем дату замены всех расходных материалов этого автомобиля
                if "consumables" in db:
                    for consumable_id, consumable_data in db["consumables"].items():
                        consumable_car_id = consumable_data.get("car_id")
                        # Конвертируем car_id из JSON в int для сравнения
                        if isinstance(consumable_car_id, str):
                            consumable_car_id = int(consumable_car_id)
                        if consumable_car_id == car_id:
                            consumable_data["last_replacement_date"] = current_date
                
                self._write_db(db)
                return True
        
        return False
    
    def get_all_cars(self) -> List[Dict]:
        """
        Получает все автомобили из базы данных.
        
        Returns:
            Список всех автомобилей
        """
        db = self._read_db()
        cars = []
        
        if "cars" in db:
            for car_data in db["cars"].values():
                car_copy = car_data.copy()
                # Убеждаемся, что user_id является int
                if isinstance(car_copy.get("user_id"), str):
                    car_copy["user_id"] = int(car_copy["user_id"])
                # Убеждаемся, что car_id является int
                if isinstance(car_copy.get("car_id"), str):
                    car_copy["car_id"] = int(car_copy["car_id"])
                cars.append(car_copy)
        
        return cars
    
    def get_all_users(self) -> List[Dict]:
        """
        Получает всех пользователей из базы данных.
        
        Returns:
            Список всех пользователей
        """
        db = self._read_db()
        users = []
        
        if "users" in db:
            for user_data in db["users"].values():
                # Убеждаемся, что user_id является int
                user_copy = user_data.copy()
                if isinstance(user_copy.get("user_id"), str):
                    user_copy["user_id"] = int(user_copy["user_id"])
                users.append(user_copy)
        
        return users
    
    def add_consumable_to_db(self, car_id: int, consumable_name: str, lifetime: int) -> str:
        """
        Добавляет расходный материал (деталь) к автомобилю.
        
        Args:
            car_id: Идентификатор автомобиля (i64)
            consumable_name: Название расходного материала (например, "Масло двигателя", "Тормозные колодки")
            lifetime: Срок службы в днях
        
        Returns:
            consumable_id: Уникальный идентификатор расходного материала
        """
        db = self._read_db()
        
        # В JSON ключи словарей должны быть строками
        car_id_str = str(car_id)
        
        # Проверяем, существует ли автомобиль
        if "cars" not in db or car_id_str not in db["cars"]:
            raise ValueError(f"Автомобиль с ID {car_id} не найден")
        
        # Инициализируем секцию consumables, если её нет
        if "consumables" not in db:
            db["consumables"] = {}
        
        # Генерируем consumable_id
        consumable_id = f"{car_id}_{consumable_name}_{len(db['consumables'])}"
        
        # Получаем дату последнего обслуживания автомобиля
        car = db["cars"][car_id_str]
        last_service_time = car.get("last_service_time", datetime.now().strftime("%Y-%m-%d"))
        
        db["consumables"][consumable_id] = {
            "consumable_id": consumable_id,
            "car_id": car_id,
            "consumable_name": consumable_name,
            "lifetime": lifetime,
            "last_replacement_date": last_service_time
        }
        
        self._write_db(db)
        return consumable_id
    
    def get_all_car_consumables(self, car_id: int) -> List[Dict]:
        """
        Получает все расходные материалы для автомобиля.
        
        Args:
            car_id: Идентификатор автомобиля (i64)
        
        Returns:
            Список словарей с информацией о расходных материалах
        """
        db = self._read_db()
        consumables = []
        
        if "consumables" in db:
            for consumable_id, consumable_data in db["consumables"].items():
                consumable_car_id = consumable_data.get("car_id")
                # Конвертируем car_id из JSON в int для сравнения
                if isinstance(consumable_car_id, str):
                    consumable_car_id = int(consumable_car_id)
                if consumable_car_id == car_id:
                    consumables.append(consumable_data.copy())
        
        return consumables

