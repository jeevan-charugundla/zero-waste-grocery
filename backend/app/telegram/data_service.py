"""
Data service for Telegram bot.

Provides unified data queries and operations for store operations,
food rescue deals, reservations, and NGO donations.
"""

from __future__ import annotations

import logging
from typing import Any

from app.config import get_settings
from app.telegram.demo_store import (
    calculate_distance_km,
    cancel_demo_reservation,
    create_demo_reservation,
    geocode_locality,
    get_all_demo_stores,
    get_all_donations,
    get_all_rescue_deals,
    get_demo_expiring_batches,
    get_demo_inventory_batches,
    get_demo_proposed_recommendations,
    get_demo_recommendation_by_id,
    get_demo_stockout_risks,
    get_demo_store,
    get_demo_store_by_id,
    get_demo_store_summary,
    get_nearby_stores,
    get_rescue_deal_by_id,
    get_user_reservations,
    review_demo_recommendation,
)

logger = logging.getLogger("freshwise.telegram.data")


def _is_demo_mode() -> bool:
    return get_settings().telegram_data_mode == "demo"


def get_store_summary(store_id: str, db: Any = None) -> dict:
    return get_demo_store_summary()


def get_inventory_status(store_id: str, db: Any = None) -> list[dict]:
    return get_demo_inventory_batches()


def get_expiring_batches(store_id: str, db: Any = None, days_threshold: int = 7) -> list[dict]:
    return get_demo_expiring_batches(days_threshold)


def get_stockout_risks(store_id: str, db: Any = None, max_units_threshold: int = 5) -> list[dict]:
    return get_demo_stockout_risks(max_units_threshold)


def get_proposed_recommendations(store_id: str, db: Any = None, limit: int = 5) -> list[dict]:
    return get_demo_proposed_recommendations(limit)


def get_recommendation_by_id(rec_id: str, store_id: str, db: Any = None) -> dict | None:
    return get_demo_recommendation_by_id(rec_id)


def review_recommendation(
    rec_id: str,
    store_id: str,
    decision: str,
    actor_id: str,
    note: str = "",
    db: Any = None,
) -> tuple[bool, str, dict | None]:
    return review_demo_recommendation(rec_id, decision, actor_id, note)
