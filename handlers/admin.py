from datetime import datetime, timedelta
import logging

from aiogram import F, types
from aiogram.types import FSInputFile
from sqlalchemy import and_, func, select

from models import Priority, Request, Status
from utils.auth import require_auth
from utils.keyboard import (
    get_admin_panel_keyboard,
    get_admin_filters_menu_keyboard,
    get_admin_export_menu_keyboard,
    get_back_keyboard,
)
from utils.messages import format_request_list, STATUS_EMOJIS, PRIORITY_EMOJIS

logger = logging.getLogger(__name__)


@require_auth
async def admin_panel_callback(callback: types.CallbackQuery, user, session):
    """Панель завхоза - главное меню"""
    logger.info(f"🔍 Admin panel access attempt: user_id={user.id}, telegram_id={user.telegram_id}, role={user.role}, is_active={user.is_active}")
    
    if user.role != "admin":
        logger.warning(f"❌ Access denied: user {user.telegram_id} tried to access admin panel but has role '{user.role}'")
        await callback.answer("У вас нет доступа")
        return

    logger.info(f"✅ Admin panel opened for user {user.telegram_id}")
    keyboard = get_admin_panel_keyboard()
    await callback.message.edit_text(
        "👑 <b>ПАНЕЛЬ ЗАВХОЗА</b>\n\n🔧 Управление заявками на ремонт",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@require_auth
async def admin_open_requests_callback(callback: types.CallbackQuery, user, session):
    """Открытые заявки - с умной группировкой по приоритету"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return

    # Получаем заявки с сортировкой по приоритету
    stmt = select(Request).where(
        Request.status.in_([Status.OPEN, Status.IN_PROGRESS])
    ).order_by(Request.priority.desc(), Request.created_at.asc())
    
    result = await session.execute(stmt)
    requests = result.scalars().all()

    if not requests:
        text = "✅ <b>Все заявки выполнены!</b>\n\n📭 Открытых заявок нет."
        keyboard = get_admin_panel_keyboard()
    else:
        # Группируем по приоритету
        high_priority = [r for r in requests if r.priority == Priority.HIGH]
        medium_priority = [r for r in requests if r.priority == Priority.MEDIUM]
        low_priority = [r for r in requests if r.priority == Priority.LOW]
        
        text = f"📋 <b>ОТКРЫТЫЕ ЗАЯВКИ ({len(requests)})</b>\n\n"
        
        if high_priority:
            text += f"🔴 <b>СРОЧНЫЕ ({len(high_priority)}):</b>\n"
            for req in high_priority[:3]:
                text += f"  #{req.id} {STATUS_EMOJIS.get(req.status, '?')} {req.title[:28]}...\n"
            if len(high_priority) > 3:
                text += f"  ... и ещё {len(high_priority) - 3}\n"
            text += "\n"
        
        if medium_priority:
            text += f"🟡 <b>СРЕДНИЙ ПРИОРИТЕТ ({len(medium_priority)}):</b>\n"
            for req in medium_priority[:2]:
                text += f"  #{req.id} - {req.title[:28]}...\n"
            text += "\n"
        
        if low_priority:
            text += f"🟢 <b>НИЗКИЙ ПРИОРИТЕТ ({len(low_priority)})</b>\n"
        
        keyboard = get_admin_filters_menu_keyboard()

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@require_auth
async def admin_filters_menu_callback(callback: types.CallbackQuery, user, session):
    """Меню фильтров"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return

    keyboard = get_admin_filters_menu_keyboard()
    await callback.message.edit_text(
        "🎯 <b>ФИЛЬТРЫ</b>\n\nВыберите нужный фильтр:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@require_auth
async def filter_priority_callback(callback: types.CallbackQuery, user, session):
    """Фильтр по приоритету"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return

    priority_str = callback.data.replace("filter_priority_", "")
    priority = Priority(priority_str)

    stmt = select(Request).where(
        and_(Request.priority == priority, Request.status.in_([Status.OPEN, Status.IN_PROGRESS]))
    ).order_by(Request.created_at.asc())
    
    result = await session.execute(stmt)
    requests = result.scalars().all()

    text = format_request_list(requests, f"Заявки с приоритетом '{priority.value}'")
    keyboard = get_back_keyboard("admin_filters_menu")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@require_auth
async def filter_status_callback(callback: types.CallbackQuery, user, session):
    """Фильтр по статусу"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return

    status_str = callback.data.replace("filter_status_", "")
    status = Status(status_str)

    stmt = select(Request).where(Request.status == status).order_by(Request.created_at.desc())
    result = await session.execute(stmt)
    requests = result.scalars().all()

    text = format_request_list(requests, f"Заявки со статусом '{status.value}'")
    keyboard = get_back_keyboard("admin_filters_menu")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@require_auth
async def filter_today_callback(callback: types.CallbackQuery, user, session):
    """Заявки за сегодня"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return

    today = datetime.utcnow().date()
    stmt = select(Request).where(
        func.date(Request.created_at) == today
    ).order_by(Request.created_at.desc())
    
    result = await session.execute(stmt)
    requests = result.scalars().all()

    text = format_request_list(requests, f"Заявки за сегодня ({len(requests)})")
    keyboard = get_back_keyboard("admin_filters_menu")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@require_auth
async def filter_week_callback(callback: types.CallbackQuery, user, session):
    """Заявки за неделю"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return

    week_ago = datetime.utcnow() - timedelta(days=7)
    stmt = select(Request).where(
        Request.created_at >= week_ago
    ).order_by(Request.created_at.desc())
    
    result = await session.execute(stmt)
    requests = result.scalars().all()

    text = format_request_list(requests, f"Заявки за неделю ({len(requests)})")
    keyboard = get_back_keyboard("admin_filters_menu")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@require_auth
async def admin_stats_callback(callback: types.CallbackQuery, user, session):
    """Статистика с полезными советами для завхоза"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return

    # Получаем метрики
    open_count = await session.scalar(
        select(func.count(Request.id)).where(Request.status == Status.OPEN)
    ) or 0
    
    in_progress_count = await session.scalar(
        select(func.count(Request.id)).where(Request.status == Status.IN_PROGRESS)
    ) or 0
    
    completed_today = await session.scalar(
        select(func.count(Request.id)).where(
            and_(
                Request.status == Status.COMPLETED,
                func.date(Request.completed_at) == func.date(datetime.utcnow())
            )
        )
    ) or 0
    
    total = await session.scalar(select(func.count(Request.id))) or 0
    completed = await session.scalar(
        select(func.count(Request.id)).where(Request.status == Status.COMPLETED)
    ) or 0

    text = "📊 <b>СТАТИСТИКА РАБОТЫ</b>\n\n"
    text += "📋 <b>Текущая ситуация:</b>\n"
    text += f"  📭 Ожидают: <b>{open_count}</b>\n"
    text += f"  ⚙️ В работе: <b>{in_progress_count}</b>\n"
    text += f"  ✅ Выполнено сегодня: <b>{completed_today}</b>\n\n"
    
    text += "📈 <b>Всего:</b>\n"
    text += f"  Заявок: {total} | Выполнено: {completed}\n\n"
    
    # Полезные советы
    total_active = open_count + in_progress_count
    if total_active > 15:
        text += "⚠️ <b>Много работы!</b> Рассмотрите распределение.\n"
    elif total_active > 10:
        text += "💪 <b>Хороший темп!</b> Продолжайте так же.\n"
    elif total_active > 0:
        text += "✅ <b>Отлично!</b> Работа идет хорошо.\n"
    else:
        text += "🎉 <b>Поздравляем!</b> Все заявки обработаны!\n"

    keyboard = get_back_keyboard("back_to_admin")
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@require_auth
async def admin_archive_callback(callback: types.CallbackQuery, user, session):
    """Архив выполненных заявок"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return

    stmt = select(Request).where(
        Request.status == Status.COMPLETED
    ).order_by(Request.completed_at.desc()).limit(50)
    
    result = await session.execute(stmt)
    requests = result.scalars().all()

    text = format_request_list(requests, "Архив (последние 50 заявок)")
    keyboard = get_back_keyboard("back_to_admin")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@require_auth
async def admin_export_menu_callback(callback: types.CallbackQuery, user, session):
    """Меню экспорта"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return

    keyboard = get_admin_export_menu_keyboard()
    await callback.message.edit_text(
        "📤 <b>ЭКСПОРТ</b>\n\nВыберите формат отчета:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@require_auth
async def export_month_callback(callback: types.CallbackQuery, user, session):
    """Экспорт отчета за месяц"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return

    try:
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        stmt = select(Request).where(
            Request.created_at >= month_ago
        ).order_by(Request.created_at.desc())
        
        result = await session.execute(stmt)
        requests = result.scalars().all()

        if not requests:
            await callback.answer("Нет данных за последний месяц")
            return

        # Создаем CSV отчет
        report_lines = [
            "Отчет по заявкам за последний месяц",
            f"Период: {month_ago.strftime('%d.%m.%Y')} - {datetime.utcnow().strftime('%d.%m.%Y')}",
            f"Всего заявок: {len(requests)}",
            "",
            "ID;Дата;Приоритет;Статус;Заголовок;Локация"
        ]
        
        for req in requests:
            line = f"{req.id};{req.created_at.strftime('%d.%m.%Y %H:%M')};{req.priority.value};{req.status.value};{req.title};{req.location}"
            report_lines.append(line)
        
        filename = f"monthly_report_{datetime.now().strftime('%Y%m%d')}.csv"
        with open(filename, 'w', encoding='utf-8-sig') as f:
            f.write("\n".join(report_lines))

        document = FSInputFile(filename)
        await callback.message.reply_document(
            document=document,
            caption="📊 Отчет по заявкам за месяц"
        )
        
        import os
        os.remove(filename)
        
    except Exception as e:
        logger.error(f"Export error: {e}", exc_info=True)
        await callback.answer(f"Ошибка экспорта: {str(e)}", show_alert=True)


@require_auth
async def export_stats_callback(callback: types.CallbackQuery, user, session):
    """Экспорт статистики"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return

    try:
        # Собираем статистику
        stats_lines = [
            "СТАТИСТИКА РАБОТЫ",
            f"Отчет от: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            ""
        ]
        
        total = await session.scalar(select(func.count(Request.id))) or 0
        completed = await session.scalar(select(func.count(Request.id)).where(Request.status == Status.COMPLETED)) or 0
        rejected = await session.scalar(select(func.count(Request.id)).where(Request.status == Status.REJECTED)) or 0
        
        stats_lines.extend([
            "ОБЩАЯ СТАТИСТИКА:",
            f"Всего заявок: {total}",
            f"Выполнено: {completed}",
            f"Отклонено: {rejected}",
            ""
        ])
        
        # По приоритетам
        stats_lines.append("ПО ПРИОРИТЕТАМ:")
        for priority in [Priority.HIGH, Priority.MEDIUM, Priority.LOW]:
            count = await session.scalar(
                select(func.count(Request.id)).where(Request.priority == priority)
            ) or 0
            stats_lines.append(f"{priority.value}: {count}")
        
        stats_lines.append("")
        
        # По статусам
        stats_lines.append("ПО СТАТУСАМ:")
        for status in [Status.OPEN, Status.IN_PROGRESS, Status.COMPLETED, Status.REJECTED]:
            count = await session.scalar(
                select(func.count(Request.id)).where(Request.status == status)
            ) or 0
            stats_lines.append(f"{status.value}: {count}")
        
        filename = f"stats_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(stats_lines))

        document = FSInputFile(filename)
        await callback.message.reply_document(
            document=document,
            caption="📊 Статистический отчет"
        )
        
        import os
        os.remove(filename)
        
    except Exception as e:
        logger.error(f"Stats export error: {e}", exc_info=True)
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)


@require_auth
async def export_all_callback(callback: types.CallbackQuery, user, session):
    """Экспорт всех заявок CSV"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return

    try:
        stmt = select(Request).order_by(Request.created_at.desc())
        result = await session.execute(stmt)
        requests = result.scalars().all()

        if not requests:
            await callback.answer("Нет заявок для экспорта")
            return

        # CSV
        report_lines = [
            "ID;Дата создания;Дата завершения;Приоритет;Статус;Заголовок;Описание;Локация;Пользователь"
        ]
        
        for req in requests:
            line = f'{req.id};{req.created_at.strftime("%d.%m.%Y %H:%M")};{req.completed_at.strftime("%d.%m.%Y %H:%M") if req.completed_at else ""};{req.priority.value};{req.status.value};"{req.title}";"{req.description}";{req.location};{req.user.username or ""}'
            report_lines.append(line)
        
        filename = f"all_requests_{datetime.now().strftime('%Y%m%d')}.csv"
        with open(filename, 'w', encoding='utf-8-sig') as f:
            f.write("\n".join(report_lines))

        document = FSInputFile(filename)
        await callback.message.reply_document(
            document=document,
            caption=f"📋 Все заявки ({len(requests)})"
        )
        
        import os
        os.remove(filename)
        
    except Exception as e:
        logger.error(f"All export error: {e}", exc_info=True)
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)


@require_auth
async def back_to_admin_callback(callback: types.CallbackQuery, user, session):
    """Возврат в админ-панель"""
    await admin_panel_callback(callback, user=user, session=session)


def register_admin_handlers(dp):
    """Регистрация обработчиков админа"""
    dp.callback_query.register(admin_panel_callback, F.data == "admin_panel")
    dp.callback_query.register(admin_panel_callback, F.data == "back_to_admin")
    
    # Основные функции
    dp.callback_query.register(admin_open_requests_callback, F.data == "admin_open_requests")
    dp.callback_query.register(admin_stats_callback, F.data == "admin_stats")
    dp.callback_query.register(admin_archive_callback, F.data == "admin_archive")
    
    # Фильтры
    dp.callback_query.register(admin_filters_menu_callback, F.data == "admin_filters_menu")
    dp.callback_query.register(filter_priority_callback, F.data.startswith("filter_priority_"))
    dp.callback_query.register(filter_status_callback, F.data.startswith("filter_status_"))
    dp.callback_query.register(filter_today_callback, F.data == "filter_today")
    dp.callback_query.register(filter_week_callback, F.data == "filter_week")
    
    # Экспорт
    dp.callback_query.register(admin_export_menu_callback, F.data == "admin_export_menu")
    dp.callback_query.register(export_month_callback, F.data == "export_month")
    dp.callback_query.register(export_stats_callback, F.data == "export_stats")
    dp.callback_query.register(export_all_callback, F.data == "export_all")
