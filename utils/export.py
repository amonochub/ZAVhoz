import csv
import io
from datetime import datetime
from database.connection import get_db
from models import Request, Status, Priority

async def export_requests_to_csv(requests: list[Request]) -> str:
    """Экспорт заявок в CSV"""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')

    # Заголовки
    writer.writerow([
        'ID заявки',
        'Название',
        'Описание',
        'Местоположение',
        'Приоритет',
        'Статус',
        'Пользователь',
        'Дата создания',
        'Дата выполнения',
        'Исполнитель'
    ])

    # Данные
    for request in requests:
        writer.writerow([
            request.id,
            request.title,
            request.description,
            request.location,
            request.priority.value,
            request.status.value,
            f"{request.user.first_name or ''} {request.user.last_name or ''} (@{request.user.username or 'N/A'})".strip(),
            request.created_at.strftime('%d.%m.%Y %H:%M'),
            request.completed_at.strftime('%d.%m.%Y %H:%M') if request.completed_at else '',
            f"{request.assignee.first_name or ''} {request.assignee.last_name or ''}".strip() if request.assignee else ''
        ])

    return output.getvalue()

async def get_requests_for_export(status: Status = None, date_from: datetime = None, date_to: datetime = None) -> list[Request]:
    """Получить заявки для экспорта"""
    async for session in get_db():
        stmt = session.query(Request).options(
            session.joinedload(Request.user),
            session.joinedload(Request.assignee)
        )

        if status:
            stmt = stmt.filter(Request.status == status)

        if date_from:
            stmt = stmt.filter(Request.created_at >= date_from)

        if date_to:
            stmt = stmt.filter(Request.created_at <= date_to)

        stmt = stmt.order_by(Request.created_at.desc())
        result = await session.execute(stmt)
        return result.scalars().all()