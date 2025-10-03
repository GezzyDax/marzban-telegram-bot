"""Улучшенные админские хендлеры с синхронизацией Marzban"""

import logging
import math
from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import (
    User,
    get_user_by_telegram_id,
    get_user_by_marzban_username,
    create_user,
    list_users,
    search_users,
    log_admin_action,
)
from bot.services import MarzbanAPI, MarzbanAPIError
from bot.services.formatters import format_bytes
from bot.keyboards.inline import (
    get_admin_main_menu,
    get_request_user_keyboard,
    get_cancel_inline,
    get_confirmation_inline,
    get_user_list_navigation,
    get_back_to_admin_menu,
)
from bot.states import AddUserStates, SearchUserStates

logger = logging.getLogger(__name__)
router = Router(name="admin_improved")


# ============= ADMIN: ADD USER =============
@router.callback_query(F.data == "admin_add_user")
async def start_add_user(callback: CallbackQuery, state: FSMContext, is_admin: bool):
    """Start add user flow"""
    if not is_admin:
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    await state.set_state(AddUserStates.waiting_for_user)

    # Need to send new message for ReplyKeyboard
    await callback.message.answer(
        "➕ <b>Добавление пользователя</b>\n\n"
        "Шаг 1: Выберите пользователя Telegram\n\n"
        "Нажмите кнопку ниже чтобы выбрать пользователя:",
        reply_markup=get_request_user_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


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
            f"❌ <b>Пользователь уже существует</b>\n\n"
            f"Telegram ID: <code>{telegram_id}</code>\n"
            f"Marzban username: <code>{existing.marzban_username}</code>",
            parse_mode="HTML"
        )
        await state.clear()
        return

    # Store and ask for marzban username
    await state.update_data(telegram_id=telegram_id)
    await state.set_state(AddUserStates.waiting_for_marzban_username)

    await message.answer(
        f"✅ Пользователь выбран: <code>{telegram_id}</code>\n\n"
        "Шаг 2: Введите <b>Marzban username</b>\n\n"
        "Если пользователя нет в Marzban, он будет создан автоматически.",
        parse_mode="HTML"
    )


