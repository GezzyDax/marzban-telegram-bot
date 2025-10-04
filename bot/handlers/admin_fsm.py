"""FSM-based admin handlers"""

import logging

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestUsers,
    ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states import AddUserStates, SearchUserStates, ToggleUserStatusStates
from bot.database import (
    create_user,
    get_user_by_telegram_id,
    list_user_bindings,
    log_admin_action,
    search_users,
)
from bot.services import MarzbanAPI, MarzbanAPIError
from bot.keyboards.admin_extended import (
    get_users_management_menu,
    get_cancel_button,
    get_confirmation_keyboard,
    get_user_search_result_keyboard,
)
from bot.utils.rate_limiter import rate_limit

logger = logging.getLogger(__name__)
router = Router(name="admin_fsm")


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

    wrapper.__name__ = handler.__name__
    wrapper.__module__ = handler.__module__
    return wrapper


# ============= User Management Menu =============
@router.callback_query(F.data == "admin_users_menu")
@admin_only
async def show_users_menu(callback: CallbackQuery, **kwargs):
    """Show user management menu"""
    await callback.message.edit_text(
        "👥 <b>Управление пользователями</b>\n\n" "Выберите действие:", reply_markup=get_users_management_menu(), parse_mode="HTML"
    )
    await callback.answer()


# ============= Add User FSM =============
@router.callback_query(F.data == "admin_add_user_start")
@admin_only
@rate_limit(seconds=3, action="add_user")
async def start_add_user(callback: CallbackQuery, state: FSMContext, **kwargs):
    """Start add user flow"""
    await state.set_state(AddUserStates.waiting_for_user)

    # Create keyboard with request_users button
    request_button = KeyboardButton(
        text="👤 Выбрать пользователя из Telegram", request_users=KeyboardButtonRequestUsers(request_id=1, user_is_bot=False)
    )
    keyboard = ReplyKeyboardMarkup(keyboard=[[request_button]], resize_keyboard=True, one_time_keyboard=True)

    await callback.message.answer(
        "➕ <b>Добавление пользователя</b>\n\n"
        "Нажмите кнопку ниже, чтобы выбрать пользователя из Telegram.\n\n"
        "Или отправьте /cancel для отмены.",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AddUserStates.waiting_for_user, F.users_shared)
@admin_only
async def user_selected(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    """Handle user selection via users_shared"""
    if not message.users_shared or not message.users_shared.users:
        await message.answer("❌ Не удалось получить информацию о пользователе")
        return

    selected_user = message.users_shared.users[0]
    telegram_id = selected_user.user_id

    # Check if user already exists
    existing_user = await get_user_by_telegram_id(session, telegram_id)
    if existing_user:
        await message.answer(
            f"❌ Пользователь с Telegram ID <code>{telegram_id}</code> уже существует\n"
            f"Marzban username: <code>{existing_user.marzban_username}</code>",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML",
        )
        await state.clear()
        return

    # Store telegram_id and ask for marzban username
    await state.update_data(telegram_id=telegram_id)
    await state.set_state(AddUserStates.waiting_for_marzban_username)

    await message.answer(
        f"✅ Пользователь выбран: <code>{telegram_id}</code>\n\n" "Теперь введите <b>Marzban username</b> для этого пользователя:",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML",
    )


@router.message(AddUserStates.waiting_for_marzban_username, F.text)
@admin_only
async def marzban_username_entered(
    message: Message, state: FSMContext, session: AsyncSession, marzban: MarzbanAPI, **kwargs
):
    """Handle marzban username input"""
    marzban_username = message.text.strip()

    data = await state.get_data()
    telegram_id = data.get("telegram_id")
    if telegram_id is None:
        await state.clear()
        await message.answer(
            "❌ Не удалось определить Telegram ID, начните заново",
            parse_mode="HTML",
        )
        return

    bindings = await list_user_bindings(session, marzban_username)
    if any(binding.telegram_id == telegram_id for binding in bindings):
        await message.answer(
            f"❌ Telegram ID <code>{telegram_id}</code> уже привязан к <code>{marzban_username}</code>",
            parse_mode="HTML",
        )
        await state.clear()
        return

    # Check if user exists in Marzban
    try:
        marzban_user = await marzban.get_user(marzban_username)
    except MarzbanAPIError:
        await message.answer(
            f"❌ Пользователь <code>{marzban_username}</code> не найден в Marzban\n\n"
            "Сначала создайте пользователя в панели Marzban: https://marzban.gezzy.ru",
            parse_mode="HTML",
        )
        return

    existing_summary = ""
    if bindings:
        summary_lines = []
        for binding in bindings:
            badge = "⭐️" if binding.primary_user else "•"
            summary_lines.append(f"{badge} <code>{binding.telegram_id}</code>")

        existing_summary = (
            "\n\n⚠️ <b>Текущие привязки:</b>\n"
            + "\n".join(summary_lines)
            + "\n➕ Новый Telegram ID будет добавлен как дополнительный."
        )
    else:
        existing_summary = "\n\n⭐️ Это будет основная привязка для пользователя."

    # Store marzban_username and show confirmation
    await state.update_data(marzban_username=marzban_username)

    await message.answer(
        f"✅ <b>Подтвердите добавление пользователя</b>\n\n"
        f"Telegram ID: <code>{telegram_id}</code>\n"
        f"Marzban username: <code>{marzban_username}</code>\n"
        f"Статус в Marzban: {marzban_user.status}"
        f"{existing_summary}",
        reply_markup=get_confirmation_keyboard("confirm_add_user"),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "confirm_add_user", AddUserStates.waiting_for_marzban_username)
@admin_only
async def confirm_add_user(callback: CallbackQuery, state: FSMContext, session: AsyncSession, **kwargs):
    """Confirm and create user"""
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
        f"telegram_id: {telegram_id}, primary={new_user.primary_user}",
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
        f"✅ <b>Пользователь успешно добавлен</b>\n\n"
        f"Telegram ID: <code>{telegram_id}</code>\n"
        f"Marzban username: <code>{marzban_username}</code>\n"
        f"{role_note}"
        f"{bindings_block}\n\n"
        "Пользователь может начать работу с ботом командой /start",
        parse_mode="HTML",
    )
    await callback.answer()
    await state.clear()


