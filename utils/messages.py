
from models import Priority, Request, Status


# Shared emoji mappings
STATUS_EMOJIS = {
    Status.OPEN: "🟢",
    Status.IN_PROGRESS: "🟡",
    Status.COMPLETED: "✅",
    Status.REJECTED: "❌"
}

PRIORITY_EMOJIS = {
    Priority.LOW: "🟢",
    Priority.MEDIUM: "🟡",
    Priority.HIGH: "🔴"
}


def format_request_info(request: Request, show_user: bool = False) -> str:
    """Форматирование информации о заявке"""
    message = f"""
📋 <b>Заявка #{request.id}</b>

🏷️ <b>Название:</b> {request.title}
📝 <b>Описание:</b> {request.description}
🏢 <b>Местоположение:</b> {request.location}
{PRIORITY_EMOJIS[request.priority]} <b>Приоритет:</b> {request.priority.value}
{STATUS_EMOJIS[request.status]} <b>Статус:</b> {request.status.value}

📅 <b>Создана:</b> {request.created_at.strftime('%d.%m.%Y %H:%M')}
"""

    if show_user:
        message += f"👤 <b>Пользователь:</b> {request.user.first_name or ''} {request.user.last_name or ''} (@{request.user.username or 'N/A'})\n"

    if request.assigned_to and request.assigned_user:
        message += f"👷 <b>Исполнитель:</b> {request.assigned_user.first_name or ''} {request.assigned_user.last_name or ''}\n"

    if request.completed_at:
        message += f"✅ <b>Выполнена:</b> {request.completed_at.strftime('%d.%m.%Y %H:%M')}\n"

    return message.strip()

def format_request_list(requests: list[Request], title: str = "Заявки") -> str:
    """Улучшенное форматирование списка заявок для завхоза"""
    if not requests:
        return f"📭 {title}: заявок не найдено"

    message = f"📋 <b>{title}</b> ({len(requests)}):\n\n"

    for i, request in enumerate(requests, 1):
        # Визуальные индикаторы для быстрого понимания
        status_emoji = {
            Status.OPEN: "⏳",        # Ожидает
            Status.IN_PROGRESS: "🔧", # В работе
            Status.COMPLETED: "✅",   # Готово
            Status.REJECTED: "❌"     # Отклонено
        }[request.status]

        priority_emoji = {
            Priority.HIGH: "🔴",     # Срочная
            Priority.MEDIUM: "🟡",   # Обычная
            Priority.LOW: "🟢"       # Не срочная
        }[request.priority]

        # Компактная информация
        message += f"{i}. {status_emoji}{priority_emoji} <b>#{request.id}</b>\n"
        message += f"   📝 {request.title[:40]}{'...' if len(request.title) > 40 else ''}\n"
        message += f"   📍 {request.location}\n"
        message += f"   📅 {request.created_at.strftime('%d.%m %H:%M')}\n\n"

    return message.strip()

def get_welcome_message(user_name: str, is_admin: bool = False) -> str:
    """Приветственное сообщение - дружелюбное и понятное"""
    if is_admin:
        message = f"👋 Добро пожаловать, {user_name}!\n\n"
        message += "🏢 <b>Вы вошли как ЗАВХОЗ</b>\n\n"
        message += "📊 Ваша панель управления готова к работе:\n"
        message += "  • 📋 Просмотр и управление заявками\n"
        message += "  • 🎯 Фильтрация по приоритету и статусу\n"
        message += "  • 📈 Статистика и отчеты\n"
        message += "  • 📤 Экспорт данных\n\n"
        message += "Начните с <b>«👑 ПАНЕЛЬ ЗАВХОЗА»</b>"
    else:
        message = f"👋 Добро пожаловать, {user_name}!\n\n"
        message += "🏠 Этот бот поможет вам быстро подать заявку на ремонт.\n\n"
        message += "🆘 <b>Что вы можете сделать:</b>\n"
        message += "  • 📸 Отправить фото проблемы\n"
        message += "  • 📝 Описать проблему текстом\n"
        message += "  • 📊 Отследить статус заявки\n"
        message += "  • 🔔 Получать уведомления\n\n"
        message += "Начните с <b>«🆘 ПОДАТЬ ЗАЯВКУ НА РЕМОНТ»</b>"
    return message


