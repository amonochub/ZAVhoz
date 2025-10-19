from models import Request, Status, Priority
from datetime import datetime

def format_request_info(request: Request, show_user: bool = False) -> str:
    """Форматирование информации о заявке"""
    status_emojis = {
        Status.OPEN: "🟢",
        Status.IN_PROGRESS: "🟡",
        Status.COMPLETED: "✅",
        Status.REJECTED: "❌"
    }

    priority_emojis = {
        Priority.LOW: "🟢",
        Priority.MEDIUM: "🟡",
        Priority.HIGH: "🔴"
    }

    message = f"""
📋 <b>Заявка #{request.id}</b>

🏷️ <b>Название:</b> {request.title}
📝 <b>Описание:</b> {request.description}
🏢 <b>Местоположение:</b> {request.location}
{priority_emojis[request.priority]} <b>Приоритет:</b> {request.priority.value}
{status_emojis[request.status]} <b>Статус:</b> {request.status.value}

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
    """Форматирование списка заявок"""
    if not requests:
        return f"📭 {title}: заявок не найдено"

    message = f"📋 <b>{title}</b> ({len(requests)}):\n\n"

    for i, request in enumerate(requests, 1):
        status_emoji = {
            Status.OPEN: "🟢",
            Status.IN_PROGRESS: "🟡",
            Status.COMPLETED: "✅",
            Status.REJECTED: "❌"
        }[request.status]

        priority_emoji = {
            Priority.LOW: "🟢",
            Priority.MEDIUM: "🟡",
            Priority.HIGH: "🔴"
        }[request.priority]

        message += f"{i}. {status_emoji}{priority_emoji} #{request.id} - {request.title[:30]}{'...' if len(request.title) > 30 else ''}\n"
        message += f"   📅 {request.created_at.strftime('%d.%m.%Y')} | 🏢 {request.location}\n\n"

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