# ============= Search User FSM =============
@router.callback_query(F.data == "admin_search_user_start")
@admin_only
@rate_limit(seconds=2, action="search")
async def start_search_user(callback: CallbackQuery, state: FSMContext, **kwargs):
    """Start search user flow"""
    await state.set_state(SearchUserStates.waiting_for_query)
    await callback.message.answer(
        "🔍 <b>Поиск пользователя</b>\n\n"
        "Введите Telegram ID или часть Marzban username:\n\n"
        "Или отправьте /cancel для отмены.",
        reply_markup=get_cancel_button(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(SearchUserStates.waiting_for_query, F.text)
@admin_only
async def search_query_entered(message: Message, state: FSMContext, session: AsyncSession, marzban: MarzbanAPI, **kwargs):
    """Handle search query"""
    query = message.text.strip()
    users = await search_users(session, query)

    if not users:
        await message.answer(f"❌ Пользователи не найдены по запросу: <code>{query}</code>", parse_mode="HTML")
        return

    await message.answer(f"🔍 <b>Найдено пользователей:</b> {len(users)}\n", parse_mode="HTML")

    # Send each user as a separate message with action buttons
    for user in users:
        admin_badge = "👑 " if user.is_admin else ""
        role_label = "⭐️ Основной" if user.primary_user else "➕ Дополнительный"

        # Get user status from Marzban
        try:
            marzban_user = await marzban.get_user(user.marzban_username)
            status_emoji = "🟢" if marzban_user.status == "active" else "🔴"
            status_text = "Активен" if marzban_user.status == "active" else "Отключен"

            text = (
                f"{admin_badge}<b>{user.marzban_username}</b> {status_emoji}\n"
                f"├ Роль: {role_label}\n"
                f"├ TG ID: <code>{user.telegram_id}</code>\n"
                f"├ Статус: {status_text}\n"
                f"└ Создан: {user.created_at.strftime('%d.%m.%Y')}\n"
            )

            # Add action buttons
            keyboard = get_user_search_result_keyboard(user.telegram_id, marzban_user.status)
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        except MarzbanAPIError as e:
            logger.error(f"Failed to get Marzban user {user.marzban_username}: {e}")
            text = (
                f"{admin_badge}<b>{user.marzban_username}</b>\n"
                f"├ Роль: {role_label}\n"
                f"├ TG ID: <code>{user.telegram_id}</code>\n"
                f"├ Статус: ⚠️ Ошибка получения данных\n"
                f"└ Создан: {user.created_at.strftime('%d.%m.%Y')}\n"
            )
            await message.answer(text, parse_mode="HTML")

    await state.clear()


# ============= Cancel FSM =============
@router.callback_query(F.data == "fsm_cancel")
async def cancel_fsm_callback(callback: CallbackQuery, state: FSMContext):
    """Cancel FSM via callback"""
    await state.clear()
    await callback.message.edit_text("❌ Операция отменена")
    await callback.answer()


@router.message(F.command("cancel"))
async def cancel_fsm_command(message: Message, state: FSMContext):
    """Cancel FSM via command"""
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("❌ Операция отменена", reply_markup=ReplyKeyboardRemove())


# ============= Toggle User Status =============
@router.callback_query(F.data.startswith("toggle_status:"))
@admin_only
@rate_limit(seconds=3, action="toggle_status")
async def toggle_status_start(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, marzban: MarzbanAPI, db_user, **kwargs
):
    """Start status toggle confirmation"""
    # Parse callback data: toggle_status:telegram_id:new_status
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("❌ Неверный формат данных", show_alert=True)
        return

    target_telegram_id = int(parts[1])
    new_status = parts[2]

    # Get target user from database
    target_user = await get_user_by_telegram_id(session, target_telegram_id)
    if not target_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    # Get current Marzban data
    try:
        marzban_user = await marzban.get_user(target_user.marzban_username)
    except MarzbanAPIError as e:
        logger.error(f"Failed to get Marzban user: {e}")
        await callback.answer("❌ Ошибка получения данных из Marzban", show_alert=True)
        return

    # Store data in FSM
    await state.update_data(
        target_telegram_id=target_telegram_id,
        target_username=target_user.marzban_username,
        new_status=new_status,
        old_status=marzban_user.status,
    )
    await state.set_state(ToggleUserStatusStates.confirmation)

    # Show confirmation
    status_change_text = f"{'🔴 Отключить' if new_status == 'disabled' else '🟢 Включить'}"
    text = (
        f"⚠️ <b>Подтверждение изменения статуса</b>\n\n"
        f"Пользователь: <b>{target_user.marzban_username}</b>\n"
        f"TG ID: <code>{target_telegram_id}</code>\n\n"
        f"Текущий статус: {'🟢 Активен' if marzban_user.status == 'active' else '🔴 Отключен'}\n"
        f"Новый статус: {status_change_text}\n\n"
        f"Подтвердите изменение:"
    )

    keyboard = get_confirmation_keyboard("toggle_status_confirm")
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "toggle_status_confirm", ToggleUserStatusStates.confirmation)
@admin_only
async def toggle_status_confirm(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, marzban: MarzbanAPI, db_user, **kwargs
):
    """Confirm and execute status toggle"""
    data = await state.get_data()
    target_telegram_id = data["target_telegram_id"]
    target_username = data["target_username"]
    new_status = data["new_status"]
    old_status = data["old_status"]

    try:
        # Update status in Marzban
        await marzban.modify_user(target_username, status=new_status)

        # Log admin action
        await log_admin_action(
            session,
            admin_id=db_user.id,
            action="toggle_status",
            details=f"Changed status for {target_username} (TG: {target_telegram_id}) from {old_status} to {new_status}",
        )

        # Send notification to target user
        try:
            from aiogram import Bot

            bot: Bot = callback.bot
            notification_text = (
                f"⚠️ <b>Изменение статуса</b>\n\n"
                f"Ваш статус был изменен администратором:\n"
                f"{'🟢 Доступ восстановлен' if new_status == 'active' else '🔴 Доступ временно приостановлен'}\n\n"
                f"По вопросам обращайтесь к администратору."
            )
            await bot.send_message(target_telegram_id, notification_text, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Failed to send notification to user {target_telegram_id}: {e}")

        # Success message
        success_text = (
            f"✅ <b>Статус изменен</b>\n\n"
            f"Пользователь: <b>{target_username}</b>\n"
            f"Новый статус: {'🟢 Активен' if new_status == 'active' else '🔴 Отключен'}\n\n"
            f"Пользователь был уведомлен об изменении."
        )
        await callback.message.edit_text(success_text, parse_mode="HTML")

    except MarzbanAPIError as e:
        logger.error(f"Failed to toggle status: {e}")
        await callback.message.edit_text(f"❌ <b>Ошибка изменения статуса</b>\n\n{str(e)}", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Unexpected error during status toggle: {e}")
        await callback.message.edit_text(f"❌ <b>Неожиданная ошибка</b>\n\n{str(e)}", parse_mode="HTML")
    finally:
        await state.clear()
        await callback.answer()
