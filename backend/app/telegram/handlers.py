"""
Telegram Bot Handlers.

Implements all user commands, food rescue deals, nearby store discovery,
reservations, NGO donations, inline callbacks, and AI Copilot interactions.
Formatted cleanly in Telegram HTML with intuitive emojis and zero random asterisks.
"""

from __future__ import annotations

import html
import logging
from typing import Any

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    constants,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.telegram.auth import (
    AuthorizedUser,
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
from app.telegram.formatter import clean_telegram_text, strip_all_tags

logger = logging.getLogger("freshwise.telegram.handlers")


def _get_user_info(update: Update) -> tuple[int, str, str]:
    """Extract user_id, username, first_name safely from update."""
    user = update.effective_user
    if not user:
        return 0, "", ""
    return user.id, user.username or "", user.first_name or ""


import inspect

async def _maybe_await(val: Any) -> Any:
    """Await val if it is a coroutine or awaitable, otherwise return it directly."""
    if inspect.isawaitable(val):
        return await val
    return val


async def safe_reply_text(
    target: Any,
    text: str,
    reply_markup: Any = None,
    parse_mode: Any = constants.ParseMode.HTML,
) -> Message | None:
    """
    Safely reply to an incoming update or message using clean Telegram HTML.
    Automatically formats text through clean_telegram_text, stripping raw asterisks
    and falling back to clean plain text if Telegram entity parsing ever fails.
    """
    if not target:
        return None
    target_msg = getattr(target, "message", None) or target
    if not hasattr(target_msg, "reply_text"):
        return None

    cleaned_text = clean_telegram_text(text) if parse_mode == constants.ParseMode.HTML else text

    try:
        return await _maybe_await(
            target_msg.reply_text(
                cleaned_text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
        )
    except Exception as exc:
        logger.warning(
            "Failed to send message with parse_mode=%s (%s). Retrying in clean plain text.",
            parse_mode,
            exc,
        )
        try:
            plain = strip_all_tags(text)
            return await _maybe_await(
                target_msg.reply_text(
                    plain,
                    reply_markup=reply_markup,
                    parse_mode=None,
                )
            )
        except Exception as fallback_exc:
            logger.error("Failed to send fallback plain text message: %s", fallback_exc)
            return None


async def safe_edit_message_text(
    query: Any,
    text: str,
    reply_markup: Any = None,
    parse_mode: Any = constants.ParseMode.HTML,
) -> Any:
    """Safely edit a callback query message with clean HTML and plain text fallback."""
    cleaned_text = clean_telegram_text(text) if parse_mode == constants.ParseMode.HTML else text
    try:
        return await _maybe_await(
            query.edit_message_text(
                cleaned_text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
        )
    except Exception as exc:
        logger.warning("Failed to edit message with parse_mode=%s (%s). Retrying plain text.", parse_mode, exc)
        plain = strip_all_tags(text)
        try:
            return await _maybe_await(
                query.edit_message_text(
                    plain,
                    reply_markup=reply_markup,
                    parse_mode=None,
                )
            )
        except Exception as fallback_exc:
            logger.error("Failed to edit message in plain text: %s", fallback_exc)
            return None


async def _check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> AuthorizedUser | None:
    """
    Validate that the incoming user is on the allowlist.
    If not, sends an unauthorized notification and returns None.
    """
    user_id, username, first_name = _get_user_info(update)
    if not user_id:
        return None

    if not is_authorized(user_id):
        unauth_msg = (
            "🔒 <b>Access Denied — Unauthorized User</b>\n\n"
            f"Your Telegram User ID: <code>{user_id}</code>\n\n"
            "You are not authorized to view or manage store inventory data.\n\n"
            "👉 <b>To authenticate as a Store Manager:</b>\n"
            "Add your Telegram User ID to <code>TELEGRAM_ALLOWED_USER_IDS</code> in <code>backend/.env</code>."
        )
        if update.message:
            await safe_reply_text(update, unauth_msg)
        elif update.callback_query:
            await update.callback_query.answer("🔒 Unauthorized: Access Denied.", show_alert=True)
        return None

    auth_user = get_authorized_user(user_id)
    return auth_user


# ---------------------------------------------------------------------------
# Command Handlers
# ---------------------------------------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user_id, username, first_name = _get_user_info(update)

    if not is_authorized(user_id):
        welcome_unauth = (
            "🌿 <b>Welcome to Freshwise Zero-Waste Assistant!</b>\n\n"
            "This bot provides proactive inventory alerts, surplus rescue deals, "
            "nearby store discovery, and AI markdown approvals.\n\n"
            f"🔒 <b>Status:</b> Unauthorized (ID: <code>{user_id}</code>)\n\n"
            "To access store data, add your Telegram User ID "
            "to <code>TELEGRAM_ALLOWED_USER_IDS</code> in <code>backend/.env</code>.\n\n"
            "Type /help for more information."
        )
        await safe_reply_text(update, welcome_unauth)
        return

    auth_user = get_authorized_user(user_id)
    store_name = auth_user.store_name if auth_user else "Freshwise Central (Demo)"

    welcome_auth = (
        f"🌿 <b>Welcome back, {html.escape(first_name or username or 'Manager')}!</b>\n\n"
        f"🏬 <b>Store:</b> {store_name}\n"
        "⚡ <i>Zero-Waste Food Rescue Network active</i>\n\n"
        "🛍️ <b>Food Rescue & Community:</b>\n"
        "• /nearby — Nearest zero-waste stores & hubs\n"
        "• /deals — Browse discounted surplus offers\n"
        "• /donations — NGO food rescue batches\n"
        "• /myreservations — Active pickup reservations\n\n"
        "📊 <b>Store Management & AI:</b>\n"
        "• /summary — Today's stock & sales briefing\n"
        "• /expiring — Batches expiring within 7 days\n"
        "• /inventory — Complete inventory breakdown\n"
        "• /stockouts — Low-stock run-out warnings\n"
        "• /recommendations — Review AI pricing actions\n"
        "• /help — Full command manual\n\n"
        "💬 <i>You can also ask questions like: \"What deals are expiring today?\"</i>"
    )
    await safe_reply_text(update, welcome_auth)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = (
        "📖 <b>Freshwise Assistant — Command Guide</b>\n\n"
        "🛍️ <b>Nearby Stores & Food Rescue:</b>\n"
        "• /nearby [location] — Locate closest stores (e.g. <code>/nearby Indiranagar</code>)\n"
        "• /deals — Browse surplus deals and reserve items\n"
        "• /donations — Surplus dispatched to NGO partners\n"
        "• /store [code] — Store profile, hours & directions\n"
        "• /myreservations — View active pickup reservation codes\n\n"
        "📊 <b>Store Operations:</b>\n"
        "• /summary — Store briefing, health & sales\n"
        "• /expiring — Batches expiring within 7 days\n"
        "• /inventory — Active stock quantities and prices\n"
        "• /stockouts — Low-stock warnings (≤ 5 units)\n"
        "• /recommendations — Review AI discount proposals\n\n"
        "🤖 <b>AI Store Copilot:</b>\n"
        "Send any operational question anytime:\n"
        "• <i>\"Top rescue opportunities today\"</i>\n"
        "• <i>\"What dairy items are expiring soon?\"</i>\n"
        "• <i>\"Find bread deals near Indiranagar\"</i>"
    )
    await safe_reply_text(update, help_text)


# ---------------------------------------------------------------------------
# Nearby Stores & Location Handlers
# ---------------------------------------------------------------------------

async def nearby_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /nearby [optional_locality_or_pincode] command."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    args = context.args or []
    query = " ".join(args).strip()

    lat = 12.9716  # Default: Central Bengaluru
    lon = 77.5946
    location_label = "Central Bengaluru (Default)"

    if query:
        if "," in query:
            try:
                parts = query.split(",")
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                location_label = f"Coordinates ({lat:.4f}, {lon:.4f})"
            except ValueError:
                geo = geocode_locality(query)
                if geo:
                    lat, lon, location_label = geo
        else:
            geo = geocode_locality(query)
            if geo:
                lat, lon, location_label = geo
            else:
                location_label = f"Locality matching '{query}'"

    nearby = get_nearby_stores(lat, lon, max_radius_km=40.0)

    loc_keyboard = [[KeyboardButton(text="📍 Share Current Location", request_location=True)]]
    reply_markup_kb = ReplyKeyboardMarkup(loc_keyboard, resize_keyboard=True, one_time_keyboard=True)

    header_msg = (
        "📍 <b>Nearby Zero-Waste Stores & Food Rescue Hubs</b>\n"
        f"🔍 <b>Location:</b> {location_label}\n"
        f"<i>(Found {len(nearby)} demo stores within radius)</i>\n\n"
        "💡 <i>Tip: Send a locality like <code>/nearby Koramangala</code> or tap the button below.</i>"
    )
    await safe_reply_text(update, header_msg, reply_markup=reply_markup_kb)

    for s in nearby[:4]:
        dist_km = s.get("distance_km", 0.0)
        deals_count = s.get("active_deals_count", 0)
        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={s['latitude']},{s['longitude']}"

        card_text = (
            f"🏬 <b>{s['name']}</b>\n"
            f"📍 <code>{dist_km:.1f} km away</code> • {s['locality']}\n"
            f"🏢 Address: {s['address']}\n"
            f"🕒 Hours: {s['pickup_hours']}\n"
            f"🏷️ Active Deals: <b>{deals_count} offer(s)</b>\n"
            f"📞 Contact: <code>{s['contact_phone']}</code>"
        )

        keyboard = [
            [
                InlineKeyboardButton("🏷️ View Deals", callback_data=f"store_deals:{s['id']}"),
                InlineKeyboardButton("🗺️ Directions", url=maps_url),
                InlineKeyboardButton("🤝 Donations", callback_data=f"store_donations:{s['id']}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await safe_reply_text(update, card_text, reply_markup=reply_markup)


async def location_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle native Telegram GPS location messages."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    loc = update.message.location if update.message else None
    if not loc:
        return

    lat = loc.latitude
    lon = loc.longitude

    nearby = get_nearby_stores(lat, lon, max_radius_km=50.0)

    await safe_reply_text(
        update,
        f"📍 <b>GPS Location Received:</b> <code>{lat:.4f}, {lon:.4f}</code>\n"
        f"Showing {len(nearby)} Freshwise stores sorted by distance:",
        reply_markup=ReplyKeyboardRemove(),
    )

    for s in nearby:
        dist_km = s.get("distance_km", 0.0)
        deals_count = s.get("active_deals_count", 0)
        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={s['latitude']},{s['longitude']}"

        card_text = (
            f"🏬 <b>{s['name']}</b>\n"
            f"📍 <code>{dist_km:.1f} km away</code> • {s['locality']}\n"
            f"🏢 Address: {s['address']}\n"
            f"🕒 Hours: {s['pickup_hours']}\n"
            f"🏷️ Active Deals: <b>{deals_count} offer(s)</b>"
        )

        keyboard = [
            [
                InlineKeyboardButton("🏷️ View Deals", callback_data=f"store_deals:{s['id']}"),
                InlineKeyboardButton("🗺️ Directions", url=maps_url),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await safe_reply_text(update, card_text, reply_markup=reply_markup)


# ---------------------------------------------------------------------------
# Deals & Food Rescue Handlers
# ---------------------------------------------------------------------------

async def deals_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /deals [optional_store_id] command."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    args = context.args or []
    filter_store_id = args[0] if args else ""

    deals = get_all_rescue_deals(store_id=filter_store_id)
    if not deals:
        await safe_reply_text(
            update,
            "🟢 <b>No active food rescue deals found.</b>\nAll surplus items have been cleared or reserved.",
        )
        return

    header = (
        "🏷️ <b>Freshwise Food Rescue Deals</b> <i>(Demo Mode)</i>\n"
        "Surplus perishable items discounted to prevent waste. Reserve now for pickup:"
    )
    await safe_reply_text(update, header)

    for d in deals:
        deal_id = d["id"]
        exp_tag = "🔴 1 DAY LEFT" if d["days_left"] == 1 else f"🟠 {d['days_left']} days left"

        card = (
            f"📦 <b>{d['product_name']}</b> ({d['sku']})\n"
            f"🏪 <b>Store:</b> {d['store_name']}\n"
            f"💰 <b>Deal:</b> <b>₹{d['rescue_price']:.1f}</b> <s>₹{d['original_price']:.1f}</s> (<code>{d['discount_percent']}% OFF</code>)\n"
            f"📦 <b>Qty:</b> <code>{d['quantity_available']} left</code> • ⏰ <b>Expiry:</b> {d['expiry_date']} ({exp_tag})\n"
            f"🕒 <b>Pickup:</b> {d['pickup_window']}"
        )

        keyboard = [
            [
                InlineKeyboardButton(f"📦 Reserve 1x (₹{d['rescue_price']:.0f})", callback_data=f"reserve_deal:{deal_id}"),
                InlineKeyboardButton("ℹ️ Details", callback_data=f"deal_details:{deal_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await safe_reply_text(update, card, reply_markup=reply_markup)


async def donations_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /donations command."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    donations = get_all_donations()
    if not donations:
        await safe_reply_text(update, "🟢 <b>No pending NGO donations at this time.</b>")
        return

    lines = [
        "🤝 <b>NGO Food Rescue & Community Donations</b> <i>(Demo Data)</i>\n",
        "Wholesome surplus food earmarked for non-profit distribution:\n",
    ]

    for don in donations:
        lines.append(
            f"• <b>{don['product_name']}</b> (<code>{don['quantity']} units</code>)\n"
            f"   🏪 <b>Store:</b> {don['store_name']}\n"
            f"   🤝 <b>Partner:</b> {don['partner_name']}\n"
            f"   🕒 <b>Pickup:</b> <code>{don['pickup_deadline']}</code> • 📌 <b>Status:</b> <code>{don['status'].upper()}</code>\n"
        )

    await safe_reply_text(update, "\n".join(lines))


async def store_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /store [optional_store_id_or_code] command."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    args = context.args or []
    target = args[0] if args else (auth_user.store_id if auth_user else "DEMO-STORE-001")

    store = get_demo_store_by_id(target)
    if not store:
        stores = get_all_demo_stores()
        list_str = "\n".join([f"• <code>{s['code']}</code> — {s['name']}" for s in stores])
        await safe_reply_text(
            update,
            f"❌ Store not found. Available demo stores:\n\n{list_str}",
        )
        return

    deals = get_all_rescue_deals(store_id=store["id"])
    maps_url = f"https://www.google.com/maps/dir/?api=1&destination={store['latitude']},{store['longitude']}"

    msg = (
        f"🏬 <b>{store['name']}</b> (<code>{store['code']}</code>)\n"
        f"📍 <b>Locality:</b> {store['locality']} (PIN: {store['pincode']})\n"
        f"🏢 <b>Address:</b> {store['address']}\n"
        f"🕒 <b>Hours:</b> {store['pickup_hours']}\n"
        f"📞 <b>Contact:</b> <code>{store['contact_phone']}</code>\n"
        f"🏷️ <b>Active Rescue Deals:</b> <code>{len(deals)} available</code>"
    )

    keyboard = [
        [
            InlineKeyboardButton("🏷️ Browse Deals", callback_data=f"store_deals:{store['id']}"),
            InlineKeyboardButton("🗺️ Directions", url=maps_url),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await safe_reply_text(update, msg, reply_markup=reply_markup)


async def myreservations_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /myreservations command."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    user_id, _, _ = _get_user_info(update)
    reservations = get_user_reservations(user_id)

    if not reservations:
        await safe_reply_text(
            update,
            "ℹ️ <b>You have no active demo reservations.</b>\n\n"
            "Use /deals or /nearby to find surplus items and reserve them for store pickup.",
        )
        return

    await safe_reply_text(
        update,
        f"🔖 <b>Your Food Rescue Reservations ({len(reservations)}):</b>",
    )

    for r in reservations:
        status_icon = "🟢 CONFIRMED" if r["status"] == "confirmed" else "⚪ CANCELLED"
        res_card = (
            f"🔖 <b>Reservation Code:</b> <code>{r['reservation_code']}</code>\n"
            f"📦 <b>Item:</b> <b>{r['product_name']}</b> ({r['quantity']}x)\n"
            f"🏪 <b>Store:</b> {r['store_name']}\n"
            f"💰 <b>Total Amount:</b> ₹{r['total_amount']:.2f}\n"
            f"🕒 <b>Pickup:</b> {r['pickup_window']}\n"
            f"📌 <b>Status:</b> <b>{status_icon}</b>"
        )

        keyboard = []
        if r["status"] == "confirmed":
            keyboard.append([InlineKeyboardButton("❌ Cancel Reservation", callback_data=f"cancel_res:{r['id']}")])

        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        await safe_reply_text(update, res_card, reply_markup=reply_markup)


# ---------------------------------------------------------------------------
# Store Operational Commands
# ---------------------------------------------------------------------------

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /summary command."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    s = get_store_summary(auth_user.store_id)
    exp_badge = "🔴" if s["expiring_soon_count"] > 0 else "🟢"
    rec_badge = "⚡" if s["open_recommendations_count"] > 0 else "✓"

    msg = (
        f"🏬 <b>Store Briefing: {s['store_name']}</b> <i>(Demo Data)</i>\n"
        f"📅 <b>Date:</b> {__import__('datetime').date.today().isoformat()}\n\n"
        "📦 <b>Inventory Overview:</b>\n"
        f"• Active Batches: <code>{s['total_batches']}</code>\n"
        f"• Units on Hand: <code>{s['total_units_on_hand']}</code> units\n\n"
        "⏰ <b>Expiry Watch:</b>\n"
        f"• {exp_badge} Expiring (≤3 days): <code>{s['expiring_soon_count']}</code> batches\n"
        f"• Expired Batches: <code>{s['expired_count']}</code>\n\n"
        "💡 <b>Action Recommendations:</b>\n"
        f"• {rec_badge} Pending Review: <code>{s['open_recommendations_count']}</code> items\n\n"
        f"📈 <b>7-Day Sales Volume:</b> <code>{s['sales_units_7d']}</code> units\n\n"
        "👉 Use /expiring for urgent batches or /recommendations to review actions."
    )
    await safe_reply_text(update, msg)


async def expiring_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /expiring command."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    batches = get_expiring_batches(auth_user.store_id, days_threshold=7)
    if not batches:
        await safe_reply_text(
            update,
            "🟢 <b>No batches expiring within the next 7 days!</b>\nAll store inventory is fresh.",
        )
        return

    lines = ["⏰ <b>Batches Expiring Soon (Next 7 Days):</b>\n"]
    for i, b in enumerate(batches, 1):
        days = b["days_left"]
        if isinstance(days, int):
            if days <= 0:
                tag = "🔴 EXPIRED"
            elif days == 1:
                tag = "🔴 1 DAY LEFT"
            elif days <= 3:
                tag = f"🟠 {days} days left"
            else:
                tag = f"🟡 {days} days left"
        else:
            tag = "⚪ Unknown"

        lines.append(
            f"• <b>{b['product_name']}</b> ({b['sku']})\n"
            f"   📦 <code>{b['quantity_on_hand']}</code> units • ⏰ <code>{b['expiry_date']}</code> ({tag})\n"
            f"   🔖 Batch: <code>{b['batch_code']}</code>\n"
        )

    lines.append("👉 Review dynamic pricing recommendations with /recommendations")
    await safe_reply_text(update, "\n".join(lines))


async def inventory_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /inventory command."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    items = get_inventory_status(auth_user.store_id)
    if not items:
        await safe_reply_text(update, "ℹ️ <b>No active inventory records found.</b>")
        return

    lines = [f"📦 <b>Store Inventory ({len(items)} batches) — Demo Data:</b>\n"]
    for it in items:
        days_str = f"exp in {it['days_left']}d" if it['days_left'] is not None else "fresh"
        lines.append(
            f"• <b>{it['product_name']}</b> (<code>{it['sku']}</code>)\n"
            f"   🏷️ {it['category'].capitalize()} • 📦 <code>{it['quantity_on_hand']}</code> units • 💰 ₹{it['selling_price']} ({days_str})\n"
        )

    await safe_reply_text(update, "\n".join(lines))


async def stockouts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stockouts command."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    risks = get_stockout_risks(auth_user.store_id, max_units_threshold=5)
    if not risks:
        await safe_reply_text(
            update,
            "🟢 <b>No stockout risks detected!</b>\nAll items have healthy shelf counts (>5 units).",
        )
        return

    lines = ["⚠️ <b>Low Stock & Stockout Warnings (≤5 units):</b>\n"]
    for r in risks:
        badge = "🚨 CRITICAL" if r["urgency"] == "CRITICAL" else "⚠️ LOW"
        lines.append(
            f"• <b>{r['product_name']}</b> ({r['sku']})\n"
            f"   📦 <b>{r['quantity_on_hand']} units left</b> • Status: {badge}\n"
            f"   🔖 Batch: <code>{r['batch_code']}</code>\n"
        )

    lines.append("👉 Consider restocking or confirming shelf inventory count.")
    await safe_reply_text(update, "\n".join(lines))


async def recommendations_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /recommendations command."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    recs = get_proposed_recommendations(auth_user.store_id, limit=5)
    if not recs:
        await safe_reply_text(
            update,
            "🟢 <b>No pending recommendations awaiting review!</b>\n"
            "All recommendations have been processed or none are currently proposed.",
        )
        return

    await safe_reply_text(
        update,
        f"💡 <b>Found {len(recs)} recommendation(s) awaiting your decision:</b>\n"
        "Tap Approve or Reject below each card to record your managerial decision.",
    )

    for r in recs:
        rec_id = r["id"]
        action = r["action"].upper()
        prod_name = r["product_name"]
        discount_text = f" • Discount: <code>{r['discount_percent']}%</code>" if r.get("discount_percent") else ""
        qty_text = f" • Qty: <code>{r['proposed_quantity']}</code>" if r.get("proposed_quantity") else ""

        card_text = (
            f"📋 <b>Recommendation #{rec_id[:12]}</b>\n"
            f"🏷️ <b>Product:</b> {prod_name} (<code>{r['sku']}</code>)\n"
            f"⚡ <b>Action:</b> <b>[{action}]</b>{discount_text}{qty_text}\n"
            f"🎯 <b>Confidence:</b> <code>{int(r['confidence'] * 100)}%</code>\n"
            f"📝 <b>Rationale:</b> {r['rationale']}"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"rec_approve:{rec_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"rec_reject:{rec_id}"),
                InlineKeyboardButton("ℹ️ Details", callback_data=f"rec_details:{rec_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await safe_reply_text(update, card_text, reply_markup=reply_markup)


# ---------------------------------------------------------------------------
# Inline Button Callback Handler
# ---------------------------------------------------------------------------

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process inline keyboard button clicks."""
    query = update.callback_query
    if not query:
        return

    user_id, username, first_name = _get_user_info(update)
    if not is_authorized(user_id):
        await query.answer("🔒 Unauthorized: Access Denied.", show_alert=True)
        return

    auth_user = get_authorized_user(user_id)
    store_id = auth_user.store_id if auth_user else "demo-store"

    data = query.data or ""
    parts = data.split(":", 1)
    if len(parts) != 2:
        await query.answer("❌ Invalid action.", show_alert=True)
        return

    action_type, target_id = parts[0], parts[1]
    actor_id = f"telegram:{user_id}" + (f" (@{username})" if username else "")

    # 1. Recommendation Details
    if action_type == "rec_details":
        rec = get_recommendation_by_id(target_id, store_id)
        if not rec:
            await query.answer("Recommendation not found.", show_alert=True)
            return
        details_msg = (
            f"Recommendation #{target_id}\n"
            f"Product: {rec['product_name']} ({rec['sku']})\n"
            f"Action: {rec['action'].upper()}\n"
            f"Confidence: {int(rec['confidence'] * 100)}%\n"
            f"Rationale: {rec['rationale']}\n"
            f"Status: {rec['status'].upper()}"
        )
        await query.answer(details_msg[:200], show_alert=True)
        return

    # 2. Recommendation Approve / Reject
    if action_type in ("rec_approve", "rec_reject"):
        decision = "approved" if action_type == "rec_approve" else "rejected"
        success, message, updated_rec = review_recommendation(
            rec_id=target_id,
            store_id=store_id,
            decision=decision,
            actor_id=actor_id,
            note=f"Decision made in Telegram Demo by {first_name or username or user_id}",
        )

        if not success:
            await query.answer(message, show_alert=True)
            if updated_rec and query.message:
                status_upper = updated_rec.get("status", "processed").upper()
                await safe_edit_message_text(
                    query,
                    f"{query.message.text}\n\n⚠️ <i>Already {status_upper} by {updated_rec.get('reviewed_by') or 'manager'}</i>",
                )
            return

        await query.answer(f"Recommendation {decision.capitalize()} (Demo)!", show_alert=False)

        status_icon = "✅ APPROVED" if decision == "approved" else "❌ REJECTED"
        original_msg = query.message.text if query.message else ""
        updated_text = (
            f"{original_msg}\n\n"
            f"═════════════════════════\n"
            f"📌 <b>{status_icon}</b> by {first_name or username or 'Manager'} (<code>{actor_id}</code>)\n"
            f"🕒 Timestamp: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            "<i>(Demo decision recorded. No physical ERP action dispatched.)</i>"
        )
        await safe_edit_message_text(query, updated_text)
        return

    # 3. Reserve Food Rescue Deal
    if action_type == "reserve_deal":
        deal = get_rescue_deal_by_id(target_id)
        if not deal:
            await query.answer("❌ Offer no longer available.", show_alert=True)
            return

        success, msg, res = create_demo_reservation(
            user_id=user_id,
            deal_id=target_id,
            quantity=1,
            actor_name=first_name or username or str(user_id),
        )

        if not success:
            await query.answer(msg, show_alert=True)
            return

        await query.answer("🎉 Demo Reservation Confirmed!", show_alert=False)
        await safe_reply_text(query.message, msg)
        return

    # 4. Cancel Reservation
    if action_type == "cancel_res":
        success, msg, res = cancel_demo_reservation(target_id, user_id)
        if not success:
            await query.answer(msg, show_alert=True)
            return

        await query.answer("Reservation cancelled.", show_alert=False)
        original_msg = query.message.text if query.message else ""
        await safe_edit_message_text(
            query,
            f"{original_msg}\n\n⚠️ <b>CANCELLED by user</b>",
        )
        return

    # 5. Deal Details popup
    if action_type == "deal_details":
        deal = get_rescue_deal_by_id(target_id)
        if not deal:
            await query.answer("Deal not found.", show_alert=True)
            return
        popup = (
            f"Deal: {deal['product_name']}\n"
            f"Rescue Price: ₹{deal['rescue_price']:.2f} ({deal['discount_percent']}% off)\n"
            f"Store: {deal['store_name']}\n"
            f"Pickup Window: {deal['pickup_window']}\n"
            f"Stock Left: {deal['quantity_available']} unit(s)"
        )
        await query.answer(popup[:200], show_alert=True)
        return

    # 6. Store Deals filter
    if action_type == "store_deals":
        deals = get_all_rescue_deals(store_id=target_id)
        if not deals:
            await query.answer("No active deals at this store.", show_alert=True)
            return
        await query.answer()
        for d in deals:
            card = (
                f"📦 <b>{d['product_name']}</b>\n"
                f"💰 <b>Price:</b> <b>₹{d['rescue_price']:.1f}</b> (<code>{d['discount_percent']}% OFF</code>)\n"
                f"🕒 <b>Pickup:</b> {d['pickup_window']}\n"
                f"📦 <b>Stock:</b> <code>{d['quantity_available']} left</code>"
            )
            keyboard = [[InlineKeyboardButton(f"📦 Reserve 1x (₹{d['rescue_price']:.0f})", callback_data=f"reserve_deal:{d['id']}")]]
            await safe_reply_text(query.message, card, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # 7. Store Donations filter
    if action_type == "store_donations":
        donations = get_all_donations(store_id=target_id)
        if not donations:
            await query.answer("No donations at this store.", show_alert=True)
            return
        await query.answer()
        lines = ["🤝 <b>NGO Food Rescue Batches:</b>\n"]
        for don in donations:
            lines.append(f"• <b>{don['product_name']}</b> ({don['quantity']}x) ➔ {don['partner_name']} (Pickup: <code>{don['pickup_deadline']}</code>)")
        await safe_reply_text(query.message, "\n".join(lines))
        return

    await query.answer("Unknown action.", show_alert=True)


# ---------------------------------------------------------------------------
# Natural-Language Message Handler
# ---------------------------------------------------------------------------

async def chat_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free-form natural language questions via Copilot adapter."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if not text:
        return

    # Send typing indicator safely
    try:
        if update.message.chat:
            await update.message.chat.send_action(action=constants.ChatAction.TYPING)
    except Exception as act_exc:
        logger.debug("Failed to send typing action: %s", act_exc)

    user_id, username, _ = _get_user_info(update)
    actor_id = f"telegram:{user_id}" + (f" (@{username})" if username else "")

    try:
        answer, is_grounded = ask_store_copilot(
            question=text,
            store_id=auth_user.store_id,
            actor_id=actor_id,
        )
    except Exception as exc:
        logger.error("Unexpected error in ask_store_copilot: %s", exc, exc_info=True)
        answer = (
            "🤖 <b>Freshwise Store Copilot</b> <i>(Demo Fallback)</i>\n\n"
            "An error occurred while answering your question. Please try again or use /summary / /inventory."
        )

    await safe_reply_text(update, answer)


def register_handlers(application: Any) -> None:
    """Register all bot commands, callbacks, and message listeners."""
    # Location Message Handler (Native Telegram GPS Location)
    application.add_handler(MessageHandler(filters.LOCATION, location_message_handler))

    # Core Store & Rescue Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("nearby", nearby_command))
    application.add_handler(CommandHandler("deals", deals_command))
    application.add_handler(CommandHandler("donations", donations_command))
    application.add_handler(CommandHandler("store", store_command))
    application.add_handler(CommandHandler("myreservations", myreservations_command))

    # Operational Management Commands
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(CommandHandler("inventory", inventory_command))
    application.add_handler(CommandHandler("expiring", expiring_command))
    application.add_handler(CommandHandler("stockouts", stockouts_command))
    application.add_handler(CommandHandler("recommendations", recommendations_command))

    # Inline button callbacks
    application.add_handler(CallbackQueryHandler(callback_query_handler))

    # Free-form natural language queries (excluding commands)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, chat_message_handler)
    )
