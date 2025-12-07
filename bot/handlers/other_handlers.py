import logging

from keyboards.common import main_menu_keyboard
from app.notifier import check_all_cars

from aiogram import F, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

logger = logging.getLogger(__name__)


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


async def run_periodic_task_handler(message: types.Message) -> None:
    """Обработчик для ручного запуска периодической задачи проверки автомобилей."""
    try:
        await message.answer("Запускаю проверку всех автомобилей...")
        bot = message.bot
        await check_all_cars(bot)
        await message.answer("✅ Проверка завершена. Уведомления отправлены пользователям.")
        logger.info(f"Periodic task manually triggered by user {message.from_user.id}")
    except Exception as e:
        error_msg = "❌ Ошибка при выполнении периодической задачи"
        logger.error(f"Error running periodic task manually: {e}")
        await message.answer(error_msg)


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


def register_periodic_task_handler(dp: Dispatcher) -> None:
    """Регистрация обработчика для ручного запуска периодической задачи."""
    dp.message.register(
        run_periodic_task_handler,
        Command("check_cars"),
    )
