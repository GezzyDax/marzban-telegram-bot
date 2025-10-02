"""Simplified keyboards with ReplyKeyboardMarkup for better UX"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButtonRequestUsers


def get_main_user_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Main user keyboard (always visible at bottom)"""
    buttons = [
        [KeyboardButton(text="📊 Подписка"), KeyboardButton(text="🔗 Ссылка")],
        [KeyboardButton(text="ℹ️ Инструкция"), KeyboardButton(text="⚙️ Настройки")],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="👑 Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_main_admin_keyboard() -> ReplyKeyboardMarkup:
    """Main admin keyboard (always visible at bottom)"""
    buttons = [
        [KeyboardButton(text="➕ Добавить"), KeyboardButton(text="📋 Список")],
        [KeyboardButton(text="🔍 Найти"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="👤 Мой аккаунт")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_request_user_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard to request user selection"""
    button = KeyboardButton(
        text="👤 Выбрать пользователя",
        request_users=KeyboardButtonRequestUsers(request_id=1, user_is_bot=False)
    )
    buttons = [
        [button],
        [KeyboardButton(text="❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Simple cancel keyboard"""
    buttons = [[KeyboardButton(text="❌ Отмена")]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_confirmation_inline(confirm_callback: str) -> InlineKeyboardMarkup:
    """Inline confirmation buttons"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=confirm_callback),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_subscription_inline() -> InlineKeyboardMarkup:
    """Inline buttons for subscription details"""
    buttons = [
        [InlineKeyboardButton(text="🔔 Настройки уведомлений", callback_data="notification_settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_notification_toggle_inline(notify_expiry: bool, notify_traffic: bool) -> InlineKeyboardMarkup:
    """Toggle notification settings"""
    expiry_text = "🔔 Уведомления об истечении" if notify_expiry else "🔕 Уведомления об истечении"
    traffic_text = "🔔 Уведомления о трафике" if notify_traffic else "🔕 Уведомления о трафике"

    buttons = [
        [InlineKeyboardButton(text=expiry_text, callback_data="toggle_notify_expiry")],
        [InlineKeyboardButton(text=traffic_text, callback_data="toggle_notify_traffic")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_instruction_inline() -> InlineKeyboardMarkup:
    """Download links for VPN clients"""
    buttons = [
        [InlineKeyboardButton(text="📱 V2Box (iOS/Android)", url="https://t.me/v2box_bot")],
        [InlineKeyboardButton(text="💻 NekoBox (Windows/Mac/Linux)", url="https://github.com/MatsuriDayo/nekoray/releases")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_user_list_navigation(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Pagination for user list"""
    buttons = []

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"users_page:{page-1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"users_page:{page+1}"))

    if nav_row:
        buttons.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)
