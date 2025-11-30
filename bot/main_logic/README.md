# UCaR - Система отслеживания состояния автомобилей

Приложение для отслеживания состояния автомобилей и автоматического оповещения пользователей о необходимости обслуживания.

## Структура проекта

- `app.py` - Основной класс приложения `CarTrackerApp` с методами для работы с пользователями и автомобилями
- `database.py` - Класс `Database` для работы с базой данных (JSON файл)
- `notifier.py` - Класс `Notifier` для фоновой проверки и отправки уведомлений
- `main.py` - Пример использования приложения

## Основные методы

### CarTrackerApp

1. **add_user(user_name, user_id)** - Добавляет пользователя в систему (user_id: int, i64)
2. **add_car(user_id, brand, model, last_service_time, year_of_manufacture)** - Добавляет автомобиль пользователю (user_id: int, i64). Автоматически получает и добавляет расходные материалы на основе данных автомобиля через Mistral API. Возвращает car_id: int (i64)
3. **get_cars(user_id)** - Получает список всех автомобилей пользователя (user_id: int, i64)
4. **update_car(user_id, car_id)** - Обновляет дату последнего обслуживания автомобиля (user_id: int, i64; car_id: int, i64)

### Database

Методы для работы с расходными материалами:

1. **add_consumable_to_db(car_id, consumable_name, lifetime)** - Добавляет расходный материал к автомобилю
   - `car_id`: Идентификатор автомобиля (int, i64)
   - `consumable_name`: Название расходного материала (например, "Масло двигателя")
   - `lifetime`: Срок службы в днях
2. **get_all_car_consumables(car_id)** - Получает все расходные материалы для автомобиля (car_id: int, i64)

### Notifier

Класс `Notifier` работает в фоновом режиме и проверяет состояние всех расходных материалов каждые 10 минут (настраивается). Уведомления отправляются для каждой детали отдельно, исходя из её индивидуального срока службы.

- **start()** - Запускает фоновый процесс проверки
- **stop()** - Останавливает фоновый процесс
- **check_now()** - Выполняет немедленную проверку всех автомобилей и их расходных материалов

## Использование

### Базовый пример

```python
from app import CarTrackerApp
from notifier import Notifier

# Создаем экземпляр приложения
app = CarTrackerApp()

# Добавляем пользователя (user_id - целое число i64)
app.add_user("Иван Иванов", 1)

# Добавляем автомобиль
app.add_car(1, "Toyota", "Camry", "2024-01-15", 2020)

# Получаем автомобили пользователя
cars = app.get_cars(1)

# Обновляем дату обслуживания
app.update_car(1, cars[0]['car_id'])

# Добавляем расходные материалы к автомобилю
app.db.add_consumable_to_db(cars[0]['car_id'], "Масло двигателя", 90)  # 90 дней
app.db.add_consumable_to_db(cars[0]['car_id'], "Тормозные колодки", 180)  # 180 дней

# Получаем все расходные материалы автомобиля
consumables = app.db.get_all_car_consumables(cars[0]['car_id'])

# Запускаем notifier
notifier = Notifier()
notifier.start()
```

## Настройки

- **Интервал проверки**: По умолчанию 10 минут. Можно задать при создании экземпляра `Notifier(check_interval_minutes=10)`
- **Срок службы расходных материалов**: Задается индивидуально для каждой детали при добавлении через `add_consumable_to_db()`
- **Логика уведомлений**: Система проверяет каждую деталь отдельно и отправляет уведомление, если прошло времени больше или равно сроку службы детали с момента последнего обслуживания

## База данных

Данные хранятся в файле `cars_db.json` в формате JSON. Структура:

```json
{
  "users": {
    "1": {
      "user_name": "...",
      "user_id": 1
    }
  },
  "cars": {
    "1": {
      "car_id": 1,
      "user_id": 1,
      "brand": "...",
      "model": "...",
      "last_service_time": "YYYY-MM-DD",
      "year_of_manufacture": 2020
    }
  },
  "consumables": {
    "consumable_id": {
      "consumable_id": "...",
      "car_id": 1,
      "consumable_name": "Масло двигателя",
      "lifetime": 90,
      "last_replacement_date": "YYYY-MM-DD"
    }
  }
}
```

