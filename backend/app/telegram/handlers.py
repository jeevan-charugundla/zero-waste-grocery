"""
Telegram Bot Handlers.

Implements all user commands, food rescue deals, nearby store discovery,
reservations, NGO donations, inline callbacks, and AI Copilot interactions.
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

logger = logging.getLogger("freshwise.telegram.handlers")


def _get_user_info(update: Update) -> tuple[int, str, str]:
    """Extract user_id, username, first_name safely from update."""
    user = update.effective_user
    if not user:
        return 0, "", ""
    return user.id, user.username or "", user.first_name or ""


async def safe_reply_text(
    update: Update,
    text: str,
    reply_markup: Any = None,
    parse_mode: Any = constants.ParseMode.MARKDOWN,
) -> Message | None:
    """
    Safely reply to an incoming message, falling back to plain text if Markdown entity parsing fails.
    Prevents unescaped Markdown from causing silent message send failures.
    """
    if not update or not update.message:
        return None

    try:
        return await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    except Exception as exc:
        logger.warning(
            "Failed to send message with parse_mode=%s (%s). Retrying in plain text.",
            parse_mode,
            exc,
        )
        try:
            return await update.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode=None,
            )
        except Exception as fallback_exc:
            logger.error("Failed to send fallback plain text message: %s", fallback_exc)
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
            "🔒 *Access Denied — Unauthorized User*\n\n"
            f"Your Telegram User ID: `{user_id}`\n\n"
            "You are not authorized to view or manage store inventory data.\n\n"
            "👉 *To authenticate as a Store Manager:*\n"
            "Add your Telegram User ID to `TELEGRAM_ALLOWED_USER_IDS` in `backend/.env`."
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
            "🌿 *Welcome to Freshwise Zero-Waste Grocery Assistant!*\n\n"
            "This bot provides proactive inventory alerts, food rescue deals, "
            "nearby store discovery, and AI-driven markdown/donation approvals.\n\n"
            f"🔒 *Status:* Unauthorized (ID: `{user_id}`)\n\n"
            "To access store data, add your Telegram User ID "
            "to `TELEGRAM_ALLOWED_USER_IDS` in `backend/.env`.\n\n"
            "Type `/help` for more information."
        )
        await update.message.reply_text(welcome_unauth, parse_mode=constants.ParseMode.MARKDOWN)
        return

    auth_user = get_authorized_user(user_id)
    store_name = auth_user.store_name if auth_user else "[DEMO] Freshwise Central"

    welcome_auth = (
        f"🌿 *Welcome back, {html.escape(first_name or username or 'Manager')}!*\n\n"
        f"🏬 *Active Network:* Freshwise Zero-Waste Grocery *(Demo)*\n"
        f"📍 *Primary Store:* {store_name}\n\n"
        "⚡ *Customer & Food Rescue Commands:*\n"
        "• `/nearby` — Find nearest zero-waste stores & food rescue spots\n"
        "• `/deals` — Browse markdown surplus offers & reserve items\n"
        "• `/donations` — View NGO food rescue & community donations\n"
        "• `/myreservations` — View or cancel active demo reservations\n\n"
        "📊 *Store Operations & AI Intelligence:*\n"
        "• `/summary` — Today's executive briefing & stock health\n"
        "• `/inventory` — Itemized stock breakdown\n"
        "• `/expiring` — Batches approaching expiry\n"
        "• `/stockouts` — Low-stock warnings\n"
        "• `/recommendations` — Review & approve AI pricing actions\n"
        "• `/help` — Full command manual\n\n"
        "💬 *You can also ask me natural questions!* (e.g. *'Find bread deals near Indiranagar'*)"
    )
    await update.message.reply_text(welcome_auth, parse_mode=constants.ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = (
        "📖 *Freshwise Store Assistant — Command Guide*\n\n"
        "🛍️ *Nearby Stores & Food Rescue (Demo):*\n"
        "• `/nearby [PIN/locality]` — Locate closest Freshwise stores (e.g. `/nearby 560038` or `/nearby Indiranagar`)\n"
        "• `/deals [store_id]` — Browse discounted surplus food deals and make instant demo reservations\n"
        "• `/donations` — View food rescue batches dispatched to NGO partners\n"
        "• `/store [code]` — View full store profile, hours, and directions\n"
        "• `/myreservations` — Check your active demo reservation codes & pickup status\n\n"
        "📊 *Store Management:*\n"
        "• `/summary` — Executive store briefing, sales, and urgent risks\n"
        "• `/expiring` — Batches expiring within 7 days sorted by urgency\n"
        "• `/inventory` — View active batches, quantities, and prices\n"
        "• `/stockouts` — Low-stock run-out warnings\n"
        "• `/recommendations` — Review and approve/reject AI markdowns\n\n"
        "🤖 *AI Store Copilot:*\n"
        "Send any message to search deals or query inventory intelligence:\n"
        "• *'Find dairy deals near Indiranagar'*\n"
        "• *'Which products are expiring this week?'*\n"
        "• *'Show NGO donations in Central Bengaluru'*"
    )
    await update.message.reply_text(help_text, parse_mode=constants.ParseMode.MARKDOWN)


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
        # Check if coordinates "lat, lon" passed directly
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

    # Location prompt keyboard button
    loc_keyboard = [[KeyboardButton(text="📍 Share Current Location", request_location=True)]]
    reply_markup_kb = ReplyKeyboardMarkup(loc_keyboard, resize_keyboard=True, one_time_keyboard=True)

    header_msg = (
        f"📍 *Nearby Zero-Waste Stores & Food Rescue Hubs*\n"
        f"🔍 *Reference Location:* {location_label}\n"
        f"*(Found {len(nearby)} demo stores within radius)*\n\n"
        "💡 *Tip:* Send a PIN or locality like `/nearby 560038` or tap the button below to share GPS location."
    )
    await update.message.reply_text(header_msg, reply_markup=reply_markup_kb, parse_mode=constants.ParseMode.MARKDOWN)

    for s in nearby[:4]:
        dist_km = s.get("distance_km", 0.0)
        deals_count = s.get("active_deals_count", 0)
        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={s['latitude']},{s['longitude']}"

        card_text = (
            f"🏬 **{s['name']}**\n"
            f"📍 `{dist_km} km away` | {s['locality']}\n"
            f"🏢 Address: {s['address']}\n"
            f"🕒 Hours: {s['pickup_hours']}\n"
            f"🏷️ Available Rescue Deals: `{deals_count} active offer(s)`\n"
            f"📞 Contact: `{s['contact_phone']}`\n\n"
            f"*(DEMO DATA)*"
        )

        keyboard = [
            [
                InlineKeyboardButton("🏷️ View Deals", callback_data=f"store_deals:{s['id']}"),
                InlineKeyboardButton("🗺️ Directions", url=maps_url),
                InlineKeyboardButton("🤝 Donations", callback_data=f"store_donations:{s['id']}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(card_text, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)


async def location_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle native Telegram GPS location messages."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    loc = update.message.location
    if not loc:
        return

    lat = loc.latitude
    lon = loc.longitude

    nearby = get_nearby_stores(lat, lon, max_radius_km=50.0)

    # Remove the location keyboard
    await update.message.reply_text(
        f"📍 *GPS Location Received:* `{lat:.4f}, {lon:.4f}`\n"
        f"Showing {len(nearby)} Freshwise stores sorted by distance:",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=constants.ParseMode.MARKDOWN,
    )

    for s in nearby:
        dist_km = s.get("distance_km", 0.0)
        deals_count = s.get("active_deals_count", 0)
        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={s['latitude']},{s['longitude']}"

        card_text = (
            f"🏬 **{s['name']}**\n"
            f"📍 `{dist_km} km away` | {s['locality']}\n"
            f"🏢 Address: {s['address']}\n"
            f"🕒 Pickup Hours: {s['pickup_hours']}\n"
            f"🏷️ Active Deals: `{deals_count} offers`\n\n"
            f"*(DEMO DATA)*"
        )

        keyboard = [
            [
                InlineKeyboardButton("🏷️ View Deals", callback_data=f"store_deals:{s['id']}"),
                InlineKeyboardButton("🗺️ Directions", url=maps_url),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(card_text, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)


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
        await update.message.reply_text(
            "🟢 *No active food rescue deals found at this time.*\nAll items sold out or fresh.",
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        return

    header = (
        f"🏷️ *Freshwise Food Rescue Deals* *(Demo Mode)*\n"
        f"Surplus perishable items discounted to prevent waste. Reserve now for store pickup:\n"
    )
    await update.message.reply_text(header, parse_mode=constants.ParseMode.MARKDOWN)

    for d in deals:
        deal_id = d["id"]
        exp_tag = "🔴 **EXPIRES TOMORROW**" if d["days_left"] == 1 else f"🟠 **{d['days_left']} days left**"

        card = (
            f"📦 **{d['product_name']}** ({d['sku']})\n"
            f"🏬 Store: {d['store_name']}\n"
            f"💰 Price: **₹{d['rescue_price']:.2f}** ~₹{d['original_price']:.2f}~ (`{d['discount_percent']}% OFF`)\n"
            f"📦 Stock Available: `{d['quantity_available']} unit(s)`\n"
            f"⏰ Expiry: `{d['expiry_date']}` ({exp_tag})\n"
            f"🕒 Pickup Window: `{d['pickup_window']}`\n\n"
            f"*(DEMO DATA)*"
        )

        keyboard = [
            [
                InlineKeyboardButton(f"📦 Reserve 1x (₹{d['rescue_price']:.0f})", callback_data=f"reserve_deal:{deal_id}"),
                InlineKeyboardButton("ℹ️ Details", callback_data=f"deal_details:{deal_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(card, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)


async def donations_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /donations command."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    donations = get_all_donations()
    if not donations:
        await update.message.reply_text("🟢 *No pending NGO donations at this time.*")
        return

    lines = [
        "🤝 *NGO Food Rescue & Community Donations* *(Demo Data)*\n",
        "Wholesome surplus food earmarked for non-profit community meal distribution:\n",
    ]

    for don in donations:
        lines.append(
            f"• **{don['product_name']}** (`{don['quantity']} units`)\n"
            f"   🏬 Store: {don['store_name']}\n"
            f"   🤝 Partner: **{don['partner_name']}**\n"
            f"   🕒 Pickup: `{don['pickup_deadline']}`\n"
            f"   🛡️ Safety: {don['eligibility_basis']}\n"
            f"   📌 Status: `{don['status'].upper()}`\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode=constants.ParseMode.MARKDOWN)


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
        list_str = "\n".join([f"• `{s['code']}` — {s['name']}" for s in stores])
        await update.message.reply_text(
            f"❌ Store not found. Available demo stores:\n\n{list_str}",
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        return

    deals = get_all_rescue_deals(store_id=store["id"])
    maps_url = f"https://www.google.com/maps/dir/?api=1&destination={store['latitude']},{store['longitude']}"

    msg = (
        f"🏬 **{store['name']}** (`{store['code']}`)\n"
        f"📍 Locality: {store['locality']} (PIN: {store['pincode']})\n"
        f"🏢 Address: {store['address']}\n"
        f"🕒 Hours: {store['pickup_hours']}\n"
        f"📞 Phone: `{store['contact_phone']}`\n"
        f"🏷️ Active Rescue Deals: `{len(deals)} available`\n\n"
        f"*(DEMO STORE)*"
    )

    keyboard = [
        [
            InlineKeyboardButton("🏷️ Browse Deals", callback_data=f"store_deals:{store['id']}"),
            InlineKeyboardButton("🗺️ Directions", url=maps_url),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)


async def myreservations_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /myreservations command."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    user_id, _, _ = _get_user_info(update)
    reservations = get_user_reservations(user_id)

    if not reservations:
        await update.message.reply_text(
            "ℹ️ *You have no active demo reservations.*\n\n"
            "Use `/deals` or `/nearby` to find discounted items and make a demo reservation.",
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        return

    await update.message.reply_text(
        f"🔖 *Your Demo Food Rescue Reservations ({len(reservations)}):*",
        parse_mode=constants.ParseMode.MARKDOWN,
    )

    for r in reservations:
        status_icon = "🟢 CONFIRMED" if r["status"] == "confirmed" else "⚪ CANCELLED"
        res_card = (
            f"🔖 **Reservation Code: `{r['reservation_code']}`**\n"
            f"📦 Item: **{r['product_name']}** ({r['quantity']}x)\n"
            f"🏬 Store: {r['store_name']}\n"
            f"💰 Total Amount: ₹{r['total_amount']:.2f} (Demo)\n"
            f"🕒 Pickup Window: `{r['pickup_window']}`\n"
            f"📌 Status: **{status_icon}**\n\n"
            f"*(DEMO RESERVATION)*"
        )

        keyboard = []
        if r["status"] == "confirmed":
            keyboard.append([InlineKeyboardButton("❌ Cancel Reservation", callback_data=f"cancel_res:{r['id']}")])

        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        await update.message.reply_text(res_card, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN)


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
        f"🏬 *Store Briefing: {s['store_name']}* *(Demo Data)*\n"
        f"📅 *As of:* {__import__('datetime').date.today().isoformat()}\n\n"
        f"📦 *Inventory Overview:*\n"
        f"• Active Batches: `{s['total_batches']}`\n"
        f"• Total Units on Hand: `{s['total_units_on_hand']}`\n\n"
        f"⏰ *Expiry Watch:*\n"
        f"• {exp_badge} Batches Expiring (<=3 days): `{s['expiring_soon_count']}`\n"
        f"• Expired Batches: `{s['expired_count']}`\n\n"
        f"💡 *Agentic Recommendations:*\n"
        f"• {rec_badge} Pending Review: `{s['open_recommendations_count']}`\n\n"
        f"📈 *7-Day Sales Volume:* `{s['sales_units_7d']}` units\n\n"
        "👉 Use `/expiring` for urgent batches, `/deals` for customer offers, or `/recommendations` to review action items."
    )
    await update.message.reply_text(msg, parse_mode=constants.ParseMode.MARKDOWN)


async def expiring_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /expiring command."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    batches = get_expiring_batches(auth_user.store_id, days_threshold=7)
    if not batches:
        await update.message.reply_text(
            "🟢 *No batches expiring within the next 7 days!*\nAll inventory is fresh.",
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        return

    lines = ["⏰ *Batches Expiring Soon (Next 7 Days) — Demo Data:*\n"]
    for b in batches:
        days = b["days_left"]
        if isinstance(days, int):
            if days <= 0:
                tag = "🔴 **EXPIRED / TODAY**"
            elif days == 1:
                tag = "🔴 **1 DAY LEFT**"
            elif days <= 3:
                tag = f"🟠 **{days} days left**"
            else:
                tag = f"🟡 {days} days left"
        else:
            tag = "⚪ Unknown"

        lines.append(
            f"• *{b['product_name']}* ({b['sku']})\n"
            f"   Batch: `{b['batch_code']}` | Qty: `{b['quantity_on_hand']}` | "
            f"Expiry: `{b['expiry_date']}` ({tag})\n"
        )

    lines.append("\n👉 Review dynamic pricing recommendations with `/recommendations`.")
    await update.message.reply_text("\n".join(lines), parse_mode=constants.ParseMode.MARKDOWN)


async def inventory_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /inventory command."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    items = get_inventory_status(auth_user.store_id)
    if not items:
        await update.message.reply_text("ℹ️ No active inventory records found.")
        return

    lines = [f"📦 *Store Inventory Status ({len(items)} batches) — Demo Data:*\n"]
    for it in items:
        days_str = f"exp in {it['days_left']}d" if it['days_left'] is not None else "no expiry"
        lines.append(
            f"• *{it['product_name']}* (`{it['sku']}`)\n"
            f"   Category: {it['category']} | Qty: `{it['quantity_on_hand']}` | ₹{it['selling_price']} | ({days_str})\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode=constants.ParseMode.MARKDOWN)


async def stockouts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stockouts command."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    risks = get_stockout_risks(auth_user.store_id, max_units_threshold=5)
    if not risks:
        await update.message.reply_text(
            "🟢 *No stockout risks detected!*\nAll items have sufficient stock levels (>5 units).",
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        return

    lines = ["⚠️ *Low Stock & Stockout Warnings (<=5 units) — Demo Data:*\n"]
    for r in risks:
        badge = "🚨" if r["urgency"] == "CRITICAL" else "⚠️"
        lines.append(
            f"• {badge} *{r['product_name']}* ({r['sku']})\n"
            f"   Batch: `{r['batch_code']}` | Units Left: `{r['quantity_on_hand']}` | Status: *{r['urgency']}*\n"
        )

    lines.append("\n👉 Consider placing purchase orders or replenishing inventory.")
    await update.message.reply_text("\n".join(lines), parse_mode=constants.ParseMode.MARKDOWN)


async def recommendations_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /recommendations command."""
    auth_user = await _check_auth(update, context)
    if not auth_user:
        return

    recs = get_proposed_recommendations(auth_user.store_id, limit=5)
    if not recs:
        await update.message.reply_text(
            "🟢 *No pending recommendations awaiting review!*\n"
            "All recommendations have been processed or none are currently proposed.",
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        return

    await update.message.reply_text(
        f"💡 *Found {len(recs)} recommendation(s) awaiting your decision:*\n"
        "Click Approve or Reject below each recommendation card to record your managerial decision.",
        parse_mode=constants.ParseMode.MARKDOWN,
    )

    for r in recs:
        rec_id = r["id"]
        action = r["action"].upper()
        prod_name = r["product_name"]
        discount_text = f" | Discount: `{r['discount_percent']}%`" if r.get("discount_percent") else ""
        qty_text = f" | Qty: `{r['proposed_quantity']}`" if r.get("proposed_quantity") else ""

        card_text = (
            f"📋 *Recommendation #{rec_id[:12]}*\n"
            f"🏷️ *Product:* {prod_name} (`{r['sku']}`)\n"
            f"⚡ *Action:* **[{action}]**{discount_text}{qty_text}\n"
            f"🎯 *Confidence:* `{int(r['confidence'] * 100)}%`\n"
            f"📝 *Rationale:* {r['rationale']}\n\n"
            f"*(Status: PROPOSED — DEMO DATA)*"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"rec_approve:{rec_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"rec_reject:{rec_id}"),
                InlineKeyboardButton("ℹ️ Details", callback_data=f"rec_details:{rec_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            card_text,
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.MARKDOWN,
        )


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
            if updated_rec:
                status_upper = updated_rec.get("status", "processed").upper()
                await query.edit_message_text(
                    f"{query.message.text}\n\n⚠️ *Already {status_upper} by {updated_rec.get('reviewed_by') or 'manager'}*",
                    parse_mode=constants.ParseMode.MARKDOWN,
                )
            return

        await query.answer(f"Recommendation {decision.capitalize()} (Demo)!", show_alert=False)

        status_icon = "✅ APPROVED" if decision == "approved" else "❌ REJECTED"
        updated_text = (
            f"{query.message.text}\n\n"
            f"═════════════════════════\n"
            f"📌 **{status_icon}** by {first_name or username or 'Manager'} (`{actor_id}`)\n"
            f"🕒 Timestamp: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"*(Demo decision recorded. No physical ERP action dispatched.)*"
        )
        await query.edit_message_text(updated_text, parse_mode=constants.ParseMode.MARKDOWN)
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
        await query.message.reply_text(msg, parse_mode=constants.ParseMode.MARKDOWN)
        return

    # 4. Cancel Reservation
    if action_type == "cancel_res":
        success, msg, res = cancel_demo_reservation(target_id, user_id)
        if not success:
            await query.answer(msg, show_alert=True)
            return

        await query.answer("Reservation cancelled.", show_alert=False)
        await query.edit_message_text(
            f"{query.message.text}\n\n⚠️ **CANCELLED by user**",
            parse_mode=constants.ParseMode.MARKDOWN,
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
                f"📦 **{d['product_name']}**\n"
                f"💰 Price: **₹{d['rescue_price']:.2f}** (`{d['discount_percent']}% OFF`)\n"
                f"🕒 Pickup: {d['pickup_window']}\n"
                f"📦 Stock: {d['quantity_available']} left\n"
            )
            keyboard = [[InlineKeyboardButton(f"📦 Reserve 1x (₹{d['rescue_price']:.0f})", callback_data=f"reserve_deal:{d['id']}")]]
            await query.message.reply_text(card, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=constants.ParseMode.MARKDOWN)
        return

    # 7. Store Donations filter
    if action_type == "store_donations":
        donations = get_all_donations(store_id=target_id)
        if not donations:
            await query.answer("No donations at this store.", show_alert=True)
            return
        await query.answer()
        lines = [f"🤝 **NGO Food Rescue Batches:**\n"]
        for don in donations:
            lines.append(f"• **{don['product_name']}** ({don['quantity']}x) -> {don['partner_name']} (Pickup: {don['pickup_deadline']})")
        await query.message.reply_text("\n".join(lines), parse_mode=constants.ParseMode.MARKDOWN)
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
            "🤖 **Freshwise Store Copilot** *(Demo Fallback)*\n\n"
            "An error occurred while answering your question. Please try again or use `/summary` / `/inventory`."
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

