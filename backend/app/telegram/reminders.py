"""
Proactive Reminder System for Telegram Bot.

Dispatches scheduled store briefings, critical expiry alerts, stockout warnings,
and pending recommendation notifications using the demo data store with
timezone awareness, quiet hours, and duplicate alert suppression.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.config import get_settings
from app.telegram.auth import get_all_authorized_users
from app.telegram.data_service import (
    get_expiring_batches,
    get_proposed_recommendations,
    get_stockout_risks,
    get_store_summary,
)

logger = logging.getLogger("freshwise.telegram.reminders")

# Deduplication cache: set of (user_id, alert_type, entity_id, date_string)
_ALERT_DEDUP_CACHE: set[str] = set()

# Lock to ensure only one scheduler task runs concurrently
_SCHEDULER_LOCK = asyncio.Lock()
_SCHEDULER_RUNNING = False


def _get_cache_key(user_id: int, alert_type: str, store_id: str, date_str: str, entity_id: str = "") -> str:
    return f"{user_id}:{alert_type}:{store_id}:{date_str}:{entity_id}"


def _is_quiet_hours(now_local: datetime) -> bool:
    """Check if current local time falls within configured quiet hours."""
    settings = get_settings()
    current_hour = now_local.hour
    start = settings.telegram_quiet_hours_start  # default 22
    end = settings.telegram_quiet_hours_end      # default 7

    if start > end:  # Overnight window (e.g. 22:00 -> 07:00)
        return current_hour >= start or current_hour < end
    else:
        return start <= current_hour < end


async def check_and_send_reminders(bot: Any) -> int:
    """
    Execute a single evaluation pass for all authorized users.
    Dispatches notifications and returns the count of sent alerts.
    """
    settings = get_settings()
    if not settings.telegram_reminders_enabled:
        return 0

    users = get_all_authorized_users()
    if not users:
        return 0

    today = date.today()
    today_str = today.isoformat()
    now_utc = datetime.now(timezone.utc)
    current_hour = now_utc.hour
    dispatched_count = 0

    for user in users:
        store_id = user.store_id or "demo-store"

        # Check quiet hours
        if _is_quiet_hours(now_utc):
            logger.debug("Quiet hours active for user %d; skipping non-critical alerts", user.user_id)
            continue

        # 1. Morning Daily Briefing
        briefing_key = _get_cache_key(user.user_id, "morning_briefing", store_id, today_str)
        if briefing_key not in _ALERT_DEDUP_CACHE and current_hour >= settings.telegram_briefing_hour:
            try:
                s = get_store_summary(store_id)
                briefing_msg = (
                    f"🌅 *Morning Store Briefing — {s['store_name']}* *(Demo)*\n"
                    f"📅 {today_str}\n\n"
                    f"📦 *Active Inventory:* `{s['total_units_on_hand']}` units in `{s['total_batches']}` batches\n"
                    f"⏰ *Expiry Watch (<=3 days):* `{s['expiring_soon_count']}` batches\n"
                    f"💡 *Recommendations to Review:* `{s['open_recommendations_count']}`\n"
                    f"📈 *7-Day Sales:* `{s['sales_units_7d']}` units\n\n"
                    "👉 Run `/summary` or `/recommendations` to manage your store."
                )
                await bot.send_message(
                    chat_id=user.user_id,
                    text=briefing_msg,
                    parse_mode="Markdown",
                )
                _ALERT_DEDUP_CACHE.add(briefing_key)
                dispatched_count += 1
                logger.info("Sent morning briefing to user %d", user.user_id)
            except Exception as exc:
                logger.error("Failed to send morning briefing to %d: %s", user.user_id, exc)

        # 2. Critical Expiry Alerts (<= 2 days left)
        try:
            expiring_batches = get_expiring_batches(store_id, days_threshold=2)
            for b in expiring_batches:
                batch_id = b.get("batch_id", "")
                exp_key = _get_cache_key(user.user_id, "urgent_expiry", store_id, today_str, batch_id)
                if exp_key in _ALERT_DEDUP_CACHE:
                    continue

                days_left = b.get("days_left", "?")
                urgency_str = "EXPIRES TODAY/TOMORROW" if days_left in (0, 1) else f"expires in {days_left} days"
                alert_text = (
                    f"🚨 *CRITICAL EXPIRY ALERT* *(Demo)*\n\n"
                    f"• *Product:* {b['product_name']} (`{b['sku']}`)\n"
                    f"• *Batch:* `{b['batch_code']}`\n"
                    f"• *Quantity on Hand:* `{b['quantity_on_hand']}` units\n"
                    f"• *Expiry Date:* `{b['expiry_date']}` ({urgency_str})\n\n"
                    "👉 Check `/recommendations` to review markdown pricing or donation routing."
                )
                await bot.send_message(
                    chat_id=user.user_id,
                    text=alert_text,
                    parse_mode="Markdown",
                )
                _ALERT_DEDUP_CACHE.add(exp_key)
                dispatched_count += 1
                logger.info("Sent urgent expiry alert for batch %s to user %d", batch_id, user.user_id)
        except Exception as exc:
            logger.error("Failed to process expiry alerts: %s", exc)

        # 3. Critical Stockout Alerts (<= 2 units left)
        try:
            stockouts = get_stockout_risks(store_id, max_units_threshold=2)
            for st in stockouts:
                batch_id = st.get("batch_id", "")
                st_key = _get_cache_key(user.user_id, "urgent_stockout", store_id, today_str, batch_id)
                if st_key in _ALERT_DEDUP_CACHE:
                    continue

                alert_text = (
                    f"⚠️ *STOCKOUT RISK WARNING* *(Demo)*\n\n"
                    f"• *Product:* {st['product_name']} (`{st['sku']}`)\n"
                    f"• *Batch:* `{st['batch_code']}`\n"
                    f"• *Remaining Stock:* `{st['quantity_on_hand']}` units left\n\n"
                    "👉 Consider restocking or reordering this item."
                )
                await bot.send_message(
                    chat_id=user.user_id,
                    text=alert_text,
                    parse_mode="Markdown",
                )
                _ALERT_DEDUP_CACHE.add(st_key)
                dispatched_count += 1
                logger.info("Sent stockout warning for batch %s to user %d", batch_id, user.user_id)
        except Exception as exc:
            logger.error("Failed to process stockout alerts: %s", exc)

        # 4. Pending Recommendations Reminder
        rec_digest_key = _get_cache_key(user.user_id, "recs_digest", store_id, today_str)
        if rec_digest_key not in _ALERT_DEDUP_CACHE:
            try:
                pending_recs = get_proposed_recommendations(store_id, limit=3)
                if pending_recs:
                    msg = (
                        f"💡 *Action Required: {len(pending_recs)} Pending AI Recommendations* *(Demo)*\n\n"
                        "Freshwise agentic engine has generated recommendations awaiting your approval:\n"
                    )
                    for r in pending_recs:
                        msg += f"• [{r['action'].upper()}] *{r['product_name']}* — {r['rationale'][:80]}...\n"
                    msg += "\n👉 Type `/recommendations` to review and approve/reject."

                    await bot.send_message(
                        chat_id=user.user_id,
                        text=msg,
                        parse_mode="Markdown",
                    )
                    _ALERT_DEDUP_CACHE.add(rec_digest_key)
                    dispatched_count += 1
            except Exception as exc:
                logger.error("Failed to process recommendations reminder: %s", exc)

    return dispatched_count


async def run_reminder_scheduler(bot: Any) -> None:
    """
    Background worker loop for the proactive reminder scheduler.
    Runs every `telegram_reminder_interval_minutes` until cancelled.
    """
    global _SCHEDULER_RUNNING

    async with _SCHEDULER_LOCK:
        if _SCHEDULER_RUNNING:
            logger.warning("Reminder scheduler already running. Duplicate instance prevented.")
            return
        _SCHEDULER_RUNNING = True

    logger.info("Proactive reminder scheduler started (demo mode enabled).")
    try:
        while True:
            settings = get_settings()
            interval_secs = max(60, settings.telegram_reminder_interval_minutes * 60)
            try:
                await check_and_send_reminders(bot)
            except Exception as exc:
                logger.error("Error in reminder scheduler cycle: %s", exc)

            await asyncio.sleep(interval_secs)
    except asyncio.CancelledError:
        logger.info("Reminder scheduler task cancelled.")
    finally:
        _SCHEDULER_RUNNING = False
