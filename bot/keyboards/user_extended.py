"""Extended user keyboards"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_user_main_menu_extended() -> InlineKeyboardMarkup:
    """Extended user main menu"""
    buttons = [
        [InlineKeyboardButton(text="📊 Моя подписка", callback_data="my_subscription")],
        [InlineKeyboardButton(text="🔗 Получить ссылку", callback_data="get_link")],
        [InlineKeyboardButton(text="ℹ️ Инструкция", callback_data="instruction_menu")],
        [InlineKeyboardButton(text="❓ Проблема с подключением", callback_data="user_feedback_start")],
        [InlineKeyboardButton(text="💬 Поддержка", url="https://t.me/hotloqer")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_subscription_submenu() -> InlineKeyboardMarkup:
    """Subscription submenu"""
    buttons = [
        [InlineKeyboardButton(text="📈 Детальная статистика", callback_data="subscription_detailed")],
        [InlineKeyboardButton(text="🔔 Настроить уведомления", callback_data="notification_settings")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_instruction_menu() -> InlineKeyboardMarkup:
    """Instruction submenu"""
    buttons = [
        [InlineKeyboardButton(text="📱 Для телефона", callback_data="instruction_mobile")],
        [InlineKeyboardButton(text="💻 Для компьютера", callback_data="instruction_desktop")],
        [InlineKeyboardButton(text="❓ FAQ", callback_data="instruction_faq")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_notification_settings_keyboard(
    notify_expiry: bool = True, notify_traffic: bool = True, notify_status: bool = True
) -> InlineKeyboardMarkup:
    """Notification settings keyboard with toggles"""
    expiry_text = "🔔 Истечение подписки" if notify_expiry else "🔕 Истечение подписки"
    traffic_text = "🔔 Превышение трафика" if notify_traffic else "🔕 Превышение трафика"
    status_text = "🔔 Смена статуса" if notify_status else "🔕 Смена статуса"

    buttons = [
        [InlineKeyboardButton(text=expiry_text, callback_data="toggle_notify_expiry")],
        [InlineKeyboardButton(text=traffic_text, callback_data="toggle_notify_traffic")],
        [InlineKeyboardButton(text=status_text, callback_data="toggle_notify_status")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="my_subscription")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
