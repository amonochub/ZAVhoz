# Обработчики команд и callback'ов
from .start import register_start_handlers
from .menu import register_menu_handlers
from .create_request import register_create_request_handlers
from .admin import register_admin_handlers
from .request_actions import register_request_actions_handlers
from .files import register_file_handlers

__all__ = [
    "register_start_handlers",
    "register_menu_handlers",
    "register_create_request_handlers",
    "register_admin_handlers",
    "register_request_actions_handlers",
    "register_file_handlers"
]