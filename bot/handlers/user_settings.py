"""User settings handlers"""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import get_notification_settings, update_notification_settings
from bot.keyboards.user_extended import get_notification_settings_keyboard, get_subscription_submenu

logger = logging.getLogger(__name__)
router = Router(name="user_settings")


@router.callback_query(F.data == "notification_settings")
async def show_notification_settings(callback: CallbackQuery, session: AsyncSession, db_user, **kwargs):
    """Show notification settings"""
    if not db_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    settings = await get_notification_settings(session, db_user.telegram_id)

    text = (
        "🔔 <b>Настройки уведомлений</b>\n\n"
        "Нажмите на кнопку, чтобы включить/выключить тип уведомлений:\n\n"
        f"{'🔔' if settings.notify_expiry else '🔕'} <b>Истечение подписки</b>\n"
        f"   Предупреждать за {settings.expiry_days} дней\n\n"
        f"{'🔔' if settings.notify_traffic else '🔕'} <b>Превышение трафика</b>\n"
        "   Уведомление при 80%, 90%, 100%\n\n"
        f"{'🔔' if settings.notify_status else '🔕'} <b>Смена статуса</b>\n"
        "   Уведомление об активации/деактивации"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_notification_settings_keyboard(
            settings.notify_expiry, settings.notify_traffic, settings.notify_status
        ),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_notify_"))
async def toggle_notification(callback: CallbackQuery, session: AsyncSession, db_user, **kwargs):
    """Toggle notification setting"""
    if not db_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    notification_type = callback.data.replace("toggle_notify_", "")
    settings = await get_notification_settings(session, db_user.telegram_id)

    if notification_type == "expiry":
        new_value = not settings.notify_expiry
        await update_notification_settings(session, db_user.telegram_id, notify_expiry=new_value)
        status = "включены" if new_value else "выключены"
        await callback.answer(f"🔔 Уведомления об истечении {status}")
    elif notification_type == "traffic":
        new_value = not settings.notify_traffic
        await update_notification_settings(session, db_user.telegram_id, notify_traffic=new_value)
        status = "включены" if new_value else "выключены"
        await callback.answer(f"🔔 Уведомления о трафике {status}")
    elif notification_type == "status":
        new_value = not settings.notify_status
        await update_notification_settings(session, db_user.telegram_id, notify_status=new_value)
        status = "включены" if new_value else "выключены"
        await callback.answer(f"🔔 Уведомления о статусе {status}")

    # Refresh the settings display
    settings = await get_notification_settings(session, db_user.telegram_id)
    text = (
        "🔔 <b>Настройки уведомлений</b>\n\n"
        "Нажмите на кнопку, чтобы включить/выключить тип уведомлений:\n\n"
        f"{'🔔' if settings.notify_expiry else '🔕'} <b>Истечение подписки</b>\n"
        f"   Предупреждать за {settings.expiry_days} дней\n\n"
        f"{'🔔' if settings.notify_traffic else '🔕'} <b>Превышение трафика</b>\n"
        "   Уведомление при 80%, 90%, 100%\n\n"
        f"{'🔔' if settings.notify_status else '🔕'} <b>Смена статуса</b>\n"
        "   Уведомление об активации/деактивации"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_notification_settings_keyboard(
            settings.notify_expiry, settings.notify_traffic, settings.notify_status
        ),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "subscription_detailed")
async def show_detailed_subscription(callback: CallbackQuery, session: AsyncSession, db_user, marzban, **kwargs):
    """Show detailed subscription statistics"""
    if not db_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    try:
        from bot.services.formatters import format_bytes, format_date
        from bot.utils.formatters import format_progress_bar, format_date_relative, format_status_emoji
        from datetime import datetime

        marzban_user = await marzban.get_user(db_user.marzban_username)

        # Calculate days since creation (estimate)
        days_active = 30  # Default estimate
        if marzban_user.expire:
            # Assume 30-day subscription
            expire_dt = datetime.fromtimestamp(marzban_user.expire) if isinstance(marzban_user.expire, (int, float)) else marzban_user.expire
            now = datetime.now()
            if expire_dt > now:
                days_active = max(1, 30 - (expire_dt - now).days)

        # Traffic info
        used = marzban_user.used_traffic
        limit = marzban_user.data_limit if marzban_user.data_limit else 0
        progress = format_progress_bar(used, limit) if limit > 0 else "Безлимит"

        # Status emoji
        expire_dt = datetime.fromtimestamp(marzban_user.expire) if isinstance(marzban_user.expire, (int, float)) else marzban_user.expire
        status_emoji = format_status_emoji(marzban_user.status, expire_dt, used, limit)

        # Average daily usage
        avg_daily = used / days_active if days_active > 0 else 0

        text = (
            f"{status_emoji} <b>Детальная статистика</b>\n\n"
            f"👤 Аккаунт: <code>{marzban_user.username}</code>\n"
            f"📊 Статус: <b>{marzban_user.status}</b>\n\n"
            f"📈 <b>Трафик</b>\n"
            f"{progress}\n"
            f"Использовано: {format_bytes(used)}\n"
        )

        if limit > 0:
            text += f"Лимит: {format_bytes(limit)}\n"
            text += f"Осталось: {format_bytes(limit - used)}\n"
        else:
            text += "Лимит: Безлимит\n"

        text += f"\n📉 <b>Средний расход</b>\n"
        text += f"В день: {format_bytes(avg_daily)}\n"

        if marzban_user.expire:
            text += f"\n📅 <b>Истекает</b>\n"
            text += format_date_relative(expire_dt)

        await callback.message.edit_text(text, reply_markup=get_subscription_submenu(), parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        logger.error(f"Failed to get detailed subscription: {e}")
        await callback.answer("❌ Не удалось получить детальную статистику", show_alert=True)
