from aiogram import types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from database.connection import get_db
from models import Request, File, Priority
from utils.auth import require_auth
from utils.keyboard import get_priority_keyboard, get_main_menu_keyboard, get_back_keyboard
from utils.messages import format_request_info
from utils.validation import validate_request_title, validate_request_description, validate_location, rate_limiter
from .menu import CreateRequestStates

@require_auth
async def title_received(message: types.Message, state: FSMContext, user, session):
    """Получено название заявки"""
    # Проверка rate limit
    if not rate_limiter.is_allowed(message.from_user.id, "create_request", max_requests=3, time_window=300):
        await message.reply("⏱️ Слишком много запросов. Попробуйте позже.")
        return

    # Валидация
    is_valid, error_msg = validate_request_title(message.text)
    if not is_valid:
        await message.reply(f"❌ {error_msg}\n\n💡 Попробуйте заново:")
        return

    await state.update_data(title=message.text.strip())
    await state.set_state(CreateRequestStates.waiting_for_description)
    await message.reply(
        "📝 Введите подробное описание проблемы:",
        reply_markup=get_back_keyboard("cancel_create")
    )

@require_auth
async def description_received(message: types.Message, state: FSMContext, user, session):
    """Получено описание заявки"""
    # Валидация
    is_valid, error_msg = validate_request_description(message.text)
    if not is_valid:
        await message.reply(f"❌ {error_msg}\n\n💡 Попробуйте заново:")
        return

    await state.update_data(description=message.text.strip())
    await state.set_state(CreateRequestStates.waiting_for_location)
    await message.reply(
        "🏢 Укажите местоположение (кабинет, этаж, здание):",
        reply_markup=get_back_keyboard("cancel_create")
    )

@require_auth
async def location_received(message: types.Message, state: FSMContext, user, session):
    """Получено местоположение"""
    # Валидация
    is_valid, error_msg = validate_location(message.text)
    if not is_valid:
        await message.reply(f"❌ {error_msg}\n\n💡 Попробуйте заново:")
        return

    await state.update_data(location=message.text.strip())
    await state.set_state(CreateRequestStates.waiting_for_priority)
    keyboard = get_priority_keyboard()
    await message.reply(
        "🔴 Выберите приоритет заявки:",
        reply_markup=keyboard
    )

@require_auth
async def priority_selected(callback: types.CallbackQuery, state: FSMContext, user, session):
    """Выбран приоритет"""
    priority_value = callback.data.replace("priority_", "")
    priority = Priority(priority_value)
    await state.update_data(priority=priority)

    data = await state.get_data()
    text = f"""
📋 <b>Проверьте данные заявки:</b>

🏷️ <b>Название:</b> {data['title']}
📝 <b>Описание:</b> {data['description']}
🏢 <b>Местоположение:</b> {data['location']}
🔴 <b>Приоритет:</b> {priority.value}

Если все верно, нажмите "Создать". Если хотите изменить - нажмите "Отмена".
"""

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✅ Создать заявку", callback_data="confirm_create")],
        [types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@require_auth
async def confirm_create_callback(callback: types.CallbackQuery, state: FSMContext, user, session):
    """Подтверждение создания заявки"""
    data = await state.get_data()

    # Создаем заявку
    request = Request(
        user_id=user.id,
        title=data['title'],
        description=data['description'],
        location=data['location'],
        priority=data['priority']
    )
    session.add(request)
    await session.commit()
    await session.refresh(request)

    # Отправляем уведомление администратору
    from utils.notifications import get_notification_service
    from bot.main import bot
    notification_service = get_notification_service(bot)
    if notification_service:
        await notification_service.notify_admin_new_request(request)

    # Очищаем состояние
    await state.clear()

    text = f"✅ <b>Заявка создана успешно!</b>\n\n{format_request_info(request)}"
    keyboard = get_main_menu_keyboard(user.role == "admin")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@require_auth
async def cancel_create_callback(callback: types.CallbackQuery, state: FSMContext, user, session):
    """Отмена создания заявки"""
    await state.clear()
    keyboard = get_main_menu_keyboard(user.role == "admin")
    await callback.message.edit_text(
        "❌ Создание заявки отменено.\n\n🏠 <b>Главное меню</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

def register_create_request_handlers(dp):
    """Регистрация обработчиков создания заявки"""
    dp.message.register(title_received, CreateRequestStates.waiting_for_title)
    dp.message.register(description_received, CreateRequestStates.waiting_for_description)
    dp.message.register(location_received, CreateRequestStates.waiting_for_location)
    dp.callback_query.register(priority_selected, F.data.startswith("priority_"))
    dp.callback_query.register(confirm_create_callback, F.data == "confirm_create")
    dp.callback_query.register(cancel_create_callback, F.data == "cancel_create")