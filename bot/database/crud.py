"""CRUD operations for database models"""

from typing import Optional

from sqlalchemy import asc, desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AdminLog, User


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
    """Get user by Telegram ID"""
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def get_user_by_marzban_username(
    session: AsyncSession, marzban_username: str, *, primary_only: bool = True
) -> Optional[User]:
    """Get user by Marzban username (primary binding by default)"""
    query = select(User).where(User.marzban_username == marzban_username)
    if primary_only:
        query = query.where(User.primary_user.is_(True))

    query = query.order_by(desc(User.created_at))
    result = await session.execute(query)
    return result.scalars().first()


async def list_user_bindings(session: AsyncSession, marzban_username: str) -> list[User]:
    """List all Telegram bindings for a Marzban username"""
    result = await session.execute(
        select(User)
        .where(User.marzban_username == marzban_username)
        .order_by(desc(User.primary_user), desc(User.created_at))
    )
    return list(result.scalars().all())


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    marzban_username: str,
    is_admin: bool = False,
    primary_user: Optional[bool] = None,
) -> User:
    """Create new user"""
    existing_by_telegram = await get_user_by_telegram_id(session, telegram_id)
    if existing_by_telegram:
        raise ValueError(f"Telegram ID {telegram_id} is already linked to {existing_by_telegram.marzban_username}")

    existing_primary = await get_user_by_marzban_username(
        session, marzban_username, primary_only=True
    )

    if primary_user is None:
        primary_user = existing_primary is None

    if primary_user and existing_primary:
        existing_primary.primary_user = False

    user = User(
        telegram_id=telegram_id,
        marzban_username=marzban_username,
        is_admin=is_admin,
        primary_user=primary_user,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, telegram_id: int) -> bool:
    """Delete user by Telegram ID"""
    user = await get_user_by_telegram_id(session, telegram_id)
    if user:
        marzban_username = user.marzban_username
        was_primary = user.primary_user

        await session.delete(user)
        await session.flush()

        if was_primary:
            replacement_result = await session.execute(
                select(User)
                .where(User.marzban_username == marzban_username)
                .order_by(desc(User.primary_user), asc(User.created_at))
                .limit(1)
            )
            replacement = replacement_result.scalars().first()
            if replacement and not replacement.primary_user:
                replacement.primary_user = True

        await session.commit()
        return True
    return False


async def list_users(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 50,
    admin_only: bool = False,
) -> tuple[list[User], int]:
    """List users with pagination"""
    query = select(User)
    if admin_only:
        query = query.where(User.is_admin == True)

    # Get total count
    count_result = await session.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    # Get users
    query = query.order_by(desc(User.created_at)).offset(offset).limit(limit)
    result = await session.execute(query)
    users = list(result.scalars().all())

    return users, total


async def update_user_admin_status(session: AsyncSession, telegram_id: int, is_admin: bool) -> Optional[User]:
    """Update user admin status"""
    user = await get_user_by_telegram_id(session, telegram_id)
    if user:
        user.is_admin = is_admin
        await session.commit()
        await session.refresh(user)
        return user
    return None


async def log_admin_action(
    session: AsyncSession,
    admin_telegram_id: int,
    action: str,
    target_username: Optional[str] = None,
    details: Optional[str] = None,
) -> AdminLog:
    """Log admin action"""
    log = AdminLog(
        admin_telegram_id=admin_telegram_id,
        action=action,
        target_username=target_username,
        details=details,
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


async def get_admin_logs(
    session: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AdminLog], int]:
    """Get admin logs with pagination"""
    query = select(AdminLog)

    # Get total count
    count_result = await session.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    # Get logs
    query = query.order_by(desc(AdminLog.created_at)).offset(offset).limit(limit)
    result = await session.execute(query)
    logs = list(result.scalars().all())

    return logs, total


async def search_users(session: AsyncSession, query: str) -> list[User]:
    """
    Search users by telegram_id or marzban_username

    Args:
        session: Database session
        query: Search query (telegram_id or partial username)

    Returns:
        List of matching users
    """
    # Try to parse as telegram_id
    try:
        telegram_id = int(query)
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        return [user] if user else []
    except ValueError:
        pass

    # Search by username (case-insensitive partial match)
    result = await session.execute(select(User).where(User.marzban_username.ilike(f"%{query}%")))
    users = list(result.scalars().all())
    return users


async def get_notification_settings(session: AsyncSession, telegram_id: int):
    """Get user notification settings (create default if not exists)"""
    from .models import NotificationSettings

    result = await session.execute(
        select(NotificationSettings).where(NotificationSettings.telegram_id == telegram_id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        # Create default settings
        settings = NotificationSettings(telegram_id=telegram_id)
        session.add(settings)
        await session.commit()
        await session.refresh(settings)

    return settings


async def update_notification_settings(
    session: AsyncSession,
    telegram_id: int,
    notify_expiry: Optional[bool] = None,
    notify_traffic: Optional[bool] = None,
    notify_status: Optional[bool] = None,
    expiry_days: Optional[int] = None,
):
    """Update user notification settings"""
    from .models import NotificationSettings

    settings = await get_notification_settings(session, telegram_id)

    if notify_expiry is not None:
        settings.notify_expiry = notify_expiry
    if notify_traffic is not None:
        settings.notify_traffic = notify_traffic
    if notify_status is not None:
        settings.notify_status = notify_status
    if expiry_days is not None:
        settings.expiry_days = expiry_days

    await session.commit()
    await session.refresh(settings)
    return settings


async def check_notification_sent(
    session: AsyncSession, telegram_id: int, notification_type: str, notification_key: str
) -> bool:
    """Check if notification was already sent"""
    from .models import SentNotifications

    result = await session.execute(
        select(SentNotifications).where(
            SentNotifications.telegram_id == telegram_id,
            SentNotifications.notification_type == notification_type,
            SentNotifications.notification_key == notification_key,
        )
    )
    return result.scalar_one_or_none() is not None


async def mark_notification_sent(
    session: AsyncSession, telegram_id: int, notification_type: str, notification_key: str
):
    """Mark notification as sent"""
    from .models import SentNotifications

    notification = SentNotifications(
        telegram_id=telegram_id, notification_type=notification_type, notification_key=notification_key
    )
    session.add(notification)
    await session.commit()
    return notification
