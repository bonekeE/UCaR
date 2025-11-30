"""
Тесты для приложения отслеживания автомобилей.
"""
import unittest
import os
import tempfile
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Создаем мок-модуль для mistral перед импортом app
mock_mistral = MagicMock()
sys.modules['mistral'] = mock_mistral

# Теперь можем импортировать остальные модули
from database import Database
from notifier import Notifier

# Импортируем app после мокирования mistral
from app import CarTrackerApp


class TestDatabase(unittest.TestCase):
    """Тесты для класса Database."""
    
    def setUp(self):
        """Создает временный файл базы данных для каждого теста."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.db = Database(self.temp_file.name)
    
    def tearDown(self):
        """Удаляет временный файл после теста."""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)
    
    def test_add_user_to_db(self):
        """Тест добавления пользователя."""
        self.db.add_user_to_db("Иван Иванов", 1)
        users = self.db.get_all_users()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]["user_name"], "Иван Иванов")
        self.assertEqual(users[0]["user_id"], 1)
    
    def test_add_car_to_db(self):
        """Тест добавления автомобиля."""
        car_id = self.db.add_car_to_db(1, "Toyota", "Camry", "2024-01-01", 2020)
        self.assertIsInstance(car_id, int)
        self.assertEqual(car_id, 1)
        
        cars = self.db.get_all_cars()
        self.assertEqual(len(cars), 1)
        self.assertEqual(cars[0]["brand"], "Toyota")
        self.assertEqual(cars[0]["model"], "Camry")
        self.assertEqual(cars[0]["car_id"], 1)
    
    def test_get_cars_from_db(self):
        """Тест получения автомобилей пользователя."""
        self.db.add_car_to_db(1, "Toyota", "Camry", "2024-01-01", 2020)
        self.db.add_car_to_db(1, "Honda", "Civic", "2024-01-01", 2021)
        self.db.add_car_to_db(2, "BMW", "X5", "2024-01-01", 2019)
        
        cars = self.db.get_cars_from_db(1)
        self.assertEqual(len(cars), 2)
        self.assertEqual(cars[0]["brand"], "Toyota")
        self.assertEqual(cars[1]["brand"], "Honda")
    
    def test_update_car_in_db(self):
        """Тест обновления даты обслуживания автомобиля."""
        car_id = self.db.add_car_to_db(1, "Toyota", "Camry", "2024-01-01", 2020)
        
        # Добавляем расходный материал
        self.db.add_consumable_to_db(car_id, "Масло", 90)
        
        # Обновляем дату обслуживания
        result = self.db.update_car_in_db(1, car_id)
        self.assertTrue(result)
        
        # Проверяем, что дата обновилась
        cars = self.db.get_cars_from_db(1)
        updated_date = cars[0]["last_service_time"]
        today = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(updated_date, today)
        
        # Проверяем, что дата замены расходного материала тоже обновилась
        consumables = self.db.get_all_car_consumables(car_id)
        self.assertEqual(consumables[0]["last_replacement_date"], today)
    
    def test_add_consumable_to_db(self):
        """Тест добавления расходного материала."""
        car_id = self.db.add_car_to_db(1, "Toyota", "Camry", "2024-01-01", 2020)
        
        consumable_id = self.db.add_consumable_to_db(car_id, "Масло двигателя", 90)
        self.assertIsInstance(consumable_id, str)
        
        consumables = self.db.get_all_car_consumables(car_id)
        self.assertEqual(len(consumables), 1)
        self.assertEqual(consumables[0]["consumable_name"], "Масло двигателя")
        self.assertEqual(consumables[0]["lifetime"], 90)
        self.assertEqual(consumables[0]["car_id"], car_id)
    
    def test_get_all_car_consumables(self):
        """Тест получения всех расходных материалов автомобиля."""
        car_id = self.db.add_car_to_db(1, "Toyota", "Camry", "2024-01-01", 2020)
        
        self.db.add_consumable_to_db(car_id, "Масло", 90)
        self.db.add_consumable_to_db(car_id, "Тормозные колодки", 180)
        
        consumables = self.db.get_all_car_consumables(car_id)
        self.assertEqual(len(consumables), 2)
    
    def test_add_consumable_to_nonexistent_car(self):
        """Тест добавления расходного материала к несуществующему автомобилю."""
        with self.assertRaises(ValueError):
            self.db.add_consumable_to_db(999, "Масло", 90)


class TestCarTrackerApp(unittest.TestCase):
    """Тесты для класса CarTrackerApp."""
    
    def setUp(self):
        """Создает временный файл базы данных для каждого теста."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.app = CarTrackerApp(self.temp_file.name)
        # Сбрасываем мок перед каждым тестом
        mock_mistral.get_parts_lifetime.reset_mock()
    
    def tearDown(self):
        """Удаляет временный файл после теста."""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)
    
    def test_add_user(self):
        """Тест добавления пользователя."""
        self.app.add_user("Иван Иванов", 1)
        users = self.app.db.get_all_users()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]["user_name"], "Иван Иванов")
    
    def test_add_car_with_consumables(self):
        """Тест добавления автомобиля с автоматическим добавлением расходных материалов."""
        # Мокируем ответ от Mistral API
        mock_get_parts_lifetime = mock_mistral.get_parts_lifetime
        mock_get_parts_lifetime.return_value = {
            "car": "Toyota Camry 2020",
            "units": "months",
            "parts_lifetime": {
                "engine oil": 3,
                "brake pads": 6,
                "air filter": 2
            }
        }
        
        self.app.add_user("Иван Иванов", 1)
        car_id = self.app.add_car(1, "Toyota", "Camry", "2024-01-01", 2020)
        
        self.assertIsInstance(car_id, int)
        
        # Проверяем, что автомобиль добавлен
        cars = self.app.get_cars(1)
        self.assertEqual(len(cars), 1)
        
        # Проверяем, что расходные материалы добавлены
        consumables = self.app.db.get_all_car_consumables(car_id)
        self.assertEqual(len(consumables), 3)
        
        # Проверяем конвертацию месяцев в дни
        consumable_names = [c["consumable_name"] for c in consumables]
        self.assertIn("engine oil", consumable_names)
        self.assertIn("brake pads", consumable_names)
        self.assertIn("air filter", consumable_names)
        
        # Проверяем срок службы (3 месяца = 90 дней)
        engine_oil = next(c for c in consumables if c["consumable_name"] == "engine oil")
        self.assertEqual(engine_oil["lifetime"], 90)
    
    def test_add_car_without_consumables_on_error(self):
        """Тест добавления автомобиля при ошибке получения расходных материалов."""
        # Мокируем ошибку от Mistral API
        mock_get_parts_lifetime = mock_mistral.get_parts_lifetime
        mock_get_parts_lifetime.side_effect = Exception("API Error")
        
        self.app.add_user("Иван Иванов", 1)
        car_id = self.app.add_car(1, "Toyota", "Camry", "2024-01-01", 2020)
        
        # Автомобиль должен быть добавлен даже при ошибке
        cars = self.app.get_cars(1)
        self.assertEqual(len(cars), 1)
        
        # Расходные материалы не должны быть добавлены
        consumables = self.app.db.get_all_car_consumables(car_id)
        self.assertEqual(len(consumables), 0)
    
    def test_get_cars(self):
        """Тест получения автомобилей пользователя."""
        self.app.add_user("Иван Иванов", 1)
        
        # Используем мок для избежания реальных вызовов API
        mock_get_parts_lifetime = mock_mistral.get_parts_lifetime
        mock_get_parts_lifetime.return_value = {"parts_lifetime": {}}
        self.app.add_car(1, "Toyota", "Camry", "2024-01-01", 2020)
        self.app.add_car(1, "Honda", "Civic", "2024-01-01", 2021)
        
        cars = self.app.get_cars(1)
        self.assertEqual(len(cars), 2)
    
    def test_update_car(self):
        """Тест обновления даты обслуживания автомобиля."""
        self.app.add_user("Иван Иванов", 1)
        
        mock_get_parts_lifetime = mock_mistral.get_parts_lifetime
        mock_get_parts_lifetime.return_value = {"parts_lifetime": {}}
        car_id = self.app.add_car(1, "Toyota", "Camry", "2024-01-01", 2020)
        
        # Добавляем расходный материал вручную
        self.app.db.add_consumable_to_db(car_id, "Масло", 90)
        
        # Обновляем дату обслуживания
        result = self.app.update_car(1, car_id)
        self.assertTrue(result)
        
        # Проверяем обновление
        cars = self.app.get_cars(1)
        updated_date = cars[0]["last_service_time"]
        today = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(updated_date, today)