@router.message(AddUserStates.waiting_for_marzban_username, F.text)
async def marzban_username_entered(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    marzban: MarzbanAPI,
    is_admin: bool
):
    """Handle marzban username entry"""
    if not is_admin:
        return

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено")
        return

    marzban_username = message.text.strip()

    # Validate username
    if not marzban_username or len(marzban_username) < 3:
        await message.answer("❌ Username должен содержать минимум 3 символа")
        return

    # Check if username already linked
    existing = await get_user_by_marzban_username(session, marzban_username)
    if existing:
        await message.answer(
            f"❌ Username <code>{marzban_username}</code> уже привязан к другому пользователю\n"
            f"Telegram ID: <code>{existing.telegram_id}</code>",
            parse_mode="HTML"
        )
        return

    # Get telegram_id from state
    data = await state.get_data()
    telegram_id = data.get("telegram_id")

    # Check if exists in Marzban, if not - create
    marzban_user = None
    try:
        marzban_user = await marzban.get_user(marzban_username)
        logger.info(f"User {marzban_username} found in Marzban (status: {marzban_user.status})")
    except MarzbanAPIError as e:
        # User not found, try to create
        logger.info(f"User {marzban_username} not found in Marzban, attempting to create")

        try:
            await message.answer(
                f"⏳ Пользователь <code>{marzban_username}</code> не найден в Marzban\n"
                "Создаю автоматически с параметрами:\n"
                "• Трафик: Безлимит\n"
                "• Срок: Бессрочно\n"
                "• Статус: Активен",
                parse_mode="HTML"
            )

            marzban_user = await marzban.create_user(
                username=marzban_username,
                data_limit=0,  # 0 = unlimited
                expire=0,  # 0 = unlimited
                status="active",
                note=f"Created via bot for TG user {telegram_id}"
            )
            logger.info(f"Successfully created user {marzban_username} in Marzban")

        except MarzbanAPIError as create_error:
            # Check if error is "already exists" (409)
            if "already exists" in str(create_error).lower() or "409" in str(create_error):
                logger.warning(f"User {marzban_username} already exists (race condition), fetching...")
                # User was created between our check and creation attempt, fetch it
                try:
                    marzban_user = await marzban.get_user(marzban_username)
                    logger.info(f"Successfully fetched existing user {marzban_username}")
                except MarzbanAPIError as fetch_error:
                    logger.error(f"Failed to fetch user after 409: {fetch_error}", exc_info=True)
                    await message.answer(
                        f"❌ Ошибка: пользователь существует в Marzban, но не удалось получить его данные",
                        parse_mode="HTML"
                    )
                    await state.clear()
                    return
            else:
                logger.error(f"Failed to create user in Marzban: {create_error}", exc_info=True)
                await message.answer(
                    f"❌ Не удалось создать пользователя в Marzban:\n{str(create_error)}",
                    parse_mode="HTML"
                )
                await state.clear()
                return

    # Safety check
    if marzban_user is None:
        logger.error(f"marzban_user is None after all attempts for {marzban_username}")
        await message.answer(
            "❌ Не удалось получить данные пользователя из Marzban",
            parse_mode="HTML"
        )
        await state.clear()
        return

    # Store and ask for confirmation
    await state.update_data(marzban_username=marzban_username)
    await state.set_state(AddUserStates.waiting_for_confirmation)

    await message.answer(
        f"✅ <b>Подтвердите добавление:</b>\n\n"
        f"Telegram ID: <code>{telegram_id}</code>\n"
        f"Marzban username: <code>{marzban_username}</code>\n"
        f"Статус в Marzban: <b>{marzban_user.status.upper()}</b>",
        reply_markup=get_confirmation_inline("confirm_add_user"),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "confirm_add_user")
async def confirm_add_user(callback: CallbackQuery, state: FSMContext, session: AsyncSession, is_admin: bool):
    """Confirm and create user in bot DB"""
    if not is_admin:
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    data = await state.get_data()
    telegram_id = data["telegram_id"]
    marzban_username = data["marzban_username"]

    await create_user(session, telegram_id, marzban_username)
    await log_admin_action(session, callback.from_user.id, "add_user", marzban_username, f"tg: {telegram_id}")

    await callback.message.edit_text(
        f"✅ <b>Пользователь успешно добавлен!</b>\n\n"
        f"Telegram ID: <code>{telegram_id}</code>\n"
        f"Marzban username: <code>{marzban_username}</code>\n\n"
        "Пользователь может начать работу с ботом командой /start",
        parse_mode="HTML"
    )
    await callback.answer("✅ Пользователь добавлен")
    await state.clear()


