"""Admin keyboards"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_main_menu() -> InlineKeyboardMarkup:
    """Get admin main menu keyboard"""
    buttons = [
        [InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_list_users")],
        [InlineKeyboardButton(text="📋 Логи действий", callback_data="admin_logs")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_user_list_keyboard(page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Get user list keyboard with pagination"""
    buttons = []

    # Pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Пред", callback_data=f"admin_users_page:{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="След ▶️", callback_data=f"admin_users_page:{page+1}"))

    if nav_buttons:
        buttons.append(nav_buttons)

    # Back button
    buttons.append([InlineKeyboardButton(text="🔙 Админ меню", callback_data="admin_menu")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_logs_keyboard(page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Get logs keyboard with pagination"""
    buttons = []

    # Pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Пред", callback_data=f"admin_logs_page:{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="След ▶️", callback_data=f"admin_logs_page:{page+1}"))

    if nav_buttons:
        buttons.append(nav_buttons)

    # Back button
    buttons.append([InlineKeyboardButton(text="🔙 Админ меню", callback_data="admin_menu")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
