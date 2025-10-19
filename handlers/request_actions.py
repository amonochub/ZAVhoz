from datetime import datetime

from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from models import Comment, File, Request, Status
from utils.auth import require_auth
from utils.keyboard import get_back_keyboard, get_request_actions_keyboard
from utils.messages import format_request_info
from utils.validation import rate_limiter, validate_comment


class CommentStates(StatesGroup):
    waiting_for_comment = State()

@require_auth
async def view_request_callback(callback: types.CallbackQuery, user, session):
    """Просмотр деталей заявки"""
    request_id = int(callback.data.split("_")[-1])

    stmt = select(Request).where(Request.id == request_id)
    result = await session.execute(stmt)
    request = result.scalar_one_or_none()

    if not request:
        await callback.answer("Заявка не найдена")
        return

    # Проверяем доступ (своя заявка или админ)
    if request.user_id != user.id and user.role != "admin":
        await callback.answer("У вас нет доступа к этой заявке")
        return

    text = format_request_info(request, show_user=user.role == "admin")
    keyboard = get_request_actions_keyboard(request.id, user.role == "admin")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

    # Отправляем фото если они есть
    file_stmt = select(File).where(File.request_id == request_id)
    file_result = await session.execute(file_stmt)
    files = file_result.scalars().all()

    if files:
        from bot.main import bot
        for file in files:
            if file.file_type == "photo":
                try:
                    await bot.send_photo(
                        callback.message.chat.id,
                        photo=file.file_id,
                        caption=f"📸 Фото заявки #{request.id}"
                    )
                except Exception as e:
                    import logging
                    logging.error(f"Error sending photo: {e}")

    await callback.answer()

@require_auth
async def take_request_callback(callback: types.CallbackQuery, user, session):
    """Взять заявку в работу"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа к этой функции")
        return

    request_id = int(callback.data.split("_")[-1])

    stmt = select(Request).where(Request.id == request_id)
    result = await session.execute(stmt)
    request = result.scalar_one_or_none()

    if not request or request.status != Status.OPEN:
        await callback.answer("Заявка не найдена или уже взята в работу")
        return

    request.status = Status.IN_PROGRESS
    request.assigned_to = user.id
    await session.commit()

    # Отправляем уведомление пользователю
    from bot.main import bot
    from utils.notifications import get_notification_service
    notification_service = get_notification_service(bot)
    if notification_service:
        await notification_service.notify_user_status_change(request)

    text = f"✅ Заявка #{request.id} взята в работу!\n\n{format_request_info(request, show_user=True)}"
    keyboard = get_request_actions_keyboard(request.id, True)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@require_auth
async def complete_request_callback(callback: types.CallbackQuery, user, session):
    """Выполнить заявку"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа к этой функции")
        return

    request_id = int(callback.data.split("_")[-1])

    stmt = select(Request).where(Request.id == request_id)
    result = await session.execute(stmt)
    request = result.scalar_one_or_none()

    if not request or request.status != Status.IN_PROGRESS:
        await callback.answer("Заявка не найдена или не в работе")
        return

    request.status = Status.COMPLETED
    request.completed_at = datetime.utcnow()
    await session.commit()

    # Отправляем уведомление пользователю
    from bot.main import bot
    from utils.notifications import get_notification_service
    notification_service = get_notification_service(bot)
    if notification_service:
        await notification_service.notify_user_status_change(request)

    text = f"✅ Заявка #{request.id} выполнена!\n\n{format_request_info(request, show_user=True)}"
    keyboard = get_back_keyboard("back_to_requests")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@require_auth
async def reject_request_callback(callback: types.CallbackQuery, user, session):
    """Отклонить заявку"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа к этой функции")
        return

    request_id = int(callback.data.split("_")[-1])

    stmt = select(Request).where(Request.id == request_id)
    result = await session.execute(stmt)
    request = result.scalar_one_or_none()

    if not request or request.status in [Status.COMPLETED, Status.REJECTED]:
        await callback.answer("Заявка не найдена или уже завершена")
        return

    request.status = Status.REJECTED
    await session.commit()

    # Отправляем уведомление пользователю
    from bot.main import bot
    from utils.notifications import get_notification_service
    notification_service = get_notification_service(bot)
    if notification_service:
        await notification_service.notify_user_status_change(request)

    text = f"❌ Заявка #{request.id} отклонена!\n\n{format_request_info(request, show_user=True)}"
    keyboard = get_back_keyboard("back_to_requests")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@require_auth
async def add_comment_callback(callback: types.CallbackQuery, state: FSMContext, user, session):
    """Добавить комментарий"""
    request_id = int(callback.data.split("_")[-1])
    await state.set_state(CommentStates.waiting_for_comment)
    await state.update_data(request_id=request_id)

    await callback.message.edit_text(
        "📝 Введите комментарий:",
        reply_markup=get_back_keyboard(f"view_request_{request_id}")
    )
    await callback.answer()

@require_auth
async def comment_received(message: types.Message, state: FSMContext, user, session):
    """Комментарий получен"""
    # Проверка rate limit
    if not rate_limiter.is_allowed(message.from_user.id, "add_comment", max_requests=10, time_window=300):
        await message.reply("⏱️ Слишком много комментариев. Попробуйте позже.")
        return

    # Валидация
    is_valid, error_msg = validate_comment(message.text)
    if not is_valid:
        await message.reply(f"❌ {error_msg}")
        return

    data = await state.get_data()
    request_id = data['request_id']

    comment = Comment(
        request_id=request_id,
        user_id=user.id,
        comment=message.text.strip()
    )
    session.add(comment)
    await session.commit()

    await state.clear()

    # Показываем заявку снова
    stmt = select(Request).where(Request.id == request_id)
    result = await session.execute(stmt)
    request = result.scalar_one_or_none()

    text = f"✅ Комментарий добавлен!\n\n{format_request_info(request, show_user=user.role == 'admin')}"
    keyboard = get_request_actions_keyboard(request.id, user.role == "admin")

    await message.reply(text, reply_markup=keyboard, parse_mode="HTML")

def register_request_actions_handlers(dp):
    """Регистрация обработчиков действий с заявками"""
    dp.callback_query.register(view_request_callback, F.data.startswith("view_request_"))
    dp.callback_query.register(take_request_callback, F.data.startswith("take_request_"))
    dp.callback_query.register(complete_request_callback, F.data.startswith("complete_request_"))
    dp.callback_query.register(reject_request_callback, F.data.startswith("reject_request_"))
    dp.callback_query.register(add_comment_callback, F.data.startswith("add_comment_"))
    dp.message.register(comment_received, CommentStates.waiting_for_comment)
