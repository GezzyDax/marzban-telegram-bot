"""Rate limiting decorator"""

import time
from functools import wraps
from typing import Dict
from aiogram.types import Message, CallbackQuery


# Store last call times: {user_id: {action: timestamp}}
_call_history: Dict[int, Dict[str, float]] = {}


def rate_limit(seconds: int = 2, action: str = "default"):
    """
    Rate limiting decorator

    Args:
        seconds: Minimum seconds between calls
        action: Action identifier for separate limits

    Usage:
        @rate_limit(seconds=5, action="search")
        async def search_handler(...):
            pass
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(event, *args, **kwargs):
            # Get user ID from event
            if isinstance(event, Message):
                user_id = event.from_user.id
            elif isinstance(event, CallbackQuery):
                user_id = event.from_user.id
            else:
                # Unknown event type, allow it
                return await func(event, *args, **kwargs)

            now = time.time()

            # Initialize user history if not exists
            if user_id not in _call_history:
                _call_history[user_id] = {}

            # Check last call time
            last_call = _call_history[user_id].get(action, 0)
            time_since = now - last_call

            if time_since < seconds:
                # Rate limited
                wait_time = int(seconds - time_since)
                if isinstance(event, Message):
                    await event.answer(f"⏳ Подождите {wait_time} секунд перед следующей командой")
                elif isinstance(event, CallbackQuery):
                    await event.answer(f"⏳ Подождите {wait_time} сек.", show_alert=True)
                return

            # Update last call time
            _call_history[user_id][action] = now

            # Call the function
            return await func(event, *args, **kwargs)

        return wrapper

    return decorator
