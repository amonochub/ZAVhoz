
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
    """Приветственное сообщение"""
    message = f"👋 Добро пожаловать, {user_name}!\n\n"
    message += "Это бот для управления заявками на ремонт и работы.\n\n"

    if is_admin:
        message += "👑 <b>Вы вошли как завхоз</b>\n"
        message += "У вас есть доступ к панели администратора.\n\n"

    message += "Выберите действие:"
    return message

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
