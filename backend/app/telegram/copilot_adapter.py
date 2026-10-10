"""
Copilot adapter for Telegram chatbot.

Answers natural-language operational questions grounded in the demo inventory dataset,
using Groq for synthesis and explanations with robust deterministic fallbacks.
Formatted cleanly for mobile Telegram with emojis, compact cards, and zero random asterisks.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from groq import Groq

from app.config import get_settings
from app.telegram.demo_store import (
    build_demo_copilot_context,
    get_all_donations,
    get_all_rescue_deals,
    get_demo_expiring_batches,
    get_demo_inventory_batches,
    get_demo_proposed_recommendations,
    get_demo_stockout_risks,
    get_demo_store_summary,
)
from app.telegram.formatter import clean_telegram_text

logger = logging.getLogger("freshwise.telegram.copilot")


SYSTEM_PROMPT = (
    "You are the Freshwise Zero-Waste Store Copilot Telegram Assistant for '(DEMO) Freshwise Central'.\n"
    "Your mission is to help grocery store managers and staff take fast, confident action on "
    "perishable inventory, expiry risks, surplus food rescue deals, and NGO donations.\n\n"
    "STRICT TELEGRAM FORMATTING & STYLE RULES:\n"
    "1. NO RAW ASTERISKS: NEVER output raw asterisks (* or **). Do not write '**Bold**' or '* bullet'.\n"
    "   Use Telegram HTML tags: <b>bold</b> for headers/names and <i>italic</i> for tips or status.\n"
    "2. CLEAN EMOJIS: Use clear, relevant emojis to make cards instantly scannable on mobile screens "
    "(🌟, 🥬, 🥛, 🍞, 🏪, 💰, 📦, ⏰, 🕒, ⚡, 💡).\n"
    "3. SHORT & COMPACT: Keep messages concise, punchy, and structured. Avoid verbose essays.\n"
    "4. MAX 3 TO 4 ITEMS: When recommending deals or opportunities, select only the TOP 3 or 4 highest priority items.\n"
    "   Combine key details into 2 or 3 short lines per item. Example format:\n"
    "   1️⃣ <b>Baby Spinach 200g</b> (40% OFF)\n"
    "   🏪 Freshwise Whitefield • 💰 ₹33 (was ₹55) • 📦 8 left\n"
    "   ⏰ 1 day left • 🕒 Today, 2:00 – 9:30 PM • ⚡ Quick sale / donation\n\n"
    "5. STRICT GROUNDING: Strictly cite real numbers from the provided context. Never invent prices or quantities.\n"
    "   Clearly state (Demo Data).\n"
    "6. COMPLETE RESPONSES: Always finish your sentences cleanly. Never truncate midway."
)


def generate_deterministic_copilot_response(question: str) -> str:
    """
    Generate a factual, grounded response directly from the demo data provider
    without requiring external AI API calls. Uses clean emoji-rich HTML.
    """
    q = question.strip().lower()

    # 1. Expiring / waste / perishable items (with category filter if specified)
    if any(w in q for w in ["expir", "spoil", "waste", "shelf life", "days left", "best before"]):
        category = None
        for cat in ["dairy", "produce", "bakery", "grains"]:
            if cat in q:
                category = cat
                break

        batches = get_demo_inventory_batches()
        if category:
            batches = [b for b in batches if b["category"] == category]

        # Check 7-day window
        expiring = [b for b in batches if b["days_left"] <= 7]

        if not expiring:
            cat_label = f" in <b>{category.capitalize()}</b>" if category else ""
            return clean_telegram_text(
                f"🌿 <b>Freshwise Store Copilot</b> <i>(Demo Data)</i>\n\n"
                f"✅ No items{cat_label} are expiring within the next 7 days.\n\n"
                f"💡 Send /inventory to view all active batches."
            )

        lines = [
            "⏰ <b>Freshwise Store Copilot — Expiring Items</b> <i>(DEMO DATA)</i>",
        ]
        if category:
            lines.append(f"🏷️ Category: <b>{category.capitalize()}</b>")
        lines.append("")

        for i, b in enumerate(expiring[:4], 1):
            num_badge = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"][i - 1]
            urgency = "🔴 1 DAY LEFT" if b["days_left"] == 1 else f"🟠 {b['days_left']} days left"
            lines.append(
                f"{num_badge} <b>{b['product_name']}</b> ({b['sku']})\n"
                f"   📦 <code>{b['quantity_on_hand']}</code> units • ⏰ <code>{b['expiry_date']}</code> ({urgency})\n"
                f"   🔖 Batch: <code>{b['batch_code']}</code>"
            )

        # Also mention recommended actions if available
        recs = [r for r in get_demo_proposed_recommendations() if (not category or r.get("category") == category)]
        if recs:
            lines.append("\n💡 <b>Recommended Actions:</b>")
            for r in recs[:2]:
                lines.append(f"• <b>{r['product_name']}</b>: {r['action'].upper()} ({r.get('discount_percent', 0)}% off)")
            lines.append("\n👉 Review & approve with /recommendations")

        return clean_telegram_text("\n".join(lines))

    # 2. Low stock / stockouts / shortages
    if any(w in q for w in ["low stock", "stockout", "running low", "shortage", "out of stock", "reorder", "low on"]):
        risks = get_demo_stockout_risks(max_units_threshold=5)
        lines = [
            "⚠️ <b>Freshwise Store Copilot — Low Stock Warning</b> <i>(DEMO DATA)</i>\n",
            "Batches with critical on-hand quantities (≤ 5 units):\n",
        ]
        for r in risks[:4]:
            badge = "🚨 CRITICAL" if r["urgency"] == "CRITICAL" else "⚠️ LOW"
            lines.append(
                f"• <b>{r['product_name']}</b> ({r['sku']})\n"
                f"   📦 <b>{r['quantity_on_hand']} units left</b> • Status: {badge}"
            )
        lines.append("\n💡 <i>Tip: Consider reordering or shelf replenishment.</i>")
        return clean_telegram_text("\n".join(lines))

    # 3. Store summary / performance overview
    if any(w in q for w in ["summary", "performance", "overview", "store status", "store metrics", "sales today", "how is the store"]):
        s = get_demo_store_summary()
        return clean_telegram_text(
            f"📊 <b>Freshwise Store Copilot — Store Overview</b> <i>(DEMO DATA)</i>\n\n"
            f"🏬 <b>Store:</b> {s['store_name']} (<code>{s['store_code']}</code>)\n"
            f"📦 <b>Total Batches Tracked:</b> <code>{s['total_batches']}</code>\n"
            f"🏷️ <b>Units on Hand:</b> <code>{s['total_units_on_hand']}</code> units\n"
            f"⏰ <b>Expiring Soon (≤3d):</b> <code>{s['expiring_soon_count']}</code> batches\n"
            f"💡 <b>Pending Recommendations:</b> <code>{s['open_recommendations_count']}</code> items\n"
            f"📈 <b>7-Day Sales Volume:</b> <code>{s['sales_units_7d']}</code> units\n\n"
            f"👉 Use /summary or /recommendations for instant action."
        )

    # 4. Deals / food rescue / surplus / nearby items (e.g. bread, milk, spinach)
    if any(w in q for w in ["deal", "rescue", "surplus", "discount", "bread", "milk", "spinach", "strawberr", "yogurt", "cheap", "save"]):
        deals = get_all_rescue_deals()
        search_term = None
        for term in ["bread", "milk", "strawberries", "spinach", "yogurt"]:
            if term in q:
                search_term = term
                break

        if search_term:
            deals = [d for d in deals if search_term in d["product_name"].lower()]

        if deals:
            lines = [
                "🌟 <b>Freshwise Store Copilot — Surplus Food Rescue Deals</b> <i>(DEMO DATA)</i>\n",
                "Here are the best surplus deals to prioritize today:\n",
            ]
            badges = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
            for i, d in enumerate(deals[:4]):
                badge = badges[i] if i < len(badges) else "•"
                lines.append(
                    f"{badge} <b>{d['product_name']}</b> ({d['discount_percent']}% OFF)\n"
                    f"   🏪 {d['store_name']}\n"
                    f"   💰 <b>₹{d['rescue_price']:.1f}</b> (was ₹{d['original_price']:.1f}) • 📦 {d['quantity_available']} left\n"
                    f"   ⏰ {d['days_left']} day(s) left • 🕒 Pickup: {d['pickup_window']}\n"
                )
            lines.append("👉 Tap /deals to reserve or /nearby for store locations.")
            return clean_telegram_text("\n".join(lines))

    # 5. NGO Donations & Community food rescue
    if any(w in q for w in ["donation", "ngo", "charity", "robin hood", "feeding india", "akshaya"]):
        donations = get_all_donations()
        lines = [
            "🤝 <b>Freshwise Store Copilot — NGO Donations</b> <i>(DEMO DATA)</i>\n",
            "Wholesome surplus food earmarked for non-profit distribution:\n",
        ]
        for don in donations[:4]:
            lines.append(
                f"• <b>{don['product_name']}</b> ({don['quantity']}x)\n"
                f"   🏪 {don['store_name']} • 🤝 <b>{don['partner_name']}</b>\n"
                f"   🕒 Pickup: <code>{don['pickup_deadline']}</code> • Status: <code>{don['status'].upper()}</code>\n"
            )
        lines.append("👉 View all donations with /donations")
        return clean_telegram_text("\n".join(lines))

    # 6. Default general assistant capabilities guide
    return clean_telegram_text(
        "🤖 <b>Freshwise Store Copilot</b> <i>(DEMO DATA)</i>\n\n"
        "I can help you monitor stock, minimize waste, and find rescue deals:\n\n"
        "⏰ <i>\"What dairy items are expiring this week?\"</i>\n"
        "💡 <i>\"Top rescue opportunities today\"</i>\n"
        "⚠️ <i>\"What products are running low?\"</i>\n"
        "📊 <i>\"Summarize today's store operations\"</i>\n"
        "🏷️ <i>\"Find bread deals near Indiranagar\"</i>\n"
        "🤝 <i>\"Show pending NGO donations\"</i>\n\n"
        "👉 <i>Type /help to see all available commands.</i>"
    )


def ask_store_copilot(
    question: str,
    store_id: str = "",
    actor_id: str = "telegram_user",
) -> tuple[str, bool]:
    """
    Process a natural-language question using demo store context and Groq.
    Returns (formatted_answer_clean_html, is_grounded).
    Guarantees star-free, emoji-rich, concise formatting.
    """
    cleaned_question = question.strip()
    if len(cleaned_question) < 2:
        return (
            "Please ask an operational question about store inventory, expiry dates, or food rescue deals.",
            False,
        )
    if len(cleaned_question) > 1000:
        cleaned_question = cleaned_question[:1000]

    # 1. Build context from unified demo store provider
    context_text, _ = build_demo_copilot_context()

    settings = get_settings()
    groq_key = settings.groq_api_key.strip() if settings.groq_api_key else ""

    if not groq_key:
        logger.info("GROQ_API_KEY is not configured; using deterministic mock data provider.")
        deterministic_ans = generate_deterministic_copilot_response(cleaned_question)
        return clean_telegram_text(deterministic_ans), True

    # 2. Attempt Groq reasoning
    model_to_use = settings.groq_model.strip() or "qwen/qwen3.8-27b"

    try:
        client = Groq(api_key=groq_key, timeout=15.0)
        response = client.chat.completions.create(
            model=model_to_use,
            temperature=0.2,
            max_tokens=650,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"Current Store Inventory & Network Context:\n{context_text}\n\n"
                        f"Manager Question: {cleaned_question}"
                    ),
                },
            ],
        )
        raw_answer = response.choices[0].message.content or ""
        if not raw_answer.strip():
            logger.warning("Groq returned empty completion; falling back to deterministic answer.")
            return generate_deterministic_copilot_response(cleaned_question), True

        # Process through the Telegram text cleaner to remove all random stars and standardize formatting
        cleaned = clean_telegram_text(raw_answer)
        return cleaned, True

    except Exception as exc:
        exc_type = type(exc).__name__
        logger.warning(
            "Groq AI reasoning error (%s): %s. Falling back to deterministic answer.",
            exc_type,
            exc,
        )
        fallback_ans = generate_deterministic_copilot_response(cleaned_question)
        return clean_telegram_text(fallback_ans), True
