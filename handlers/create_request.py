from aiogram import F, types
from aiogram.fsm.context import FSMContext

from models import File, Priority, Request
from utils.auth import require_auth
from utils.keyboard import get_back_keyboard, get_main_menu_keyboard, get_priority_keyboard
from utils.messages import format_request_info
from utils.validation import rate_limiter

from .menu import CreateRequestStates


def get_yes_no_keyboard():
    """Клавиатура Да/Нет"""
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅ Да, дополнить", callback_data="additional_yes"),
            types.InlineKeyboardButton(text="❌ Нет, готово", callback_data="additional_no")
        ],
        [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="cancel_create")]
    ])

@require_auth
async def description_received(update: types.Message, state: FSMContext, user, session):
    """Получено описание (фото, документ или текст)"""
    message = update  # update is the Message object for message handlers
    # Проверка rate limit
    if not rate_limiter.is_allowed(message.from_user.id, "create_request", max_requests=5, time_window=300):
        await message.reply("⏱️ Слишком много запросов. Попробуйте позже.")
        return

    description = ""
    file_id = None
    file_type = None
    file_name = None

    # Проверяем фото с подписью
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
        description = message.caption or "📸 Фото без описания"
    # Проверяем документ с подписью
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
        file_name = message.document.file_name or "документ"
        description = message.caption or f"📄 {file_name}"
    elif message.text:
        description = message.text.strip()
    else:
        await message.reply("❌ Отправьте пожалуйста фото, документ или текст описания")
        return

    if not description or len(description.strip()) < 3:
        await message.reply("❌ Описание слишком короткое. Минимум 3 символа.\n\n💡 Попробуйте заново:")
        return

    if len(description) > 1000:
        await message.reply("❌ Описание слишком длинное. Максимум 1000 символов.\n\n💡 Попробуйте заново:")
        return

    # Сохраняем в состояние
    await state.update_data(
        description=description,
        file_id=file_id,
        file_type=file_type,
        file_name=file_name
    )

    # Переходим к вопросу о дополнении
    await state.set_state(CreateRequestStates.waiting_for_additional)
    await message.reply(
        "✅ Спасибо! Описание получено.\n\n"
        "💬 Хотите дополнить описание деталями (приоритет, локация, комментарий)?",
        reply_markup=get_yes_no_keyboard()
    )

@require_auth
async def additional_yes_callback(callback: types.CallbackQuery, state: FSMContext, user, session):
    """Пользователь хочет дополнить"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📍 Указать локацию", callback_data="add_location")],
        [types.InlineKeyboardButton(text="💬 Добавить комментарий", callback_data="add_comment")],
        [types.InlineKeyboardButton(text="✅ Готово, выбрать приоритет", callback_data="go_priority")]
    ])

    await callback.message.edit_text(
        "📝 Что вы хотите дополнить?",
        reply_markup=keyboard
    )
    await callback.answer()

@require_auth
async def additional_no_callback(callback: types.CallbackQuery, state: FSMContext, user, session):
    """Пользователь не хочет дополнять - переходим к приоритету"""
    await state.set_state(CreateRequestStates.waiting_for_priority)
    keyboard = get_priority_keyboard()
    await callback.message.edit_text(
        "🔴 <b>Выберите приоритет заявки:</b>\n\n"
        "🔴 Высокий - срочно\n"
        "🟡 Средний - в течение дня\n"
        "🟢 Низкий - когда будет время",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@require_auth
async def priority_selected(callback: types.CallbackQuery, state: FSMContext, user, session):
    """Выбран приоритет - создаём заявку"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        priority_value = callback.data.replace("priority_", "")
        logger.info(f"Priority selected: {priority_value}")
        priority = Priority(priority_value)

        data = await state.get_data()
        logger.info(f"State data keys: {list(data.keys())}")
        logger.info(f"State data: {data}")

        # СТРОГАЯ валидация description
        description = data.get('description', '').strip()
        if not description:
            logger.error(f"Empty description in state data: {data}")
            await callback.message.edit_text(
                "❌ <b>Ошибка создания заявки</b>\n\n"
                "Описание заявки не найдено. Попробуйте создать заявку заново.",
                reply_markup=get_back_keyboard("back_to_main"),
                parse_mode="HTML"
            )
            await state.clear()
            await callback.answer("Ошибка валидации", show_alert=True)
            return

        # Дополнительная валидация
        from utils.validation import validate_request_description
        is_valid, error_msg = validate_request_description(description)
        if not is_valid:
            await callback.message.edit_text(
                f"❌ <b>Ошибка валидации</b>\n\n{error_msg}",
                reply_markup=get_back_keyboard("back_to_main"),
                parse_mode="HTML"
            )
            await callback.answer("Ошибка валидации", show_alert=True)
            return

        # Создание title с гарантией не пустоты
        title = description[:100].strip()
        if not title:
            title = "Заявка"
        
        logger.info(f"Creating request with title: {title}, description length: {len(description)}")

        # Создаём заявку
        request = Request(
            user_id=user.id,
            title=title,
            description=description,
            location=data.get('location', 'Не указано'),
            priority=priority
        )
        session.add(request)
        await session.commit()
        await session.refresh(request)
        logger.info(f"Request created: ID={request.id}, user_id={user.id}, title={title}")

        # Если есть фото - прикрепляем файл
        if data.get('file_id'):
            file = File(
                request_id=request.id,
                file_id=data['file_id'],
                file_type=data.get('file_type', 'photo'),
                file_name=data.get('file_name'),
                uploaded_by=user.id
            )
            session.add(file)
            await session.commit()
            logger.info(f"File attached to request {request.id}")

        # Отправляем уведомление администратору
        from bot.main import bot
        from utils.notifications import get_notification_service

        notification_service = get_notification_service(bot)
        if notification_service:
            logger.info(f"Sending notification to admin about request {request.id}")
            await notification_service.notify_admin_new_request(request)
            logger.info("✅ Notification sent successfully")
        else:
            logger.error("Notification service not available")

        # Очищаем состояние
        await state.clear()

        text = f"✅ <b>Заявка создана успешно!</b>\n\n{format_request_info(request)}"
        keyboard = get_main_menu_keyboard(user.role == "admin")

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        logger.info(f"User notified about successful request creation")

    except Exception as e:
        logger.error(f"Error creating request: {e}", exc_info=True)
        await callback.message.edit_text(
            f"❌ Ошибка при создании заявки:\n\n{str(e)}",
            reply_markup=get_back_keyboard("back_to_main")
        )
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)

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

