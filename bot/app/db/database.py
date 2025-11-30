from datetime import datetime
from typing import List, Dict, Optional
import os
from psycopg2 import pool, extras, IntegrityError


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
            self.connection_pool = pool.ThreadedConnectionPool(
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
                        user_name VARCHAR(255) NOT NULL
                    )
                """)
                
                # Создаем таблицу автомобилей
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS cars (
                        car_id SERIAL PRIMARY KEY,
                        brand VARCHAR(255) NOT NULL,
                        model VARCHAR(255) NOT NULL,
                        year_of_manufacture INTEGER NOT NULL,
                        UNIQUE(brand, model, year_of_manufacture)
                    )
                """)
                
                # Создаем таблицу связи пользователей и автомобилей (many-to-many)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_cars (
                        user_car_id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        car_id INTEGER NOT NULL,
                        last_service_time DATE NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                        FOREIGN KEY (car_id) REFERENCES cars(car_id) ON DELETE CASCADE
                    )
                """)
                
                # Создаем таблицу расходных материалов
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS consumables (
                        consumable_id SERIAL PRIMARY KEY,
                        car_id INTEGER NOT NULL,
                        consumable_name VARCHAR(255) NOT NULL,
                        lifetime_months INTEGER NOT NULL,
                        FOREIGN KEY (car_id) REFERENCES cars(car_id) ON DELETE CASCADE,
                        UNIQUE(car_id, consumable_name)
                    )
                """)
                
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"Ошибка при создании таблиц: {e}")
        finally:
            self._return_connection(conn)
    
    def add_user_to_db(self, user_name: str, user_id: int) -> None:
        """
        Добавляет или обновляет пользователя в базе данных.
        
        Args:
            user_name: Имя пользователя
            user_id: Уникальный идентификатор пользователя (Telegram user_id)
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
    
    def add_car(self, brand: str, model: str, year_of_manufacture: int) -> int:
        """
        Добавляет автомобиль в базу данных.
        Дедупликация обеспечивается ограничением UNIQUE(brand, model, year_of_manufacture).
        
        Args:
            brand: Марка автомобиля
            model: Модель автомобиля
            year_of_manufacture: Год выпуска
        
        Returns:
            car_id: Идентификатор автомобиля
        
        Raises:
            Exception: Если автомобиль с такими параметрами уже существует
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO cars (brand, model, year_of_manufacture)
                    VALUES (%s, %s, %s)
                    RETURNING car_id
                """, (brand, model, year_of_manufacture))
                
                car_id = cur.fetchone()[0]
                conn.commit()
                return car_id
        except IntegrityError as e:
            conn.rollback()
            # Если автомобиль уже существует, получаем его car_id
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT car_id FROM cars
                    WHERE brand = %s AND model = %s AND year_of_manufacture = %s
                """, (brand, model, year_of_manufacture))
                result = cur.fetchone()
                if result:
                    return result[0]
            raise Exception(f"Автомобиль уже существует, но не удалось получить его ID: {e}")
        except Exception as e:
            conn.rollback()
            raise Exception(f"Ошибка при добавлении автомобиля: {e}")
        finally:
            self._return_connection(conn)
    
    def add_user_car(self, user_id: int, car_id: int, last_service_time: str) -> int:
        """
        Добавляет связь между пользователем и автомобилем.
        
        Args:
            user_id: Идентификатор пользователя
            car_id: Идентификатор автомобиля
            last_service_time: Дата последнего ТО (формат: YYYY-MM-DD)
        
        Returns:
            user_car_id: Идентификатор связи
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_cars (user_id, car_id, last_service_time)
                    VALUES (%s, %s, %s)
                    RETURNING user_car_id
                """, (user_id, car_id, last_service_time))
                
                user_car_id = cur.fetchone()[0]
                conn.commit()
                return user_car_id
        except Exception as e:
            conn.rollback()
            raise Exception(f"Ошибка при добавлении связи пользователь-автомобиль: {e}")
        finally:
            self._return_connection(conn)
    
    def get_user_cars(self, user_id: int) -> List[Dict]:
        """
        Получает все автомобили пользователя с датами последнего ТО.
        
        Args:
            user_id: Идентификатор пользователя
        
        Returns:
            Список словарей с полями:
            - car_id
            - brand
            - model
            - year_of_manufacture
            - last_service_time
            - user_car_id
        """
        conn = self._get_connection()
        try:
            # Явно преобразуем user_id в int для корректного сравнения
            user_id = int(user_id)
            
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        c.car_id,
                        c.brand,
                        c.model,
                        c.year_of_manufacture,
                        uc.last_service_time,
                        uc.user_car_id
                    FROM user_cars uc
                    JOIN cars c ON uc.car_id = c.car_id
                    WHERE uc.user_id = %s::BIGINT
                    ORDER BY uc.last_service_time DESC
                """, (user_id,))
                
                rows = cur.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            raise Exception(f"Ошибка при получении автомобилей пользователя: {e}")
        finally:
            self._return_connection(conn)
    
    def update_user_car_service_time(self, user_id: int, car_id: int, 
                                     last_service_time: Optional[str] = None) -> bool:
        """
        Обновляет дату последнего ТО для конкретной пары пользователь-автомобиль.
        
        Args:
            user_id: Идентификатор пользователя
            car_id: Идентификатор автомобиля
            last_service_time: Новая дата ТО (если None, используется текущая дата)
        
        Returns:
            True если обновление успешно, False иначе
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                if last_service_time is None:
                    service_date = datetime.now().date()
                else:
                    service_date = datetime.strptime(last_service_time, "%Y-%m-%d").date()
                
                cur.execute("""
                    UPDATE user_cars
                    SET last_service_time = %s
                    WHERE user_id = %s AND car_id = %s
                """, (service_date, user_id, car_id))
                
                conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise Exception(f"Ошибка при обновлении даты ТО: {e}")
        finally:
            self._return_connection(conn)
    
    def add_consumable_to_car(self, car_id: int, consumable_name: str, 
                              lifetime_months: int) -> int:
        """
        Добавляет расходный материал к автомобилю.
        Если деталь уже существует для этого автомобиля, обновляет срок службы.
        
        Args:
            car_id: Идентификатор автомобиля
            consumable_name: Название детали
            lifetime_months: Срок службы в месяцах
        
        Returns:
            consumable_id: Идентификатор расходного материала
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO consumables (car_id, consumable_name, lifetime_months)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (car_id, consumable_name)
                    DO UPDATE SET lifetime_months = EXCLUDED.lifetime_months
                    RETURNING consumable_id
                """, (car_id, consumable_name, lifetime_months))
                
                consumable_id = cur.fetchone()[0]
                conn.commit()
                return consumable_id
        except Exception as e:
            conn.rollback()
            raise Exception(f"Ошибка при добавлении расходного материала: {e}")
        finally:
            self._return_connection(conn)
    
    def add_consumables_from_llm_json(self, car_id: int, llm_json: Dict) -> int:
        """
        Добавляет расходные материалы к автомобилю из JSON ответа LLM.
        
        Формат JSON:
        {
            "car": "<car_name>",
            "units": "months",
            "parts_lifetime": {
                "<part_name_1>": <integer_months>,
                "<part_name_2>": <integer_months>,
                ...
            }
        }
        
        Args:
            car_id: Идентификатор автомобиля
            llm_json: Словарь с данными от LLM API
        
        Returns:
            Количество успешно добавленных деталей
        
        Raises:
            ValueError: Если формат JSON некорректный или отсутствует parts_lifetime
        """
        # Проверяем формат JSON
        if not isinstance(llm_json, dict):
            raise ValueError("llm_json должен быть словарем")
        
        parts_lifetime = llm_json.get("parts_lifetime")
        if not parts_lifetime:
            raise ValueError("В JSON отсутствует поле 'parts_lifetime'")
        
        if not isinstance(parts_lifetime, dict):
            raise ValueError("Поле 'parts_lifetime' должно быть словарем")
        
        added_count = 0
        errors = []
        
        # Добавляем каждую деталь
        for part_name, lifetime_months in parts_lifetime.items():
            try:
                # Проверяем, что название детали - строка
                if not isinstance(part_name, str) or not part_name.strip():
                    errors.append(f"Некорректное название детали: {part_name}")
                    continue
                
                # Проверяем, что срок службы - число
                if not isinstance(lifetime_months, (int, float)):
                    errors.append(f"Некорректный срок службы для '{part_name}': {lifetime_months}")
                    continue
                
                lifetime_months_int = int(lifetime_months)
                if lifetime_months_int <= 0:
                    errors.append(f"Срок службы для '{part_name}' должен быть положительным числом: {lifetime_months_int}")
                    continue
                
                # Добавляем деталь
                try:
                    self.add_consumable_to_car(car_id, part_name.strip(), lifetime_months_int)
                    added_count += 1
                except Exception as e:
                    errors.append(f"Ошибка при добавлении детали '{part_name}': {e}")
                    continue
                    
            except Exception as e:
                errors.append(f"Неожиданная ошибка при обработке детали '{part_name}': {e}")
                continue
        
        # Если не удалось добавить ни одной детали, выбрасываем исключение
        if added_count == 0 and errors:
            error_msg = "Не удалось добавить ни одной детали:\n" + "\n".join(errors)
            raise ValueError(error_msg)
        
        # Если были ошибки, но хотя бы одна деталь добавлена, логируем предупреждение
        if errors:
            print(f"Предупреждение: при добавлении деталей возникли ошибки:")
            for error in errors:
                print(f"  - {error}")
        
        return added_count
    
    def get_car_consumables(self, car_id: int) -> List[Dict]:
        """
        Получает все расходные материалы для автомобиля.
        
        Args:
            car_id: Идентификатор автомобиля
        
        Returns:
            Список словарей с полями:
            - consumable_id
            - consumable_name
            - lifetime_months
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        consumable_id,
                        consumable_name,
                        lifetime_months
                    FROM consumables
                    WHERE car_id = %s
                    ORDER BY consumable_name
                """, (car_id,))
                
                rows = cur.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            raise Exception(f"Ошибка при получении расходных материалов: {e}")
        finally:
            self._return_connection(conn)
    
    def get_car_consumables_with_remaining(self, user_id: int, car_id: int) -> List[Dict]:
        """
        Получает расходные материалы автомобиля с расчетом остатка ресурса в месяцах.
        
        Args:
            user_id: Идентификатор пользователя (для получения last_service_time)
            car_id: Идентификатор автомобиля
        
        Returns:
            Список словарей с полями:
            - consumable_id
            - consumable_name
            - lifetime_months
            - last_service_time (из user_cars)
            - months_remaining (рассчитанное значение)
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        cons.consumable_id,
                        cons.consumable_name,
                        cons.lifetime_months,
                        uc.last_service_time,
                        (cons.lifetime_months - EXTRACT(YEAR FROM AGE(CURRENT_DATE, uc.last_service_time)) * 12 
                         - EXTRACT(MONTH FROM AGE(CURRENT_DATE, uc.last_service_time))) AS months_remaining
                    FROM consumables cons
                    JOIN user_cars uc ON cons.car_id = uc.car_id
                    WHERE cons.car_id = %s AND uc.user_id = %s
                    ORDER BY months_remaining ASC
                """, (car_id, user_id))
                
                rows = cur.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            raise Exception(f"Ошибка при получении расходных материалов с остатком ресурса: {e}")
        finally:
            self._return_connection(conn)
    
    def get_all_users_with_cars(self) -> List[Dict]:
        """
        Получает всех пользователей с их автомобилями.
        Используется нотификатором для проверки всех пользователей.
        
        Returns:
            Список словарей с полями:
            - user_id
            - user_name
            - cars: список автомобилей пользователя
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        u.user_id,
                        u.user_name
                    FROM users u
                    ORDER BY u.user_id
                """)
                
                users = cur.fetchall()
                result = []
                
                for user in users:
                    user_dict = dict(user)
                    # Получаем автомобили для каждого пользователя
                    # Используем отдельное соединение, чтобы избежать проблем с пулом
                    user_dict['cars'] = self.get_user_cars(user_dict['user_id'])
                    result.append(user_dict)
                
                return result
        except Exception as e:
            raise Exception(f"Ошибка при получении пользователей с автомобилями: {e}")
        finally:
            self._return_connection(conn)
    
    def get_consumables_needing_replacement(self) -> List[Dict]:
        """
        Получает все расходные материалы, требующие замены.
        Используется нотификатором для отправки уведомлений.
        
        Returns:
            Список словарей с полями:
            - user_id
            - user_name
            - car_id
            - brand
            - model
            - consumable_id
            - consumable_name
            - lifetime_months
            - last_service_time
            - months_passed (сколько месяцев прошло с последнего ТО)
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        u.user_id,
                        u.user_name,
                        c.car_id,
                        c.brand,
                        c.model,
                        cons.consumable_id,
                        cons.consumable_name,
                        cons.lifetime_months,
                        uc.last_service_time,
                        (EXTRACT(YEAR FROM AGE(CURRENT_DATE, uc.last_service_time)) * 12 
                         + EXTRACT(MONTH FROM AGE(CURRENT_DATE, uc.last_service_time))) AS months_passed
                    FROM consumables cons
                    JOIN cars c ON cons.car_id = c.car_id
                    JOIN user_cars uc ON c.car_id = uc.car_id
                    JOIN users u ON uc.user_id = u.user_id
                    WHERE (EXTRACT(EPOCH FROM (CURRENT_DATE - uc.last_service_time)) / 2592000) >= cons.lifetime_months
                    ORDER BY u.user_id, c.car_id, cons.consumable_name
                """)
                
                rows = cur.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            raise Exception(f"Ошибка при получении расходных материалов, требующих замены: {e}")
        finally:
            self._return_connection(conn)
    
    def get_car_by_id(self, car_id: int) -> Optional[Dict]:
        """
        Получает информацию об автомобиле по ID.
        
        Args:
            car_id: Идентификатор автомобиля
        
        Returns:
            Словарь с информацией об автомобиле или None
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        car_id,
                        brand,
                        model,
                        year_of_manufacture
                    FROM cars
                    WHERE car_id = %s
                """, (car_id,))
                
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as e:
            raise Exception(f"Ошибка при получении автомобиля: {e}")
        finally:
            self._return_connection(conn)
    
    def delete_user_car(self, user_id: int, car_id: int) -> bool:
        """
        Удаляет связь между пользователем и автомобилем.
        Не удаляет сам автомобиль, если у него есть другие владельцы.
        
        Args:
            user_id: Идентификатор пользователя
            car_id: Идентификатор автомобиля
        
        Returns:
            True если удаление успешно, False иначе
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM user_cars
                    WHERE user_id = %s AND car_id = %s
                """, (user_id, car_id))
                
                conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise Exception(f"Ошибка при удалении связи пользователь-автомобиль: {e}")
        finally:
            self._return_connection(conn)
    
    def close(self):
        """Закрывает пул соединений."""
        if hasattr(self, 'connection_pool'):
            self.connection_pool.closeall()
