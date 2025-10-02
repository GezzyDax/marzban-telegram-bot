"""Formatting utilities for beautiful messages"""

from datetime import datetime, timedelta
from typing import Optional


def format_progress_bar(current: int, total: int, length: int = 10) -> str:
    """
    Create a progress bar

    Args:
        current: Current value
        total: Total value
        length: Length of the bar in characters

    Returns:
        Progress bar string like [████████░░] 80%
    """
    if total == 0:
        percentage = 0
    else:
        percentage = min(100, int((current / total) * 100))

    filled = int((percentage / 100) * length)
    empty = length - filled

    bar = "█" * filled + "░" * empty
    return f"[{bar}] {percentage}%"


def format_date_relative(target_date: Optional[datetime]) -> str:
    """
    Format date relative to now

    Args:
        target_date: Target datetime

    Returns:
        String like "до 15 января 2025 (через 14 дней)"
    """
    if not target_date:
        return "не указано"

    now = datetime.now()

    # Remove timezone info for comparison if present
    if target_date.tzinfo is not None:
        target_date = target_date.replace(tzinfo=None)

    delta = target_date - now

    # Format the date
    months_ru = [
        "января",
        "февраля",
        "марта",
        "апреля",
        "мая",
        "июня",
        "июля",
        "августа",
        "сентября",
        "октября",
        "ноября",
        "декабря",
    ]
    formatted_date = f"{target_date.day} {months_ru[target_date.month - 1]} {target_date.year}"

    # Calculate relative time
    days = delta.days
    if days < 0:
        return f"{formatted_date} (истекло {abs(days)} дн. назад)"
    elif days == 0:
        hours = delta.seconds // 3600
        if hours == 0:
            return f"{formatted_date} (истекает сегодня)"
        return f"{formatted_date} (через {hours} ч.)"
    elif days == 1:
        return f"{formatted_date} (завтра)"
    elif days < 7:
        return f"{formatted_date} (через {days} дн.)"
    elif days < 30:
        weeks = days // 7
        return f"{formatted_date} (через {weeks} нед.)"
    else:
        months = days // 30
        return f"{formatted_date} (через {months} мес.)"


def format_traffic_speed(used_bytes: int, days: int) -> str:
    """
    Calculate and format average daily traffic usage

    Args:
        used_bytes: Total bytes used
        days: Number of days

    Returns:
        String like "В среднем 2.5 GB в день"
    """
    if days == 0:
        days = 1

    avg_per_day = used_bytes / days

    if avg_per_day < 1024:
        return f"В среднем {avg_per_day:.1f} B в день"
    elif avg_per_day < 1024**2:
        return f"В среднем {avg_per_day / 1024:.1f} KB в день"
    elif avg_per_day < 1024**3:
        return f"В среднем {avg_per_day / (1024**2):.1f} MB в день"
    else:
        return f"В среднем {avg_per_day / (1024**3):.1f} GB в день"


def format_status_emoji(status: str, expire: Optional[datetime] = None, used: int = 0, limit: int = 0) -> str:
    """
    Get status emoji based on subscription state

    Args:
        status: Subscription status (active/limited/expired/disabled)
        expire: Expiry date
        used: Used traffic
        limit: Traffic limit

    Returns:
        Emoji: 🟢 Active / 🟡 Expiring soon / 🔴 Expired/Limited / ⚫ Disabled
    """
    if status == "disabled":
        return "⚫"

    if status in ["expired", "limited"]:
        return "🔴"

    # Check if expiring soon (within 7 days)
    if expire:
        now = datetime.now()
        if expire.tzinfo is not None:
            expire = expire.replace(tzinfo=None)

        days_left = (expire - now).days
        if days_left < 0:
            return "🔴"
        elif days_left <= 7:
            return "🟡"

    # Check traffic usage
    if limit > 0 and used >= limit * 0.9:
        return "🟡"

    return "🟢"
