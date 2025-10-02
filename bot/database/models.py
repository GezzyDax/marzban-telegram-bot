"""SQLAlchemy database models"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models"""

    pass


class User(Base):
    """User model - связь между Telegram ID и Marzban username"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    marzban_username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"User(id={self.id}, telegram_id={self.telegram_id}, "
            f"marzban_username={self.marzban_username}, is_admin={self.is_admin})"
        )


class AdminLog(Base):
    """Admin action log model"""

    __tablename__ = "admin_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return (
            f"AdminLog(id={self.id}, admin_telegram_id={self.admin_telegram_id}, "
            f"action={self.action}, target_username={self.target_username})"
        )


class NotificationSettings(Base):
    """User notification preferences"""

    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    notify_expiry: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_traffic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expiry_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)  # Warn N days before
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"NotificationSettings(telegram_id={self.telegram_id})"


class SentNotifications(Base):
    """Track sent notifications to prevent duplicates"""

    __tablename__ = "sent_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)  # expiry/traffic/status
    notification_key: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # Unique key like "expiry_7days_2025-01-15"
    sent_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"SentNotifications(id={self.id}, telegram_id={self.telegram_id}, type={self.notification_type})"
