from aiogram import types, F
from sqlalchemy import select, func, and_
from database.connection import get_db
from models import Request, Status, Priority
from utils.auth import require_auth
from utils.keyboard import (
    get_admin_panel_keyboard, get_filter_keyboard, get_request_actions_keyboard, 
    get_back_keyboard, get_priority_filter_keyboard, get_status_filter_keyboard,
    get_search_filter_keyboard
)
from utils.messages import format_request_list, format_request_info, get_stats_message
from utils.export import export_requests_to_csv, get_requests_for_export
from aiogram.types import FSInputFile
from datetime import datetime, timedelta

@require_auth
async def admin_panel_callback(callback: types.CallbackQuery, user, session):
    """Панель администратора"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа к этой функции")
        return

    keyboard = get_admin_panel_keyboard()
    await callback.message.edit_text(
        "👑 <b>Панель завхоза</b>\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@require_auth
async def admin_open_requests_callback(callback: types.CallbackQuery, user, session):
    """Показать открытые заявки"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа к этой функции")
        return

    stmt = select(Request).where(Request.status.in_([Status.OPEN, Status.IN_PROGRESS])).order_by(Request.priority.desc(), Request.created_at.asc())
    result = await session.execute(stmt)
    requests = result.scalars().all()

    if not requests:
        text = "📭 Открытых заявок нет."
        keyboard = get_admin_panel_keyboard()
    else:
        text = format_request_list(requests, "Открытые заявки")
        keyboard = get_filter_keyboard()

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@require_auth
async def admin_stats_callback(callback: types.CallbackQuery, user, session):
    """Показать статистику"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа к этой функции")
        return

    # Общее количество заявок
    stmt_total = select(func.count(Request.id))
    result_total = await session.execute(stmt_total)
    total_requests = result_total.scalar()

    # Количество выполненных заявок
    stmt_completed = select(func.count(Request.id)).where(Request.status == Status.COMPLETED)
    result_completed = await session.execute(stmt_completed)
    completed_requests = result_completed.scalar()

    # Среднее время выполнения (в часах)
    stmt_avg_time = select(
        func.avg(
            func.extract('epoch', Request.completed_at) - func.extract('epoch', Request.created_at)
        ) / 3600
    ).where(Request.status == Status.COMPLETED)
    result_avg_time = await session.execute(stmt_avg_time)
    avg_completion_time = result_avg_time.scalar()

    text = get_stats_message(total_requests, completed_requests, avg_completion_time)
    keyboard = get_back_keyboard("back_to_admin")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@require_auth
async def admin_archive_callback(callback: types.CallbackQuery, user, session):
    """Показать архив выполненных заявок"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа к этой функции")
        return

    stmt = select(Request).where(Request.status == Status.COMPLETED).order_by(Request.completed_at.desc()).limit(50)
    result = await session.execute(stmt)
    requests = result.scalars().all()

    if not requests:
        text = "📭 Архив пуст."
    else:
        text = format_request_list(requests, "Архив выполненных заявок")

    keyboard = get_back_keyboard("back_to_admin")
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@require_auth
async def back_to_admin_callback(callback: types.CallbackQuery, user, session):
    """Возврат в панель администратора"""
    await admin_panel_callback(callback, user, session)

