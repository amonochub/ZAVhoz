"""
Модуль аналитики для ZAVhoz - генерирует статистику и тренды по заявкам.
"""

from datetime import datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Priority, Request, Status


class RequestAnalytics:
    """Класс для анализа статистики заявок"""

    @staticmethod
    async def get_daily_stats(session: AsyncSession, days: int = 7) -> dict:
        """Получить ежедневную статистику за N дней"""
        start_date = datetime.utcnow() - timedelta(days=days)

        stmt = select(
            func.date(Request.created_at).label('date'),
            func.count(Request.id).label('count')
        ).where(
            Request.created_at >= start_date
        ).group_by(
            func.date(Request.created_at)
        ).order_by('date')

        result = await session.execute(stmt)
        rows = result.all()

        return {
            "period_days": days,
            "daily": [{"date": str(row[0]), "count": row[1]} for row in rows]
        }

    @staticmethod
    async def get_priority_distribution(session: AsyncSession) -> dict:
        """Распределение заявок по приоритету"""
        stmt = select(
            Request.priority,
            func.count(Request.id).label('count')
        ).group_by(Request.priority)

        result = await session.execute(stmt)
        rows = result.all()

        priority_map = {
            Priority.HIGH: "🔴 Высокий",
            Priority.MEDIUM: "🟡 Средний",
            Priority.LOW: "🟢 Низкий"
        }

        return {
            "distribution": [
                {"priority": priority_map.get(row[0], str(row[0])), "count": row[1]}
                for row in rows
            ]
        }

    @staticmethod
    async def get_status_distribution(session: AsyncSession) -> dict:
        """Распределение заявок по статусу"""
        stmt = select(
            Request.status,
            func.count(Request.id).label('count')
        ).group_by(Request.status)

        result = await session.execute(stmt)
        rows = result.all()

        status_map = {
            Status.OPEN: "📭 Открыта",
            Status.IN_PROGRESS: "⚙️ В работе",
            Status.COMPLETED: "✅ Выполнена",
            Status.REJECTED: "❌ Отклонена"
        }

        return {
            "distribution": [
                {"status": status_map.get(row[0], str(row[0])), "count": row[1]}
                for row in rows
            ]
        }

    @staticmethod
    async def get_avg_completion_time(session: AsyncSession) -> dict:
        """Среднее время выполнения заявок (в часах)"""
        stmt = select(
            func.avg(
                func.extract('epoch', Request.completed_at - Request.created_at) / 3600
            )
        ).where(Request.status == Status.COMPLETED)

        result = await session.execute(stmt)
        avg_hours = result.scalar() or 0

        return {
            "avg_hours": round(avg_hours, 2),
            "avg_days": round(avg_hours / 24, 2)
        }

    @staticmethod
    async def get_performance_metrics(session: AsyncSession) -> dict:
        """Метрики производительности"""
        total_stmt = select(func.count(Request.id))
        completed_stmt = select(func.count(Request.id)).where(Request.status == Status.COMPLETED)
        rejected_stmt = select(func.count(Request.id)).where(Request.status == Status.REJECTED)
        in_progress_stmt = select(func.count(Request.id)).where(Request.status == Status.IN_PROGRESS)
        open_stmt = select(func.count(Request.id)).where(Request.status == Status.OPEN)

        total = await session.execute(total_stmt)
        completed = await session.execute(completed_stmt)
        rejected = await session.execute(rejected_stmt)
        in_progress = await session.execute(in_progress_stmt)
        open_req = await session.execute(open_stmt)

        total_count = total.scalar() or 0
        completed_count = completed.scalar() or 0

        completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0

        return {
            "total": total_count,
            "completed": completed_count,
            "rejected": rejected.scalar() or 0,
            "in_progress": in_progress.scalar() or 0,
            "open": open_req.scalar() or 0,
            "completion_rate": round(completion_rate, 2)
        }

    @staticmethod
    async def get_high_priority_pending(session: AsyncSession) -> int:
        """Количество просроченных высокоприоритетных заявок"""
        two_days_ago = datetime.utcnow() - timedelta(days=2)

        stmt = select(func.count(Request.id)).where(
            and_(
                Request.priority == Priority.HIGH,
                Request.status.in_([Status.OPEN, Status.IN_PROGRESS]),
                Request.created_at <= two_days_ago
            )
        )

        result = await session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    async def get_full_report(session: AsyncSession) -> dict:
        """Полный аналитический отчёт"""
        metrics = await RequestAnalytics.get_performance_metrics(session)
        daily = await RequestAnalytics.get_daily_stats(session, days=7)
        priority_dist = await RequestAnalytics.get_priority_distribution(session)
        status_dist = await RequestAnalytics.get_status_distribution(session)
        avg_time = await RequestAnalytics.get_avg_completion_time(session)
        overdue = await RequestAnalytics.get_high_priority_pending(session)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "daily_stats": daily,
            "priority_distribution": priority_dist,
            "status_distribution": status_dist,
            "avg_completion_time": avg_time,
            "overdue_high_priority": overdue
        }


def format_analytics_report(report: dict) -> str:
    """Форматировать аналитический отчёт в текст"""
    metrics = report["metrics"]
    priority = report["priority_distribution"]["distribution"]
    status = report["status_distribution"]["distribution"]
    avg_time = report["avg_completion_time"]
    overdue = report["overdue_high_priority"]

    text = "📊 <b>АНАЛИТИЧЕСКИЙ ОТЧЁТ</b>\n\n"

    text += "<b>📈 Общая статистика:</b>\n"
    text += f"  📋 Всего заявок: {metrics['total']}\n"
    text += f"  ✅ Выполнено: {metrics['completed']}\n"
    text += f"  ❌ Отклонено: {metrics['rejected']}\n"
    text += f"  ⚙️ В работе: {metrics['in_progress']}\n"
    text += f"  📭 Открыто: {metrics['open']}\n"
    text += f"  📊 Процент выполнения: {metrics['completion_rate']}%\n\n"

    text += "<b>🎯 По приоритету:</b>\n"
    for p in priority:
        text += f"  {p['priority']}: {p['count']}\n"
    text += "\n"

    text += "<b>📊 По статусу:</b>\n"
    for s in status:
        text += f"  {s['status']}: {s['count']}\n"
    text += "\n"

    text += "<b>⏱️ Время выполнения:</b>\n"
    text += f"  Среднее: {avg_time['avg_hours']} ч ({avg_time['avg_days']} дн)\n\n"

    if overdue > 0:
        text += f"⚠️ <b>ВНИМАНИЕ!</b> {overdue} заявок высокого приоритета просрочены!\n"

    return text
