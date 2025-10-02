"""Common handlers"""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.database import User
from bot.keyboards import get_user_main_menu, get_admin_main_menu


logger = logging.getLogger(__name__)
router = Router(name="common")


@router.message(Command("start"))
async def cmd_start(message: Message, db_user: User | None, is_admin: bool):
    """Handle /start command"""
    if not db_user:
        await message.answer(
            "❌ <b>Доступ запрещен</b>\n\n"
            "Вы не зарегистрированы в системе.\n"
            "Обратитесь к администратору для получения доступа к VPN.\n\n"
            "Контакт поддержки: @hotloqer",
            parse_mode="HTML",
        )
        return

    if is_admin:
        keyboard = get_admin_main_menu()
        await message.answer(
            f"👑 <b>Добро пожаловать, администратор!</b>\n\n"
            f"🔐 Ваш аккаунт: <code>{db_user.marzban_username}</code>\n\n"
            "Выберите действие:",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    else:
        keyboard = get_user_main_menu()
        await message.answer(
            f"👋 <b>Добро пожаловать!</b>\n\n"
            f"🔐 Ваш аккаунт: <code>{db_user.marzban_username}</code>\n\n"
            "Выберите действие:",
            reply_markup=keyboard,
            parse_mode="HTML",
        )


@router.message(Command("help"))
async def cmd_help(message: Message, db_user: User | None, is_admin: bool):
    """Handle /help command"""
    if not db_user:
        await message.answer(
            "ℹ️ <b>Помощь</b>\n\n"
            "Этот бот предоставляет доступ к VPN сервису Gezzolith.\n\n"
            "Для получения доступа обратитесь к администратору: @hotloqer",
            parse_mode="HTML",
        )
        return

    help_text = (
        "ℹ️ <b>Помощь</b>\n\n"
        "<b>Доступные команды:</b>\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n\n"
    )

    if is_admin:
        help_text += (
            "<b>Админские команды:</b>\n"
            "/add_user &lt;telegram_id&gt; &lt;marzban_username&gt; - Добавить пользователя\n"
            "/remove_user &lt;telegram_id&gt; - Удалить пользователя\n"
            "/make_admin &lt;telegram_id&gt; - Назначить админа\n"
            "/revoke_admin &lt;telegram_id&gt; - Забрать права админа\n\n"
        )

    help_text += "Если у вас возникли вопросы, обратитесь в поддержку: @hotloqer"

    await message.answer(help_text, parse_mode="HTML")
