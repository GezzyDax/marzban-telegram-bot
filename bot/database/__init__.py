"""Database package"""

from .models import Base, User, AdminLog, NotificationSettings, SentNotifications
from .crud import (
    get_user_by_telegram_id,
    get_user_by_marzban_username,
    create_user,
    delete_user,
    list_users,
    update_user_admin_status,
    log_admin_action,
    get_admin_logs,
    search_users,
    get_notification_settings,
    update_notification_settings,
    check_notification_sent,
    mark_notification_sent,
)

__all__ = [
    "Base",
    "User",
    "AdminLog",
    "NotificationSettings",
    "SentNotifications",
    "get_user_by_telegram_id",
    "get_user_by_marzban_username",
    "create_user",
    "delete_user",
    "list_users",
    "update_user_admin_status",
    "log_admin_action",
    "get_admin_logs",
    "search_users",
    "get_notification_settings",
    "update_notification_settings",
    "check_notification_sent",
    "mark_notification_sent",
]
