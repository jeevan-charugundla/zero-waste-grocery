"""
Copilot adapter for Telegram chatbot.

Answers natural-language operational questions grounded in the demo inventory dataset,
using Groq for synthesis and explanations with robust deterministic fallbacks.
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

logger = logging.getLogger("freshwise.telegram.copilot")


SYSTEM_PROMPT = (
    "You are the Freshwise Zero-Waste Store Copilot Telegram Assistant for '(DEMO) Freshwise Central'.\n"
    "You assist grocery store managers and staff in minimizing perishable food waste, monitoring stock levels, "
    "tracking product expiry dates, and discovering surplus food rescue opportunities.\n\n"
    "CRITICAL RULES:\n"
    "1. Base your answer strictly and exclusively on the provided Store Inventory and Rescue Deals context.\n"
    "2. NEVER invent, hallucinate, or alter any stock quantities, prices, batch codes, store distances, or expiry dates.\n"
    "3. If specific information is not in the context, explicitly state that it is not available in the demo records.\n"
    "4. Clearly mention that this data represents DEMO operational data.\n"
    "5. Format your response clearly for Telegram using bold titles and clean bullet points (- or •). "
    "DO NOT use raw brackets like [DEMO] without URLs, as that breaks Telegram Markdown link parsing. Write (DEMO) instead.\n"
    "6. Keep responses concise, direct, and actionable for a busy store manager."
)


def generate_deterministic_copilot_response(question: str) -> str:
    """
    Generate a factual, grounded response directly from the demo data provider
    without requiring external AI API calls.
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
            cat_label = f"in category '{category.capitalize()}'" if category else ""
            return (
                f"🌿 **Freshwise Store Copilot** *(DEMO DATA)*\n\n"
                f"No items {cat_label} are expiring within the next 7 days in the demo store.\n\n"
                f"💡 *Tip:* Send `/inventory` to check all active batches."
            )

        lines = [
            f"🌿 **Freshwise Store Copilot — Expiring Items** *(DEMO DATA)*\n",
        ]
        if category:
            lines.append(f"🏷️ Category Filter: **{category.capitalize()}**\n")

        for b in expiring:
            urgency = "🔴 **1 DAY LEFT**" if b["days_left"] == 1 else f"🟠 **{b['days_left']} days left**"
            lines.append(
                f"• **{b['product_name']}** ({b['sku']})\n"
                f"   Batch: `{b['batch_code']}` | Qty: `{b['quantity_on_hand']}` units | Expiry: `{b['expiry_date']}` ({urgency})\n"
            )

        # Also mention recommended actions if available
        recs = [r for r in get_demo_proposed_recommendations() if (not category or r.get("category") == category)]
        if recs:
            lines.append("💡 **Recommended Actions:**")
            for r in recs:
                lines.append(f"• {r['product_name']}: {r['action'].upper()} (`{r.get('discount_percent', 0)}% off`) — {r['rationale']}")
            lines.append("\n👉 Review in Telegram with `/recommendations`.")

        return "\n".join(lines)

    # 2. Low stock / stockouts / shortages
    if any(w in q for w in ["low stock", "stockout", "running low", "shortage", "out of stock", "reorder", "low on"]):
        risks = get_demo_stockout_risks(max_units_threshold=5)
        lines = [
            "⚠️ **Freshwise Store Copilot — Low Stock Warning** *(DEMO DATA)*\n",
            "The following batches have critical on-hand quantities (<= 5 units):\n",
        ]
        for r in risks:
            badge = "🚨 CRITICAL" if r["urgency"] == "CRITICAL" else "⚠️ LOW"
            lines.append(
                f"• **{r['product_name']}** (`{r['sku']}`): **{r['quantity_on_hand']} units** remaining ({badge})"
            )
        lines.append("\n💡 *Tip:* Consider ordering replenishment batches or verifying physical shelf count.")
        return "\n".join(lines)

    # 3. Store summary / performance overview
    if any(w in q for w in ["summary", "performance", "overview", "store status", "store metrics", "sales today", "how is the store"]):
        s = get_demo_store_summary()
        return (
            f"📊 **Freshwise Store Copilot — Store Overview** *(DEMO DATA)*\n\n"
            f"🏬 **Store:** {s['store_name']} (`{s['store_code']}`)\n"
            f"📦 **Total Batches Tracked:** {s['total_batches']}\n"
            f"🏷️ **Total Units on Hand:** {s['total_units_on_hand']} units\n"
            f"⏰ **Expiring Soon (<=3d):** {s['expiring_soon_count']} batch(es)\n"
            f"💡 **Open Recommendations:** {s['open_recommendations_count']} pending manager review\n"
            f"📈 **7-Day Sales Volume:** {s['sales_units_7d']} units sold\n\n"
            f"💡 *Tip:* Send `/summary` or `/recommendations` for quick managerial actions."
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
                "🏷️ **Freshwise Store Copilot — Surplus Food Rescue Deals** *(DEMO DATA)*\n",
                "Found active discounted deals to prevent perishable food waste:\n",
            ]
            for d in deals:
                lines.append(
                    f"• **{d['product_name']}** @ {d['store_name']}\n"
                    f"   Price: **₹{d['rescue_price']:.2f}** (`{d['discount_percent']}% OFF`, was ₹{d['original_price']:.2f})\n"
                    f"   Available: `{d['quantity_available']}` left | Pickup: `{d['pickup_window']}`\n"
                )
            lines.append("👉 Reserve in Telegram using `/deals` or find nearby hubs with `/nearby`.")
            return "\n".join(lines)

    # 5. NGO Donations & Community food rescue
    if any(w in q for w in ["donation", "ngo", "charity", "robin hood", "feeding india", "akshaya"]):
        donations = get_all_donations()
        lines = [
            "🤝 **Freshwise Store Copilot — NGO Food Rescue Batches** *(DEMO DATA)*\n",
            "Wholesome surplus food allocated for non-profit distribution:\n",
        ]
        for don in donations:
            lines.append(
                f"• **{don['product_name']}** ({don['quantity']}x) @ {don['store_name']}\n"
                f"   Partner: **{don['partner_name']}** | Pickup: `{don['pickup_deadline']}`\n"
                f"   Status: `{don['status'].upper()}`\n"
            )
        lines.append("👉 View all donations with `/donations`.")
        return "\n".join(lines)

    # 6. Default general assistant capabilities guide
    return (
        "🤖 **Freshwise Store Copilot** *(DEMO DATA)*\n\n"
        "I can help you analyze store operations, prevent waste, and discover food rescue opportunities:\n\n"
        "• ⏰ *\"What dairy items are expiring this week?\"*\n"
        "• 💡 *\"Which products are likely to be wasted?\"*\n"
        "• ⚠️ *\"What items are running low?\"*\n"
        "• 📊 *\"Summarize today's store performance\"*\n"
        "• 🏷️ *\"What nearby stores have surplus bread?\"*\n"
        "• 🤝 *\"Show pending NGO donations\"*\n\n"
        "*(Ask any operational question or use `/help` to see all available commands.)*"
    )


def ask_store_copilot(
    question: str,
    store_id: str = "",
    actor_id: str = "telegram_user",
) -> tuple[str, bool]:
    """
    Process a natural-language question using demo store context and Groq.
    Returns (formatted_answer_markdown, is_grounded).
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
        return deterministic_ans, True

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
        answer = response.choices[0].message.content or ""
        if not answer.strip():
            logger.warning("Groq returned empty completion; falling back to deterministic answer.")
            return generate_deterministic_copilot_response(cleaned_question), True

        # Sanitize any raw brackets that could break Telegram legacy markdown
        sanitized_answer = answer.replace("[DEMO]", "(DEMO)").replace("[demo]", "(demo)")
        return sanitized_answer, True

    except Exception as exc:
        exc_type = type(exc).__name__
        logger.warning(
            "Groq AI reasoning error (%s): %s. Falling back to deterministic answer.",
            exc_type,
            exc,
        )
        fallback_ans = generate_deterministic_copilot_response(cleaned_question)
        return fallback_ans, True

