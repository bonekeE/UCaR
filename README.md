
# Схема данных:

## Таблица `users` (Пользователи)

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

## Таблица `cars` (Автомобили)

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

## Таблица `user_cars` (Связь пользователей и автомобилей - many-to-many)

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

## Таблица `consumables` (Расходные материалы / Детали)

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

Текущая формула расчета остатка ресурса детали:
months_remaining = lifetime_months - (текущая_дата - last_service_time) в месяцах