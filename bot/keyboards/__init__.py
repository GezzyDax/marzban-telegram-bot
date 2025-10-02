"""Keyboards package"""

from .user import get_user_main_menu, get_back_button, get_instruction_keyboard
from .admin import get_admin_main_menu, get_user_list_keyboard, get_logs_keyboard
from .admin_extended import (
    get_admin_main_menu_extended,
    get_users_management_menu,
    get_permissions_management_menu,
    get_stats_menu,
    get_settings_menu,
    get_cancel_button,
    get_confirmation_keyboard,
)
from .user_extended import (
    get_user_main_menu_extended,
    get_subscription_submenu,
    get_instruction_menu,
    get_notification_settings_keyboard,
)

__all__ = [
    # Legacy
    "get_user_main_menu",
    "get_back_button",
    "get_instruction_keyboard",
    "get_admin_main_menu",
    "get_user_list_keyboard",
    "get_logs_keyboard",
    # Extended admin
    "get_admin_main_menu_extended",
    "get_users_management_menu",
    "get_permissions_management_menu",
    "get_stats_menu",
    "get_settings_menu",
    "get_cancel_button",
    "get_confirmation_keyboard",
    # Extended user
    "get_user_main_menu_extended",
    "get_subscription_submenu",
    "get_instruction_menu",
    "get_notification_settings_keyboard",
]