**Примечание**: 
- В JSON ключи словарей всегда строки, но значения `user_id` и `car_id` хранятся как числа (int). При чтении из базы данных значения автоматически конвертируются в int.
- При обновлении даты обслуживания автомобиля (`update_car`) автоматически обновляется дата замены всех расходных материалов этого автомобиля, так как считается, что на каждом обслуживании меняются все детали.

## Схема данных PostgreSQL

### Таблица `users` (Пользователи)

```sql
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    user_name VARCHAR(255) NOT NULL
);
```

**Поля:**
- `user_id` - Уникальный идентификатор пользователя (Telegram user_id, BIGINT)
- `user_name` - Имя пользователя (VARCHAR(255), обязательное поле)

---

### Таблица `cars` (Автомобили)

```sql
CREATE TABLE IF NOT EXISTS cars (
    car_id SERIAL PRIMARY KEY,
    brand VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    year_of_manufacture INTEGER NOT NULL,
    UNIQUE(brand, model, year_of_manufacture)
);
```

**Поля:**
- `car_id` - Уникальный идентификатор автомобиля (SERIAL, автоинкремент)
- `brand` - Марка автомобиля (VARCHAR(255), обязательное поле)
- `model` - Модель автомобиля (VARCHAR(255), обязательное поле)
- `year_of_manufacture` - Год выпуска (INTEGER, обязательное поле)

**Ограничения:**
- `UNIQUE(brand, model, year_of_manufacture)` - Дедупликация: один автомобиль (бренд + модель + год) хранится один раз в базе

---

### Таблица `user_cars` (Связь пользователей и автомобилей - many-to-many)

```sql
CREATE TABLE IF NOT EXISTS user_cars (
    user_car_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    car_id INTEGER NOT NULL,
    last_service_time DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (car_id) REFERENCES cars(car_id) ON DELETE CASCADE
);
```

**Поля:**
- `user_car_id` - Уникальный идентификатор связи (SERIAL, автоинкремент)
- `user_id` - Идентификатор пользователя (BIGINT, внешний ключ на `users.user_id`)
- `car_id` - Идентификатор автомобиля (INTEGER, внешний ключ на `cars.car_id`)
- `last_service_time` - Дата последнего обслуживания для этого пользователя и этого автомобиля (DATE, обязательное поле)

**Связи:**
- `user_cars.user_id` → `users.user_id` (ON DELETE CASCADE - при удалении пользователя удаляются все его связи с автомобилями)
- `user_cars.car_id` → `cars.car_id` (ON DELETE CASCADE - при удалении автомобиля удаляются все связи с пользователями)

---

### Таблица `consumables` (Расходные материалы / Детали)

```sql
CREATE TABLE IF NOT EXISTS consumables (
    consumable_id SERIAL PRIMARY KEY,
    car_id INTEGER NOT NULL,
    consumable_name VARCHAR(255) NOT NULL,
    lifetime_months INTEGER NOT NULL,
    FOREIGN KEY (car_id) REFERENCES cars(car_id) ON DELETE CASCADE,
    UNIQUE(car_id, consumable_name)
);
```

**Поля:**
- `consumable_id` - Уникальный идентификатор расходного материала (SERIAL, автоинкремент)
- `car_id` - Идентификатор автомобиля (INTEGER, внешний ключ на `cars.car_id`)
- `consumable_name` - Название расходного материала/детали (VARCHAR(255), обязательное поле)
- `lifetime_months` - Срок службы в месяцах (INTEGER, обязательное поле)

**Связи:**
- `consumables.car_id` → `cars.car_id` (ON DELETE CASCADE - при удалении автомобиля удаляются все его расходные материалы)

**Ограничения:**
- `UNIQUE(car_id, consumable_name)` - Один тип детали одного типа на автомобиль (предотвращает дубликаты)

---

### Логика работы схемы

#### При добавлении автомобиля пользователю:
1. Проверяется, существует ли автомобиль с такими `brand`, `model`, `year_of_manufacture` в таблице `cars`
2. Если автомобиль не существует:
   - Создается новая запись в таблице `cars`
   - Выполняется запрос к LLM (Mistral API) для получения списка деталей и их сроков службы
   - Для каждой детали из ответа LLM создается запись в таблице `consumables`:
     - `consumable_name` - название детали из LLM
     - `lifetime_months` - срок службы в месяцах из LLM