@require_auth
async def add_location_callback(callback: types.CallbackQuery, state: FSMContext, user, session):
    """Пользователь хочет добавить локацию"""
    await state.update_data(add_location=True, add_comment=False)
    await callback.message.edit_text(
        "📍 Укажите местоположение (кабинет, этаж, здание, коридор и т.д.):"
    )
    await callback.answer()

@require_auth
async def add_comment_callback(callback: types.CallbackQuery, state: FSMContext, user, session):
    """Пользователь хочет добавить комментарий"""
    await state.update_data(add_location=False, add_comment=True)
    await callback.message.edit_text(
        "💬 Добавьте комментарий (максимум 500 символов):"
    )
    await callback.answer()

@require_auth
async def location_or_comment_received(update: types.Message, state: FSMContext, user, session):
    """Получена локация или комментарий"""
    message = update  # update is the Message object for message handlers
    data = await state.get_data()

    if data.get('add_location'):
        # Пользователь указывает локацию
        location = message.text.strip()
        if not location or len(location) < 2:
            await message.reply("❌ Локация слишком короткая. Минимум 2 символа.\n\n💡 Попробуйте заново:")
            return

        if len(location) > 100:
            await message.reply("❌ Локация слишком длинная. Максимум 100 символов.\n\n💡 Попробуйте заново:")
            return

        await state.update_data(location=location)
        await message.reply("✅ Локация сохранена!")

    elif data.get('add_comment'):
        # Пользователь добавляет комментарий
        comment = message.text.strip()
        if not comment or len(comment) < 2:
            await message.reply("❌ Комментарий слишком короткий. Минимум 2 символа.\n\n💡 Попробуйте заново:")
            return

        if len(comment) > 500:
            await message.reply("❌ Комментарий слишком длинный. Максимум 500 символов.\n\n💡 Попробуйте заново:")
            return

        await state.update_data(comment=comment)
        await message.reply("✅ Комментарий сохранён!")

    # Показываем меню что дальше
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📍 Указать локацию", callback_data="add_location")],
        [types.InlineKeyboardButton(text="💬 Добавить комментарий", callback_data="add_comment")],
        [types.InlineKeyboardButton(text="✅ Готово, выбрать приоритет", callback_data="go_priority")],
        [types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create")]
    ])

    await message.reply(
        "📝 Что дальше?",
        reply_markup=keyboard
    )

    await state.update_data(add_location=False, add_comment=False)

@require_auth
async def go_priority_callback(callback: types.CallbackQuery, state: FSMContext, user, session):
    """Перейти к выбору приоритета"""
    data = await state.get_data()

    # Обновляем локацию если её нет
    if 'location' not in data:
        await state.update_data(location="Не указано")

    await state.set_state(CreateRequestStates.waiting_for_priority)
    keyboard = get_priority_keyboard()
    await callback.message.edit_text(
        "🔴 <b>Выберите приоритет заявки:</b>\n\n"
        "🔴 Высокий - срочно\n"
        "🟡 Средний - в течение дня\n"
        "🟢 Низкий - когда будет время",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

def register_create_request_handlers(dp):
    """Регистрация обработчиков создания заявки"""
    # Описание получаемое в состоянии ожидания описания
    dp.message.register(description_received, CreateRequestStates.waiting_for_description)
    
    # Callback обработчики
    dp.callback_query.register(additional_yes_callback, F.data == "additional_yes")
    dp.callback_query.register(additional_no_callback, F.data == "additional_no")
    dp.callback_query.register(priority_selected, F.data.startswith("priority_"))
    dp.callback_query.register(cancel_create_callback, F.data == "cancel_create")
    dp.callback_query.register(add_location_callback, F.data == "add_location")
    dp.callback_query.register(add_comment_callback, F.data == "add_comment")
    dp.callback_query.register(go_priority_callback, F.data == "go_priority")
    
    # Локация или комментарий в состоянии дополнения
    dp.message.register(location_or_comment_received, CreateRequestStates.waiting_for_additional)
