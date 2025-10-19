"""
Модуль уведомлений для ZAVhoz.
"""

from datetime import datetime, timedelta
from typing import Optional
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from models import Request, Status, Priority
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис уведомлений"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def notify_admin_new_request(self, request) -> None:
        """Уведомить администратора о новой заявке"""
        try:
            from utils.messages import format_request_info
            admin_id = int(__import__('os').getenv('ADMIN_USER_ID', '0'))
            
            if admin_id == 0:
                logger.warning("ADMIN_USER_ID not configured")
                return
            
            text = f"🆕 <b>Новая заявка!</b>\n\n{format_request_info(request)}"
            await self.bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error notifying admin: {e}")

    async def notify_user_status_changed(self, request, new_status: str) -> None:
        """Уведомить пользователя об изменении статуса"""
        try:
            from utils.messages import format_request_info
            
            status_messages = {
                Status.IN_PROGRESS: "✅ Ваша заявка принята в работу!",
                Status.COMPLETED: "🎉 Ваша заявка выполнена!",
                Status.REJECTED: "❌ Ваша заявка отклонена."
            }
            
            message = status_messages.get(new_status, f"📝 Статус заявки изменён на {new_status}")
            text = f"{message}\n\n{format_request_info(request)}"
            
            await self.bot.send_message(request.user.telegram_id, text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error notifying user: {e}")

    async def notify_sla_breach(self, request, sla_hours: int = 24) -> None:
        """Уведомить администратора о нарушении SLA"""
        try:
            admin_id = int(__import__('os').getenv('ADMIN_USER_ID', '0'))
            
            if admin_id == 0:
                return
            
            hours_elapsed = (datetime.utcnow() - request.created_at).total_seconds() / 3600
            
            text = f"""⚠️ <b>SLA НАРУШЕНИЕ!</b>

🎯 Заявка: {request.title}
⏱️ Прошло {int(hours_elapsed)} часов (SLA: {sla_hours}ч)
🎯 Приоритет: {request.priority.value}
📍 Локация: {request.location}
📊 Статус: {request.status.value}

<i>Заявка требует срочного внимания!</i>"""
            
            await self.bot.send_message(admin_id, text, parse_mode="HTML")
            logger.warning(f"SLA breach for request {request.id}")
        except Exception as e:
            logger.error(f"Error sending SLA breach notification: {e}")

    async def notify_high_priority_pending(self, session: AsyncSession) -> None:
        """Уведомить администратора о застрявших высокоприоритетных заявках"""
        try:
            admin_id = int(__import__('os').getenv('ADMIN_USER_ID', '0'))
            
            if admin_id == 0:
                return
            
            two_days_ago = datetime.utcnow() - timedelta(days=2)
            
            stmt = select(Request).where(
                and_(
                    Request.priority == Priority.HIGH,
                    Request.status.in_([Status.OPEN, Status.IN_PROGRESS]),
                    Request.created_at <= two_days_ago
                )
            )
            
            result = await session.execute(stmt)
            requests = result.scalars().all()
            
            if requests:
                text = f"""🚨 <b>КРИТИЧЕСКИЕ ЗАЯВКИ ПРОСРОЧЕНЫ!</b>

Обнаружено {len(requests)} заявок высокого приоритета, которые в работе более 2 дней:

"""
                for req in requests[:5]:  # Показываем максимум 5
                    hours = (datetime.utcnow() - req.created_at).total_seconds() / 3600
                    text += f"  • {req.title} ({int(hours)}ч назад)\n"
                
                if len(requests) > 5:
                    text += f"\n... и ещё {len(requests) - 5} заявок\n"
                
                text += f"\n⚡ <b>Требуется срочная эскалация!</b>"
                
                await self.bot.send_message(admin_id, text, parse_mode="HTML")
                logger.warning(f"Found {len(requests)} overdue high-priority requests")
        except Exception as e:
            logger.error(f"Error sending high priority notification: {e}")

    async def send_daily_digest(self, session: AsyncSession) -> None:
        """Отправить дневной дайджест администратору"""
        try:
            from utils.analytics import RequestAnalytics, format_analytics_report
            admin_id = int(__import__('os').getenv('ADMIN_USER_ID', '0'))
            
            if admin_id == 0:
                return
            
            report = await RequestAnalytics.get_full_report(session)
            text = format_analytics_report(report)
            
            await self.bot.send_message(admin_id, text, parse_mode="HTML")
            logger.info("Daily digest sent to admin")
        except Exception as e:
            logger.error(f"Error sending daily digest: {e}")


def get_notification_service(bot: Bot) -> Optional[NotificationService]:
    """Получить сервис уведомлений"""
    try:
        return NotificationService(bot)
    except Exception as e:
        logger.error(f"Error creating notification service: {e}")
        return None