def get_help_message_for_user() -> str:
    """Справка для пользователя"""
    return (
        "❓ <b>СПРАВКА ДЛЯ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        "📝 <b>Как подать заявку?</b>\n"
        "1. Нажмите «🆘 ПОДАТЬ ЗАЯВКУ НА РЕМОНТ»\n"
        "2. Отправьте фото или описание проблемы\n"
        "3. Выберите приоритет\n"
        "4. Готово! Завхоз получит уведомление\n\n"
        "📸 <b>Как отправить фото?</b>\n"
        "• Сфотографируйте проблему\n"
        "• Напишите описание в подпись\n"
        "• Пример: 'Сломан кран в кабинете 101'\n\n"
        "⏱️ <b>Как долго ждать?</b>\n"
        "• 🔴 Высокий приоритет: 1-2 часа\n"
        "• 🟡 Средний приоритет: до 24 часов\n"
        "• 🟢 Низкий приоритет: до недели\n\n"
        "Выберите нужную справку ⬇️"
    )


def get_help_photo_message() -> str:
    """Справка: как отправить фото или документ"""
    return (
        "📸 <b>КАК ОТПРАВИТЬ ФОТО ИЛИ ДОКУМЕНТ</b>\n\n"
        "<b>Пошаговая инструкция:</b>\n"
        "1️⃣ Откройте камеру или выберите файл\n"
        "2️⃣ Сделайте фото или выберите документ\n"
        "3️⃣ Откройте файл в боте\n"
        "4️⃣ <b>Напишите описание в подпись</b>\n"
        "   (это важно!)\n"
        "5️⃣ Отправьте\n\n"
        "<b>Поддерживаемые форматы:</b>\n"
        "📸 Фото (JPG, PNG)\n"
        "📄 Документы (PDF, DOC, DOCX, XLS и др.)\n\n"
        "<b>Примеры хорошего описания:</b>\n"
        "✅ 'Течет кран, кабинет 101'\n"
        "✅ 'Разбитое окно, коридор 2 этажа'\n"
        "✅ 'Ведомость о ремонте, приложен счет'\n\n"
        "<b>Плохие примеры:</b>\n"
        "❌ 'Окно' (слишком коротко)\n"
        "❌ Файл без описания\n"
        "❌ 'Всё сломалось' (неясно)\n\n"
        "📝 Чем подробнее описание, тем\n"
        "быстрее помогут!"
    )


def get_help_timing_message() -> str:
    """Справка: как долго ждать"""
    return (
        "⏱️ <b>ВРЕМЯ ОТВЕТА</b>\n\n"
        "<b>Время выполнения по приоритету:</b>\n\n"
        "🔴 <b>ВЫСОКИЙ ПРИОРИТЕТ</b>\n"
        "   ⏰ 1-2 часа\n"
        "   🎯 Срочные проблемы\n"
        "   Например: нет воды, отопления\n\n"
        "🟡 <b>СРЕДНИЙ ПРИОРИТЕТ</b>\n"
        "   ⏰ До 24 часов\n"
        "   🎯 Обычные проблемы\n"
        "   Например: сломан кран, лампочка\n\n"
        "🟢 <b>НИЗКИЙ ПРИОРИТЕТ</b>\n"
        "   ⏰ До недели\n"
        "   🎯 Некритичные проблемы\n"
        "   Например: косметический ремонт\n\n"
        "📲 <b>Вы получите уведомление когда:</b>\n"
        "✅ Заявка принята в работу\n"
        "✅ Работа выполнена\n"
        "✅ Заявка закрыта"
    )


