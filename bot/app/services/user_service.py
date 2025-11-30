from app.db.database import Database


class UserService:
    """Сервис для работы с пользователями."""
    
    def __init__(self, db: Database):
        """
        Инициализация сервиса.
        
        Args:
            db: Экземпляр класса Database для работы с БД
        """
        self.db = db
    
    def register_user(self, user_id: int, user_name: str) -> None:
        """
        Регистрирует или обновляет пользователя в системе.
        
        Args:
            user_id: Уникальный идентификатор пользователя
            user_name: Имя пользователя
        """
        self.db.add_user_to_db(user_name, user_id)
    
    def get_all_users(self) -> list:
        """
        Получает всех пользователей с их автомобилями.
        
        Returns:
            Список словарей с информацией о пользователях
        """
        return self.db.get_all_users_with_cars()
