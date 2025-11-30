from keyboards.common import main_menu_keyboard

from aiogram import F, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command


async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    """Handler for cancel action."""
    current_state = await state.get_state()
    if current_state is None:
        return

    await message.answer(
        "Действие отменено",
        reply_markup=types.ReplyKeyboardRemove(),
    )

    await state.clear()
    await message.answer(
        "Выберите действие:",
        reply_markup=main_menu_keyboard(),
    )


def register_handlers_cancel_action(dp: Dispatcher) -> None:
    """Register handlers for cancel action."""
    dp.message.register(
        cancel_handler,
        Command("cancel"),
    )
    dp.message.register(
        cancel_handler,
        F.text.lower() == "Cancel".lower(),
    )