def get_help_not_fixed_message() -> str:
    """Справка: что если не помогло"""
    return (
        "🚫 <b>ЧТО ЕСЛИ ПРОБЛЕМА НЕ РЕШЕНА?</b>\n\n"
        "<b>Если завхоз не приступил:</b>\n"
        "1. Проверьте интернет\n"
        "2. Убедитесь, что заявка видна в 'Мои заявки'\n"
        "3. Подождите указанное время\n"
        "4. Если срок превышен, создайте новую заявку\n\n"
        "<b>Если работа не помогла:</b>\n"
        "1. Создайте дополнительную заявку\n"
        "2. Опишите, что уже делали\n"
        "3. Отправьте новое фото\n"
        "4. Отметьте как 'Высокий приоритет'\n\n"
        "<b>Контакт завхоза:</b>\n"
        "📞 Уточните номер телефона у администрации\n"
        "📧 Или напишите в школе\n\n"
        "💡 <b>Совет:</b> Чем точнее описание, тем\n"
        "быстрее помогут!"
    )


def get_admin_help_message() -> str:
    """Справка для завхоза"""
    return (
        "👑 <b>СПРАВКА ДЛЯ ЗАВХОЗА</b>\n\n"
        "📊 <b>Как использовать панель?</b>\n\n"
        "<b>Основные кнопки:</b>\n"
        "📋 <b>Открытые заявки</b>\n"
        "   → Список всех текущих заявок\n"
        "   → Группировка по приоритету\n\n"
        "🎯 <b>Фильтры</b>\n"
        "   → По приоритету (срочные первыми)\n"
        "   → По статусу (в работе, выполнено)\n"
        "   → По дате (сегодня, неделя)\n\n"
        "📊 <b>Статистика</b>\n"
        "   → Текущая нагрузка\n"
        "   → Выполнено за день\n"
        "   → Полезные советы\n\n"
        "📁 <b>Архив</b>\n"
        "   → Последние 50 выполненных\n\n"
        "📤 <b>Экспорт</b>\n"
        "   → Отчет за месяц (CSV)\n"
        "   → Статистика (TXT)\n"
        "   → Все заявки (CSV)"
    )


def get_admin_export_help_message() -> str:
    """Справка: как экспортировать"""
    return (
        "📤 <b>КАК ЭКСПОРТИРОВАТЬ ОТЧЕТ</b>\n\n"
        "<b>Доступные форматы:</b>\n\n"
        "📊 <b>Отчет за месяц</b>\n"
        "   📋 Формат: CSV\n"
        "   📈 Содержит: ID, дата, приоритет, статус\n"
        "   💾 Откройте в Excel для анализа\n\n"
        "📈 <b>Статистика</b>\n"
        "   📋 Формат: TXT (текст)\n"
        "   📊 Содержит: общие данные, по приоритетам,\n"
        "             по статусам\n"
        "   💾 Легко делиться и печатать\n\n"
        "📋 <b>Все заявки</b>\n"
        "   📋 Формат: CSV (все данные)\n"
        "   📝 Содержит: полная информация\n"
        "   💾 Для глубокого анализа\n\n"
        "<b>Как использовать:</b>\n"
        "1. Выберите нужный отчет\n"
        "2. Дождитесь загрузки файла\n"
        "3. Откройте файл на компьютере\n"
        "4. Используйте для анализа или печати"
    )


def get_stats_message(total_requests: int, completed_requests: int, avg_completion_time: float = None) -> str:
    """Сообщение со статистикой"""
    message = "📊 <b>Статистика заявок</b>\n\n"
    message += f"📋 Всего заявок: {total_requests}\n"
    message += f"✅ Выполнено: {completed_requests}\n"

    if avg_completion_time:
        hours = int(avg_completion_time)
        minutes = int((avg_completion_time - hours) * 60)
        message += f"⏱️ Среднее время выполнения: {hours}ч {minutes}мин\n"

    return message
