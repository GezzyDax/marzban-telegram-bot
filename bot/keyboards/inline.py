"""Inline keyboards - все взаимодействия только через callback кнопки"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, KeyboardButtonRequestUsers


# ============= USER MENU =============
def get_user_main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Main user menu - inline buttons"""
    buttons = [
        [
            InlineKeyboardButton(text="📊 Подписка", callback_data="user_subscription"),
            InlineKeyboardButton(text="🔗 Ссылка", callback_data="user_link")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Инструкция", callback_data="user_instruction"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="user_settings")
        ],
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton(text="👑 Админ-панель", callback_data="admin_menu")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============= ADMIN MENU =============
def get_admin_main_menu() -> InlineKeyboardMarkup:
    """Main admin menu - inline buttons"""
    buttons = [
        [
            InlineKeyboardButton(text="➕ Добавить пользователя", callback_data="admin_add_user"),
        ],
        [
            InlineKeyboardButton(text="📋 Список пользователей", callback_data="admin_list_users"),
        ],
        [
            InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="admin_search_user"),
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton(text="ℹ️ О боте", callback_data="admin_about"),
        ],
        [
            InlineKeyboardButton(text="👤 Вернуться в аккаунт", callback_data="back_to_user_menu"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============= USER SUBSCRIPTION =============
def get_subscription_menu() -> InlineKeyboardMarkup:
    """Subscription detail menu"""
    buttons = [
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="user_subscription")],
        [InlineKeyboardButton(text="🔗 Получить ссылку", callback_data="user_link")],
        [InlineKeyboardButton(text="« Назад", callback_data="back_to_user_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============= USER SETTINGS =============
def get_notification_settings_menu(notify_expiry: bool, notify_traffic: bool) -> InlineKeyboardMarkup:
    """Notification settings toggles"""
    expiry_icon = "🔔" if notify_expiry else "🔕"
    traffic_icon = "🔔" if notify_traffic else "🔕"

    buttons = [
        [InlineKeyboardButton(
            text=f"{expiry_icon} Уведомления об истечении",
            callback_data="toggle_notify_expiry"
        )],
        [InlineKeyboardButton(
            text=f"{traffic_icon} Уведомления о трафике",
            callback_data="toggle_notify_traffic"
        )],
        [InlineKeyboardButton(text="« Назад", callback_data="back_to_user_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============= INSTRUCTION =============
def get_instruction_menu() -> InlineKeyboardMarkup:
    """Instruction menu with platform selection"""
    buttons = [
        [InlineKeyboardButton(text="📱 Для телефона (iOS/Android)", callback_data="instruction_mobile")],
        [InlineKeyboardButton(text="💻 Для компьютера (Windows/Mac/Linux)", callback_data="instruction_desktop")],
        [InlineKeyboardButton(text="❓ Частые вопросы", callback_data="instruction_faq")],
        [InlineKeyboardButton(text="« Назад", callback_data="back_to_user_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_instruction_details_menu() -> InlineKeyboardMarkup:
    """Download links for VPN clients"""
    buttons = [
        [InlineKeyboardButton(text="📱 V2Box (iOS/Android)", url="https://apps.apple.com/app/v2box/id6446814690")],
        [InlineKeyboardButton(text="💻 NekoBox (Windows/Mac/Linux)", url="https://github.com/MatsuriDayo/nekoray/releases")],
        [InlineKeyboardButton(text="« Назад к инструкции", callback_data="user_instruction")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============= ADMIN: ADD USER =============
def get_request_user_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard to request user selection (needs ReplyKeyboard for user sharing)"""
    button = KeyboardButton(
        text="👤 Выбрать пользователя",
        request_users=KeyboardButtonRequestUsers(request_id=1, user_is_bot=False)
    )
    buttons = [
        [button],
        [KeyboardButton(text="❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)


def get_cancel_inline() -> InlineKeyboardMarkup:
    """Cancel button"""
    buttons = [[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirmation_inline(confirm_callback: str) -> InlineKeyboardMarkup:
    """Confirmation buttons"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=confirm_callback),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============= ADMIN: USER LIST =============
def get_user_list_navigation(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Pagination for user list"""
    buttons = []

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_users_page:{page-1}"))

    nav_row.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))

    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_users_page:{page+1}"))

    buttons.append(nav_row)
    buttons.append([InlineKeyboardButton(text="« Назад в админ-панель", callback_data="admin_menu")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============= BACK BUTTONS =============
def get_back_to_menu() -> InlineKeyboardMarkup:
    """Simple back button"""
    buttons = [[InlineKeyboardButton(text="« Назад в меню", callback_data="back_to_user_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_admin_menu() -> InlineKeyboardMarkup:
    """Back to admin menu"""
    buttons = [[InlineKeyboardButton(text="« Назад в админ-панель", callback_data="admin_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
