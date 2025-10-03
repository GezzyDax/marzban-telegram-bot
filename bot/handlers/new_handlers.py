"""Улучшенные хендлеры - только callback кнопки, расширенная функциональность"""

import logging
import math
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import (
    User,
    get_user_by_telegram_id,
    get_user_by_marzban_username,
    create_user,
    list_users,
    search_users,
    get_notification_settings,
    update_notification_settings,
    log_admin_action,
)
from bot.services import MarzbanAPI, MarzbanAPIError
from bot.services.formatters import format_bytes
from bot.utils.formatters import format_progress_bar, format_date_relative, format_status_emoji
from bot.keyboards.inline import (
    get_user_main_menu,
    get_admin_main_menu,
    get_subscription_menu,
    get_notification_settings_menu,
    get_instruction_menu,
    get_instruction_details_menu,
    get_request_user_keyboard,
    get_cancel_inline,
    get_confirmation_inline,
    get_user_list_navigation,
    get_back_to_menu,
    get_back_to_admin_menu,
)
from bot.states import AddUserStates, SearchUserStates

logger = logging.getLogger(__name__)
router = Router(name="new_handlers")


# ============= COMMANDS =============
@router.message(CommandStart())
async def cmd_start(message: Message, db_user: User | None, is_admin: bool):
    """Start command - show main menu"""
    if not db_user:
        await message.answer(
            "👋 <b>Добро пожаловать!</b>\n\n"
            "❌ Вы не зарегистрированы в системе.\n"
            "Обратитесь к администратору для получения доступа к VPN.\n\n"
            "Контакт поддержки: @hotloqer",
            parse_mode="HTML"
        )
        return

    await message.answer(
        f"👋 <b>Добро пожаловать!</b>\n\n"
        f"🔐 Ваш аккаунт: <code>{db_user.marzban_username}</code>\n\n"
        "Выберите действие:",
        reply_markup=get_user_main_menu(is_admin=is_admin),
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_help(message: Message, db_user: User | None, is_admin: bool):
    """Help command"""
    if not db_user:
        await message.answer(
            "ℹ️ <b>Помощь</b>\n\n"
            "Этот бот предоставляет доступ к VPN сервису Gezzolith.\n\n"
            "Для получения доступа обратитесь к администратору: @hotloqer",
            parse_mode="HTML"
        )
        return

    help_text = (
        "ℹ️ <b>Помощь</b>\n\n"
        "<b>Доступные команды:</b>\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n\n"
        "Используйте кнопки в сообщениях для навигации.\n\n"
        "Поддержка: @hotloqer"
    )

    await message.answer(help_text, parse_mode="HTML")


# ============= USER MENU =============
@router.callback_query(F.data == "back_to_user_menu")
async def back_to_user_menu(callback: CallbackQuery, db_user: User | None, is_admin: bool):
    """Return to user main menu"""
    if not db_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    await callback.message.edit_text(
        f"👤 <b>Главное меню</b>\n\n"
        f"🔐 Ваш аккаунт: <code>{db_user.marzban_username}</code>\n\n"
        "Выберите действие:",
        reply_markup=get_user_main_menu(is_admin=is_admin),
        parse_mode="HTML"
    )
    await callback.answer()


# ============= USER: SUBSCRIPTION =============
@router.callback_query(F.data == "user_subscription")
async def show_subscription(callback: CallbackQuery, db_user: User | None, marzban: MarzbanAPI):
    """Show detailed subscription info"""
    if not db_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    try:
        marzban_user = await marzban.get_user(db_user.marzban_username)

        # Parse dates
        expire_dt = None
        if marzban_user.expire:
            expire_dt = datetime.fromtimestamp(marzban_user.expire) if isinstance(marzban_user.expire, (int, float)) else marzban_user.expire

        # Status emoji
        status_emoji = format_status_emoji(
            marzban_user.status,
            expire_dt,
            marzban_user.used_traffic,
            marzban_user.data_limit if marzban_user.data_limit else 0
        )

        used = marzban_user.used_traffic
        limit = marzban_user.data_limit if marzban_user.data_limit else 0

        # Build message
        text = (
            f"{status_emoji} <b>Информация о подписке</b>\n\n"
            f"👤 Username: <code>{marzban_user.username}</code>\n"
            f"📊 Статус: <b>{marzban_user.status.upper()}</b>\n"
        )

        # Add online status if available
        online_at = getattr(marzban_user, 'online_at', None)
        if online_at:
            online_dt = datetime.fromtimestamp(online_at) if isinstance(online_at, (int, float)) else online_at
            now = datetime.now()
            if (now - online_dt).total_seconds() < 300:  # 5 minutes
                text += f"🟢 <b>ONLINE</b>\n"
            else:
                text += f"⚪️ Последняя активность: {online_dt.strftime('%d.%m.%Y %H:%M')}\n"

        text += "\n"

        # Traffic info
        text += f"📊 <b>Трафик:</b>\n"
        if limit > 0:
            progress = format_progress_bar(used, limit)
            text += f"{progress}\n"
            text += f"└ Использовано: <b>{format_bytes(used)}</b> из <b>{format_bytes(limit)}</b>\n"
            remaining = limit - used
            if remaining > 0:
                text += f"└ Осталось: <b>{format_bytes(remaining)}</b>\n"
            else:
                text += f"└ ⚠️ Трафик исчерпан\n"
        else:
            text += f"└ Использовано: <b>{format_bytes(used)}</b>\n"
            text += f"└ Лимит: <b>♾ Безлимит</b>\n"

        # Expiry info
        if expire_dt:
            text += f"\n📅 <b>Срок действия:</b>\n"
            text += format_date_relative(expire_dt)
        else:
            text += f"\n📅 <b>Срок действия:</b> ♾ Бессрочно\n"

        # Links count
        if hasattr(marzban_user, 'links') and marzban_user.links:
            text += f"\n🔗 Активных подключений: <b>{len(marzban_user.links)}</b>\n"

        await callback.message.edit_text(
            text,
            reply_markup=get_subscription_menu(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Failed to get subscription: {e}", exc_info=True)
        await callback.answer("❌ Не удалось получить информацию о подписке", show_alert=True)


# ============= USER: SUBSCRIPTION LINK =============
@router.callback_query(F.data == "user_link")
async def get_subscription_link(callback: CallbackQuery, db_user: User | None, marzban: MarzbanAPI):
    """Get subscription link"""
    if not db_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    try:
        marzban_user = await marzban.get_user(db_user.marzban_username)

        if not marzban_user.subscription_url:
            await callback.answer("❌ Subscription URL не найден. Обратитесь к администратору.", show_alert=True)
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
            "Если у вас ещё нет VPN клиента, вернитесь назад и выберите 'ℹ️ Инструкция'"
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_menu(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Failed to get subscription link: {e}", exc_info=True)
        await callback.answer("❌ Не удалось получить ссылку на подписку", show_alert=True)


# ============= USER: INSTRUCTION =============
@router.callback_query(F.data == "user_instruction")
async def show_instruction(callback: CallbackQuery):
    """Show instruction menu"""
    text = (
        "ℹ️ <b>Инструкция по подключению</b>\n\n"
        "Выберите вашу платформу для получения подробной инструкции:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_instruction_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "instruction_mobile")
async def instruction_mobile(callback: CallbackQuery):
    """Mobile instruction"""
    text = (
        "📱 <b>Инструкция для телефона</b>\n\n"
        "<b>iOS:</b>\n"
        "1. Установите V2Box из App Store\n"
        "2. Вернитесь в бот → '🔗 Ссылка'\n"
        "3. Скопируйте ссылку подписки\n"
        "4. Откройте V2Box → '+' → 'Импорт из буфера обмена'\n"
        "5. Нажмите на сервер → Включите VPN\n\n"
        "<b>Android:</b>\n"
        "1. Установите V2Box из Google Play\n"
        "2. Получите ссылку подписки в боте\n"
        "3. В V2Box: '+' → 'Импорт из буфера обмена'\n"
        "4. Подключитесь к серверу\n\n"
        "Нажмите кнопку ниже для скачивания:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_instruction_details_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "instruction_desktop")
async def instruction_desktop(callback: CallbackQuery):
    """Desktop instruction"""
    text = (
        "💻 <b>Инструкция для компьютера</b>\n\n"
        "<b>Windows/Mac/Linux:</b>\n"
        "1. Скачайте NekoBox для вашей ОС\n"
        "2. Скопируйте ссылку подписки из бота\n"
        "3. Откройте NekoBox → Программа → Добавить профиль из буфера обмена\n"
        "4. Двойной клик на сервер → Запустить\n\n"
        "Нажмите кнопку ниже для скачивания:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_instruction_details_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "instruction_faq")
async def instruction_faq(callback: CallbackQuery):
    """FAQ"""
    text = (
        "❓ <b>Часто задаваемые вопросы</b>\n\n"
        "<b>Q: Не подключается VPN</b>\n"
        "A: Проверьте, что импортировали правильную ссылку. Попробуйте переключить сервер в настройках клиента.\n\n"
        "<b>Q: Медленная скорость</b>\n"
        "A: Проверьте остаток трафика в разделе 'Подписка'. Попробуйте другой сервер из списка.\n\n"
        "<b>Q: Где найти ссылку подписки?</b>\n"
        "A: Главное меню → '🔗 Ссылка'\n\n"
        "<b>Q: Ошибка при импорте ссылки</b>\n"
        "A: Убедитесь что скопировали ссылку полностью. Попробуйте обновить ссылку в боте.\n\n"
        "Если проблема не решена, обратитесь в поддержку: @hotloqer"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_instruction_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


# ============= USER: SETTINGS =============
@router.callback_query(F.data == "user_settings")
async def show_user_settings(callback: CallbackQuery, session: AsyncSession, db_user: User | None):
    """Show user settings"""
    if not db_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    settings = await get_notification_settings(session, db_user.telegram_id)

    text = (
        "⚙️ <b>Настройки уведомлений</b>\n\n"
        "Управляйте уведомлениями о вашей подписке:\n\n"
    )

    if settings.notify_expiry:
        text += f"🔔 Уведомления об истечении: <b>Включены</b>\n"
        text += f"└ За {settings.expiry_days} дней до истечения\n\n"
    else:
        text += f"🔕 Уведомления об истечении: <b>Выключены</b>\n\n"

    if settings.notify_traffic:
        text += f"🔔 Уведомления о трафике: <b>Включены</b>\n"
        text += f"└ При достижении 80% и 95% лимита\n"
    else:
        text += f"🔕 Уведомления о трафике: <b>Выключены</b>\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_notification_settings_menu(settings.notify_expiry, settings.notify_traffic),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_notify_"))
async def toggle_notification(callback: CallbackQuery, session: AsyncSession, db_user: User | None):
    """Toggle notification setting"""
    if not db_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    notification_type = callback.data.replace("toggle_notify_", "")
    settings = await get_notification_settings(session, db_user.telegram_id)

    if notification_type == "expiry":
        new_value = not settings.notify_expiry
        await update_notification_settings(session, db_user.telegram_id, notify_expiry=new_value)
        await callback.answer(f"{'🔔 Уведомления включены' if new_value else '🔕 Уведомления выключены'}")
    elif notification_type == "traffic":
        new_value = not settings.notify_traffic
        await update_notification_settings(session, db_user.telegram_id, notify_traffic=new_value)
        await callback.answer(f"{'🔔 Уведомления включены' if new_value else '🔕 Уведомления выключены'}")

    # Refresh display
    settings = await get_notification_settings(session, db_user.telegram_id)

    text = (
        "⚙️ <b>Настройки уведомлений</b>\n\n"
        "Управляйте уведомлениями о вашей подписке:\n\n"
    )

    if settings.notify_expiry:
        text += f"🔔 Уведомления об истечении: <b>Включены</b>\n"
        text += f"└ За {settings.expiry_days} дней до истечения\n\n"
    else:
        text += f"🔕 Уведомления об истечении: <b>Выключены</b>\n\n"

    if settings.notify_traffic:
        text += f"🔔 Уведомления о трафике: <b>Включены</b>\n"
        text += f"└ При достижении 80% и 95% лимита\n"
    else:
        text += f"🔕 Уведомления о трафике: <b>Выключены</b>\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_notification_settings_menu(settings.notify_expiry, settings.notify_traffic),
        parse_mode="HTML"
    )


# ============= ADMIN MENU =============
@router.callback_query(F.data == "admin_menu")
async def show_admin_menu(callback: CallbackQuery, is_admin: bool):
    """Show admin menu"""
    if not is_admin:
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    text = (
        "👑 <b>Админ-панель</b>\n\n"
        "Управление пользователями и система:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_admin_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


# Продолжение в следующем файле (слишком большой)
