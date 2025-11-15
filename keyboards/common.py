from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)


def car_inline_keyboard(cars: list) -> InlineKeyboardMarkup:
    """Создание клавиатуры с кнопками для выбора машины"""
    keyboard_buttons = []
    for car in cars:
        car_id = car.get('id')
        brand = car.get('brand')
        model = car.get('model')
        button_text = f"{brand} {model}"
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=str(car_id),
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
            ],
        ],
        resize_keyboard=True,
    ) 
    
    return markupKeyboard
