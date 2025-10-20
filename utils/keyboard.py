from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from models import Priority


def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Главное меню - дружелюбное и понятное"""
    if is_admin:
        # Меню для завхоза - фокус на управлении заявками
        keyboard = [
            [InlineKeyboardButton(text="👑 ПАНЕЛЬ ЗАВХОЗА", callback_data="admin_panel")],
            [InlineKeyboardButton(text="📋 Мои заявки (как пользователь)", callback_data="my_requests")],
            [InlineKeyboardButton(text="ℹ️ Справка", callback_data="help_menu")],
        ]
    else:
        # Меню для пользователя - фокус на подачу заявок
        keyboard = [
            [InlineKeyboardButton(text="🆘 ПОДАТЬ ЗАЯВКУ НА РЕМОНТ", callback_data="create_request")],
            [InlineKeyboardButton(text="📋 Мои заявки", callback_data="my_requests")],
            [InlineKeyboardButton(text="❓ Как это работает?", callback_data="help_user")],
        ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_user_help_keyboard() -> InlineKeyboardMarkup:
    """Справка для пользователя - как пользоваться ботом"""
    keyboard = [
        [InlineKeyboardButton(text="📸 Как отправить фото?", callback_data="help_photo")],
        [InlineKeyboardButton(text="⏱️ Как долго ждать?", callback_data="help_timing")],
        [InlineKeyboardButton(text="🚫 Что если не помогло?", callback_data="help_not_fixed")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_help_keyboard() -> InlineKeyboardMarkup:
    """Справка для завхоза"""
    keyboard = [
        [InlineKeyboardButton(text="📊 Как использовать панель?", callback_data="help_admin_panel")],
        [InlineKeyboardButton(text="📤 Как экспортировать отчет?", callback_data="help_export")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_admin")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_priority_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора приоритета"""
    keyboard = [
        [InlineKeyboardButton(text="🔴 Высокий", callback_data=f"priority_{Priority.HIGH.value}")],
        [InlineKeyboardButton(text="🟡 Средний", callback_data=f"priority_{Priority.MEDIUM.value}")],
        [InlineKeyboardButton(text="🟢 Низкий", callback_data=f"priority_{Priority.LOW.value}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_request_actions_keyboard(request_id: int, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура действий с заявкой"""
    keyboard = [
        [InlineKeyboardButton(text="📝 Добавить комментарий", callback_data=f"add_comment_{request_id}")],
        [InlineKeyboardButton(text="📎 Добавить фото/документ", callback_data=f"add_file_{request_id}")],
    ]
    if is_admin:
        keyboard.append([
            InlineKeyboardButton(text="✅ Взять в работу", callback_data=f"take_request_{request_id}"),
            InlineKeyboardButton(text="✔️ Выполнить", callback_data=f"complete_request_{request_id}"),
        ])
        keyboard.append([
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_request_{request_id}"),
        ])
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_requests")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Упрощённая панель завхоза - только необходимые функции"""
    keyboard = [
        [InlineKeyboardButton(text="📋 Открытые заявки", callback_data="admin_open_requests")],
        [InlineKeyboardButton(text="🎯 Фильры", callback_data="admin_filters_menu")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📁 Архив", callback_data="admin_archive")],
        [InlineKeyboardButton(text="📤 Экспорт", callback_data="admin_export_menu")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_filters_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню фильтров для завхоза"""
    keyboard = [
        [InlineKeyboardButton(text="🔴 Высокий приоритет", callback_data="filter_priority_HIGH")],
        [InlineKeyboardButton(text="🟡 Средний приоритет", callback_data="filter_priority_MEDIUM")],
        [InlineKeyboardButton(text="⚙️ В работе", callback_data="filter_status_IN_PROGRESS")],
        [InlineKeyboardButton(text="📅 Сегодня", callback_data="filter_today")],
        [InlineKeyboardButton(text="📅 На неделю", callback_data="filter_week")],
        [InlineKeyboardButton(text="📋 Все открытые", callback_data="admin_open_requests")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_admin")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_export_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню экспорта для завхоза"""
    keyboard = [
        [InlineKeyboardButton(text="📊 Отчет за месяц", callback_data="export_month")],
        [InlineKeyboardButton(text="📈 Статистика", callback_data="export_stats")],
        [InlineKeyboardButton(text="📋 Все заявки CSV", callback_data="export_all")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_admin")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_filter_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура фильтров"""
    keyboard = [
        [InlineKeyboardButton(text="📅 По дате", callback_data="filter_date")],
        [InlineKeyboardButton(text="🏢 По местоположению", callback_data="filter_location")],
        [InlineKeyboardButton(text="🔴 По приоритету", callback_data="filter_priority")],
        [InlineKeyboardButton(text="👤 По пользователю", callback_data="filter_user")],
        [InlineKeyboardButton(text="🔄 Сбросить фильтры", callback_data="reset_filters")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_admin")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_priority_filter_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура фильтра по приоритету"""
    keyboard = [
        [InlineKeyboardButton(text="🔴 ВЫСОКИЙ", callback_data="filter_priority_HIGH")],
        [InlineKeyboardButton(text="🟡 СРЕДНИЙ", callback_data="filter_priority_MEDIUM")],
        [InlineKeyboardButton(text="🟢 НИЗКИЙ", callback_data="filter_priority_LOW")],
        [InlineKeyboardButton(text="📋 ВСЕ ПРИОРИТЕТЫ", callback_data="filter_priority_ALL")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_admin")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_status_filter_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура фильтра по статусу"""
    keyboard = [
        [InlineKeyboardButton(text="📭 ОТКРЫТЫЕ", callback_data="filter_status_OPEN")],
        [InlineKeyboardButton(text="⚙️ В РАБОТЕ", callback_data="filter_status_IN_PROGRESS")],
        [InlineKeyboardButton(text="✅ ВЫПОЛНЕНО", callback_data="filter_status_COMPLETED")],
        [InlineKeyboardButton(text="❌ ОТКЛОНЕНО", callback_data="filter_status_REJECTED")],
        [InlineKeyboardButton(text="📋 ВСЕ СТАТУСЫ", callback_data="filter_status_ALL")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_admin")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_search_filter_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура расширенного поиска"""
    keyboard = [
        [InlineKeyboardButton(text="🎯 По приоритету", callback_data="search_priority")],
        [InlineKeyboardButton(text="📊 По статусу", callback_data="search_status")],
        [InlineKeyboardButton(text="🗓️ По дате", callback_data="search_date")],
        [InlineKeyboardButton(text="📍 По локации", callback_data="search_location")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_admin")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_keyboard(callback_data: str = "back") -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой назад"""
    keyboard = [[InlineKeyboardButton(text="⬅️ Назад", callback_data=callback_data)]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
