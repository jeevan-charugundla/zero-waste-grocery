"""
Telegram Authorization & Store Access Control.

Enforces allowlist authorization (TELEGRAM_ALLOWED_USER_IDS) and provides
instant access to the Freshwise demo store without requiring Supabase.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.config import get_settings
from app.telegram.demo_store import DEMO_STORE

logger = logging.getLogger("freshwise.telegram.auth")


@dataclass
class AuthorizedUser:
    user_id: int
    username: str = ""
    first_name: str = ""
    store_id: str = DEMO_STORE["id"]
    store_name: str = DEMO_STORE["name"]
    role: str = "manager"  # manager, staff, admin
    paired_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# In-memory registry for authorized Telegram sessions
_AUTHORIZED_REGISTRY: dict[int, AuthorizedUser] = {}


def get_authorized_user(telegram_user_id: int) -> AuthorizedUser | None:
    """
    Check if a Telegram user ID is authorized via TELEGRAM_ALLOWED_USER_IDS.
    If authorized, assigns access to the Freshwise store.
    """
    settings = get_settings()

    # Reject immediately if not in allowlist
    if telegram_user_id not in settings.allowed_telegram_user_ids:
        return None

    if telegram_user_id in _AUTHORIZED_REGISTRY:
        return _AUTHORIZED_REGISTRY[telegram_user_id]

    # In demo mode (default), bind to demo store directly without blocking on Supabase
    store_id = DEMO_STORE["id"]
    store_name = DEMO_STORE["name"]

    if settings.telegram_data_mode == "supabase":
        try:
            from app.db import get_supabase
            db = get_supabase()
            configured_id = settings.telegram_default_store_id.strip() or DEMO_STORE["id"]
            resp = (
                db.table("stores")
                .select("id,name,is_active")
                .or_(f"id.eq.{configured_id},code.eq.{configured_id}")
                .limit(1)
                .execute()
            )
            if resp.data and resp.data[0].get("is_active", True):
                store_id = resp.data[0]["id"]
                store_name = resp.data[0]["name"]
        except Exception as exc:
            logger.warning("Supabase lookup failed, falling back to demo store: %s", exc)

    user = AuthorizedUser(
        user_id=telegram_user_id,
        username="",
        first_name="",
        store_id=store_id,
        store_name=store_name,
        role="manager",
    )
    _AUTHORIZED_REGISTRY[telegram_user_id] = user
    return user


def is_authorized(telegram_user_id: int) -> bool:
    """Return True if the Telegram user ID is in the allowlist."""
    settings = get_settings()
    return telegram_user_id in settings.allowed_telegram_user_ids


def authorize_user(
    telegram_user_id: int,
    store_id: str = DEMO_STORE["id"],
    role: str = "manager",
    username: str = "",
    first_name: str = "",
    store_name: str = DEMO_STORE["name"],
) -> AuthorizedUser:
    """Register an authorized user in the runtime registry (e.g. for testing)."""
    user = AuthorizedUser(
        user_id=telegram_user_id,
        username=username,
        first_name=first_name,
        store_id=store_id,
        store_name=store_name,
        role=role,
    )
    _AUTHORIZED_REGISTRY[telegram_user_id] = user
    return user


def get_all_authorized_users() -> list[AuthorizedUser]:
    """Return list of all allowlisted users."""
    settings = get_settings()
    users: list[AuthorizedUser] = []
    for uid in settings.allowed_telegram_user_ids:
        user = get_authorized_user(uid)
        if user:
            users.append(user)
    return users