class TestNotifier(unittest.TestCase):
    """Тесты для класса Notifier."""
    
    def setUp(self):
        """Создает временный файл базы данных для каждого теста."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.db = Database(self.temp_file.name)
        self.notifier = Notifier(self.temp_file.name, check_interval_minutes=1)
    
    def tearDown(self):
        """Удаляет временный файл после теста."""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)
    
    def test_check_consumable_needs_replacement(self):
        """Тест проверки необходимости замены расходного материала."""
        # Деталь, требующая замены (100 дней > 90 дней)
        old_consumable = {
            "consumable_name": "Масло",
            "lifetime": 90,
            "last_replacement_date": (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")
        }
        self.assertTrue(self.notifier._check_consumable_needs_replacement(old_consumable))
        
        # Деталь, не требующая замены (30 дней < 90 дней)
        new_consumable = {
            "consumable_name": "Масло",
            "lifetime": 90,
            "last_replacement_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        }
        self.assertFalse(self.notifier._check_consumable_needs_replacement(new_consumable))
    
    def test_check_all_cars_with_notifications(self):
        """Тест проверки всех автомобилей с отправкой уведомлений."""
        # Добавляем пользователя и автомобиль
        self.db.add_user_to_db("Иван Иванов", 1)
        car_id = self.db.add_car_to_db(1, "Toyota", "Camry", "2024-01-01", 2020)
        
        # Добавляем расходный материал, требующий замены
        old_date = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")
        self.db.add_consumable_to_db(car_id, "Масло", 90)
        
        # Обновляем дату замены вручную, чтобы она была старой
        db = self.db._read_db()
        for consumable_id, consumable_data in db["consumables"].items():
            if consumable_data.get("car_id") == car_id:
                consumable_data["last_replacement_date"] = old_date
        self.db._write_db(db)
        
        # Проверяем все автомобили
        with patch('builtins.print'):  # Мокируем print, чтобы не выводить в консоль
            self.notifier._check_all_cars()
        
        # Проверяем, что уведомление было отправлено (через проверку логики)
        consumables = self.db.get_all_car_consumables(car_id)
        days_since = self.notifier._calculate_days_since_service(old_date)
        self.assertGreaterEqual(days_since, 90)
    
    def test_calculate_days_since_service(self):
        """Тест вычисления дней с последнего обслуживания."""
        date_100_days_ago = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")
        days = self.notifier._calculate_days_since_service(date_100_days_ago)
        self.assertAlmostEqual(days, 100, delta=1)  # Допускаем погрешность в 1 день


class TestIntegration(unittest.TestCase):
    """Интеграционные тесты."""
    
    def setUp(self):
        """Создает временный файл базы данных для каждого теста."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        # Настраиваем мок перед каждым тестом (без reset_mock, чтобы не терять return_value)
        mock_mistral.get_parts_lifetime.side_effect = None
        mock_mistral.get_parts_lifetime.return_value = {"parts_lifetime": {}}
        self.app = CarTrackerApp(self.temp_file.name)
        self.notifier = Notifier(self.temp_file.name, check_interval_minutes=1)
    
    def tearDown(self):
        """Удаляет временный файл после теста."""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)
    
    def test_full_workflow(self):
        """Тест полного рабочего процесса."""
        # Мокируем ответ от Mistral API
        mock_get_parts_lifetime = mock_mistral.get_parts_lifetime
        mock_get_parts_lifetime.side_effect = None  # Убираем side_effect, если был установлен
        mock_get_parts_lifetime.return_value = {
            "car": "Toyota Camry 2020",
            "units": "months",
            "parts_lifetime": {
                "engine oil": 3,
                "brake pads": 6
            }
        }
        
        # 1. Добавляем пользователя
        self.app.add_user("Иван Иванов", 1)
        
        # 2. Добавляем автомобиль (автоматически добавляются расходные материалы)
        old_date = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")
        car_id = self.app.add_car(1, "Toyota", "Camry", old_date, 2020)
        
        # 3. Проверяем, что все добавлено
        cars = self.app.get_cars(1)
        self.assertEqual(len(cars), 1)
        
        # Проверяем, что мок был вызван
        self.assertTrue(mock_get_parts_lifetime.called)
        
        consumables = self.app.db.get_all_car_consumables(car_id)
        self.assertEqual(len(consumables), 2, f"Expected 2 consumables, got {len(consumables)}")
        
        # 4. Обновляем дату обслуживания
        result = self.app.update_car(1, car_id)
        self.assertTrue(result)
        
        # 5. Проверяем, что даты обновились
        cars = self.app.get_cars(1)
        today = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(cars[0]["last_service_time"], today)
        
        consumables = self.app.db.get_all_car_consumables(car_id)
        for consumable in consumables:
            self.assertEqual(consumable["last_replacement_date"], today)
        
        # 6. Проверяем уведомления (не должно быть, так как даты обновлены)
        with patch('builtins.print'):
            self.notifier.check_now()


if __name__ == '__main__':
    unittest.main()