# ============= ADMIN: LIST USERS (с синхронизацией Marzban) =============
@router.callback_query(F.data == "admin_list_users")
@router.callback_query(F.data.startswith("admin_users_page:"))
async def list_all_users(callback: CallbackQuery, is_admin: bool, session: AsyncSession, marzban: MarzbanAPI):
    """List users with Marzban sync"""
    if not is_admin:
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    # Parse page
    page = 0
    if ":" in callback.data:
        page = int(callback.data.split(":")[1])

    page_size = 10
    offset = page * page_size

    try:
        # Get Marzban users
        logger.info(f"Fetching Marzban users list (offset={offset}, limit={page_size})")
        marzban_users_list, marzban_total = await marzban.list_users(offset=offset, limit=page_size)

        if marzban_users_list is None:
            logger.error("marzban.list_users() returned None for users list")
            await callback.answer("❌ Marzban API вернул пустой ответ", show_alert=True)
            return

        logger.info(f"Got {len(marzban_users_list)} users from Marzban (total: {marzban_total})")

        # Get bot DB users
        db_users, db_total = await list_users(session, offset=0, limit=1000)
        db_users_dict = {u.marzban_username: u for u in db_users}
        logger.info(f"Got {db_total} users from bot database")

        total_pages = math.ceil(marzban_total / page_size) if marzban_total > 0 else 1

        text = (
            f"📋 <b>Список пользователей Marzban</b>\n"
            f"Страница {page + 1}/{total_pages}\n"
            f"Всего в Marzban: <b>{marzban_total}</b>\n"
            f"Зарегистрировано в боте: <b>{db_total}</b>\n\n"
        )

        if not marzban_users_list:
            text += "📭 Пользователей не найдено на этой странице"
        else:
            for i, marzban_user_data in enumerate(marzban_users_list, start=offset + 1):
                if not isinstance(marzban_user_data, dict):
                    logger.warning(f"Invalid user data format at index {i}: {type(marzban_user_data)}")
                    continue

                username = marzban_user_data.get('username', 'unknown')
                status = marzban_user_data.get('status', 'unknown')
                used = marzban_user_data.get('used_traffic', 0)

                # Check if in bot DB
                in_bot = "✅" if username in db_users_dict else "❌"

                # Admin badge
                admin_badge = "👑 " if username in db_users_dict and db_users_dict[username].is_admin else ""

                text += (
                    f"{i}. {admin_badge}<b>{username}</b> {in_bot}\n"
                    f"   ├ Статус: {status}\n"
                    f"   └ Использовано: {format_bytes(used)}\n\n"
                )

            text += "\n✅ - в боте | ❌ - не в боте"

        await callback.message.edit_text(
            text,
            reply_markup=get_user_list_navigation(page, total_pages),
            parse_mode="HTML"
        )
        await callback.answer()

    except MarzbanAPIError as e:
        logger.error(f"Marzban API error while listing users: {e}", exc_info=True)
        await callback.answer(f"❌ Ошибка Marzban API: {str(e)}", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error while listing users: {e}", exc_info=True)
        await callback.answer("❌ Не удалось получить список пользователей", show_alert=True)


# ============= ADMIN: SEARCH USER =============
@router.callback_query(F.data == "admin_search_user")
async def start_search(callback: CallbackQuery, state: FSMContext, is_admin: bool):
    """Start search flow"""
    if not is_admin:
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    await state.set_state(SearchUserStates.waiting_for_query)

    await callback.message.answer(
        "🔍 <b>Поиск пользователя</b>\n\n"
        "Введите Telegram ID или Marzban username:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(SearchUserStates.waiting_for_query, F.text)
async def search_query(message: Message, state: FSMContext, session: AsyncSession, marzban: MarzbanAPI, is_admin: bool):
    """Handle search query"""
    if not is_admin:
        return

    query = message.text.strip()

    # Search in bot DB
    db_users = await search_users(session, query)

    # Try to find in Marzban
    marzban_user = None
    try:
        marzban_user = await marzban.get_user(query)
    except MarzbanAPIError:
        pass

    if not db_users and not marzban_user:
        await message.answer(
            f"❌ Не найдено: <code>{query}</code>\n\n"
            "Пользователь не найден ни в боте, ни в Marzban.",
            parse_mode="HTML"
        )
        await state.clear()
        return

    text = f"🔍 <b>Результаты поиска:</b> <code>{query}</code>\n\n"

    # Bot DB results
    if db_users:
        text += f"<b>📊 В базе бота ({len(db_users)}):</b>\n\n"
        for user in db_users:
            admin_badge = "👑 " if user.is_admin else ""
            text += (
                f"{admin_badge}<b>{user.marzban_username}</b>\n"
                f"├ TG ID: <code>{user.telegram_id}</code>\n"
                f"└ Создан: {user.created_at.strftime('%d.%m.%Y')}\n\n"
            )

    # Marzban results
    if marzban_user:
        in_bot = any(u.marzban_username == marzban_user.username for u in db_users) if db_users else False

        text += f"\n<b>🔐 В Marzban:</b>\n\n"
        text += f"<b>{marzban_user.username}</b>\n"
        text += f"├ Статус: {marzban_user.status}\n"
        text += f"├ Использовано: {format_bytes(marzban_user.used_traffic)}\n"
        text += f"└ В боте: {'✅ Да' if in_bot else '❌ Нет'}\n"

    await message.answer(text, parse_mode="HTML")
    await state.clear()


# ============= ADMIN: STATISTICS (улучшенная) =============
@router.callback_query(F.data == "admin_stats")
async def show_advanced_stats(callback: CallbackQuery, is_admin: bool, session: AsyncSession, marzban: MarzbanAPI):
    """Show advanced statistics with Marzban data"""
    if not is_admin:
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    try:
        # Get bot users
        logger.info("Fetching bot database users for statistics")
        db_users, db_total = await list_users(session, limit=1000)
        db_admins = sum(1 for u in db_users if u.is_admin)
        logger.info(f"Bot DB: {db_total} users ({db_admins} admins)")

        # Get Marzban stats
        logger.info("Fetching Marzban users for statistics")
        marzban_users_list, marzban_total = await marzban.list_users(offset=0, limit=1000)

        if marzban_users_list is None:
            logger.error("marzban.list_users() returned None in statistics")
            marzban_users_list = []
            marzban_total = 0

        logger.info(f"Marzban API: {marzban_total} users ({len(marzban_users_list)} fetched)")

        # Calculate Marzban stats
        active_users = sum(1 for u in marzban_users_list if isinstance(u, dict) and u.get('status') == 'active')
        disabled_users = sum(1 for u in marzban_users_list if isinstance(u, dict) and u.get('status') == 'disabled')
        limited_users = sum(1 for u in marzban_users_list if isinstance(u, dict) and u.get('status') == 'limited')
        expired_users = sum(1 for u in marzban_users_list if isinstance(u, dict) and u.get('status') == 'expired')

        # Calculate total traffic
        total_traffic = sum(u.get('used_traffic', 0) for u in marzban_users_list if isinstance(u, dict))

        # Calculate online users (активность за последние 5 минут)
        now = datetime.now().timestamp()
        online_users = sum(1 for u in marzban_users_list
                          if isinstance(u, dict) and u.get('online_at') and (now - u.get('online_at')) < 300)

        text = (
            "📊 <b>Расширенная статистика</b>\n\n"
            "<b>📊 База бота:</b>\n"
            f"├ Всего пользователей: <b>{db_total}</b>\n"
            f"├ Администраторов: <b>{db_admins}</b>\n"
            f"└ Обычных: <b>{db_total - db_admins}</b>\n\n"
            "<b>🔐 Marzban панель:</b>\n"
            f"├ Всего аккаунтов: <b>{marzban_total}</b>\n"
            f"├ 🟢 Активных: <b>{active_users}</b>\n"
            f"├ 🔴 Отключенных: <b>{disabled_users}</b>\n"
            f"├ 🟡 Ограниченных: <b>{limited_users}</b>\n"
            f"├ ⚪️ Истекших: <b>{expired_users}</b>\n"
            f"└ 💚 Онлайн сейчас: <b>{online_users}</b>\n\n"
            "<b>📈 Трафик:</b>\n"
            f"└ Общий использованный: <b>{format_bytes(total_traffic)}</b>\n\n"
            f"<b>🔗 Синхронизация:</b>\n"
            f"└ В боте / В Marzban: <b>{db_total}/{marzban_total}</b>"
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_admin_menu(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        await callback.answer("❌ Не удалось получить статистику", show_alert=True)


# ============= CANCEL ACTIONS =============
@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext, is_admin: bool):
    """Cancel current action"""
    await state.clear()

    if is_admin:
        await callback.message.edit_text(
            "❌ Действие отменено",
            reply_markup=get_admin_main_menu()
        )
    else:
        await callback.message.edit_text("❌ Действие отменено")

    await callback.answer()


# No-op handler for pagination display
@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    """No operation - just for display"""
    await callback.answer()
