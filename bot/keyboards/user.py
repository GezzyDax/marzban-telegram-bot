"""User keyboards"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_user_main_menu() -> InlineKeyboardMarkup:
    """Get user main menu keyboard"""
    buttons = [
        [InlineKeyboardButton(text="📊 Моя подписка", callback_data="my_subscription")],
        [InlineKeyboardButton(text="🔗 Получить ссылку", callback_data="get_link")],
        [InlineKeyboardButton(text="ℹ️ Инструкция", callback_data="instruction")],
        [InlineKeyboardButton(text="💬 Поддержка", url="https://t.me/hotloqer")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_button() -> InlineKeyboardMarkup:
    """Get back button keyboard"""
    buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_instruction_keyboard() -> InlineKeyboardMarkup:
    """Get instruction keyboard with download links"""
    buttons = [
        [InlineKeyboardButton(text="📱 V2Box для iOS", url="https://apps.apple.com/app/v2box-v2ray-client/id6446814690")],
        [InlineKeyboardButton(text="📱 V2Box для Android", url="https://play.google.com/store/search?q=v2box&c=apps")],
        [InlineKeyboardButton(text="💻 NekoBox для ПК", url="https://getnekobox.com/en/")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
