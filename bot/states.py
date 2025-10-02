"""FSM States for bot conversations"""

from aiogram.fsm.state import State, StatesGroup


class AddUserStates(StatesGroup):
    """States for adding a new user"""

    waiting_for_user = State()  # Waiting for user selection via request_users
    waiting_for_marzban_username = State()  # Waiting for Marzban username input
    confirmation = State()  # Confirmation before creating user


class SearchUserStates(StatesGroup):
    """States for searching users"""

    waiting_for_query = State()  # Waiting for search query (telegram_id or username)


class MakeAdminStates(StatesGroup):
    """States for making user admin"""

    waiting_for_user = State()  # Waiting for user selection
    confirmation = State()  # Confirmation before granting admin


class RevokeAdminStates(StatesGroup):
    """States for revoking admin rights"""

    waiting_for_user = State()  # Waiting for user selection
    confirmation = State()  # Confirmation before revoking


class RemoveUserStates(StatesGroup):
    """States for removing user"""

    waiting_for_user = State()  # Waiting for user selection
    confirmation = State()  # Confirmation before deletion


class BroadcastStates(StatesGroup):
    """States for broadcasting messages"""

    select_audience = State()  # Select target audience (all/admins/users)
    waiting_for_message = State()  # Waiting for message text
    confirmation = State()  # Preview and confirmation


class UserFeedbackStates(StatesGroup):
    """States for user feedback/support"""

    waiting_for_message = State()  # Waiting for problem description
