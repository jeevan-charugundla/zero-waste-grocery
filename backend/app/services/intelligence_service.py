"""
Intelligence service: batch risk calculation and store-level recalculation.

Reuses calculate_batch_risk from services/risk.py and
moving_average_forecast from services/forecast.py.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.services.forecast import moving_average_forecast
from app.services.risk import calculate_batch_risk


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> date:
    return date.today()


# ---------------------------------------------------------------------------
# Batch risk
# ---------------------------------------------------------------------------

def get_batch_risks(store_id: str, db: Any) -> list[dict]:
    """
    For each inventory batch in the store, compute risk using calculate_batch_risk.

    If fewer than 2 days of sales data exist for a product, forecast_demand
    is set to 0 and insufficient_data=True is flagged.
    """
    # Fetch all batches for the store, joined with product info
    try:
        batches_resp = (
            db.table("inventory_batches")
            .select(
                "id,batch_code,product_id,received_at,expiry_date,"
                "quantity_received,quantity_on_hand,"
                "products!inventory_batches_product_id_fkey(id,name,sku,category)"
            )
            .eq("store_id", store_id)
            .execute()
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch inventory batches: {exc}") from exc

    batches = batches_resp.data or []
    if not batches:
        return []

    today = _today()
    # Fetch sales from last 7 days for the store to estimate daily demand
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    try:
        sales_resp = (
            db.table("sales_records")
            .select("product_id,quantity,sold_at")
            .eq("store_id", store_id)
            .gte("sold_at", week_ago)
            .execute()
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch sales records: {exc}") from exc

    # Aggregate daily sales per product
    from collections import defaultdict
    daily_sales: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for sale in sales_resp.data or []:
        pid = sale["product_id"]
        day_str = sale["sold_at"][:10]  # YYYY-MM-DD
        daily_sales[pid][day_str] += int(sale["quantity"] or 0)

    results = []
    for batch in batches:
        product = batch.get("products") or {}
        product_id = batch["product_id"]
        product_name = product.get("name", "Unknown")
        sku = product.get("sku", "")

        expiry_str = batch.get("expiry_date", "")
        try:
            expiry_date = date.fromisoformat(expiry_str)
        except (ValueError, TypeError):
            expiry_date = today

        qty_on_hand = int(batch.get("quantity_on_hand") or 0)

        # Compute forecast demand before expiry
        pid_daily = daily_sales.get(product_id, {})
        days_with_data = len(pid_daily)
        days_to_expiry = (expiry_date - today).days

        insufficient_data = days_with_data < 2

        if insufficient_data or days_to_expiry <= 0:
            avg_daily = 0.0
        else:
            daily_values = list(pid_daily.values())
            try:
                forecast = moving_average_forecast(daily_values, window=min(7, len(daily_values)))
                avg_daily = forecast["forecast_units"]
            except ValueError:
                avg_daily = 0.0

        forecast_demand = int(avg_daily * max(0, days_to_expiry))

        risk = calculate_batch_risk(
            quantity=qty_on_hand,
            forecast_demand_before_expiry=forecast_demand,
            expiry_date=expiry_date,
            as_of=today,
        )

        results.append({
            "batch_id": batch["id"],
            "batch_code": batch["batch_code"],
            "product_id": product_id,
            "product_name": product_name,
            "sku": sku,
            "expiry_date": expiry_str,
            "quantity_on_hand": qty_on_hand,
            "days_to_expiry": risk.days_to_expiry,
            "at_risk_units": risk.at_risk_units,
            "risk_percent": risk.risk_percent,
            "forecast_demand_before_expiry": forecast_demand,
            "insufficient_data": insufficient_data,
        })

    return results


# ---------------------------------------------------------------------------
# Recalculate store intelligence
# ---------------------------------------------------------------------------

def recalculate_store(store_id: str, db: Any) -> dict:
    """
    Run full intelligence recalculation for a store:
    1. Compute batch risks.
    2. For products with >= 7 days of sales data, write demand_forecasts.
    3. For high-risk batches (risk_percent >= 50), write markdown recommendations.
    4. Log to ai_runs.
    """
    from collections import defaultdict

    batch_risks = get_batch_risks(store_id, db)
    today = _today()

    # Fetch last 28 days of sales for demand forecast
    four_weeks_ago = (datetime.now(timezone.utc) - timedelta(days=28)).isoformat()
    try:
        sales_resp = (
            db.table("sales_records")
            .select("product_id,quantity,sold_at")
            .eq("store_id", store_id)
            .gte("sold_at", four_weeks_ago)
            .execute()
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch sales for forecast: {exc}") from exc

    # Build per-product daily totals
    product_daily: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for sale in sales_resp.data or []:
        pid = sale["product_id"]
        day_str = sale["sold_at"][:10]
        product_daily[pid][day_str] += float(sale["quantity"] or 0)

    forecasts_written = 0
    for product_id, daily_dict in product_daily.items():
        if len(daily_dict) < 7:
            continue  # insufficient history

        # Fill missing days with 0 for a continuous 28-day window
        all_days = sorted(daily_dict.keys())
        daily_values = [daily_dict.get(d, 0.0) for d in all_days]

        try:
            forecast = moving_average_forecast(daily_values, window=7)
        except ValueError:
            continue

        forecast_row = {
            "store_id": store_id,
            "product_id": product_id,
            "forecast_date": today.isoformat(),
            "horizon_days": 7,
            "forecast_units": forecast["forecast_units"],
            "lower_bound": max(0.0, forecast["forecast_units"] * 0.7),
            "upper_bound": forecast["forecast_units"] * 1.3,
            "model_name": "moving_average_baseline",
            "model_version": "1.0",
            "metrics": {"observations_used": forecast["observations_used"], "mae": None},
        }
        try:
            db.table("demand_forecasts").upsert(
                [forecast_row],
                on_conflict="store_id,product_id,forecast_date,horizon_days,model_name",
            ).execute()
            forecasts_written += 1
        except Exception:
            pass

    # Log freshness ai_run
    try:
        db.table("ai_runs").insert([{
            "run_type": "freshness",
            "store_id": store_id,
            "input_summary": {"batches_analyzed": len(batch_risks)},
            "output_summary": {"high_risk": sum(1 for b in batch_risks if b["risk_percent"] >= 50)},
            "status": "completed",
            "started_at": _now_utc_iso(),
            "completed_at": _now_utc_iso(),
        }]).execute()
    except Exception:
        pass

    # Log demand ai_run
    try:
        db.table("ai_runs").insert([{
            "run_type": "demand",
            "store_id": store_id,
            "input_summary": {"products_evaluated": len(product_daily)},
            "output_summary": {"forecasts_written": forecasts_written},
            "status": "completed",
            "started_at": _now_utc_iso(),
            "completed_at": _now_utc_iso(),
        }]).execute()
    except Exception:
        pass

    # Generate recommendations for high-risk batches
    recs_written = 0
    for batch in batch_risks:
        if batch["risk_percent"] < 50:
            continue

        batch_id = batch["batch_id"]
        product_id = batch["product_id"]
        action = "markdown"

        # Check for existing active/proposed recommendation
        try:
            existing = (
                db.table("recommendations")
                .select("id")
                .eq("store_id", store_id)
                .eq("batch_id", batch_id)
                .eq("action", action)
                .in_("status", ["proposed", "approved"])
                .execute()
            )
            if existing.data:
                continue
        except Exception:
            pass

        rationale = (
            f"{batch['product_name']} batch {batch['batch_code']} has "
            f"{batch['risk_percent']}% at-risk units ({batch['at_risk_units']} of "
            f"{batch['quantity_on_hand']}). Expires in {batch['days_to_expiry']} day(s). "
            f"Forecast demand before expiry: {batch['forecast_demand_before_expiry']} units."
        )
        rec_row = {
            "store_id": store_id,
            "product_id": product_id,
            "batch_id": batch_id,
            "action": action,
            "status": "proposed",
            "confidence": 0.6,
            "confidence_type": "heuristic",
            "rationale": rationale,
            "evidence": [{"batch_id": batch_id, "risk_percent": batch["risk_percent"]}],
            "created_by_agent": "intelligence_service/recalculate",
        }
        try:
            db.table("recommendations").insert([rec_row]).execute()
            recs_written += 1
        except Exception:
            pass

        # Extra donate recommendation for extremely high risk
        if batch["risk_percent"] >= 100 and batch["days_to_expiry"] <= 1:
            donate_row = {**rec_row, "action": "donate", "rationale": rationale + " Consider donation."}
            try:
                db.table("recommendations").insert([donate_row]).execute()
                recs_written += 1
            except Exception:
                pass

    return {
        "batches_analyzed": len(batch_risks),
        "forecasts_written": forecasts_written,
        "recommendations_written": recs_written,
    }
