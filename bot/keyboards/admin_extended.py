"""Extended admin keyboards with hierarchical navigation"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_main_menu_extended() -> InlineKeyboardMarkup:
    """Get extended admin main menu"""
    buttons = [
        [InlineKeyboardButton(text="👥 Управление пользователями", callback_data="admin_users_menu")],
        [InlineKeyboardButton(text="👑 Управление правами", callback_data="admin_permissions_menu")],
        [InlineKeyboardButton(text="📊 Статистика и отчёты", callback_data="admin_stats_menu")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings_menu")],
        [InlineKeyboardButton(text="ℹ️ О боте", callback_data="admin_about")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_users_management_menu() -> InlineKeyboardMarkup:
    """Submenu for user management"""
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить пользователя", callback_data="admin_add_user_start")],
        [InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="admin_search_user_start")],
        [InlineKeyboardButton(text="📋 Список пользователей", callback_data="admin_list_users")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_permissions_management_menu() -> InlineKeyboardMarkup:
    """Submenu for permissions management"""
    buttons = [
        [InlineKeyboardButton(text="⬆️ Назначить админом", callback_data="admin_make_admin_start")],
        [InlineKeyboardButton(text="⬇️ Снять админа", callback_data="admin_revoke_admin_start")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_stats_menu() -> InlineKeyboardMarkup:
    """Submenu for statistics"""
    buttons = [
        [InlineKeyboardButton(text="📈 Общая статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📋 Логи действий", callback_data="admin_logs")],
        [InlineKeyboardButton(text="💾 Экспорт данных", callback_data="admin_export")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_settings_menu() -> InlineKeyboardMarkup:
    """Submenu for settings"""
    buttons = [
        [InlineKeyboardButton(text="🔔 Уведомления", callback_data="admin_notifications_settings")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast_start")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_button() -> InlineKeyboardMarkup:
    """Cancel button for FSM dialogs"""
    buttons = [[InlineKeyboardButton(text="❌ Отмена", callback_data="fsm_cancel")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirmation_keyboard(confirm_data: str, cancel_data: str = "fsm_cancel") -> InlineKeyboardMarkup:
    """Confirmation keyboard"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=confirm_data),
            InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_data),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_user_search_result_keyboard(telegram_id: int, current_status: str) -> InlineKeyboardMarkup:
    """Keyboard for user search result with status toggle"""
    # Determine toggle button text based on current status
    if current_status == "active":
        status_button_text = "🔴 Отключить"
        status_button_data = f"toggle_status:{telegram_id}:disabled"
    else:
        status_button_text = "🟢 Включить"
        status_button_data = f"toggle_status:{telegram_id}:active"

    buttons = [
        [InlineKeyboardButton(text=status_button_text, callback_data=status_button_data)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
