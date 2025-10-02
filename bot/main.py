"""Main entry point for the bot"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.config import settings
from bot.database.models import Base
from bot.handlers.simple import router as simple_router
from bot.middleware import AuthMiddleware, DatabaseMiddleware
from bot.services import MarzbanAPI


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def create_tables(engine):
    """Create database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def main():
    """Main function"""
    logger.info("Starting Marzban Telegram Bot...")

    # Create database engine
    engine = create_async_engine(settings.database_url, echo=False, future=True)
    session_pool = async_sessionmaker(engine, expire_on_commit=False)

    # Create tables
    await create_tables(engine)

    # Initialize bot and dispatcher with FSM storage
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Initialize Marzban API client
    marzban = MarzbanAPI(
        base_url=settings.marzban_api_url,
        username=settings.marzban_admin_username,
        password=settings.marzban_admin_password,
    )

    # Check Marzban connection
    if not await marzban.check_connection():
        logger.error("Failed to connect to Marzban API. Please check your configuration.")
        sys.exit(1)
    logger.info("Marzban API connection successful")

    # Register middlewares
    dp.update.middleware(DatabaseMiddleware(session_pool))
    dp.update.middleware(AuthMiddleware())

    # Inject MarzbanAPI into all handlers
    async def marzban_middleware(handler, event, data):
        data["marzban"] = marzban
        return await handler(event, data)

    dp.update.middleware.register(marzban_middleware)

    # Register simplified router
    dp.include_router(simple_router)

    logger.info("Bot configuration complete")
    logger.info(f"Admin IDs: {settings.admin_ids}")

    # Start polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
