"""Admin handlers"""

import logging
import math

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import (
    User,
    create_user,
    delete_user,
    get_user_by_telegram_id,
    get_user_by_marzban_username,
    list_users,
    update_user_admin_status,
    log_admin_action,
    get_admin_logs,
)
from bot.services import MarzbanAPI, MarzbanAPIError
from bot.keyboards import get_admin_main_menu, get_user_list_keyboard, get_logs_keyboard
from bot.keyboards.admin_extended import (
    get_admin_main_menu_extended,
    get_users_management_menu,
    get_permissions_management_menu,
    get_stats_menu,
)


logger = logging.getLogger(__name__)
router = Router(name="admin")


def admin_only(handler):
    """Decorator to check admin rights"""

    async def wrapper(event, *args, **kwargs):
        is_admin = kwargs.get("is_admin", False)
        if not is_admin:
            if isinstance(event, Message):
                await event.answer("❌ Эта команда доступна только администраторам")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ Доступ запрещён", show_alert=True)
            return
        return await handler(event, *args, **kwargs)

    # Preserve handler metadata for aiogram
    wrapper.__name__ = handler.__name__
    wrapper.__module__ = handler.__module__
    return wrapper


@router.callback_query(F.data == "admin_menu")
@admin_only
async def show_admin_menu(callback: CallbackQuery, **kwargs):
    """Show admin menu (extended)"""
    await callback.message.edit_text(
        "👑 <b>Админ-панель</b>\n\n" "Выберите раздел:",
        reply_markup=get_admin_main_menu_extended(),
        parse_mode="HTML",
    )
    await callback.answer()


