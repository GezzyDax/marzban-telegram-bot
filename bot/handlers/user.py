"""User handlers"""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.database import User
from bot.services import MarzbanAPI
from bot.services.formatters import format_subscription_status, format_bytes
from bot.keyboards import get_user_main_menu, get_back_button, get_instruction_keyboard
from bot.keyboards.user_extended import get_user_main_menu_extended, get_subscription_submenu, get_instruction_menu
from bot.utils.formatters import format_progress_bar, format_date_relative, format_status_emoji
from datetime import datetime


logger = logging.getLogger(__name__)
router = Router(name="user")


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, db_user: User | None, is_admin: bool):
    """Handle back to menu button"""
    if not db_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    keyboard = get_user_main_menu_extended()
    await callback.message.edit_text(
        f"👋 <b>Главное меню</b>\n\n"
        f"🔐 Ваш аккаунт: <code>{db_user.marzban_username}</code>\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "my_subscription")
async def show_subscription(callback: CallbackQuery, db_user: User | None, marzban: MarzbanAPI):
    """Show user subscription info (enhanced)"""
    if not db_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    try:
        marzban_user = await marzban.get_user(db_user.marzban_username)

        # Convert expire to datetime if needed
        expire_dt = None
        if marzban_user.expire:
            expire_dt = datetime.fromtimestamp(marzban_user.expire) if isinstance(marzban_user.expire, (int, float)) else marzban_user.expire

        # Get status emoji
        status_emoji = format_status_emoji(
            marzban_user.status,
            expire_dt,
            marzban_user.used_traffic,
            marzban_user.data_limit if marzban_user.data_limit else 0
        )

        # Traffic progress
        used = marzban_user.used_traffic
        limit = marzban_user.data_limit if marzban_user.data_limit else 0

        text = (
            f"{status_emoji} <b>Моя подписка</b>\n\n"
            f"👤 Аккаунт: <code>{marzban_user.username}</code>\n"
            f"📊 Статус: <b>{marzban_user.status}</b>\n\n"
            f"📈 <b>Трафик</b>\n"
        )

        if limit > 0:
            progress = format_progress_bar(used, limit)
            text += f"{progress}\n"
            text += f"Использовано: {format_bytes(used)} из {format_bytes(limit)}\n"
        else:
            text += f"Использовано: {format_bytes(used)}\n"
            text += "Лимит: Безлимит\n"

        if expire_dt:
            text += f"\n📅 <b>Срок действия</b>\n"
            text += format_date_relative(expire_dt)

        await callback.message.edit_text(
            text,
            reply_markup=get_subscription_submenu(),
            parse_mode="HTML",
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Failed to get user subscription: {e}")
        await callback.answer(
            "❌ Не удалось получить информацию о подписке. Попробуйте позже.",
            show_alert=True,
        )


@router.callback_query(F.data == "get_link")
async def get_subscription_link(callback: CallbackQuery, db_user: User | None, marzban: MarzbanAPI):
    """Send subscription link to user"""
    if not db_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    try:
        marzban_user = await marzban.get_user(db_user.marzban_username)

        if not marzban_user.subscription_url:
            await callback.answer(
                "❌ Subscription URL не найден. Обратитесь к администратору.",
                show_alert=True,
            )
            return

        text = (
            "🔗 <b>Ссылка на подписку</b>\n\n"
            "Скопируйте ссылку ниже и импортируйте её в ваш VPN клиент:\n\n"
            f"<code>{marzban_user.subscription_url}</code>\n\n"
            "📱 <b>Как использовать:</b>\n"
            "1. Скопируйте ссылку (нажмите на неё)\n"
            "2. Откройте ваш VPN клиент (V2Box/NekoBox)\n"
            "3. Нажмите '+' → 'Импорт из буфера обмена'\n"
            "4. Подключитесь к серверу\n\n"
            "Если у вас ещё нет VPN клиента, нажмите 'ℹ️ Инструкция'"
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_back_button(),
            parse_mode="HTML",
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Failed to get subscription link: {e}")
        await callback.answer(
            "❌ Не удалось получить ссылку на подписку. Попробуйте позже.",
            show_alert=True,
        )


@router.callback_query(F.data == "instruction")
async def show_instruction(callback: CallbackQuery):
    """Show connection instruction (menu)"""
    text = (
        "ℹ️ <b>Инструкция по подключению</b>\n\n"
        "Выберите вашу платформу:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_instruction_menu(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "instruction_menu")
async def show_instruction_menu(callback: CallbackQuery):
    """Show instruction menu"""
    text = (
        "ℹ️ <b>Инструкция по подключению</b>\n\n"
        "Выберите вашу платформу:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_instruction_menu(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "instruction_mobile")
async def show_mobile_instruction(callback: CallbackQuery):
    """Show mobile instruction"""
    text = (
        "📱 <b>Инструкция для телефона</b>\n\n"
        "<b>iOS/Android:</b>\n"
        "1. Установите приложение V2Box\n"
        "2. Вернитесь в бот → '🔗 Получить ссылку'\n"
        "3. Скопируйте ссылку подписки\n"
        "4. Откройте V2Box → '+' → 'Импорт из буфера обмена'\n"
        "5. Нажмите на сервер → Включите VPN"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_instruction_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "instruction_desktop")
async def show_desktop_instruction(callback: CallbackQuery):
    """Show desktop instruction"""
    text = (
        "💻 <b>Инструкция для компьютера</b>\n\n"
        "<b>Windows/Mac/Linux:</b>\n"
        "1. Скачайте NekoBox\n"
        "2. Скопируйте ссылку подписки из бота\n"
        "3. Откройте NekoBox → Программа → Добавить профиль из буфера обмена\n"
        "4. Двойной клик на сервер → Запустить"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_instruction_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "instruction_faq")
async def show_faq(callback: CallbackQuery):
    """Show FAQ"""
    text = (
        "❓ <b>Часто задаваемые вопросы</b>\n\n"
        "<b>Q: Не подключается VPN</b>\n"
        "A: Проверьте, что импортировали правильную ссылку. Попробуйте переключить сервер.\n\n"
        "<b>Q: Медленная скорость</b>\n"
        "A: Проверьте остаток трафика. Попробуйте другой сервер.\n\n"
        "<b>Q: Где найти ссылку подписки?</b>\n"
        "A: Главное меню → '🔗 Получить ссылку'\n\n"
        "Если проблема не решена, нажмите '❓ Проблема с подключением' в главном меню."
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_instruction_menu(),
        parse_mode="HTML",
    )
    await callback.answer()
