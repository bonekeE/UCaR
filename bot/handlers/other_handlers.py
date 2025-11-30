from keyboards.common import main_menu_keyboard

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text


async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    """Handler for cancel action."""
    current_state = await state.get_state()
    if current_state is None:
        return

    await message.answer(
        "Действие отменено",
        reply_markup=types.ReplyKeyboardRemove(),
    )

    await state.finish()
    await message.answer(
        "Выберите действие:",
        reply_markup=main_menu_keyboard(),
    )


def register_handlers_cancel_action(dispatcher: Dispatcher) -> None:
    """Register handlers for cancel action."""
    dispatcher.register_message_handler(
        cancel_handler,
        state="*",
        commands=["cancel"],
    )
    dispatcher.register_message_handler(
        cancel_handler,
        Text(equals="Cancel", ignore_case=True),
        state="*",
    )
