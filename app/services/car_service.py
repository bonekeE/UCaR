from typing import List, Dict, Optional
from app.db.database import Database
from main_logic.mistral import get_parts_lifetime


class CarService:
    """Сервис для работы с автомобилями."""
    
    def __init__(self, db: Database):
        """
        Инициализация сервиса.
        
        Args:
            db: Экземпляр класса Database для работы с БД
        """
        self.db = db
    
    def add_car(
        self,
        user_id: int,
        brand: str,
        model: str,
        year_of_manufacture: int,
        last_service_time: str
    ) -> int:
        """
        Добавляет автомобиль пользователю и автоматически добавляет расходные материалы.
        
        Args:
            user_id: Идентификатор пользователя
            brand: Марка автомобиля
            model: Модель автомобиля
            year_of_manufacture: Год выпуска
            last_service_time: Дата последнего ТО (формат: YYYY-MM-DD)
        
        Returns:
            car_id: Идентификатор созданного автомобиля
        """
        # Создаем автомобиль в БД (или получаем существующий)
        car_id = self.db.add_car(brand, model, year_of_manufacture)
        
        # Создаем связь пользователь-автомобиль
        self.db.add_user_car(user_id, car_id, last_service_time)
        
        # Получаем данные о расходных материалах от LLM
        car_name = f"{brand} {model} {year_of_manufacture}"
        try:
            parts_data = get_parts_lifetime(car_name)
            # Добавляем расходные материалы в БД
            self.db.add_consumables_from_llm_json(car_id, parts_data)
        except Exception as e:
            # Логируем ошибку, но не прерываем процесс добавления автомобиля
            print(f"Предупреждение: не удалось получить данные о расходных материалах для {car_name}: {e}")
            print("Автомобиль добавлен, но расходные материалы не были добавлены автоматически.")
        
        return car_id
    
    def get_user_cars(self, user_id: int) -> List[Dict]:
        """
        Получает список автомобилей пользователя.
        
        Args:
            user_id: Идентификатор пользователя
        
        Returns:
            Список словарей с информацией об автомобилях пользователя
        """
        return self.db.get_user_cars(user_id)
    
    def update_car_service_time(
        self,
        user_id: int,
        car_id: int,
        last_service_time: Optional[str] = None
    ) -> bool:
        """
        Обновляет дату последнего ТО для автомобиля пользователя.
        
        Args:
            user_id: Идентификатор пользователя
            car_id: Идентификатор автомобиля
            last_service_time: Новая дата ТО (если None, используется текущая дата)
        
        Returns:
            True если обновление успешно, False иначе
        """
        return self.db.update_user_car_service_time(
            user_id, car_id, last_service_time
        )
    
    def delete_user_car(self, user_id: int, car_id: int) -> bool:
        """
        Удаляет автомобиль у пользователя.
        
        Args:
            user_id: Идентификатор пользователя
            car_id: Идентификатор автомобиля
        
        Returns:
            True если удаление успешно, False иначе
        """
        return self.db.delete_user_car(user_id, car_id)
    
    def get_car_consumables_with_remaining(
        self,
        user_id: int,
        car_id: int
    ) -> List[Dict]:
        """
        Получает расходные материалы автомобиля с расчетом остатка ресурса.
        
        Args:
            user_id: Идентификатор пользователя
            car_id: Идентификатор автомобиля
        
        Returns:
            Список словарей с информацией о расходных материалах и остатке ресурса
        """
        return self.db.get_car_consumables_with_remaining(user_id, car_id)