# Submenus
@router.callback_query(F.data == "admin_permissions_menu")
@admin_only
async def show_permissions_menu(callback: CallbackQuery, **kwargs):
    """Show permissions management menu"""
    await callback.message.edit_text(
        "👑 <b>Управление правами</b>\n\n" "Выберите действие:",
        reply_markup=get_permissions_management_menu(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats_menu")
@admin_only
async def show_stats_menu(callback: CallbackQuery, **kwargs):
    """Show statistics menu"""
    await callback.message.edit_text(
        "📊 <b>Статистика и отчёты</b>\n\n" "Выберите действие:",
        reply_markup=get_stats_menu(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("add_user"))
@admin_only
async def cmd_add_user(message: Message, session: AsyncSession, marzban: MarzbanAPI, **kwargs):
    """Add user: /add_user <telegram_id> <marzban_username>"""
    args = message.text.split()
    if len(args) != 3:
        await message.answer(
            "❌ <b>Неверный формат команды</b>\n\n"
            "Использование: /add_user &lt;telegram_id&gt; &lt;marzban_username&gt;\n\n"
            "Пример: /add_user 123456789 john_doe",
            parse_mode="HTML",
        )
        return

    try:
        telegram_id = int(args[1])
        marzban_username = args[2]
    except ValueError:
        await message.answer("❌ Telegram ID должен быть числом")
        return

    # Check if user already exists
    existing_user = await get_user_by_telegram_id(session, telegram_id)
    if existing_user:
        await message.answer(
            f"❌ Пользователь с Telegram ID <code>{telegram_id}</code> уже существует\n"
            f"Marzban username: <code>{existing_user.marzban_username}</code>",
            parse_mode="HTML",
        )
        return

    # Check if marzban username already linked
    existing_marzban = await get_user_by_marzban_username(session, marzban_username)
    if existing_marzban:
        await message.answer(
            f"❌ Marzban username <code>{marzban_username}</code> уже привязан\n"
            f"Telegram ID: <code>{existing_marzban.telegram_id}</code>",
            parse_mode="HTML",
        )
        return

    # Check if user exists in Marzban
    try:
        await marzban.get_user(marzban_username)
    except MarzbanAPIError:
        await message.answer(
            f"❌ Пользователь <code>{marzban_username}</code> не найден в Marzban\n\n"
            "Сначала создайте пользователя в панели Marzban: https://marzban.gezzy.ru",
            parse_mode="HTML",
        )
        return

    # Create user
    user = await create_user(session, telegram_id, marzban_username)

    # Log action
    await log_admin_action(
        session,
        message.from_user.id,
        "add_user",
        marzban_username,
        f"telegram_id: {telegram_id}",
    )

    await message.answer(
        f"✅ <b>Пользователь успешно добавлен</b>\n\n"
        f"Telegram ID: <code>{telegram_id}</code>\n"
        f"Marzban username: <code>{marzban_username}</code>\n\n"
        "Пользователь может начать работу с ботом командой /start",
        parse_mode="HTML",
    )


@router.message(Command("remove_user"))
@admin_only
async def cmd_remove_user(message: Message, session: AsyncSession, **kwargs):
    """Remove user: /remove_user <telegram_id>"""
    args = message.text.split()
    if len(args) != 2:
        await message.answer(
            "❌ <b>Неверный формат команды</b>\n\n"
            "Использование: /remove_user &lt;telegram_id&gt;\n\n"
            "Пример: /remove_user 123456789",
            parse_mode="HTML",
        )
        return

    try:
        telegram_id = int(args[1])
    except ValueError:
        await message.answer("❌ Telegram ID должен быть числом")
        return

    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        await message.answer(f"❌ Пользователь с ID <code>{telegram_id}</code> не найден", parse_mode="HTML")
        return

    marzban_username = user.marzban_username
    await delete_user(session, telegram_id)

    # Log action
    await log_admin_action(
        session,
        message.from_user.id,
        "remove_user",
        marzban_username,
        f"telegram_id: {telegram_id}",
    )

    await message.answer(
        f"✅ <b>Пользователь удалён</b>\n\n"
        f"Telegram ID: <code>{telegram_id}</code>\n"
        f"Marzban username: <code>{marzban_username}</code>",
        parse_mode="HTML",
    )


@router.message(Command("make_admin"))
@admin_only
async def cmd_make_admin(message: Message, session: AsyncSession, **kwargs):
    """Make user admin: /make_admin <telegram_id>"""
    args = message.text.split()
    if len(args) != 2:
        await message.answer(
            "❌ <b>Неверный формат команды</b>\n\n"
            "Использование: /make_admin &lt;telegram_id&gt;\n\n"
            "Пример: /make_admin 123456789",
            parse_mode="HTML",
        )
        return

    try:
        telegram_id = int(args[1])
    except ValueError:
        await message.answer("❌ Telegram ID должен быть числом")
        return

    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        await message.answer(f"❌ Пользователь с ID <code>{telegram_id}</code> не найден", parse_mode="HTML")
        return

    if user.is_admin:
        await message.answer(f"ℹ️ Пользователь <code>{telegram_id}</code> уже является админом", parse_mode="HTML")
        return

    await update_user_admin_status(session, telegram_id, True)

    # Log action
    await log_admin_action(
        session,
        message.from_user.id,
        "make_admin",
        user.marzban_username,
        f"telegram_id: {telegram_id}",
    )

    await message.answer(
        f"✅ Пользователь <code>{telegram_id}</code> назначен админом\n"
        f"Marzban username: <code>{user.marzban_username}</code>",
        parse_mode="HTML",
    )


@router.message(Command("revoke_admin"))
@admin_only
async def cmd_revoke_admin(message: Message, session: AsyncSession, **kwargs):
    """Revoke admin rights: /revoke_admin <telegram_id>"""
    args = message.text.split()
    if len(args) != 2:
        await message.answer(
            "❌ <b>Неверный формат команды</b>\n\n"
            "Использование: /revoke_admin &lt;telegram_id&gt;\n\n"
            "Пример: /revoke_admin 123456789",
            parse_mode="HTML",
        )
        return

    try:
        telegram_id = int(args[1])
    except ValueError:
        await message.answer("❌ Telegram ID должен быть числом")
        return

    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        await message.answer(f"❌ Пользователь с ID <code>{telegram_id}</code> не найден", parse_mode="HTML")
        return

    if not user.is_admin:
        await message.answer(f"ℹ️ Пользователь <code>{telegram_id}</code> не является админом", parse_mode="HTML")
        return

    await update_user_admin_status(session, telegram_id, False)

    # Log action
    await log_admin_action(
        session,
        message.from_user.id,
        "revoke_admin",
        user.marzban_username,
        f"telegram_id: {telegram_id}",
    )

    await message.answer(
        f"✅ Права админа забраны у <code>{telegram_id}</code>\n"
        f"Marzban username: <code>{user.marzban_username}</code>",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin_list_users")
@router.callback_query(F.data.startswith("admin_users_page:"))
@admin_only
async def show_user_list(callback: CallbackQuery, session: AsyncSession, **kwargs):
    """Show user list with pagination"""
    # Parse page number
    page = 0
    if ":" in callback.data:
        page = int(callback.data.split(":")[1])

    page_size = 10
    offset = page * page_size

    users, total = await list_users(session, offset=offset, limit=page_size)
    total_pages = math.ceil(total / page_size)

    if not users:
        await callback.message.edit_text(
            "📋 <b>Список пользователей</b>\n\n" "Пользователей не найдено",
            reply_markup=get_admin_main_menu(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    text = f"👥 <b>Список пользователей</b> (Страница {page + 1}/{total_pages})\n" f"Всего: {total}\n\n"

    for i, user in enumerate(users, start=offset + 1):
        admin_badge = "👑 " if user.is_admin else ""
        text += (
            f"{i}. {admin_badge}<b>{user.marzban_username}</b>\n"
            f"   ├ TG ID: <code>{user.telegram_id}</code>\n"
            f"   └ Создан: {user.created_at.strftime('%d.%m.%Y')}\n\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=get_user_list_keyboard(page, total_pages),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
@admin_only
async def show_stats(callback: CallbackQuery, session: AsyncSession, marzban: MarzbanAPI, **kwargs):
    """Show statistics"""
    try:
        users, total = await list_users(session, limit=1000)

        text = (
            "📊 <b>Статистика системы</b>\n\n"
            f"👥 Всего пользователей: <b>{total}</b>\n"
            f"👑 Администраторов: <b>{sum(1 for u in users if u.is_admin)}</b>\n"
            f"👤 Обычных пользователей: <b>{sum(1 for u in users if not u.is_admin)}</b>\n"
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_admin_main_menu(),
            parse_mode="HTML",
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        await callback.answer("❌ Не удалось получить статистику", show_alert=True)


@router.callback_query(F.data == "admin_logs")
@router.callback_query(F.data.startswith("admin_logs_page:"))
@admin_only
async def show_logs(callback: CallbackQuery, session: AsyncSession, **kwargs):
    """Show admin action logs"""
    # Parse page number
    page = 0
    if ":" in callback.data:
        page = int(callback.data.split(":")[1])

    page_size = 10
    offset = page * page_size

    logs, total = await get_admin_logs(session, offset=offset, limit=page_size)
    total_pages = math.ceil(total / page_size)

    if not logs:
        await callback.message.edit_text(
            "📋 <b>Логи действий</b>\n\n" "Логов не найдено",
            reply_markup=get_admin_main_menu(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    text = f"📋 <b>Логи действий</b> (Страница {page + 1}/{total_pages})\n\n"

    for log in logs:
        text += (
            f"🕐 {log.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"├ Админ: <code>{log.admin_telegram_id}</code>\n"
            f"├ Действие: <b>{log.action}</b>\n"
        )
        if log.target_username:
            text += f"├ Пользователь: <code>{log.target_username}</code>\n"
        if log.details:
            text += f"└ Детали: {log.details}\n"
        text += "\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_logs_keyboard(page, total_pages),
        parse_mode="HTML",
    )
    await callback.answer()
