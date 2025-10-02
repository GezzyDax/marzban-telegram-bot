"""Custom exceptions for the bot"""


class MarzbanConnectionError(Exception):
    """Raised when connection to Marzban API fails"""

    pass


class MarzbanAuthError(Exception):
    """Raised when authentication with Marzban API fails"""

    pass


class MarzbanNotFoundError(Exception):
    """Raised when requested resource not found in Marzban"""

    pass


class DatabaseError(Exception):
    """Raised when database operation fails"""

    pass