3. Если автомобиль уже существует - используется существующий `car_id`
4. Создается запись в таблице `user_cars` с `user_id`, `car_id` и `last_service_time`

#### При обновлении ТО (`update_car`):
1. Обновляется `user_cars.last_service_time` для конкретной пары `(user_id, car_id)` на текущую дату
2. Для расчета остатка ресурса деталей используется `user_cars.last_service_time` (предполагается, что на ТО меняются все детали)

#### При получении автомобилей пользователя:
```sql
SELECT 
    c.car_id,
    c.brand,
    c.model,
    c.year_of_manufacture,
    uc.last_service_time
FROM user_cars uc
JOIN cars c ON uc.car_id = c.car_id
WHERE uc.user_id = ?
ORDER BY uc.last_service_time DESC;
```

#### Расчет остатка ресурса детали:
Остаток ресурса в месяцах рассчитывается как:
```
months_remaining = lifetime_months - (текущая_дата - last_service_time) в месяцах
```

Пример SQL запроса для получения остатка ресурса для конкретного пользователя и автомобиля:
```sql
SELECT 
    cons.consumable_name,
    cons.lifetime_months,
    uc.last_service_time,
    (cons.lifetime_months - EXTRACT(YEAR FROM AGE(CURRENT_DATE, uc.last_service_time)) * 12 
     - EXTRACT(MONTH FROM AGE(CURRENT_DATE, uc.last_service_time))) AS months_remaining
FROM consumables cons
JOIN user_cars uc ON cons.car_id = uc.car_id
WHERE cons.car_id = ? AND uc.user_id = ?
ORDER BY months_remaining ASC;
```

#### Для нотификатора:
Нотификатор проверяет все расходные материалы и отправляет уведомления, если:
```
(текущая_дата - last_service_time) в месяцах >= lifetime_months
```

Пример SQL запроса для нотификатора:
```sql
SELECT 
    u.user_id,
    u.user_name,
    c.car_id,
    c.brand,
    c.model,
    cons.consumable_id,
    cons.consumable_name,
    cons.lifetime_months,
    uc.last_service_time
FROM consumables cons
JOIN cars c ON cons.car_id = c.car_id
JOIN user_cars uc ON c.car_id = uc.car_id
JOIN users u ON uc.user_id = u.user_id
WHERE (EXTRACT(EPOCH FROM (CURRENT_DATE - uc.last_service_time)) / 2592000) >= cons.lifetime_months;
```

---

### Преимущества схемы с many-to-many

1. **Дедупликация**: Один автомобиль (бренд + модель + год) хранится один раз в базе, даже если у него несколько владельцев
2. **Гибкость**: У разных пользователей могут быть разные даты ТО для одного и того же автомобиля
3. **Экономия места**: Детали хранятся один раз на автомобиль, а не дублируются для каждого пользователя

## Запуск примера

```bash
python main.py
```

## Запуск тестов

Для запуска тестов используйте стандартный модуль unittest:

```bash
# Тесты основного приложения
python -m unittest test_app -v

# Тесты модуля mistral.py
python -m unittest test_mistral -v

# Все тесты
python -m unittest discover -v
```

### Тесты основного приложения (test_app.py)

Покрывают:
- Работу с базой данных (добавление пользователей, автомобилей, расходных материалов)
- Основные методы приложения (add_user, add_car, get_cars, update_car)
- Логику уведомлений (проверка необходимости замены деталей)
- Интеграционные сценарии (полный рабочий процесс)

### Тесты модуля mistral.py (test_mistral.py)

Покрывают:
- Функцию `_extract_json` (извлечение JSON из ответов с markdown и без)
- Функцию `get_parts_lifetime` (успешные запросы, обработка ошибок API, валидация JSON)
- Инициализацию модуля (проверка констант и настроек)

**Примечание**: Все тесты используют моки для Mistral API и внешних зависимостей, поэтому не требуют реального подключения к API.

## Требования

Python 3.6+ 

Зависимости:
- `mistralai>=1.0.0` - для работы с Mistral API
- `httpx>=0.24.0` - HTTP клиент для Mistral API