@require_auth
async def export_csv_callback(callback: types.CallbackQuery, user, session):
    """Экспорт заявок в CSV"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа к этой функции")
        return

    # Получаем все выполненные заявки за последний месяц
    date_from = datetime.utcnow() - timedelta(days=30)
    requests = await get_requests_for_export(Status.COMPLETED, date_from)

    if not requests:
        await callback.answer("Нет данных для экспорта")
        return

    # Создаем CSV
    csv_content = await export_requests_to_csv(requests)

    # Создаем временный файл
    filename = f"requests_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, 'w', encoding='utf-8-sig') as f:
        f.write(csv_content)

    # Отправляем файл
    document = FSInputFile(filename)
    await callback.message.reply_document(
        document=document,
        caption="📊 Экспорт выполненных заявок за последний месяц"
    )

    # Удаляем временный файл
    import os
    os.remove(filename)

    await callback.answer()

@require_auth
async def filter_priority_callback(callback: types.CallbackQuery, user, session):
    """Фильтр по приоритету"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return
    
    priority = callback.data.split("_")[-1]
    
    if priority == "ALL":
        stmt = select(Request).where(Request.status.in_([Status.OPEN, Status.IN_PROGRESS])).order_by(Request.priority.desc(), Request.created_at.asc())
    else:
        stmt = select(Request).where(
            and_(
                Request.status.in_([Status.OPEN, Status.IN_PROGRESS]),
                Request.priority == Priority[priority]
            )
        ).order_by(Request.created_at.asc())
    
    result = await session.execute(stmt)
    requests = result.scalars().all()
    
    priority_text = {
        "HIGH": "🔴 ВЫСОКИЙ",
        "MEDIUM": "🟡 СРЕДНИЙ", 
        "LOW": "🟢 НИЗКИЙ",
        "ALL": "📋 ВСЕ"
    }
    
    if not requests:
        text = f"📭 Заявок с приоритетом {priority_text.get(priority, priority)} нет."
        keyboard = get_back_keyboard("back_to_admin")
    else:
        text = format_request_list(requests, f"Заявки: {priority_text.get(priority, priority)} приоритет")
        keyboard = get_back_keyboard("back_to_admin")
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@require_auth
async def filter_status_callback(callback: types.CallbackQuery, user, session):
    """Фильтр по статусу"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return
    
    status_name = callback.data.split("_")[-1]
    
    if status_name == "ALL":
        stmt = select(Request).order_by(Request.created_at.desc())
    else:
        stmt = select(Request).where(Request.status == Status[status_name]).order_by(Request.created_at.desc())
    
    result = await session.execute(stmt)
    requests = result.scalars().all()
    
    status_text = {
        "OPEN": "📭 ОТКРЫТЫЕ",
        "IN_PROGRESS": "⚙️ В РАБОТЕ",
        "COMPLETED": "✅ ВЫПОЛНЕНО",
        "REJECTED": "❌ ОТКЛОНЕНО",
        "ALL": "📋 ВСЕ"
    }
    
    if not requests:
        text = f"📭 Заявок со статусом {status_text.get(status_name, status_name)} нет."
        keyboard = get_back_keyboard("back_to_admin")
    else:
        text = format_request_list(requests, f"Заявки: {status_text.get(status_name, status_name)}")
        keyboard = get_back_keyboard("back_to_admin")
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@require_auth
async def show_advanced_search_callback(callback: types.CallbackQuery, user, session):
    """Показать меню расширенного поиска"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return
    
    keyboard = get_search_filter_keyboard()
    await callback.message.edit_text(
        "🔍 <b>Расширенный поиск</b>\n\nВыберите критерий:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@require_auth
async def search_by_date_callback(callback: types.CallbackQuery, user, session):
    """Поиск по дате (последние 7 дней)"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return
    
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    stmt = select(Request).where(Request.created_at >= seven_days_ago).order_by(Request.created_at.desc())
    result = await session.execute(stmt)
    requests = result.scalars().all()
    
    if not requests:
        text = "📭 Заявок за последние 7 дней нет."
        keyboard = get_back_keyboard("back_to_admin")
    else:
        text = format_request_list(requests, f"Заявки за последние 7 дней ({len(requests)} шт.)")
        keyboard = get_back_keyboard("back_to_admin")
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@require_auth
async def admin_advanced_analytics_callback(callback: types.CallbackQuery, user, session):
    """Показать расширенную аналитику"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return
    
    try:
        from utils.analytics import RequestAnalytics, format_analytics_report
        
        report = await RequestAnalytics.get_full_report(session)
        text = format_analytics_report(report)
        
        keyboard = get_back_keyboard("back_to_admin")
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        await callback.answer(f"❌ Ошибка загрузки аналитики: {str(e)}", show_alert=True)
    
    await callback.answer()

@require_auth
async def admin_priority_filter_callback(callback: types.CallbackQuery, user, session):
    """Показать меню фильтра по приоритету"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return
    
    from utils.keyboard import get_priority_filter_keyboard
    keyboard = get_priority_filter_keyboard()
    await callback.message.edit_text(
        "🎯 <b>Фильтр по приоритету</b>\n\nВыберите приоритет:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@require_auth
async def admin_status_filter_callback(callback: types.CallbackQuery, user, session):
    """Показать меню фильтра по статусу"""
    if user.role != "admin":
        await callback.answer("У вас нет доступа")
        return
    
    from utils.keyboard import get_status_filter_keyboard
    keyboard = get_status_filter_keyboard()
    await callback.message.edit_text(
        "📊 <b>Фильтр по статусу</b>\n\nВыберите статус:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

def register_admin_handlers(dp):
    """Регистрация обработчиков администратора"""
    dp.callback_query.register(admin_panel_callback, F.data == "admin_panel")
    dp.callback_query.register(admin_open_requests_callback, F.data == "admin_open_requests")
    dp.callback_query.register(admin_stats_callback, F.data == "admin_stats")
    dp.callback_query.register(admin_archive_callback, F.data == "admin_archive")
    dp.callback_query.register(export_csv_callback, F.data == "export_csv")
    dp.callback_query.register(back_to_admin_callback, F.data == "back_to_admin")
    dp.callback_query.register(admin_advanced_analytics_callback, F.data == "admin_advanced_analytics")
    dp.callback_query.register(admin_priority_filter_callback, F.data == "admin_priority_filter")
    dp.callback_query.register(admin_status_filter_callback, F.data == "admin_status_filter")
    
    # Регистрируем обработчики фильтров
    register_admin_filters_handlers(dp)

def register_admin_filters_handlers(dp):
    """Регистрация обработчиков фильтров"""
    dp.callback_query.register(filter_priority_callback, F.data.startswith("filter_priority_"))
    dp.callback_query.register(filter_status_callback, F.data.startswith("filter_status_"))
    dp.callback_query.register(show_advanced_search_callback, F.data == "search_menu")
    dp.callback_query.register(search_by_date_callback, F.data == "search_date")