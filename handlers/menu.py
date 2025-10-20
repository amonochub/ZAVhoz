from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from models import Request
from utils.auth import require_auth
from utils.keyboard import (
    get_back_keyboard,
    get_main_menu_keyboard,
    get_user_help_keyboard,
    get_admin_help_keyboard,
)
from utils.messages import (
    format_request_list,
    get_welcome_message,
    get_help_message_for_user,
    get_help_photo_message,
    get_help_timing_message,
    get_help_not_fixed_message,
    get_admin_help_message,
    get_admin_export_help_message,
)


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
    """Создание заявки - начало с примерами и инструкциями"""
    await state.set_state(CreateRequestStates.waiting_for_description)
    await callback.message.edit_text(
        "📸 <b>Создание заявки на ремонт</b>\n\n"
        "<b>Как подать заявку:</b>\n"
        "• 📷 <b>Фото с подписью:</b> сфотографируйте проблему и напишите описание\n"
        "• 💬 <b>Текст:</b> просто опишите проблему словами\n\n"
        "<b>Примеры:</b>\n"
        "✅ <i>Фото + 'Течет кран в кабинете 101'</i>\n"
        "✅ <i>'Сломалась лампочка в коридоре 3 этажа'</i>\n"
        "✅ <i>'Нет горячей воды в классе А'</i>\n\n"
        "<i>Отправьте фото или напишите описание:</i>",
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

@require_auth
async def help_user_callback(callback: types.CallbackQuery, user, session):
    """Справка для пользователя"""
    keyboard = get_user_help_keyboard()
    text = get_help_message_for_user()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@require_auth
async def help_photo_callback(callback: types.CallbackQuery, user, session):
    """Справка: как отправить фото"""
    text = get_help_photo_message()
    keyboard = get_back_keyboard("help_user")
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@require_auth
async def help_timing_callback(callback: types.CallbackQuery, user, session):
    """Справка: как долго ждать"""
    text = get_help_timing_message()
    keyboard = get_back_keyboard("help_user")
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@require_auth
async def help_not_fixed_callback(callback: types.CallbackQuery, user, session):
    """Справка: что если не помогло"""
    text = get_help_not_fixed_message()
    keyboard = get_back_keyboard("help_user")
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@require_auth
async def help_admin_callback(callback: types.CallbackQuery, user, session):
    """Справка для завхоза"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return
    
    keyboard = get_admin_help_keyboard()
    text = get_admin_help_message()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@require_auth
async def help_admin_panel_callback(callback: types.CallbackQuery, user, session):
    """Справка: как использовать панель"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return
    
    text = get_admin_help_message()
    keyboard = get_back_keyboard("help_menu")
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@require_auth
async def help_export_callback(callback: types.CallbackQuery, user, session):
    """Справка: как экспортировать"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return
    
    text = get_admin_export_help_message()
    keyboard = get_back_keyboard("help_menu")
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@require_auth
async def help_menu_callback(callback: types.CallbackQuery, user, session):
    """Меню справки"""
    if user.role == "admin":
        keyboard = get_admin_help_keyboard()
        text = (
            "👑 <b>СПРАВКА ДЛЯ ЗАВХОЗА</b>\n\n"
            "Выберите интересующий раздел:"
        )
    else:
        keyboard = get_user_help_keyboard()
        text = (
            "❓ <b>СПРАВКА ПОЛЬЗОВАТЕЛЯ</b>\n\n"
            "Выберите нужную справку:"
        )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


def register_menu_handlers(dp):
    """Регистрация обработчиков меню"""
    dp.callback_query.register(main_menu_callback, F.data == "back_to_main")
    dp.callback_query.register(create_request_callback, F.data == "create_request")
    dp.callback_query.register(my_requests_callback, F.data == "my_requests")
    
    # Справка для пользователя
    dp.callback_query.register(help_user_callback, F.data == "help_user")
    dp.callback_query.register(help_photo_callback, F.data == "help_photo")
    dp.callback_query.register(help_timing_callback, F.data == "help_timing")
    dp.callback_query.register(help_not_fixed_callback, F.data == "help_not_fixed")
    
    # Справка для завхоза
    dp.callback_query.register(help_menu_callback, F.data == "help_menu")
    dp.callback_query.register(help_admin_callback, F.data == "help_admin_panel")
    dp.callback_query.register(help_admin_panel_callback, F.data == "help_admin_panel")
    dp.callback_query.register(help_export_callback, F.data == "help_export")
