"""
Пример использования приложения для отслеживания автомобилей.
"""
from app import CarTrackerApp
from notifier import Notifier
import time


def main():
    """Пример использования приложения."""
    # Создаем экземпляр приложения
    app = CarTrackerApp()
    
    # Добавляем пользователей
    app.add_user("Иван Иванов", 1)
    app.add_user("Петр Петров", 2)
    
    # Добавляем автомобили
    # Автомобиль, который требует обслуживания (последнее обслуживание 200 дней назад)
    from datetime import datetime, timedelta
    old_service_date = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d")
    app.add_car(1, "Toyota", "Camry", old_service_date, 2020)
    
    # Автомобиль с недавним обслуживанием
    recent_service_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    app.add_car(1, "Honda", "Civic", recent_service_date, 2021)
    
    # Еще один автомобиль, требующий обслуживания
    very_old_service_date = (datetime.now() - timedelta(days=250)).strftime("%Y-%m-%d")
    app.add_car(2, "BMW", "X5", very_old_service_date, 2019)
    
    # Получаем автомобили пользователя
    print("Автомобили пользователя с ID 1:")
    cars = app.get_cars(1)
    for car in cars:
        print(f"  - {car['brand']} {car['model']} (ID: {car['car_id']})")
    
    print("\n" + "=" * 50 + "\n")
    
    # Добавляем расходные материалы к автомобилям
    if cars:
        car_id = cars[0]['car_id']  # Toyota Camry
        # Добавляем расходные материалы с разными сроками службы
        app.db.add_consumable_to_db(car_id, "Масло двигателя", 90)  # 90 дней
        app.db.add_consumable_to_db(car_id, "Тормозные колодки", 180)  # 180 дней
        app.db.add_consumable_to_db(car_id, "Воздушный фильтр", 60)  # 60 дней
        
        print(f"Добавлены расходные материалы для {cars[0]['brand']} {cars[0]['model']}")
        consumables = app.db.get_all_car_consumables(car_id)
        for cons in consumables:
            print(f"  - {cons['consumable_name']} (срок службы: {cons['lifetime']} дней)")
    
    # Добавляем расходные материалы ко второму автомобилю
    cars_user1 = app.get_cars(1)
    if len(cars_user1) > 1:
        car_id2 = cars_user1[1]['car_id']  # Honda Civic
        app.db.add_consumable_to_db(car_id2, "Масло двигателя", 90)
        app.db.add_consumable_to_db(car_id2, "Свечи зажигания", 200)
    
    # Добавляем расходные материалы к автомобилю второго пользователя
    cars_user2 = app.get_cars(2)
    if cars_user2:
        car_id3 = cars_user2[0]['car_id']  # BMW X5
        app.db.add_consumable_to_db(car_id3, "Масло двигателя", 90)
        app.db.add_consumable_to_db(car_id3, "Тормозные колодки", 180)
        app.db.add_consumable_to_db(car_id3, "Масляный фильтр", 90)
    
    print("\n" + "=" * 50 + "\n")
    
    # Запускаем notifier
    notifier = Notifier()
    notifier.start()
    
    # Выполняем немедленную проверку
    notifier.check_now()
    
    # Демонстрация: ждем немного и проверяем снова
    print("Ожидание 2 секунды перед следующей проверкой...\n")
    time.sleep(2)
    
    # Обновляем дату обслуживания одного автомобиля
    if cars:
        car_id = cars[0]['car_id']
        app.update_car(1, car_id)
        print(f"Обновлена дата обслуживания для автомобиля {car_id}\n")
    
    # Проверяем снова
    notifier.check_now()
    
    # Останавливаем notifier (в реальном приложении он будет работать постоянно)
    print("\nОстановка notifier через 3 секунды...")
    time.sleep(3)
    notifier.stop()


if __name__ == "__main__":
    main()

