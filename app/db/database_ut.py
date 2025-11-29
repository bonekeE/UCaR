"""
Юнит-тесты для модуля database.py
"""
import unittest
import os
from datetime import datetime, timedelta
from database import Database


class TestDatabase(unittest.TestCase):
    """Тесты для класса Database."""
    
    @classmethod
    def setUpClass(cls):
        """Создает тестовую базу данных перед всеми тестами."""
        # Используем тестовую базу данных
        cls.test_db_name = os.getenv('POSTGRES_DB_TEST', 'ucar_db_test')
        cls.db = Database(database=cls.test_db_name)
    
    @classmethod
    def tearDownClass(cls):
        """Закрывает соединение после всех тестов."""
        if hasattr(cls, 'db'):
            cls.db.close()
    
    def setUp(self):
        """Очищает данные перед каждым тестом."""
        conn = self.db._get_connection()
        try:
            with conn.cursor() as cur:
                # Удаляем все данные из таблиц (в правильном порядке из-за внешних ключей)
                cur.execute("DELETE FROM consumables")
                cur.execute("DELETE FROM user_cars")
                cur.execute("DELETE FROM cars")
                cur.execute("DELETE FROM users")
                conn.commit()
        finally:
            self.db._return_connection(conn)
    
    def test_add_user_to_db(self):
        """Тест добавления пользователя."""
        self.db.add_user_to_db("Иван Иванов", 1)
        
        # Проверяем, что пользователь добавлен
        users = self.db.get_all_users_with_cars()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]["user_id"], 1)
        self.assertEqual(users[0]["user_name"], "Иван Иванов")
    
    def test_add_car(self):
        """Тест добавления автомобиля."""
        car_id = self.db.add_car("Toyota", "Camry", 2020)
        self.assertIsInstance(car_id, int)
        self.assertGreater(car_id, 0)
        
        # Проверяем, что автомобиль создан
        car = self.db.get_car_by_id(car_id)
        self.assertIsNotNone(car)
        self.assertEqual(car["brand"], "Toyota")
        self.assertEqual(car["model"], "Camry")
        self.assertEqual(car["year_of_manufacture"], 2020)
    
    def test_add_car_duplicate(self):
        """Тест добавления дубликата автомобиля (дедупликация через UNIQUE constraint)."""
        car_id1 = self.db.add_car("Toyota", "Camry", 2020)
        
        # При попытке добавить тот же автомобиль должен вернуться тот же car_id
        # (благодаря обработке IntegrityError)
        car_id2 = self.db.add_car("Toyota", "Camry", 2020)
        
        # Должен вернуться тот же car_id
        self.assertEqual(car_id1, car_id2)
    
    def test_add_user_car(self):
        """Тест добавления связи пользователь-автомобиль."""
        self.db.add_user_to_db("Иван Иванов", 1)
        car_id = self.db.add_car("Toyota", "Camry", 2020)
        
        user_car_id = self.db.add_user_car(1, car_id, "2024-01-15")
        self.assertIsInstance(user_car_id, int)
        
        # Проверяем, что связь создана
        user_cars = self.db.get_user_cars(1)
        self.assertEqual(len(user_cars), 1)
        self.assertEqual(user_cars[0]["car_id"], car_id)
        self.assertEqual(user_cars[0]["last_service_time"], datetime(2024, 1, 15).date())
    
    def test_get_user_cars(self):
        """Тест получения автомобилей пользователя."""
        self.db.add_user_to_db("Иван Иванов", 1)
        car_id1 = self.db.add_car("Toyota", "Camry", 2020)
        car_id2 = self.db.add_car("Honda", "Civic", 2021)
        
        self.db.add_user_car(1, car_id1, "2024-01-15")
        self.db.add_user_car(1, car_id2, "2024-02-20")
        
        user_cars = self.db.get_user_cars(1)
        self.assertEqual(len(user_cars), 2)
        self.assertEqual(user_cars[0]["brand"], "Honda")  # Сортировка по дате ТО DESC
        self.assertEqual(user_cars[1]["brand"], "Toyota")
    
    def test_update_user_car_service_time(self):
        """Тест обновления даты ТО."""
        self.db.add_user_to_db("Иван Иванов", 1)
        car_id = self.db.add_car("Toyota", "Camry", 2020)
        self.db.add_user_car(1, car_id, "2024-01-15")
        
        # Обновляем дату ТО
        result = self.db.update_user_car_service_time(1, car_id, "2024-03-10")
        self.assertTrue(result)
        
        # Проверяем обновление
        user_cars = self.db.get_user_cars(1)
        self.assertEqual(user_cars[0]["last_service_time"], datetime(2024, 3, 10).date())
    
    def test_update_user_car_service_time_current_date(self):
        """Тест обновления даты ТО на текущую дату."""
        self.db.add_user_to_db("Иван Иванов", 1)
        car_id = self.db.add_car("Toyota", "Camry", 2020)
        self.db.add_user_car(1, car_id, "2024-01-15")
        
        # Обновляем без указания даты (должна использоваться текущая)
        result = self.db.update_user_car_service_time(1, car_id)
        self.assertTrue(result)
        
        # Проверяем, что дата обновилась на сегодня
        user_cars = self.db.get_user_cars(1)
        today = datetime.now().date()
        self.assertEqual(user_cars[0]["last_service_time"], today)
    
    def test_add_consumable_to_car(self):
        """Тест добавления расходного материала."""
        car_id = self.db.add_car("Toyota", "Camry", 2020)
        
        consumable_id = self.db.add_consumable_to_car(car_id, "Масло двигателя", 3)
        self.assertIsInstance(consumable_id, int)
        
        # Проверяем, что деталь добавлена
        consumables = self.db.get_car_consumables(car_id)
        self.assertEqual(len(consumables), 1)
        self.assertEqual(consumables[0]["consumable_name"], "Масло двигателя")
        self.assertEqual(consumables[0]["lifetime_months"], 3)
    
    def test_add_consumable_to_car_update_existing(self):
        """Тест обновления существующего расходного материала."""
        car_id = self.db.add_car("Toyota", "Camry", 2020)
        
        # Добавляем деталь
        self.db.add_consumable_to_car(car_id, "Масло двигателя", 3)
        
        # Обновляем срок службы
        self.db.add_consumable_to_car(car_id, "Масло двигателя", 6)
        
        # Проверяем, что срок службы обновился
        consumables = self.db.get_car_consumables(car_id)
        self.assertEqual(len(consumables), 1)
        self.assertEqual(consumables[0]["lifetime_months"], 6)
    
    def test_get_car_consumables(self):
        """Тест получения расходных материалов автомобиля."""
        car_id = self.db.add_car("Toyota", "Camry", 2020)
        
        self.db.add_consumable_to_car(car_id, "Масло двигателя", 3)
        self.db.add_consumable_to_car(car_id, "Тормозные колодки", 6)
        
        consumables = self.db.get_car_consumables(car_id)
        self.assertEqual(len(consumables), 2)
        consumable_names = [c["consumable_name"] for c in consumables]
        self.assertIn("Масло двигателя", consumable_names)
        self.assertIn("Тормозные колодки", consumable_names)
    
    def test_get_car_consumables_with_remaining(self):
        """Тест получения расходных материалов с расчетом остатка ресурса."""
        self.db.add_user_to_db("Иван Иванов", 1)
        car_id = self.db.add_car("Toyota", "Camry", 2020)
        
        # Добавляем связь пользователь-автомобиль с датой ТО 3 месяца назад
        old_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        self.db.add_user_car(1, car_id, old_date)
        
        # Добавляем деталь со сроком службы 3 месяца
        self.db.add_consumable_to_car(car_id, "Масло двигателя", 3)
        
        # Получаем детали с остатком ресурса
        consumables = self.db.get_car_consumables_with_remaining(1, car_id)
        self.assertEqual(len(consumables), 1)
        self.assertIn("months_remaining", consumables[0])
        # Остаток должен быть около 0 (3 месяца прошло, срок службы 3 месяца)
        self.assertLessEqual(consumables[0]["months_remaining"], 1)
    
    def test_get_all_users_with_cars(self):
        """Тест получения всех пользователей с их автомобилями."""
        self.db.add_user_to_db("Иван Иванов", 1)
        self.db.add_user_to_db("Петр Петров", 2)
        
        car_id1 = self.db.add_car("Toyota", "Camry", 2020)
        car_id2 = self.db.add_car("Honda", "Civic", 2021)
        
        self.db.add_user_car(1, car_id1, "2024-01-15")
        self.db.add_user_car(2, car_id2, "2024-02-20")
        
        users = self.db.get_all_users_with_cars()
        self.assertEqual(len(users), 2)
        
        # Проверяем первого пользователя
        user1 = next(u for u in users if u["user_id"] == 1)
        self.assertEqual(len(user1["cars"]), 1)
        self.assertEqual(user1["cars"][0]["brand"], "Toyota")
    
    def test_get_consumables_needing_replacement(self):
        """Тест получения расходных материалов, требующих замены."""
        self.db.add_user_to_db("Иван Иванов", 1)
        car_id = self.db.add_car("Toyota", "Camry", 2020)
        
        # Добавляем связь с датой ТО 4 месяца назад
        old_date = (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d")
        self.db.add_user_car(1, car_id, old_date)
        
        # Добавляем деталь со сроком службы 3 месяца (уже просрочена)
        self.db.add_consumable_to_car(car_id, "Масло двигателя", 3)
        
        # Добавляем деталь со сроком службы 6 месяцев (еще не просрочена)
        self.db.add_consumable_to_car(car_id, "Тормозные колодки", 6)
        
        # Получаем детали, требующие замены
        needing_replacement = self.db.get_consumables_needing_replacement()
        self.assertEqual(len(needing_replacement), 1)
        self.assertEqual(needing_replacement[0]["consumable_name"], "Масло двигателя")
        self.assertGreaterEqual(needing_replacement[0]["months_passed"], 3)
    
    def test_get_car_by_id(self):
        """Тест получения автомобиля по ID."""
        car_id = self.db.add_car("Toyota", "Camry", 2020)
        
        car = self.db.get_car_by_id(car_id)
        self.assertIsNotNone(car)
        self.assertEqual(car["car_id"], car_id)
        self.assertEqual(car["brand"], "Toyota")
        self.assertEqual(car["model"], "Camry")
        self.assertEqual(car["year_of_manufacture"], 2020)
    
    def test_get_car_by_id_nonexistent(self):
        """Тест получения несуществующего автомобиля."""
        car = self.db.get_car_by_id(99999)
        self.assertIsNone(car)
    
    def test_delete_user_car(self):
        """Тест удаления связи пользователь-автомобиль."""
        self.db.add_user_to_db("Иван Иванов", 1)
        car_id = self.db.add_car("Toyota", "Camry", 2020)
        self.db.add_user_car(1, car_id, "2024-01-15")
        
        # Удаляем связь
        result = self.db.delete_user_car(1, car_id)
        self.assertTrue(result)
        
        # Проверяем, что связь удалена
        user_cars = self.db.get_user_cars(1)
        self.assertEqual(len(user_cars), 0)
        
        # Проверяем, что автомобиль остался в базе
        car = self.db.get_car_by_id(car_id)
        self.assertIsNotNone(car)
    
    def test_multiple_users_same_car(self):
        """Тест того, что несколько пользователей могут иметь один автомобиль."""
        self.db.add_user_to_db("Иван Иванов", 1)
        self.db.add_user_to_db("Петр Петров", 2)
        
        car_id = self.db.add_car("Toyota", "Camry", 2020)
        
        self.db.add_user_car(1, car_id, "2024-01-15")
        self.db.add_user_car(2, car_id, "2024-02-20")
        
        # Проверяем, что оба пользователя имеют этот автомобиль
        user1_cars = self.db.get_user_cars(1)
        user2_cars = self.db.get_user_cars(2)
        
        self.assertEqual(len(user1_cars), 1)
        self.assertEqual(len(user2_cars), 1)
        self.assertEqual(user1_cars[0]["car_id"], car_id)
        self.assertEqual(user2_cars[0]["car_id"], car_id)
        
        # Проверяем, что автомобиль один в базе
        all_cars = [self.db.get_car_by_id(car_id)]
        self.assertEqual(len([c for c in all_cars if c]), 1)
    
    def test_add_consumables_from_llm_json(self):
        """Тест добавления расходных материалов из JSON от LLM."""
        car_id = self.db.add_car("Toyota", "Camry", 2020)
        
        llm_json = {
            "car": "Toyota Camry 2020",
            "units": "months",
            "parts_lifetime": {
                "engine oil": 3,
                "brake pads": 6,
                "air filter": 2
            }
        }
        
        added_count = self.db.add_consumables_from_llm_json(car_id, llm_json)
        self.assertEqual(added_count, 3)
        
        # Проверяем, что все детали добавлены
        consumables = self.db.get_car_consumables(car_id)
        self.assertEqual(len(consumables), 3)
        
        consumable_names = [c["consumable_name"] for c in consumables]
        self.assertIn("engine oil", consumable_names)
        self.assertIn("brake pads", consumable_names)
        self.assertIn("air filter", consumable_names)
    
    def test_add_consumables_from_llm_json_invalid_format(self):
        """Тест обработки некорректного формата JSON."""
        car_id = self.db.add_car("Toyota", "Camry", 2020)
        
        # Тест без parts_lifetime
        with self.assertRaises(ValueError) as context:
            self.db.add_consumables_from_llm_json(car_id, {"car": "Toyota"})
        self.assertIn("parts_lifetime", str(context.exception))
        
        # Тест с parts_lifetime не словарем
        with self.assertRaises(ValueError) as context:
            self.db.add_consumables_from_llm_json(car_id, {"parts_lifetime": "invalid"})
        self.assertIn("parts_lifetime", str(context.exception))
    
    def test_add_consumables_from_llm_json_partial_errors(self):
        """Тест обработки частичных ошибок при добавлении деталей."""
        car_id = self.db.add_car("Toyota", "Camry", 2020)
        
        llm_json = {
            "car": "Toyota Camry 2020",
            "units": "months",
            "parts_lifetime": {
                "engine oil": 3,  # Валидная
                "brake pads": "invalid",  # Некорректный тип
                "air filter": -1,  # Отрицательное значение
                "": 5,  # Пустое название
                "valid part": 4  # Валидная
            }
        }
        
        # Должны добавиться только валидные детали
        added_count = self.db.add_consumables_from_llm_json(car_id, llm_json)
        self.assertEqual(added_count, 2)  # engine oil и valid part
        
        consumables = self.db.get_car_consumables(car_id)
        self.assertEqual(len(consumables), 2)
        consumable_names = [c["consumable_name"] for c in consumables]
        self.assertIn("engine oil", consumable_names)
        self.assertIn("valid part", consumable_names)


if __name__ == "__main__":
    unittest.main()
