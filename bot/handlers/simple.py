"""Simplified handlers with clear UX"""

import logging
import math
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import (
    User,
    get_user_by_telegram_id,
    list_user_bindings,
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
from bot.keyboards.simple import (
    get_main_user_keyboard,
    get_main_admin_keyboard,
    get_request_user_keyboard,
    get_cancel_keyboard,
    get_confirmation_inline,
    get_subscription_inline,
    get_notification_toggle_inline,
    get_instruction_inline,
    get_user_list_navigation,
)
from bot.states import AddUserStates, SearchUserStates

logger = logging.getLogger(__name__)
router = Router(name="simple")


# ============= START =============
@router.message(CommandStart())
async def cmd_start(message: Message, db_user: User | None, is_admin: bool):
    """Start command - show appropriate keyboard"""
    if not db_user:
        await message.answer(
            "👋 Добро пожаловать!\n\n"
            "❌ Вы не зарегистрированы в системе.\n"
            "Обратитесь к администратору для получения доступа."
        )
        return

    # Always show user mode first
    await message.answer(
        f"👋 <b>Добро пожаловать!</b>\n\n"
        f"🔐 Ваш аккаунт: <code>{db_user.marzban_username}</code>\n\n"
        "Используйте кнопки ниже:",
        reply_markup=get_main_user_keyboard(is_admin=is_admin),
        parse_mode="HTML"
    )


# ============= MODE SWITCHING =============
@router.message(F.text == "👑 Админ-панель")
async def switch_to_admin(message: Message, is_admin: bool):
    """Switch to admin mode"""
    if not is_admin:
        await message.answer("❌ Доступно только администраторам")
        return

    await message.answer(
        "👑 <b>Админ-панель</b>\n\n"
        "Управление пользователями:",
        reply_markup=get_main_admin_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "👤 Мой аккаунт")
async def switch_to_user(message: Message, is_admin: bool, db_user: User | None):
    """Switch to user mode"""
    if not db_user:
        await message.answer("❌ Пользователь не найден")
        return

    await message.answer(
        f"👤 <b>Ваш аккаунт</b>\n\n"
        f"🔐 Username: <code>{db_user.marzban_username}</code>",
        reply_markup=get_main_user_keyboard(is_admin=is_admin),
        parse_mode="HTML"
    )


# ============= USER ACTIONS =============
@router.message(F.text == "📊 Подписка")
async def show_subscription(message: Message, db_user: User | None, marzban: MarzbanAPI):
    """Show subscription with beautiful formatting"""
    if not db_user:
        await message.answer("❌ Пользователь не найден")
        return

    try:
        marzban_user = await marzban.get_user(db_user.marzban_username)

        # Convert expire
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

        text = (
            f"{status_emoji} <b>Моя подписка</b>\n\n"
            f"👤 <code>{marzban_user.username}</code>\n"
            f"📊 Статус: <b>{marzban_user.status}</b>\n\n"
            f"📈 <b>Трафик:</b>\n"
        )

        if limit > 0:
            progress = format_progress_bar(used, limit)
            text += f"{progress}\n"
            text += f"Использовано: <b>{format_bytes(used)}</b> из <b>{format_bytes(limit)}</b>\n"
            remaining = limit - used
            if remaining > 0:
                text += f"Осталось: <b>{format_bytes(remaining)}</b>\n"
        else:
            text += f"Использовано: <b>{format_bytes(used)}</b>\n"
            text += "Лимит: <b>Безлимит</b>\n"

        if expire_dt:
            text += f"\n📅 <b>Истекает:</b>\n{format_date_relative(expire_dt)}"

        await message.answer(
            text,
            reply_markup=get_subscription_inline(),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Failed to get subscription: {e}")
        await message.answer("❌ Не удалось получить информацию о подписке")


@router.message(F.text == "🔗 Ссылка")
async def get_link(message: Message, db_user: User | None, marzban: MarzbanAPI):
    """Get subscription link"""
    if not db_user:
        await message.answer("❌ Пользователь не найден")
        return

    try:
        marzban_user = await marzban.get_user(db_user.marzban_username)

        if not marzban_user.subscription_url:
            await message.answer("❌ Subscription URL не найден")
            return

        text = (
            "🔗 <b>Ссылка на подписку</b>\n\n"
            "Скопируйте ссылку и импортируйте её в VPN клиент:\n\n"
            f"<code>{marzban_user.subscription_url}</code>\n\n"
            "📱 Как использовать:\n"
            "1. Скопируйте ссылку (нажмите на неё)\n"
            "2. Откройте VPN клиент\n"
            "3. Нажмите '+' → 'Импорт из буфера обмена'"
        )

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Failed to get link: {e}")
        await message.answer("❌ Не удалось получить ссылку")


@router.message(F.text == "ℹ️ Инструкция")
async def show_instruction(message: Message):
    """Show instruction"""
    text = (
        "ℹ️ <b>Инструкция по подключению</b>\n\n"
        "<b>📱 Для телефона:</b>\n"
        "1. Установите V2Box\n"
        "2. Получите ссылку подписки в боте\n"
        "3. В V2Box: '+' → 'Импорт из буфера обмена'\n"
        "4. Включите VPN\n\n"
        "<b>💻 Для компьютера:</b>\n"
        "1. Скачайте NekoBox\n"
        "2. Скопируйте ссылку из бота\n"
        "3. NekoBox → Программа → Добавить профиль из буфера\n"
        "4. Запустите\n\n"
        "Скачать клиенты:"
    )

    await message.answer(
        text,
        reply_markup=get_instruction_inline(),
        parse_mode="HTML"
    )


@router.message(F.text == "⚙️ Настройки")
async def show_user_settings(message: Message, session: AsyncSession, db_user: User | None):
    """Show user settings"""
    if not db_user:
        await message.answer("❌ Пользователь не найден")
        return

    settings = await get_notification_settings(session, db_user.telegram_id)

    text = (
        "⚙️ <b>Настройки</b>\n\n"
        f"{'🔔' if settings.notify_expiry else '🔕'} Уведомления об истечении\n"
        f"{'🔔' if settings.notify_traffic else '🔕'} Уведомления о трафике\n\n"
        "Нажмите на кнопку чтобы изменить:"
    )

    await message.answer(
        text,
        reply_markup=get_notification_toggle_inline(settings.notify_expiry, settings.notify_traffic),
        parse_mode="HTML"
    )


# ============= NOTIFICATION SETTINGS =============
@router.callback_query(F.data == "notification_settings")
async def notification_settings_callback(callback: CallbackQuery, session: AsyncSession, db_user: User | None):
    """Show notification settings"""
    if not db_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    settings = await get_notification_settings(session, db_user.telegram_id)

    text = (
        "🔔 <b>Настройки уведомлений</b>\n\n"
        f"{'🔔' if settings.notify_expiry else '🔕'} Уведомления об истечении\n"
        f"{'🔔' if settings.notify_traffic else '🔕'} Уведомления о трафике\n\n"
        "Нажмите на кнопку чтобы изменить:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_notification_toggle_inline(settings.notify_expiry, settings.notify_traffic),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_notify_"))
async def toggle_notification(callback: CallbackQuery, session: AsyncSession, db_user: User | None):
    """Toggle notification"""
    if not db_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    notification_type = callback.data.replace("toggle_notify_", "")
    settings = await get_notification_settings(session, db_user.telegram_id)

    if notification_type == "expiry":
        new_value = not settings.notify_expiry
        await update_notification_settings(session, db_user.telegram_id, notify_expiry=new_value)
        await callback.answer(f"{'🔔 Включено' if new_value else '🔕 Выключено'}")
    elif notification_type == "traffic":
        new_value = not settings.notify_traffic
        await update_notification_settings(session, db_user.telegram_id, notify_traffic=new_value)
        await callback.answer(f"{'🔔 Включено' if new_value else '🔕 Выключено'}")

    # Refresh
    settings = await get_notification_settings(session, db_user.telegram_id)
    text = (
        "🔔 <b>Настройки уведомлений</b>\n\n"
        f"{'🔔' if settings.notify_expiry else '🔕'} Уведомления об истечении\n"
        f"{'🔔' if settings.notify_traffic else '🔕'} Уведомления о трафике\n\n"
        "Нажмите на кнопку чтобы изменить:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_notification_toggle_inline(settings.notify_expiry, settings.notify_traffic),
        parse_mode="HTML"
    )


# ============= ADMIN: ADD USER =============
@router.message(F.text == "➕ Добавить")
async def start_add_user(message: Message, state: FSMContext, is_admin: bool):
    """Start add user flow"""
    if not is_admin:
        await message.answer("❌ Доступно только админам")
        return

    await state.set_state(AddUserStates.waiting_for_user)
    await message.answer(
        "➕ <b>Добавление пользователя</b>\n\n"
        "Нажмите кнопку ниже чтобы выбрать пользователя:",
        reply_markup=get_request_user_keyboard(),
        parse_mode="HTML"
    )


@router.message(AddUserStates.waiting_for_user, F.users_shared)
async def user_selected(message: Message, state: FSMContext, session: AsyncSession, is_admin: bool):
    """Handle user selection"""
    if not is_admin:
        return

    if not message.users_shared or not message.users_shared.users:
        await message.answer("❌ Не удалось получить пользователя")
        return

    telegram_id = message.users_shared.users[0].user_id

    # Check if exists
    existing = await get_user_by_telegram_id(session, telegram_id)
    if existing:
        await message.answer(
            f"❌ Пользователь уже существует\n"
            f"Marzban username: <code>{existing.marzban_username}</code>",
            reply_markup=get_main_admin_keyboard(),
            parse_mode="HTML"
        )
        await state.clear()
        return

    # Store and ask for marzban username
    await state.update_data(telegram_id=telegram_id)
    await state.set_state(AddUserStates.waiting_for_marzban_username)

    await message.answer(
        f"✅ Пользователь выбран: <code>{telegram_id}</code>\n\n"
        "Теперь введите <b>Marzban username</b>:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AddUserStates.waiting_for_marzban_username, F.text)
async def marzban_username_entered(
    message: Message, state: FSMContext, session: AsyncSession, marzban: MarzbanAPI, is_admin: bool
):
    """Handle marzban username"""
    if not is_admin:
        return

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_main_admin_keyboard())
        return

    marzban_username = message.text.strip()

    # Get telegram_id from state
    data = await state.get_data()
    telegram_id = data.get("telegram_id")

    # Check existing bindings for Marzban user
    existing_bindings = await list_user_bindings(session, marzban_username)

    # Prevent duplicate telegram binding
    if any(binding.telegram_id == telegram_id for binding in existing_bindings):
        await message.answer(
            f"❌ Telegram ID <code>{telegram_id}</code> уже привязан к <code>{marzban_username}</code>",
            parse_mode="HTML",
        )
        await state.clear()
        return

    # Check if exists in Marzban, if not - create
    try:
        marzban_user = await marzban.get_user(marzban_username)
    except MarzbanAPIError:
        # User not found, create automatically
        try:
            await message.answer(
                f"⏳ Пользователь <code>{marzban_username}</code> не найден в Marzban\n"
                "Создаю автоматически...",
                parse_mode="HTML"
            )
            marzban_user = await marzban.create_user(
                username=marzban_username,
                data_limit=None,  # Unlimited
                expire=None,  # Unlimited
                status="active",
                note=f"Created via bot for TG user {telegram_id}"
            )
            logger.info(f"Auto-created user {marzban_username} in Marzban")
        except MarzbanAPIError as e:
            await message.answer(
                f"❌ Не удалось создать пользователя в Marzban: {e}",
                parse_mode="HTML"
            )
            return

    existing_summary = ""
    if existing_bindings:
        summary_lines = []
        for binding in existing_bindings:
            badge = "⭐️" if binding.primary_user else "•"
            summary_lines.append(f"{badge} <code>{binding.telegram_id}</code>")

        existing_summary = (
            "\n\n⚠️ <b>Текущие привязки:</b>\n"
            + "\n".join(summary_lines)
            + "\n➕ Новый Telegram ID будет добавлен как дополнительный."
        )
    else:
        existing_summary = "\n\n⭐️ Это будет основная привязка для пользователя."

    # Store and confirm
    await state.update_data(marzban_username=marzban_username)

    await message.answer(
        f"✅ <b>Подтвердите:</b>\n\n"
        f"Telegram ID: <code>{data['telegram_id']}</code>\n"
        f"Marzban username: <code>{marzban_username}</code>\n"
        f"Статус: {marzban_user.status}"
        f"{existing_summary}",
        reply_markup=get_confirmation_inline("confirm_add_user"),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "confirm_add_user")
async def confirm_add_user(callback: CallbackQuery, state: FSMContext, session: AsyncSession, is_admin: bool):
    """Confirm and create user"""
    if not is_admin:
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    data = await state.get_data()
    telegram_id = data["telegram_id"]
    marzban_username = data["marzban_username"]

    try:
        new_user = await create_user(session, telegram_id, marzban_username)
    except ValueError as error:
        await callback.answer(f"❌ {error}", show_alert=True)
        return

    await log_admin_action(
        session,
        callback.from_user.id,
        "add_user",
        marzban_username,
        f"tg: {telegram_id}, primary={new_user.primary_user}",
    )

    bindings = await list_user_bindings(session, marzban_username)
    bindings_lines = []
    for binding in bindings:
        badge = "⭐️" if binding.primary_user else "•"
        bindings_lines.append(f"{badge} <code>{binding.telegram_id}</code>")

    role_note = (
        "⭐️ Назначен основным Telegram-аккаунтом."
        if new_user.primary_user
        else "➕ Добавлен как дополнительный Telegram-аккаунт."
    )

    bindings_block = (
        "\n\n📌 <b>Актуальные привязки:</b>\n" + "\n".join(bindings_lines)
        if bindings_lines
        else ""
    )

    await callback.message.edit_text(
        f"✅ <b>Пользователь добавлен</b>\n\n"
        f"Telegram ID: <code>{telegram_id}</code>\n"
        f"Marzban username: <code>{marzban_username}</code>\n"
        f"{role_note}"
        f"{bindings_block}",
        parse_mode="HTML"
    )
    await callback.answer()
    await state.clear()

    # Send notification with keyboard
    await callback.message.answer(
        "Готово! Используйте кнопки ниже:",
        reply_markup=get_main_admin_keyboard()
    )


# ============= ADMIN: SEARCH USER =============
@router.message(F.text == "🔍 Найти")
async def start_search(message: Message, state: FSMContext, is_admin: bool):
    """Start search"""
    if not is_admin:
        await message.answer("❌ Доступно только админам")
        return

    await state.set_state(SearchUserStates.waiting_for_query)
    await message.answer(
        "🔍 <b>Поиск пользователя</b>\n\n"
        "Введите Telegram ID или Marzban username:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(SearchUserStates.waiting_for_query, F.text)
async def search_query(message: Message, state: FSMContext, session: AsyncSession, is_admin: bool):
    """Handle search query"""
    if not is_admin:
        return

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_main_admin_keyboard())
        return

    query = message.text.strip()
    users = await search_users(session, query)

    if not users:
        await message.answer(f"❌ Не найдено: <code>{query}</code>", parse_mode="HTML")
        return

    text = f"🔍 <b>Найдено ({len(users)}):</b>\n\n"
    for user in users:
        admin_badge = "👑 " if user.is_admin else ""
        role_label = "⭐️ Основной" if user.primary_user else "➕ Дополнительный"
        text += (
            f"{admin_badge}<b>{user.marzban_username}</b>\n"
            f"├ Роль: {role_label}\n"
            f"├ TG ID: <code>{user.telegram_id}</code>\n"
            f"└ Создан: {user.created_at.strftime('%d.%m.%Y')}\n\n"
        )

    await message.answer(text, reply_markup=get_main_admin_keyboard(), parse_mode="HTML")
    await state.clear()


# ============= ADMIN: LIST USERS =============
@router.message(F.text == "📋 Список")
async def list_all_users(message: Message, is_admin: bool, session: AsyncSession):
    """List users with pagination"""
    if not is_admin:
        await message.answer("❌ Доступно только админам")
        return

    await show_users_page(message, session, 0)


async def show_users_page(message: Message, session: AsyncSession, page: int):
    """Show users page"""
    page_size = 10
    offset = page * page_size

    users, total = await list_users(session, offset=offset, limit=page_size)
    total_pages = math.ceil(total / page_size)

    if not users:
        await message.answer("📋 Пользователей не найдено")
        return

    text = f"👥 <b>Список пользователей</b> (стр. {page + 1}/{total_pages})\nВсего: {total}\n\n"

    for i, user in enumerate(users, start=offset + 1):
        admin_badge = "👑 " if user.is_admin else ""
        role_label = "⭐️ Основной" if user.primary_user else "➕ Дополнительный"
        text += (
            f"{i}. {admin_badge}<b>{user.marzban_username}</b>\n"
            f"   ├ Роль: {role_label}\n"
            f"   ├ TG ID: <code>{user.telegram_id}</code>\n"
            f"   └ Создан: {user.created_at.strftime('%d.%m.%Y')}\n\n"
        )

    await message.answer(
        text,
        reply_markup=get_user_list_navigation(page, total_pages),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("users_page:"))
async def users_pagination(callback: CallbackQuery, session: AsyncSession, is_admin: bool):
    """Handle pagination"""
    if not is_admin:
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    page = int(callback.data.split(":")[1])
    page_size = 10
    offset = page * page_size

    users, total = await list_users(session, offset=offset, limit=page_size)
    total_pages = math.ceil(total / page_size)

    text = f"👥 <b>Список пользователей</b> (стр. {page + 1}/{total_pages})\nВсего: {total}\n\n"

    for i, user in enumerate(users, start=offset + 1):
        admin_badge = "👑 " if user.is_admin else ""
        role_label = "⭐️ Основной" if user.primary_user else "➕ Дополнительный"
        text += (
            f"{i}. {admin_badge}<b>{user.marzban_username}</b>\n"
            f"   ├ Роль: {role_label}\n"
            f"   ├ TG ID: <code>{user.telegram_id}</code>\n"
            f"   └ Создан: {user.created_at.strftime('%d.%m.%Y')}\n\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=get_user_list_navigation(page, total_pages),
        parse_mode="HTML"
    )
    await callback.answer()


# ============= ADMIN: STATS =============
@router.message(F.text == "📊 Статистика")
async def show_stats(message: Message, is_admin: bool, session: AsyncSession):
    """Show statistics"""
    if not is_admin:
        await message.answer("❌ Доступно только админам")
        return

    users, total = await list_users(session, limit=1000)

    admin_count = sum(1 for u in users if u.is_admin)
    primary_count = sum(1 for u in users if u.primary_user)
    secondary_count = total - primary_count

    text = (
        "📊 <b>Статистика</b>\n\n"
        f"👥 Всего привязок: <b>{total}</b>\n"
        f"⭐️ Основных аккаунтов: <b>{primary_count}</b>\n"
        f"➕ Дополнительных аккаунтов: <b>{secondary_count}</b>\n"
        f"👑 Администраторов: <b>{admin_count}</b>\n"
        f"👤 Обычных: <b>{total - admin_count}</b>"
    )

    await message.answer(text, parse_mode="HTML")


# ============= CANCEL =============
@router.message(F.text == "❌ Отмена")
async def cancel_action(message: Message, state: FSMContext, is_admin: bool):
    """Cancel any action"""
    await state.clear()
    keyboard = get_main_admin_keyboard() if is_admin else get_main_user_keyboard()
    await message.answer("❌ Отменено", reply_markup=keyboard)


@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext, is_admin: bool):
    """Cancel via callback"""
    await state.clear()
    await callback.message.edit_text("❌ Отменено")
    await callback.answer()

    keyboard = get_main_admin_keyboard() if is_admin else get_main_user_keyboard()
    await callback.message.answer(
        "Используйте кнопки ниже:",
        reply_markup=keyboard
    )
