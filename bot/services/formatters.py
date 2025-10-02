"""Message formatting utilities"""

from datetime import datetime
from typing import Optional


def format_bytes(bytes_value: Optional[int]) -> str:
    """Format bytes to human-readable string"""
    if bytes_value is None:
        return "∞"

    if bytes_value == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    value = float(bytes_value)

    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1

    return f"{value:.2f} {units[unit_index]}"


def format_date(dt: Optional[datetime]) -> str:
    """Format datetime to readable string"""
    if dt is None:
        return "∞"
    return dt.strftime("%d.%m.%Y %H:%M")


def format_user_info(username: str, telegram_id: int, marzban_username: str, is_admin: bool) -> str:
    """Format user info for display"""
    admin_badge = "👑 " if is_admin else ""
    return (
        f"{admin_badge}<b>{username}</b>\n"
        f"├ Telegram ID: <code>{telegram_id}</code>\n"
        f"└ Marzban: <code>{marzban_username}</code>"
    )


def format_subscription_status(
    username: str,
    status: str,
    used_traffic: int,
    data_limit: Optional[int],
    expire: Optional[datetime],
) -> str:
    """Format subscription status message"""
    status_emoji = {
        "active": "✅",
        "limited": "⚠️",
        "expired": "❌",
        "disabled": "🚫",
    }

    emoji = status_emoji.get(status, "❓")
    status_text = {
        "active": "Активна",
        "limited": "Ограничена",
        "expired": "Истекла",
        "disabled": "Отключена",
    }.get(status, status.capitalize())

    used = format_bytes(used_traffic)
    limit = format_bytes(data_limit) if data_limit else "∞"

    # Calculate percentage if limit is set
    percentage = ""
    if data_limit and data_limit > 0:
        percent = (used_traffic / data_limit) * 100
        percentage = f" ({percent:.1f}%)"

    expire_text = format_date(expire)

    return (
        f"📊 <b>Информация о подписке</b>\n\n"
        f"👤 Пользователь: <code>{username}</code>\n"
        f"{emoji} Статус: <b>{status_text}</b>\n\n"
        f"📈 Использовано: <b>{used}</b> / {limit}{percentage}\n"
        f"📅 Действует до: <b>{expire_text}</b>"
    )
