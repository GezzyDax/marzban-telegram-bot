"""Marzban API client"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

import aiohttp


logger = logging.getLogger(__name__)


@dataclass
class MarzbanUser:
    """Marzban user data"""

    username: str
    status: str
    used_traffic: int
    data_limit: Optional[int]
    expire: Optional[datetime]
    subscription_url: str
    links: list[str]


class MarzbanAPIError(Exception):
    """Base exception for Marzban API errors"""

    pass


class MarzbanAPI:
    """Marzban API client"""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.token: Optional[str] = None
        self.token_expires: Optional[datetime] = None

    async def _get_token(self) -> str:
        """Get access token (with caching)"""
        if self.token and self.token_expires and datetime.now() < self.token_expires:
            return self.token

        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field("username", self.username)
            data.add_field("password", self.password)

            async with session.post(f"{self.base_url}/api/admin/token", data=data) as response:
                if response.status != 200:
                    raise MarzbanAPIError(f"Authentication failed: {response.status}")

                result = await response.json()
                self.token = result["access_token"]
                # Token обычно действует 1 час, сохраним на 50 минут для безопасности
                self.token_expires = datetime.now() + timedelta(minutes=50)
                logger.info("Obtained new Marzban API token")
                return self.token

    async def get_user(self, username: str) -> MarzbanUser:
        """Get user information from Marzban"""
        token = await self._get_token()

        headers = {"Authorization": f"Bearer {token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/user/{username}", headers=headers) as response:
                if response.status == 404:
                    raise MarzbanAPIError(f"User {username} not found in Marzban")
                if response.status != 200:
                    raise MarzbanAPIError(f"Failed to get user: {response.status}")

                data = await response.json()

                # Parse expire date
                expire = None
                if data.get("expire"):
                    try:
                        expire = datetime.fromtimestamp(data["expire"])
                    except (ValueError, TypeError):
                        logger.warning(f"Failed to parse expire date: {data.get('expire')}")

                return MarzbanUser(
                    username=data["username"],
                    status=data.get("status", "unknown"),
                    used_traffic=data.get("used_traffic", 0),
                    data_limit=data.get("data_limit"),
                    expire=expire,
                    subscription_url=data.get("subscription_url", ""),
                    links=data.get("links", []),
                )

    async def list_users(self, offset: int = 0, limit: int = 100) -> tuple[list[dict], int]:
        """List all users from Marzban"""
        token = await self._get_token()

        headers = {"Authorization": f"Bearer {token}"}
        params = {"offset": offset, "limit": limit}

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/users", headers=headers, params=params) as response:
                if response.status != 200:
                    raise MarzbanAPIError(f"Failed to list users: {response.status}")

                data = await response.json()
                return data.get("users", []), data.get("total", 0)

    async def create_user(
        self,
        username: str,
        data_limit: Optional[int] = None,
        expire: Optional[int] = None,
        status: str = "active",
        inbounds: Optional[dict] = None,
        note: Optional[str] = None,
    ) -> MarzbanUser:
        """Create new user in Marzban

        Args:
            username: Username for new user
            data_limit: Data limit in bytes (None = unlimited)
            expire: Expiry timestamp (None = unlimited)
            status: User status (active/disabled/limited/expired/on_hold)
            inbounds: Inbound protocols dict (if None, uses all available)
            note: Optional note for user

        Returns:
            MarzbanUser object with created user data
        """
        token = await self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Default inbounds if not specified (empty = use all available)
        if inbounds is None:
            inbounds = {}

        payload = {
            "username": username,
            "status": status,
            "data_limit": data_limit if data_limit is not None else 0,  # 0 = unlimited
            "data_limit_reset_strategy": "no_reset",
            "expire": expire if expire is not None else 0,  # 0 = unlimited
            "inbounds": inbounds,
        }

        if note:
            payload["note"] = note

        logger.info(f"Creating user {username} with payload: {payload}")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/user",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 409:
                    raise MarzbanAPIError(f"User {username} already exists in Marzban")
                if response.status != 200:
                    error_text = await response.text()
                    raise MarzbanAPIError(f"Failed to create user: {response.status} - {error_text}")

                data = await response.json()
                logger.info(f"Created user {username} in Marzban")

                # Parse expire date
                expire_dt = None
                if data.get("expire"):
                    try:
                        expire_dt = datetime.fromtimestamp(data["expire"])
                    except (ValueError, TypeError):
                        logger.warning(f"Failed to parse expire date: {data.get('expire')}")

                return MarzbanUser(
                    username=data["username"],
                    status=data.get("status", "active"),
                    used_traffic=data.get("used_traffic", 0),
                    data_limit=data.get("data_limit"),
                    expire=expire_dt,
                    subscription_url=data.get("subscription_url", ""),
                    links=data.get("links", []),
                )

    async def check_connection(self) -> bool:
        """Check if Marzban API is accessible"""
        try:
            await self._get_token()
            return True
        except Exception as e:
            logger.error(f"Marzban API connection check failed: {e}")
            return False
