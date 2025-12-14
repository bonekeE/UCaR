from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def car_inline_keyboard(cars: list) -> InlineKeyboardMarkup:
    """Создание клавиатуры с кнопками для выбора машины"""
    keyboard_buttons = []
    for car in cars:
        car_id = car.get('id')
        brand = car.get('brand')
        model = car.get('model')
        production_year = car.get('production_year')
        button_text = f"{brand} {model} {production_year}"
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=str(car_id),
            )
        ])

    keyboard_buttons.append([
            InlineKeyboardButton(
                text="cancel",
                callback_data=str(-1),
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Создание главного меню клавиатуры"""
    markupKeyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Добавить машину', callback_data='add_car'),
                InlineKeyboardButton(text='Обновить машину', callback_data='update_car'),
            ],
            [
                InlineKeyboardButton(text='Просмотреть машины', callback_data='get_cars'),
                InlineKeyboardButton(text='Удалить машину', callback_data='delete_car'),
            ],
        ],
        resize_keyboard=True,
    ) 
    
    return markupKeyboard


def select_cancel() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="cancel")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    return keyboard
