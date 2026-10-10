"""
Comprehensive Test Suite for Freshwise Telegram Bot Demo Mode.

Tests static allowlist authorization, demo store data providers, commands,
callbacks, idempotency, reminder deduplication, quiet hours, and Copilot fallbacks.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, Chat, Location, Message, Update, User
from telegram.ext import ContextTypes

from app.telegram.auth import (
    AuthorizedUser,
    _AUTHORIZED_REGISTRY,
    authorize_user,
    get_all_authorized_users,
    get_authorized_user,
    is_authorized,
)
from app.telegram.copilot_adapter import ask_store_copilot
from app.telegram.data_service import (
    calculate_distance_km,
    cancel_demo_reservation,
    create_demo_reservation,
    geocode_locality,
    get_all_demo_stores,
    get_all_donations,
    get_all_rescue_deals,
    get_demo_store_by_id,
    get_expiring_batches,
    get_inventory_status,
    get_nearby_stores,
    get_proposed_recommendations,
    get_recommendation_by_id,
    get_rescue_deal_by_id,
    get_stockout_risks,
    get_store_summary,
    get_user_reservations,
    review_recommendation,
)
from app.telegram.demo_store import (
    _DEMO_RECOMMENDATIONS,
    _DEMO_RESERVATIONS,
    _DEMO_RESCUE_DEALS,
    get_demo_expiring_batches,
    get_demo_inventory_batches,
    get_demo_proposed_recommendations,
    get_demo_stockout_risks,
    get_demo_store_summary,
    review_demo_recommendation,
)
from app.telegram.handlers import (
    callback_query_handler,
    chat_message_handler,
    deals_command,
    donations_command,
    expiring_command,
    help_command,
    inventory_command,
    location_message_handler,
    myreservations_command,
    nearby_command,
    recommendations_command,
    start_command,
    stockouts_command,
    store_command,
    summary_command,
)
from app.telegram.reminders import (
    _ALERT_DEDUP_CACHE,
    _is_quiet_hours,
    check_and_send_reminders,
)


@pytest.fixture(autouse=True)
def clean_state():
    """Reset authorization registry, dedup cache, demo recommendations, reservations, and deals."""
    _AUTHORIZED_REGISTRY.clear()
    _ALERT_DEDUP_CACHE.clear()
    _DEMO_RESERVATIONS.clear()
    for r in _DEMO_RECOMMENDATIONS.values():
        r["status"] = "proposed"
        r["reviewed_by"] = None
        r["reviewed_at"] = None
        r["review_note"] = None

    # Reset deal quantities
    _DEMO_RESCUE_DEALS["deal-milk-01"]["quantity_available"] = 14
    _DEMO_RESCUE_DEALS["deal-straw-01"]["quantity_available"] = 10
    _DEMO_RESCUE_DEALS["deal-bread-02"]["quantity_available"] = 16
    _DEMO_RESCUE_DEALS["deal-yogurt-03"]["quantity_available"] = 20
    _DEMO_RESCUE_DEALS["deal-spinach-04"]["quantity_available"] = 8

    yield

    _AUTHORIZED_REGISTRY.clear()
    _ALERT_DEDUP_CACHE.clear()
    _DEMO_RESERVATIONS.clear()


# ---------------------------------------------------------------------------
# 1. Authorization & Store Resolution Tests
# ---------------------------------------------------------------------------

def test_unauthorized_user_rejection():
    """Verify unknown user IDs not on TELEGRAM_ALLOWED_USER_IDS are rejected."""
    with patch("app.telegram.auth.get_settings") as mock_settings:
        mock_settings.return_value.allowed_telegram_user_ids = {6349143766}
        mock_settings.return_value.telegram_data_mode = "demo"
        assert not is_authorized(999999999)
        assert get_authorized_user(999999999) is None


def test_allowlisted_user_access_demo_store():
    """Test allowlisted user resolves demo store immediately without Supabase requirement."""
    with patch("app.telegram.auth.get_settings") as mock_settings:
        mock_settings.return_value.allowed_telegram_user_ids = {6349143766}
        mock_settings.return_value.telegram_data_mode = "demo"

        assert is_authorized(6349143766)
        user = get_authorized_user(6349143766)
        assert user is not None
        assert user.user_id == 6349143766
        assert user.store_id == "27934f1c-f6cb-4731-a419-570b18e39f0a"
        assert user.store_name == "[DEMO] Freshwise Central"


def test_comma_separated_allowlist_parsing():
    """Verify trailing commas and spaces in TELEGRAM_ALLOWED_USER_IDS are handled robustly."""
    from app.config import Settings
    s = Settings(telegram_allowed_user_ids="6349143766, 12345678, ")
    assert s.allowed_telegram_user_ids == {6349143766, 12345678}


# ---------------------------------------------------------------------------
# 2. Demo Data Provider & Review Operation Tests
# ---------------------------------------------------------------------------

def test_demo_store_summary():
    """Test demo store summary computation."""
    summary = get_demo_store_summary()
    assert summary["store_name"] == "[DEMO] Freshwise Central"
    assert summary["total_batches"] == 8
    assert summary["total_units_on_hand"] > 0
    assert summary["expiring_soon_count"] >= 2
    assert summary["open_recommendations_count"] >= 2
    assert summary["sales_units_7d"] == 105


def test_demo_inventory_and_expiring_batches():
    """Test inventory batches and dynamic expiry calculations."""
    batches = get_demo_inventory_batches()
    assert len(batches) == 8
    skus = [b["sku"] for b in batches]
    assert "DEMO-MILK-1L" in skus
    assert "DEMO-STRAW-250" in skus

    expiring = get_demo_expiring_batches(days_threshold=3)
    assert len(expiring) >= 2
    for b in expiring:
        assert b["days_left"] <= 3


def test_demo_stockouts():
    """Test low stock identification in demo data."""
    risks = get_demo_stockout_risks(max_units_threshold=5)
    assert len(risks) >= 2
    for r in risks:
        assert r["quantity_on_hand"] <= 5


def test_review_recommendation_and_decision_logging():
    """Test recommendation review approval, state transition, and idempotency in demo state."""
    # 1. Approve rec-demo-001
    success, msg, updated = review_recommendation(
        rec_id="rec-demo-001",
        store_id="27934f1c-f6cb-4731-a419-570b18e39f0a",
        decision="approved",
        actor_id="telegram:6349143766",
        note="Approved Milk discount",
    )
    assert success
    assert "approved" in msg
    assert updated["status"] == "approved"

    # 2. Double-click (idempotency)
    success2, msg2, rec2 = review_recommendation(
        rec_id="rec-demo-001",
        store_id="27934f1c-f6cb-4731-a419-570b18e39f0a",
        decision="approved",
        actor_id="telegram:6349143766",
    )
    assert not success2
    assert "already been approved" in msg2


# ---------------------------------------------------------------------------
# 3. Distance Calculations & Locality Geocoding
# ---------------------------------------------------------------------------

def test_geographic_distance_calculation():
    """Verify Haversine distance formula calculation between coordinates."""
    # Central Bengaluru (12.9716, 77.5946) to Indiranagar (12.9784, 77.6408) is ~5.07 km
    dist = calculate_distance_km(12.9716, 77.5946, 12.9784, 77.6408)
    assert 4.5 < dist < 5.5

    # Same location distance is 0.0
    dist_zero = calculate_distance_km(12.9716, 77.5946, 12.9716, 77.5946)
    assert dist_zero == 0.0


def test_locality_and_pincode_geocoding_fallback():
    """Verify PIN code and locality string resolution to coordinates."""
    # PIN 560038 -> Indiranagar
    res_pin = geocode_locality("560038")
    assert res_pin is not None
    lat, lon, label = res_pin
    assert round(lat, 2) == 12.98
    assert "Indiranagar" in label

    # Locality text -> Koramangala
    res_loc = geocode_locality("koramangala")
    assert res_loc is not None
    assert round(res_loc[0], 2) == 12.94

    # Unknown location fallback returns None
    res_unknown = geocode_locality("unknown-nonexistent-place-999")
    assert res_unknown is None


def test_nearby_stores_distance_sorting():
    """Verify get_nearby_stores calculates distances and sorts closest first."""
    # From Indiranagar (12.9784, 77.6408)
    stores = get_nearby_stores(12.9784, 77.6408, max_radius_km=30.0)
    assert len(stores) >= 3
    # Closest should be Indiranagar store
    assert stores[0]["locality"] == "Indiranagar"
    assert stores[0]["distance_km"] == 0.0
    # Next closest should have higher distance
    assert stores[1]["distance_km"] > 0.0


# ---------------------------------------------------------------------------
# 4. Food Rescue Deals, Donations, and Reservations Lifecycle
# ---------------------------------------------------------------------------

def test_get_all_rescue_deals():
    """Verify retrieval of food rescue deals with discount and expiry sorting."""
    deals = get_all_rescue_deals()
    assert len(deals) >= 4
    for d in deals:
        assert d["quantity_available"] > 0
        assert d["discount_percent"] > 0
        assert "pickup_window" in d
        assert "rescue_price" in d


def test_get_all_donations():
    """Verify NGO donation batches retrieval and partner routing."""
    donations = get_all_donations()
    assert len(donations) >= 3
    partners = [d["partner_name"] for d in donations]
    assert any("Robin Hood Army" in p for p in partners)
    assert any("Feeding India" in p for p in partners)


def test_reservation_lifecycle_and_duplicate_prevention():
    """Verify creating a demo reservation, duplicate prevention, and inventory decrement."""
    user_id = 6349143766
    deal_id = "deal-milk-01"
    initial_qty = _DEMO_RESCUE_DEALS[deal_id]["quantity_available"]

    # 1. Create valid reservation
    ok, msg, res = create_demo_reservation(user_id=user_id, deal_id=deal_id, quantity=1, actor_name="Manager")
    assert ok
    assert "Confirmed" in msg
    assert res is not None
    assert res["status"] == "confirmed"
    assert res["reservation_code"].startswith("FW-RES-")
    assert _DEMO_RESCUE_DEALS[deal_id]["quantity_available"] == initial_qty - 1

    # 2. Duplicate reservation attempt for same active deal is blocked
    ok_dup, msg_dup, _ = create_demo_reservation(user_id=user_id, deal_id=deal_id, quantity=1, actor_name="Manager")
    assert not ok_dup
    assert "already have an active reservation" in msg_dup

    # 3. User reservations retrieval
    user_res = get_user_reservations(user_id)
    assert len(user_res) == 1
    assert user_res[0]["deal_id"] == deal_id


def test_over_reservation_and_unavailable_deal():
    """Verify over-reservation and invalid deal requests are cleanly rejected."""
    user_id = 6349143766
    # Quantity exceeds stock
    ok, msg, _ = create_demo_reservation(user_id=user_id, deal_id="deal-straw-01", quantity=999)
    assert not ok
    assert "Not enough items left" in msg

    # Non-existent deal
    ok_inv, msg_inv, _ = create_demo_reservation(user_id=user_id, deal_id="deal-nonexistent-99")
    assert not ok_inv
    assert "not found" in msg_inv


def test_reservation_cancellation_and_inventory_restoration():
    """Verify reservation cancellation restores available stock and prevents double cancellation."""
    user_id = 6349143766
    deal_id = "deal-bread-02"
    initial_qty = _DEMO_RESCUE_DEALS[deal_id]["quantity_available"]

    # Create reservation
    ok, _, res = create_demo_reservation(user_id=user_id, deal_id=deal_id, quantity=2)
    assert ok
    assert _DEMO_RESCUE_DEALS[deal_id]["quantity_available"] == initial_qty - 2

    # Unauthorized user cannot cancel another user's reservation
    ok_unauth, msg_unauth, _ = cancel_demo_reservation(res["id"], user_id=999999)
    assert not ok_unauth
    assert "Unauthorized" in msg_unauth

    # Authorized user cancels reservation
    ok_cancel, msg_cancel, res_cancelled = cancel_demo_reservation(res["id"], user_id=user_id)
    assert ok_cancel
    assert "cancelled" in msg_cancel
    assert res_cancelled["status"] == "cancelled"
    # Inventory restored
    assert _DEMO_RESCUE_DEALS[deal_id]["quantity_available"] == initial_qty

    # Double cancellation is blocked
    ok_double, msg_double, _ = cancel_demo_reservation(res["id"], user_id=user_id)
    assert not ok_double
    assert "already cancelled" in msg_double


# ---------------------------------------------------------------------------
# 5. Copilot Adapter & Food Rescue Queries
# ---------------------------------------------------------------------------

def test_copilot_deterministic_fallback():
    """Verify clean deterministic factual summary when Groq API key is empty."""
    with patch("app.telegram.copilot_adapter.get_settings") as mock_s:
        mock_s.return_value.groq_api_key = ""
        ans, grounded = ask_store_copilot("What items are expiring?", "demo-store")
        assert grounded
        assert "Freshwise Store Copilot" in ans
        assert "Whole Milk 1L" in ans


def test_copilot_food_rescue_query_deterministic():
    """Verify natural-language food rescue query returns accurate demo deals when Groq is unavailable."""
    with patch("app.telegram.copilot_adapter.get_settings") as mock_s:
        mock_s.return_value.groq_api_key = ""
        ans, grounded = ask_store_copilot("Find bread deals near me", "demo-store")
        assert grounded
        assert "Whole Wheat Bread" in ans
        assert "DEMO DATA" in ans


def test_copilot_dairy_expiring_query_deterministic():
    """Verify natural-language question about expiring dairy returns accurate demo items."""
    with patch("app.telegram.copilot_adapter.get_settings") as mock_s:
        mock_s.return_value.groq_api_key = ""
        ans, grounded = ask_store_copilot("What dairy items are expiring this week?", "demo-store")
        assert grounded
        assert "Whole Milk 1L" in ans
        assert "Dairy" in ans
        assert "DEMO DATA" in ans


def test_copilot_low_stock_query_deterministic():
    """Verify natural-language question about low stock items returns accurate demo records."""
    with patch("app.telegram.copilot_adapter.get_settings") as mock_s:
        mock_s.return_value.groq_api_key = ""
        ans, grounded = ask_store_copilot("What items are running low?", "demo-store")
        assert grounded
        assert "Baby Spinach 200g" in ans
        assert "Free Range Eggs 12pk" in ans
        assert "DEMO DATA" in ans


def test_copilot_performance_summary_query_deterministic():
    """Verify natural-language question about performance returns store overview."""
    with patch("app.telegram.copilot_adapter.get_settings") as mock_s:
        mock_s.return_value.groq_api_key = ""
        ans, grounded = ask_store_copilot("Summarize today's store performance.", "demo-store")
        assert grounded
        assert "Store Overview" in ans
        assert "Total Batches Tracked" in ans
        assert "DEMO DATA" in ans


def test_copilot_out_of_domain_query_capabilities():
    """Verify out-of-domain natural-language query returns capability suggestions."""
    with patch("app.telegram.copilot_adapter.get_settings") as mock_s:
        mock_s.return_value.groq_api_key = ""
        ans, grounded = ask_store_copilot("What is the weather today?", "demo-store")
        assert grounded
        assert "Freshwise Store Copilot" in ans
        assert "What dairy items are expiring" in ans


def test_copilot_groq_mocked_client_success():
    """Verify Groq API call receives system prompt, context, and model parameters."""
    with patch("app.telegram.copilot_adapter.get_settings") as mock_s:
        mock_s.return_value.groq_api_key = "test-groq-key"
        mock_s.return_value.groq_model = "test-model-qwen"
        with patch("app.telegram.copilot_adapter.Groq") as mock_groq_class:
            mock_client = MagicMock()
            mock_groq_class.return_value = mock_client
            mock_completion = MagicMock()
            mock_completion.choices = [
                MagicMock(message=MagicMock(content="Here are the dairy items expiring: Whole Milk 1L."))
            ]
            mock_client.chat.completions.create.return_value = mock_completion

            ans, grounded = ask_store_copilot("What dairy items are expiring this week?", "demo-store")
            assert grounded
            assert "Whole Milk 1L" in ans
            mock_groq_class.assert_called_once_with(api_key="test-groq-key", timeout=15.0)
            create_kwargs = mock_client.chat.completions.create.call_args[1]
            assert create_kwargs["model"] == "test-model-qwen"
            assert len(create_kwargs["messages"]) == 2
            assert "Zero-Waste Store Copilot" in create_kwargs["messages"][0]["content"]


def test_copilot_with_groq_exception_fallback():
    """Verify graceful fallback when Groq API call encounters error."""
    with patch("app.telegram.copilot_adapter.get_settings") as mock_s:
        mock_s.return_value.groq_api_key = "dummy-key"
        mock_s.return_value.groq_model = "test-model"
        with patch("app.telegram.copilot_adapter.Groq") as mock_groq:
            mock_groq.side_effect = RuntimeError("Service connection error")
            ans, grounded = ask_store_copilot("How much milk is left?", "demo-store")
            assert grounded
            assert "Whole Milk" in ans



# ---------------------------------------------------------------------------
# 6. Proactive Reminders & Deduplication
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_duplicate_reminder_prevention():
    """Verify the same alert is not sent twice on the same day."""
    with patch("app.telegram.auth.get_settings") as mock_settings:
        mock_settings.return_value.allowed_telegram_user_ids = {6349143766}
        mock_settings.return_value.telegram_data_mode = "demo"
        mock_settings.return_value.telegram_reminders_enabled = True
        mock_settings.return_value.telegram_briefing_hour = 0
        mock_settings.return_value.telegram_quiet_hours_start = 22
        mock_settings.return_value.telegram_quiet_hours_end = 7

        authorize_user(6349143766)

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()

        with patch("app.telegram.reminders._is_quiet_hours", return_value=False):
            # First pass: dispatches alerts
            dispatched_1 = await check_and_send_reminders(mock_bot)
            assert dispatched_1 >= 1
            call_count_1 = mock_bot.send_message.call_count

            # Second pass on same day: suppresses duplicates
            dispatched_2 = await check_and_send_reminders(mock_bot)
            assert dispatched_2 == 0
            assert mock_bot.send_message.call_count == call_count_1


def test_quiet_hours_calculation():
    """Test quiet hours detection."""
    with patch("app.telegram.reminders.get_settings") as mock_s:
        mock_s.return_value.telegram_quiet_hours_start = 22
        mock_s.return_value.telegram_quiet_hours_end = 7

        assert _is_quiet_hours(datetime(2026, 10, 9, 23, 0))
        assert _is_quiet_hours(datetime(2026, 10, 9, 3, 0))
        assert not _is_quiet_hours(datetime(2026, 10, 9, 14, 0))


# ---------------------------------------------------------------------------
# 7. Handler Commands & Callbacks (Nearby, Deals, Donations, Store, Reservations)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unauthorized_command_blocked():
    """Verify unauthorized users receive access denied message on commands."""
    with patch("app.telegram.handlers.is_authorized", return_value=False):
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(id=9999, username="intruder", first_name="Intruder")
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        await summary_command(update, context)
        update.message.reply_text.assert_called_once()
        reply_text = update.message.reply_text.call_args[0][0]
        assert "Access Denied" in reply_text


@pytest.mark.asyncio
async def test_authorized_all_commands():
    """Verify authorized manager can run all commands against the demo store."""
    with patch("app.telegram.handlers.is_authorized", return_value=True):
        authorize_user(6349143766)

        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(id=6349143766, username="manager", first_name="Manager")
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        # /start
        await start_command(update, context)
        assert "Freshwise Central" in update.message.reply_text.call_args[0][0]

        # /help
        await help_command(update, context)
        assert "Command Guide" in update.message.reply_text.call_args[0][0]

        # /summary
        await summary_command(update, context)
        assert "Store Briefing" in update.message.reply_text.call_args[0][0]

        # /inventory
        await inventory_command(update, context)
        assert "Whole Milk 1L" in update.message.reply_text.call_args[0][0]

        # /expiring
        await expiring_command(update, context)
        assert "Batches Expiring" in update.message.reply_text.call_args[0][0]

        # /stockouts
        await stockouts_command(update, context)
        assert "Low Stock" in update.message.reply_text.call_args[0][0]

        # /recommendations
        await recommendations_command(update, context)
        assert update.message.reply_text.call_count >= 7


@pytest.mark.asyncio
async def test_nearby_command_and_locality_fallback():
    """Verify /nearby command with default locality and with custom PIN code argument."""
    with patch("app.telegram.handlers.is_authorized", return_value=True):
        authorize_user(6349143766)

        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(id=6349143766, username="manager", first_name="Manager")
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = ["560038"]  # Indiranagar PIN

        await nearby_command(update, context)
        assert update.message.reply_text.call_count >= 2
        first_call = update.message.reply_text.call_args_list[0][0][0]
        assert "Indiranagar" in first_call
        assert "Nearby Zero-Waste Stores" in first_call


@pytest.mark.asyncio
async def test_location_message_handler():
    """Verify native Telegram GPS location sharing message handling."""
    with patch("app.telegram.handlers.is_authorized", return_value=True):
        authorize_user(6349143766)

        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(id=6349143766, username="manager", first_name="Manager")
        update.message = MagicMock(spec=Message)
        loc = MagicMock(spec=Location)
        loc.latitude = 12.9352
        loc.longitude = 77.6245  # Koramangala
        update.message.location = loc
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        await location_message_handler(update, context)
        assert update.message.reply_text.call_count >= 2
        header_text = update.message.reply_text.call_args_list[0][0][0]
        assert "GPS Location Received" in header_text


@pytest.mark.asyncio
async def test_deals_and_donations_and_store_commands():
    """Verify /deals, /donations, /store, and /myreservations commands."""
    with patch("app.telegram.handlers.is_authorized", return_value=True):
        authorize_user(6349143766)

        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(id=6349143766, username="manager", first_name="Manager")
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = []

        # 1. /deals
        await deals_command(update, context)
        assert update.message.reply_text.call_count >= 2
        deals_header = update.message.reply_text.call_args_list[0][0][0]
        assert "Food Rescue Deals" in deals_header

        # Reset call count
        update.message.reply_text.reset_mock()

        # 2. /donations
        await donations_command(update, context)
        assert update.message.reply_text.call_count == 1
        donations_text = update.message.reply_text.call_args[0][0]
        assert "NGO Food Rescue & Community Donations" in donations_text
        assert "Robin Hood Army" in donations_text

        # Reset call count
        update.message.reply_text.reset_mock()

        # 3. /store
        context.args = ["DEMO-STORE-002"]
        await store_command(update, context)
        assert update.message.reply_text.call_count == 1
        store_text = update.message.reply_text.call_args[0][0]
        assert "Freshwise Indiranagar" in store_text

        # Reset call count
        update.message.reply_text.reset_mock()

        # 4. /myreservations (empty initially)
        context.args = []
        await myreservations_command(update, context)
        assert update.message.reply_text.call_count == 1
        res_text = update.message.reply_text.call_args[0][0]
        assert "no active demo reservations" in res_text


@pytest.mark.asyncio
async def test_rescue_deal_callbacks():
    """Verify inline callbacks for reserving a deal, cancelling reservation, and viewing details."""
    with patch("app.telegram.handlers.is_authorized", return_value=True):
        authorize_user(6349143766)

        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(id=6349143766, username="manager", first_name="Manager")
        update.callback_query = MagicMock(spec=CallbackQuery)
        update.callback_query.data = "reserve_deal:deal-straw-01"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_reply_markup = AsyncMock()
        update.callback_query.message = MagicMock(spec=Message)
        update.callback_query.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        # 1. Trigger reservation callback
        await callback_query_handler(update, context)
        update.callback_query.answer.assert_called_with("🎉 Demo Reservation Confirmed!", show_alert=False)
        update.callback_query.message.reply_text.assert_called_once()
        confirm_text = update.callback_query.message.reply_text.call_args[0][0]
        assert "Reservation Confirmed" in confirm_text
        assert "Strawberries 250g" in confirm_text

        # Find created reservation ID
        user_res = get_user_reservations(6349143766)
        assert len(user_res) == 1
        res_id = user_res[0]["id"]

        # 2. Trigger cancel callback
        update.callback_query.data = f"cancel_res:{res_id}"
        update.callback_query.answer.reset_mock()
        update.callback_query.edit_message_text = AsyncMock()

        await callback_query_handler(update, context)
        update.callback_query.answer.assert_called_with("Reservation cancelled.", show_alert=False)


@pytest.mark.asyncio
async def test_chat_message_handler_authorized():
    """Verify regular text messages reach the Copilot adapter and respond to the user."""
    with patch("app.telegram.handlers.is_authorized", return_value=True):
        authorize_user(6349143766)

        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(id=6349143766, username="manager", first_name="Manager")
        update.message = MagicMock(spec=Message)
        update.message.text = "What dairy items are expiring this week?"
        update.message.chat = MagicMock()
        update.message.chat.send_action = AsyncMock()
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        await chat_message_handler(update, context)

        # Typing indicator called
        update.message.chat.send_action.assert_called_once()
        # Reply text called
        update.message.reply_text.assert_called_once()
        reply_content = update.message.reply_text.call_args[0][0]
        assert "Whole Milk 1L" in reply_content


@pytest.mark.asyncio
async def test_chat_message_handler_unauthorized():
    """Verify unauthorized users receive access denied when sending regular text messages."""
    with patch("app.telegram.handlers.is_authorized", return_value=False):
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(id=999999, username="intruder", first_name="Intruder")
        update.message = MagicMock(spec=Message)
        update.message.text = "Tell me everything about the inventory"
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        await chat_message_handler(update, context)

        update.message.reply_text.assert_called_once()
        reply_content = update.message.reply_text.call_args[0][0]
        assert "Access Denied" in reply_content


@pytest.mark.asyncio
async def test_safe_reply_text_markdown_failure_fallback():
    """Verify safe_reply_text catches Markdown entity parse error and falls back to plain text."""
    from app.telegram.handlers import safe_reply_text

    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)

    # First call with parse_mode=MARKDOWN raises BadRequest
    def mock_reply_side_effect(*args, **kwargs):
        if kwargs.get("parse_mode") is not None:
            raise RuntimeError("BadRequest: can't parse entities")
        return MagicMock()

    update.message.reply_text = AsyncMock(side_effect=mock_reply_side_effect)

    result = await safe_reply_text(update, "Sample text with *broken markdown")
    assert result is not None
    assert update.message.reply_text.call_count == 2
    # Second call had parse_mode=None (plain text fallback)
    assert update.message.reply_text.call_args_list[1][1]["parse_mode"] is None


@pytest.mark.asyncio
async def test_chat_message_handler_exception_resilience():
    """Verify internal exception in Copilot does not crash handler and sends friendly fallback."""
    with patch("app.telegram.handlers.is_authorized", return_value=True):
        authorize_user(6349143766)

        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(id=6349143766, username="manager", first_name="Manager")
        update.message = MagicMock(spec=Message)
        update.message.text = "What is the stock?"
        update.message.chat = MagicMock()
        update.message.chat.send_action = AsyncMock()
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        with patch("app.telegram.handlers.ask_store_copilot", side_effect=ValueError("Unexpected crash")):
            await chat_message_handler(update, context)

            update.message.reply_text.assert_called_once()
            reply_content = update.message.reply_text.call_args[0][0]
            assert "error occurred" in reply_content.lower()


