from .db.database import Database
from .services import UserService, CarService


db = Database()
user_service = UserService(db)
car_service = CarService(db)


__all__ = [
    'user_service',
    'car_service',
]
