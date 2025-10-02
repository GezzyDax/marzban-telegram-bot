"""Authentication middleware"""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import get_user_by_telegram_id, create_user
from bot.config import settings


logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """Middleware to check user authentication and admin status"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        session: AsyncSession = data.get("session")
        telegram_user = data.get("event_from_user")

        if not telegram_user or not session:
            return await handler(event, data)

        # Get or create user record
        user = await get_user_by_telegram_id(session, telegram_user.id)

        # Auto-add initial admins
        if not user and telegram_user.id in settings.admin_ids:
            logger.info(f"Auto-adding initial admin: {telegram_user.id}")
            user = await create_user(
                session,
                telegram_id=telegram_user.id,
                marzban_username=f"admin_{telegram_user.id}",
                is_admin=True,
            )

        # Add user and admin status to data
        data["db_user"] = user
        data["is_admin"] = user.is_admin if user else False

        return await handler(event, data)
