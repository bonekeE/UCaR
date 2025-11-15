"""
Модуль для фоновых уведомлений о необходимости обслуживания автомобилей.
"""
from datetime import datetime, timedelta
from typing import List, Dict
import threading
import time
from database import Database


class Notifier:
    """Класс для фоновой проверки и уведомлений о необходимости обслуживания."""
    
    # Интервал между обслуживаниями (в днях)
    SERVICE_INTERVAL_DAYS = 180  # 6 месяцев
    
    def __init__(self, db_file: str = "cars_db.json", check_interval_minutes: int = 10):
        """
        Инициализация уведомителя.
        
        Args:
            db_file: Путь к файлу базы данных
            check_interval_minutes: Интервал проверки в минутах (по умолчанию 10)
        """
        self.db = Database(db_file)
        self.check_interval = check_interval_minutes * 60  # Конвертируем в секунды
        self.running = False
        self.thread = None
    
    def _calculate_days_since_service(self, last_service_time: str) -> int:
        """
        Вычисляет количество дней с последнего обслуживания.
        
        Args:
            last_service_time: Дата последнего обслуживания (формат: YYYY-MM-DD)
        
        Returns:
            Количество дней с последнего обслуживания
        """
        try:
            service_date = datetime.strptime(last_service_time, "%Y-%m-%d")
            delta = datetime.now() - service_date
            return delta.days
        except ValueError:
            # Если формат даты некорректный, считаем что обслуживание давно
            return self.SERVICE_INTERVAL_DAYS + 1
    
    def _check_consumable_needs_replacement(self, consumable: Dict) -> bool:
        """
        Проверяет, нужно ли заменять расходный материал.
        
        Args:
            consumable: Словарь с информацией о расходном материале
        
        Returns:
            True если нужна замена, False в противном случае
        """
        last_replacement = consumable.get("last_replacement_date")
        if not last_replacement:
            return True
        
        lifetime = consumable.get("lifetime", 0)
        if lifetime <= 0:
            return False
        
        days_since_replacement = self._calculate_days_since_service(last_replacement)
        return days_since_replacement >= lifetime
    
    def _send_notification(self, user_id: int, user_name: str, car: Dict, consumable: Dict):
        """
        Отправляет уведомление пользователю о необходимости замены расходного материала.
        
        Args:
            user_id: Идентификатор пользователя (i64)
            user_name: Имя пользователя
            car: Словарь с информацией об автомобиле
            consumable: Словарь с информацией о расходном материале
        """
        brand = car.get("brand", "Unknown")
        model = car.get("model", "Unknown")
        consumable_name = consumable.get("consumable_name", "Unknown")
        last_replacement = consumable.get("last_replacement_date", "Unknown")
        lifetime = consumable.get("lifetime", 0)
        days_since = self._calculate_days_since_service(last_replacement)
        
        message = (
            f"Уведомление для {user_name} (ID: {user_id}):\n"
            f"Автомобиль: {brand} {model}\n"
            f"Требуется замена: {consumable_name}\n"
            f"Последняя замена: {last_replacement}\n"
            f"Срок службы: {lifetime} дней\n"
            f"Прошло дней: {days_since}\n"
            f"Рекомендуется заменить деталь.\n"
        )
        
        print(f"[NOTIFICATION] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(message)
        print("-" * 50)
    
    def _check_all_cars(self):
        """Проверяет все автомобили и их расходные материалы, отправляет уведомления при необходимости."""
        users = self.db.get_all_users()
        cars = self.db.get_all_cars()
        
        # Создаем словарь пользователей для быстрого доступа
        users_dict = {user["user_id"]: user for user in users}
        
        notifications_sent = 0
        
        for car in cars:
            car_id = car.get("car_id")
            # Убеждаемся, что car_id является int
            if isinstance(car_id, str):
                car_id = int(car_id)
            
            user_id = car.get("user_id")
            user = users_dict.get(user_id)
            
            if not user:
                continue
            
            user_name = user.get("user_name", "Unknown")
            
            # Получаем все расходные материалы для этого автомобиля
            consumables = self.db.get_all_car_consumables(car_id)
            
            # Проверяем каждую деталь отдельно
            for consumable in consumables:
                if self._check_consumable_needs_replacement(consumable):
                    self._send_notification(user_id, user_name, car, consumable)
                    notifications_sent += 1
        
        if notifications_sent > 0:
            print(f"Отправлено уведомлений: {notifications_sent}\n")
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Проверка завершена. Уведомлений не требуется.\n")
    
    def _run_loop(self):
        """Основной цикл проверки (работает в фоновом потоке)."""
        print(f"Notifier запущен. Проверка каждые {self.check_interval // 60} минут.")
        print(f"Проверка расходных материалов по их индивидуальному сроку службы.\n")
        
        while self.running:
            try:
                self._check_all_cars()
            except Exception as e:
                print(f"Ошибка при проверке автомобилей: {e}\n")
            
            # Ждем указанный интервал
            time.sleep(self.check_interval)
    
    def start(self):
        """Запускает фоновый процесс проверки."""
        if self.running:
            print("Notifier уже запущен.")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("Notifier запущен в фоновом режиме.")
    
    def stop(self):
        """Останавливает фоновый процесс проверки."""
        if not self.running:
            print("Notifier не запущен.")
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("Notifier остановлен.")
    
    def check_now(self):
        """Выполняет немедленную проверку всех автомобилей."""
        print("Выполняется немедленная проверка...\n")
        self._check_all_cars()

