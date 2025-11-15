"""
Модуль для работы с базой данных автомобилей и пользователей.
"""
from datetime import datetime
from typing import List, Dict, Optional
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool


class Database:
    """Класс для работы с базой данных PostgreSQL."""
    
    def __init__(self, 
                 host: Optional[str] = None,
                 port: Optional[int] = None,
                 database: Optional[str] = None,
                 user: Optional[str] = None,
                 password: Optional[str] = None,
                 connection_pool_min: int = 1,
                 connection_pool_max: int = 5):
        """
        Инициализирует подключение к базе данных PostgreSQL.
        
        Args:
            host: Хост базы данных (по умолчанию из переменных окружения или localhost)
            port: Порт базы данных (по умолчанию из переменных окружения или 5432)
            database: Имя базы данных (по умолчанию из переменных окружения или ucar_db)
            user: Пользователь базы данных (по умолчанию из переменных окружения или postgres)
            password: Пароль базы данных (по умолчанию из переменных окружения или postgres)
            connection_pool_min: Минимальное количество соединений в пуле
            connection_pool_max: Максимальное количество соединений в пуле
        """
        self.host = host or os.getenv('POSTGRES_HOST', 'localhost')
        self.port = port or int(os.getenv('POSTGRES_PORT', '5432'))
        self.database = database or os.getenv('POSTGRES_DB', 'ucar_db')
        self.user = user or os.getenv('POSTGRES_USER', 'postgres')
        self.password = password or os.getenv('POSTGRES_PASSWORD', 'postgres')
        
        # Создаем пул соединений
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                connection_pool_min,
                connection_pool_max,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
        except Exception as e:
            raise ConnectionError(f"Не удалось создать пул соединений: {e}")
        
        self._ensure_tables_exist()
    
    def __del__(self):
        self.close()
    
    def _get_connection(self):
        """Получает соединение из пула."""
        conn = self.connection_pool.getconn()
        return conn
    
    def _return_connection(self, conn):
        """Возвращает соединение в пул."""
        self.connection_pool.putconn(conn)
    
    def _ensure_tables_exist(self):
        """Создает таблицы, если их нет."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Создаем таблицу пользователей
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        user_name VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Создаем таблицу автомобилей
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS cars (
                        car_id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        brand VARCHAR(255) NOT NULL,
                        model VARCHAR(255) NOT NULL,
                        last_service_time DATE NOT NULL,
                        year_of_manufacture INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                    )
                """)
                
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"Ошибка при создании таблиц: {e}")
        finally:
            self._return_connection(conn)
    
    def add_user_to_db(self, user_name: str, user_id: int):
        """
        Добавляет пользователя в базу данных.
        
        Args:
            user_name: Имя пользователя
            user_id: Уникальный идентификатор пользователя (i64)
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (user_id, user_name)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id) 
                    DO UPDATE SET user_name = EXCLUDED.user_name
                """, (user_id, user_name))
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"Ошибка при добавлении пользователя: {e}")
        finally:
            self._return_connection(conn)
    
    def add_car_to_db(self, user_id: int, brand: str, model: str, 
                     last_service_time: str, year_of_manufacture: int) -> str:
        """
        Добавляет автомобиль в базу данных.
        
        Args:
            user_id: Идентификатор пользователя (i64)
            brand: Марка автомобиля
            model: Модель автомобиля
            last_service_time: Дата последнего обслуживания (формат: YYYY-MM-DD)
            year_of_manufacture: Год выпуска
        
        Returns:
            car_id: Уникальный идентификатор автомобиля
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Получаем количество автомобилей пользователя для генерации car_id
                cur.execute("""
                    SELECT COUNT(*) FROM cars WHERE user_id = %s
                """, (user_id,))
                count = cur.fetchone()[0]
                
                car_id = f"{user_id}_{brand}_{model}_{count}"
                
                cur.execute("""
                    INSERT INTO cars (car_id, user_id, brand, model, last_service_time, year_of_manufacture)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (car_id, user_id, brand, model, last_service_time, year_of_manufacture))
                
                conn.commit()
                return car_id
        except Exception as e:
            conn.rollback()
            raise Exception(f"Ошибка при добавлении автомобиля: {e}")
        finally:
            self._return_connection(conn)
    
    def get_cars_from_db(self, user_id: int) -> List[Dict]:
        """
        Получает список автомобилей пользователя.
        
        Args:
            user_id: Идентификатор пользователя (i64)
        
        Returns:
            Список словарей с информацией об автомобилях
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT car_id, user_id, brand, model, 
                           last_service_time, year_of_manufacture
                    FROM cars
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
                
                rows = cur.fetchall()
                # Конвертируем RealDictRow в обычный словарь
                return [dict(row) for row in rows]
        except Exception as e:
            raise Exception(f"Ошибка при получении автомобилей: {e}")
        finally:
            self._return_connection(conn)
    
    def update_car_in_db(self, user_id: int, car_id: str) -> bool:
        """
        Обновляет дату последнего обслуживания автомобиля.
        
        Args:
            user_id: Идентификатор пользователя (i64)
            car_id: Идентификатор автомобиля
        
        Returns:
            True, если обновление прошло успешно, False иначе
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE cars
                    SET last_service_time = %s
                    WHERE car_id = %s AND user_id = %s
                """, (datetime.now().date(), car_id, user_id))
                
                conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise Exception(f"Ошибка при обновлении автомобиля: {e}")
        finally:
            self._return_connection(conn)
    
    def get_all_cars(self) -> List[Dict]:
        """
        Получает все автомобили из базы данных.
        
        Returns:
            Список всех автомобилей
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT car_id, user_id, brand, model, 
                           last_service_time, year_of_manufacture
                    FROM cars
                    ORDER BY created_at DESC
                """)
                
                rows = cur.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            raise Exception(f"Ошибка при получении всех автомобилей: {e}")
        finally:
            self._return_connection(conn)
    
    def get_all_users(self) -> List[Dict]:
        """
        Получает всех пользователей из базы данных.
        
        Returns:
            Список всех пользователей
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT user_id, user_name
                    FROM users
                    ORDER BY created_at DESC
                """)
                
                rows = cur.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            raise Exception(f"Ошибка при получении всех пользователей: {e}")
        finally:
            self._return_connection(conn)
    
    def close(self):
        """Закрывает пул соединений."""
        if hasattr(self, 'connection_pool'):
            self.connection_pool.closeall()

