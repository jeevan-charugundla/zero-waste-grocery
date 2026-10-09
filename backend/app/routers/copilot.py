"""
Copilot router — data-aware AI assistant endpoint.

Server-side Supabase queries build the context; the frontend only sends
the question and optional filters. No authoritative inventory data should
ever come from the client.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from groq import Groq
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db import get_supabase

router = APIRouter(tags=["copilot"])


class CopilotRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    store_id: str | None = None
    filters: dict = Field(default_factory=dict)


class CopilotResponse(BaseModel):
    answer: str
    grounded: bool
    context_summary: str = ""


def _build_context(store_id: str | None, db) -> tuple[str, str]:
    """
    Query Supabase for current inventory state and build a text context string.

    Returns (context_text, context_summary).
    Raises RuntimeError on Supabase failure.
    """
    now_utc = datetime.now(timezone.utc)
    seven_days_ago = (datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).__class__(
        year=now_utc.year, month=now_utc.month, day=now_utc.day,
        tzinfo=now_utc.tzinfo
    ) - __import__("datetime").timedelta(days=7)).isoformat()

    def q(query_fn):
        try:
            return query_fn().execute().data or []
        except Exception as exc:
            raise RuntimeError(f"Supabase query failed: {exc}") from exc

    # 1. Expiry watch — top 10 soonest-expiring batches
    expiry_query = (
        db.table("inventory_batches")
        .select("id,batch_code,expiry_date,quantity_on_hand,product_id,products!inventory_batches_product_id_fkey(name,sku,category)")
        .order("expiry_date", desc=False)
        .limit(10)
    )
    if store_id:
        expiry_query = expiry_query.eq("store_id", store_id)
    expiring = q(lambda: expiry_query)

    # 2. Sales summary — last 7 days per product
    sales_base = (
        db.table("sales_records")
        .select("product_id,quantity,products(name)")
        .gte("sold_at", seven_days_ago)
    )
    if store_id:
        sales_base = sales_base.eq("store_id", store_id)
    sales_raw = q(lambda: sales_base)

    # Aggregate by product_id
    from collections import defaultdict
    sales_by_product: dict[str, dict] = defaultdict(lambda: {"name": "", "total": 0})
    for s in sales_raw:
        pid = s["product_id"]
        sales_by_product[pid]["total"] += int(s.get("quantity") or 0)
        if s.get("products"):
            sales_by_product[pid]["name"] = s["products"].get("name", "")

    # 3. Active promotions
    promo_base = (
        db.table("promotions")
        .select("name,discount_percent,status,starts_at,ends_at,products(name)")
        .in_("status", ["approved", "active"])
        .gte("ends_at", now_utc.isoformat())
        .limit(10)
    )
    if store_id:
        promo_base = promo_base.eq("store_id", store_id)
    promos = q(lambda: promo_base)

    # 4. Latest demand forecasts per product (most recent)
    forecast_base = (
        db.table("demand_forecasts")
        .select("product_id,forecast_units,forecast_date,products(name)")
        .order("forecast_date", desc=True)
        .limit(20)
    )
    if store_id:
        forecast_base = forecast_base.eq("store_id", store_id)
    forecasts_raw = q(lambda: forecast_base)
    # Keep only the most recent per product
    seen_forecast_pids: set[str] = set()
    forecasts: list[dict] = []
    for f in forecasts_raw:
        pid = f["product_id"]
        if pid not in seen_forecast_pids:
            seen_forecast_pids.add(pid)
            forecasts.append(f)

    # 5. Open recommendations
    rec_base = (
        db.table("recommendations")
        .select("action,rationale,products(name)")
        .eq("status", "proposed")
        .limit(10)
    )
    if store_id:
        rec_base = rec_base.eq("store_id", store_id)
    recs = q(lambda: rec_base)

    # Check if all data is empty
    all_empty = (not expiring and not sales_raw and not promos
                 and not forecasts and not recs)
    if all_empty:
        return (
            "[NO DATA] Database contains no relevant records for this query.",
            "No inventory data found.",
        )

    today = now_utc.date()
    lines: list[str] = []

    # Expiry watch section
    lines.append("=== Expiry Watch (soonest expiring first) ===")
    if expiring:
        for b in expiring:
            prod = b.get("products") or {}
            name = prod.get("name", "Unknown")
            sku = prod.get("sku", "")
            try:
                exp_date = __import__("datetime").date.fromisoformat(b["expiry_date"])
                days_left = (exp_date - today).days
            except Exception:
                days_left = "?"
            lines.append(
                f"  • {name} ({sku}) | batch {b['batch_code']} | "
                f"qty_on_hand={b['quantity_on_hand']} | expiry={b['expiry_date']} | "
                f"days_to_expiry={days_left}"
            )
    else:
        lines.append("  No expiry data available.")

    # Sales section
    lines.append("\n=== Recent Sales (last 7 days) ===")
    if sales_by_product:
        for pid, info in list(sales_by_product.items())[:10]:
            lines.append(f"  • {info['name']} | total_sold={info['total']} units")
    else:
        lines.append("  No sales data for the last 7 days.")

    # Promotions section
    lines.append("\n=== Active Promotions ===")
    if promos:
        for p in promos:
            prod = p.get("products") or {}
            lines.append(
                f"  • {prod.get('name','?')} | {p['name']} | "
                f"{p['discount_percent']}% off | status={p['status']}"
            )
    else:
        lines.append("  No active promotions.")

    # Forecasts section
    lines.append("\n=== Latest Demand Forecasts ===")
    if forecasts:
        for f in forecasts[:10]:
            prod = f.get("products") or {}
            lines.append(
                f"  • {prod.get('name','?')} | forecast={f['forecast_units']} units/day | "
                f"as_of={f['forecast_date']}"
            )
    else:
        lines.append("  No demand forecasts computed yet. Run /api/v1/intelligence/recalculate first.")

    # Recommendations section
    lines.append("\n=== Open Recommendations (proposed) ===")
    if recs:
        for r in recs:
            prod = r.get("products") or {}
            lines.append(f"  • [{r['action'].upper()}] {prod.get('name','?')}: {r['rationale'][:120]}")
    else:
        lines.append("  No open recommendations.")

    context_text = "\n".join(lines)
    context_summary = (
        f"Queried: {len(expiring)} expiring batches, "
        f"7-day sales for {len(sales_by_product)} products, "
        f"{len(promos)} active promotion(s), "
        f"{len(forecasts)} demand forecast(s), "
        f"{len(recs)} open recommendation(s)."
    )

    return context_text, context_summary


@router.post("/copilot/answer", response_model=CopilotResponse)
def answer_question(request: CopilotRequest):
    """Ask the AI Copilot a question grounded in live inventory data from Supabase."""
    settings = get_settings()
    if not settings.groq_api_key:
        raise HTTPException(status_code=503, detail="Set GROQ_API_KEY in backend/.env.")

    # Verify store_id if provided
    store_id = request.store_id or None
    if store_id:
        try:
            db = get_supabase()
            store_check = db.table("stores").select("id").eq("id", store_id).execute()
            if not store_check.data:
                raise HTTPException(status_code=404, detail=f"Store '{store_id}' not found.")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail="Data retrieval failed; cannot produce a grounded answer.",
            ) from exc
    else:
        try:
            db = get_supabase()
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    # Build server-side context
    try:
        context_text, context_summary = _build_context(store_id, db)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail="Data retrieval failed; cannot produce a grounded answer.",
        ) from exc

    # Check for empty data
    if context_text.startswith("[NO DATA]"):
        return CopilotResponse(
            answer=(
                "No inventory data is currently available. "
                "Please seed demo data or upload CSV data first."
            ),
            grounded=False,
            context_summary="Database returned no records.",
        )

    # Call Groq
    try:
        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model=settings.groq_model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a grocery operations copilot. Answer ONLY from the supplied "
                        "inventory context. If data is missing or insufficient, say so clearly. "
                        "Never invent inventory numbers, expiry dates, sales figures, or prices. "
                        "Never execute actions autonomously — manager approval is required for "
                        "all operational decisions. Be concise and specific."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Current inventory context:\n{context_text}\n\n"
                        f"Question: {request.question}"
                    ),
                },
            ],
        )
        answer = response.choices[0].message.content or "No answer produced."
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Groq request failed; check server logs and API settings.",
        ) from exc

    # Log to ai_runs
    try:
        db.table("ai_runs").insert([{
            "run_type": "copilot",
            "store_id": store_id,
            "input_summary": {"question": request.question[:200]},
            "output_summary": {"answer_length": len(answer)},
            "status": "completed",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }]).execute()
    except Exception:
        pass  # logging failure must not fail the response

    return CopilotResponse(answer=answer, grounded=True, context_summary=context_summary)
