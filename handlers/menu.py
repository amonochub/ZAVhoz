from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from models import Request
from utils.auth import require_auth
from utils.keyboard import (
    get_back_keyboard,
    get_main_menu_keyboard,
)
from utils.messages import format_request_list


class CreateRequestStates(StatesGroup):
    waiting_for_description = State()  # Фото/текст описание
    waiting_for_additional = State()   # Хотите дополнить?
    waiting_for_priority = State()     # Выбор приоритета

@require_auth
async def main_menu_callback(callback: types.CallbackQuery, user, session):
    """Главное меню"""
    is_admin = user.role == "admin"
    keyboard = get_main_menu_keyboard(is_admin)
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@require_auth
async def create_request_callback(callback: types.CallbackQuery, state: FSMContext, user, session):
    """Создание заявки - начало"""
    await state.set_state(CreateRequestStates.waiting_for_description)
    await callback.message.edit_text(
        "📸 <b>Создание заявки</b>\n\n"
        "Опишите проблему:\n"
        "• Отправьте фото с подписью\n"
        "• Или просто напишите текст\n\n"
        "Например: 'Трещина в окне, кабинет 101'",
        reply_markup=get_back_keyboard("back_to_main"),
        parse_mode="HTML"
    )
    await callback.answer()

@require_auth
async def my_requests_callback(callback: types.CallbackQuery, user, session):
    """Показать заявки пользователя"""
    stmt = select(Request).where(Request.user_id == user.id).order_by(Request.created_at.desc())
    result = await session.execute(stmt)
    requests = result.scalars().all()

    if not requests:
        text = "📭 У вас пока нет заявок.\n\nСоздайте первую заявку!"
        keyboard = get_main_menu_keyboard(user.role == "admin")
    else:
        text = format_request_list(requests, "Ваши заявки")
        keyboard = get_back_keyboard("back_to_main")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def back_to_main_callback(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    await main_menu_callback(callback)

def register_menu_handlers(dp):
    """Регистрация обработчиков меню"""
    dp.callback_query.register(main_menu_callback, F.data == "back_to_main")
    dp.callback_query.register(create_request_callback, F.data == "create_request")
    dp.callback_query.register(my_requests_callback, F.data == "my_requests")
    dp.callback_query.register(back_to_main_callback, F.data == "back")
