"""
CSV ingestion service: parse, validate, and upsert rows into Supabase.

[DEV/DEMO ONLY] — No store-level authentication is enforced. Do not use
in production without adding proper auth.
"""

from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Result schema
# ---------------------------------------------------------------------------

class ImportError(BaseModel):
    row: int
    field: str
    message: str


class ImportResult(BaseModel):
    accepted: int = 0
    rejected: int = 0
    duplicates: int = 0
    errors: list[ImportError] = []
    import_id: str = ""


# ---------------------------------------------------------------------------
# Column definitions
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS: dict[str, list[str]] = {
    "products":   ["sku", "name", "category", "selling_price", "unit_cost"],
    "inventory":  ["sku", "batch_code", "received_at", "expiry_date",
                   "quantity_received", "quantity_on_hand"],
    "sales":      ["sku", "sold_at", "quantity", "unit_price"],
    "promotions": ["sku", "name", "discount_percent", "starts_at", "ends_at"],
}

VALID_PROMO_STATUSES = {
    "draft", "pending_approval", "approved", "active", "paused",
    "completed", "cancelled",
}

VALID_RUN_TYPES = {
    "demand", "freshness", "replenishment", "markdown", "transfer",
    "orchestration", "copilot", "bundle", "campaign", "donation",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date(value: str) -> datetime | None:
    """Try ISO 8601 datetime or YYYY-MM-DD. Returns None on failure."""
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value).strip(), fmt)
        except ValueError:
            continue
    # Try pandas parsing as a last resort
    try:
        ts = pd.Timestamp(value)
        if pd.isna(ts):
            return None
        return ts.to_pydatetime()
    except Exception:
        return None


def _parse_bool(value: str) -> bool | None:
    v = str(value).strip().lower()
    if v in ("true", "1", "yes"):
        return True
    if v in ("false", "0", "no"):
        return False
    return None


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# CSV parsing & column validation
# ---------------------------------------------------------------------------

def parse_and_validate_csv(
    file_bytes: bytes,
    dataset_type: str,
) -> tuple[list[dict], list[ImportError]]:
    """
    Parse file_bytes as CSV and check that required columns are present.

    Returns (valid_rows, errors).  Errors from this function are
    file-level (missing columns, empty file) rather than row-level.
    Individual row errors are collected by the upsert functions.
    """
    if dataset_type not in REQUIRED_COLUMNS:
        return [], [ImportError(row=0, field="dataset_type",
                                message=f"Unknown dataset type: {dataset_type}")]

    try:
        df = pd.read_csv(io.BytesIO(file_bytes), dtype=str, keep_default_na=False)
    except Exception as exc:
        return [], [ImportError(row=0, field="file",
                                message=f"Could not parse CSV: {exc}")]

    if df.empty:
        return [], [ImportError(row=0, field="file",
                                message="CSV file contains no data rows.")]

    required = REQUIRED_COLUMNS[dataset_type]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return [], [ImportError(row=0, field=", ".join(missing),
                                message=f"Missing required column(s): {', '.join(missing)}")]

    return df.to_dict(orient="records"), []


# ---------------------------------------------------------------------------
# ai_runs logging helpers
# ---------------------------------------------------------------------------

def _start_import_run(db: Any, run_type: str, dataset_type: str) -> str:
    """Insert an ai_runs row with status=running; return its id."""
    row = {
        "run_type": run_type,
        "input_summary": {"dataset": dataset_type},
        "output_summary": {},
        "status": "running",
        "started_at": _now_utc_iso(),
    }
    try:
        resp = db.table("ai_runs").insert([row]).execute()
        return resp.data[0]["id"] if resp.data else str(uuid.uuid4())
    except Exception:
        return str(uuid.uuid4())


def _finish_import_run(
    db: Any,
    run_id: str,
    accepted: int,
    rejected: int,
    status: str = "completed",
    error_message: str | None = None,
) -> None:
    update = {
        "status": status,
        "output_summary": {"accepted": accepted, "rejected": rejected},
        "completed_at": _now_utc_iso(),
    }
    if error_message:
        update["error_message"] = error_message
    try:
        db.table("ai_runs").update(update).eq("id", run_id).execute()
    except Exception:
        pass  # logging failure must not fail the import


def log_import_run(
    db: Any,
    run_type: str,
    input_summary: dict,
    output_summary: dict,
    status: str,
) -> str:
    """Public helper for callers that want a single-call log."""
    actual_run_type = run_type if run_type in VALID_RUN_TYPES else "orchestration"
    row = {
        "run_type": actual_run_type,
        "input_summary": input_summary,
        "output_summary": output_summary,
        "status": status,
        "started_at": _now_utc_iso(),
        "completed_at": _now_utc_iso(),
    }
    try:
        resp = db.table("ai_runs").insert([row]).execute()
        return resp.data[0]["id"] if resp.data else str(uuid.uuid4())
    except Exception:
        return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Store and product ID resolution helpers
# ---------------------------------------------------------------------------

def _resolve_store_id(db: Any, store_code: str) -> str | None:
    try:
        resp = db.table("stores").select("id").eq("code", store_code).execute()
        return resp.data[0]["id"] if resp.data else None
    except Exception:
        return None


def _resolve_product_ids(db: Any, skus: list[str]) -> dict[str, str]:
    """Return {sku: product_id} for all found SKUs."""
    if not skus:
        return {}
    try:
        resp = db.table("products").select("id,sku").in_("sku", list(set(skus))).execute()
        return {r["sku"]: r["id"] for r in resp.data}
    except Exception:
        return {}


def _resolve_batch_ids(
    db: Any, store_id: str, product_ids: list[str], batch_codes: list[str]
) -> dict[str, str]:
    """Return {batch_code: batch_id}."""
    if not batch_codes:
        return {}
    try:
        resp = (
            db.table("inventory_batches")
            .select("id,batch_code")
            .eq("store_id", store_id)
            .in_("product_id", list(set(product_ids)))
            .in_("batch_code", list(set(batch_codes)))
            .execute()
        )
        return {r["batch_code"]: r["id"] for r in resp.data}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Products upsert
# ---------------------------------------------------------------------------

def upsert_products(rows: list[dict], db: Any) -> ImportResult:
    run_id = _start_import_run(db, "orchestration", "products")
    result = ImportResult(import_id=run_id)

    valid_rows: list[dict] = []
    for i, row in enumerate(rows, start=2):
        errors: list[str] = []

        sku = str(row.get("sku", "")).strip()
        name = str(row.get("name", "")).strip()
        category = str(row.get("category", "")).strip()

        if not sku:
            errors.append(("sku", "sku is required"))
        if not name:
            errors.append(("name", "name is required"))
        if not category:
            errors.append(("category", "category is required"))

        selling_price = row.get("selling_price", "")
        unit_cost = row.get("unit_cost", "")
        try:
            sp = float(selling_price)
            if sp < 0:
                raise ValueError
        except (ValueError, TypeError):
            errors.append(("selling_price",
                           f"selling_price must be a non-negative number, got '{selling_price}'"))
            sp = None

        try:
            uc = float(unit_cost)
            if uc < 0:
                raise ValueError
        except (ValueError, TypeError):
            errors.append(("unit_cost",
                           f"unit_cost must be a non-negative number, got '{unit_cost}'"))
            uc = None

        shelf_days = row.get("default_shelf_life_days", "")
        shelf_days_val = None
        if shelf_days:
            try:
                shelf_days_val = int(shelf_days)
                if shelf_days_val <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                errors.append(("default_shelf_life_days",
                               f"default_shelf_life_days must be a positive integer, got '{shelf_days}'"))

        is_perishable = row.get("is_perishable", "")
        is_perishable_val = None
        if is_perishable:
            parsed = _parse_bool(is_perishable)
            if parsed is None:
                errors.append(("is_perishable",
                               f"is_perishable must be true/false/1/0, got '{is_perishable}'"))
            else:
                is_perishable_val = parsed

        if errors:
            for field, msg in errors:
                result.errors.append(ImportError(row=i, field=field, message=msg))
            result.rejected += 1
            continue

        db_row: dict = {
            "sku": sku,
            "name": name,
            "category": category,
            "selling_price": sp,
            "unit_cost": uc,
            "is_active": True,
        }
        if row.get("unit"):
            db_row["unit"] = str(row["unit"]).strip()
        if row.get("barcode"):
            db_row["barcode"] = str(row["barcode"]).strip()
        if shelf_days_val is not None:
            db_row["default_shelf_life_days"] = shelf_days_val
        if is_perishable_val is not None:
            db_row["is_perishable"] = is_perishable_val
        if row.get("min_margin_percent"):
            try:
                db_row["min_margin_percent"] = float(row["min_margin_percent"])
            except (ValueError, TypeError):
                pass

        valid_rows.append(db_row)

    if valid_rows:
        try:
            resp = db.table("products").upsert(valid_rows, on_conflict="sku").execute()
            result.accepted = len(resp.data)
        except Exception as exc:
            result.errors.append(ImportError(row=0, field="db", message=f"Database error: {exc}"))
            result.rejected += len(valid_rows)
            _finish_import_run(db, run_id, result.accepted, result.rejected, "failed", str(exc))
            return result

    _finish_import_run(db, run_id, result.accepted, result.rejected)
    return result


# ---------------------------------------------------------------------------
# Inventory upsert
# ---------------------------------------------------------------------------

def upsert_inventory(rows: list[dict], db: Any, store_id: str) -> ImportResult:
    run_id = _start_import_run(db, "orchestration", "inventory")
    result = ImportResult(import_id=run_id)

    skus = [str(r.get("sku", "")).strip() for r in rows]
    product_map = _resolve_product_ids(db, skus)

    valid_rows: list[dict] = []
    for i, row in enumerate(rows, start=2):
        errors: list[str] = []

        sku = str(row.get("sku", "")).strip()
        batch_code = str(row.get("batch_code", "")).strip()
        received_at_raw = str(row.get("received_at", "")).strip()
        expiry_date_raw = str(row.get("expiry_date", "")).strip()
        qty_recv_raw = str(row.get("quantity_received", "")).strip()
        qty_oh_raw = str(row.get("quantity_on_hand", "")).strip()

        product_id = product_map.get(sku)
        if not sku:
            errors.append(("sku", "sku is required"))
        elif product_id is None:
            errors.append(("sku", f"sku '{sku}' not found in products table"))

        if not batch_code:
            errors.append(("batch_code", "batch_code is required"))

        received_dt = _parse_date(received_at_raw) if received_at_raw else None
        if not received_at_raw:
            errors.append(("received_at", "received_at is required"))
        elif received_dt is None:
            errors.append(("received_at",
                           f"received_at must be ISO 8601 date or datetime, got '{received_at_raw}'"))

        expiry_dt = _parse_date(expiry_date_raw) if expiry_date_raw else None
        if not expiry_date_raw:
            errors.append(("expiry_date", "expiry_date is required"))
        elif expiry_dt is None:
            errors.append(("expiry_date",
                           f"expiry_date must be YYYY-MM-DD, got '{expiry_date_raw}'"))

        if received_dt and expiry_dt:
            if expiry_dt.date() < received_dt.date():
                errors.append(("expiry_date",
                               "expiry_date must be on or after received_at date"))

        qty_recv = None
        try:
            qty_recv = int(qty_recv_raw)
            if qty_recv < 0:
                raise ValueError
        except (ValueError, TypeError):
            errors.append(("quantity_received",
                           f"quantity_received must be a non-negative integer, got '{qty_recv_raw}'"))

        qty_oh = None
        try:
            qty_oh = int(qty_oh_raw)
            if qty_oh < 0:
                raise ValueError
        except (ValueError, TypeError):
            errors.append(("quantity_on_hand",
                           f"quantity_on_hand must be a non-negative integer, got '{qty_oh_raw}'"))

        if qty_recv is not None and qty_oh is not None and qty_oh > qty_recv:
            errors.append(("quantity_on_hand",
                           f"quantity_on_hand ({qty_oh}) cannot exceed quantity_received ({qty_recv})"))

        if errors:
            for field, msg in errors:
                result.errors.append(ImportError(row=i, field=field, message=msg))
            result.rejected += 1
            continue

        db_row: dict = {
            "store_id": store_id,
            "product_id": product_id,
            "batch_code": batch_code,
            "received_at": received_dt.isoformat(),
            "expiry_date": expiry_dt.strftime("%Y-%m-%d"),
            "quantity_received": qty_recv,
            "quantity_on_hand": qty_oh,
        }
        if row.get("source_receipt_ref"):
            db_row["source_receipt_ref"] = str(row["source_receipt_ref"]).strip()

        valid_rows.append(db_row)

    if valid_rows:
        try:
            resp = db.table("inventory_batches").upsert(
                valid_rows, on_conflict="store_id,product_id,batch_code"
            ).execute()
            result.accepted = len(resp.data)
        except Exception as exc:
            result.errors.append(ImportError(row=0, field="db", message=f"Database error: {exc}"))
            result.rejected += len(valid_rows)
            _finish_import_run(db, run_id, result.accepted, result.rejected, "failed", str(exc))
            return result

    _finish_import_run(db, run_id, result.accepted, result.rejected)
    return result


# ---------------------------------------------------------------------------
# Sales upsert
# ---------------------------------------------------------------------------

def upsert_sales(rows: list[dict], db: Any, store_id: str) -> ImportResult:
    run_id = _start_import_run(db, "orchestration", "sales")
    result = ImportResult(import_id=run_id)

    skus = [str(r.get("sku", "")).strip() for r in rows]
    product_map = _resolve_product_ids(db, skus)

    batch_codes = [str(r.get("batch_code", "")).strip() for r in rows if r.get("batch_code")]
    product_ids_list = list(product_map.values())
    batch_map = _resolve_batch_ids(db, store_id, product_ids_list, batch_codes)

    valid_rows: list[dict] = []
    for i, row in enumerate(rows, start=2):
        errors: list[str] = []

        sku = str(row.get("sku", "")).strip()
        sold_at_raw = str(row.get("sold_at", "")).strip()
        qty_raw = str(row.get("quantity", "")).strip()
        price_raw = str(row.get("unit_price", "")).strip()
        source_ref = str(row.get("source_ref", "")).strip() or None
        batch_code = str(row.get("batch_code", "")).strip() or None

        product_id = product_map.get(sku)
        if not sku:
            errors.append(("sku", "sku is required"))
        elif product_id is None:
            errors.append(("sku", f"sku '{sku}' not found in products table"))

        sold_dt = _parse_date(sold_at_raw) if sold_at_raw else None
        if not sold_at_raw:
            errors.append(("sold_at", "sold_at is required"))
        elif sold_dt is None:
            errors.append(("sold_at",
                           f"sold_at must be ISO 8601 datetime, got '{sold_at_raw}'"))

        qty = None
        try:
            qty = int(qty_raw)
            if qty <= 0:
                raise ValueError
        except (ValueError, TypeError):
            errors.append(("quantity",
                           f"quantity must be a positive integer, got '{qty_raw}'"))

        price = None
        try:
            price = float(price_raw)
            if price < 0:
                raise ValueError
        except (ValueError, TypeError):
            errors.append(("unit_price",
                           f"unit_price must be a non-negative number, got '{price_raw}'"))

        if errors:
            for field, msg in errors:
                result.errors.append(ImportError(row=i, field=field, message=msg))
            result.rejected += 1
            continue

        # Idempotency check: skip if same (store_id, product_id, sold_at, source_ref) exists
        if source_ref and product_id and sold_dt:
            try:
                existing = (
                    db.table("sales_records")
                    .select("id")
                    .eq("store_id", store_id)
                    .eq("product_id", product_id)
                    .eq("sold_at", sold_dt.isoformat())
                    .eq("source_ref", source_ref)
                    .execute()
                )
                if existing.data:
                    result.duplicates += 1
                    continue
            except Exception:
                pass  # If check fails, proceed with insert

        batch_id = batch_map.get(batch_code) if batch_code else None

        db_row: dict = {
            "store_id": store_id,
            "product_id": product_id,
            "sold_at": sold_dt.isoformat(),
            "quantity": qty,
            "unit_price": price,
        }
        if source_ref:
            db_row["source_ref"] = source_ref
        if batch_id:
            db_row["batch_id"] = batch_id

        valid_rows.append(db_row)

    if valid_rows:
        try:
            resp = db.table("sales_records").insert(valid_rows).execute()
            result.accepted = len(resp.data)
        except Exception as exc:
            result.errors.append(ImportError(row=0, field="db", message=f"Database error: {exc}"))
            result.rejected += len(valid_rows)
            _finish_import_run(db, run_id, result.accepted, result.rejected, "failed", str(exc))
            return result

    _finish_import_run(db, run_id, result.accepted, result.rejected)
    return result


# ---------------------------------------------------------------------------
# Promotions upsert
# ---------------------------------------------------------------------------

def upsert_promotions(rows: list[dict], db: Any, store_id: str) -> ImportResult:
    run_id = _start_import_run(db, "orchestration", "promotions")
    result = ImportResult(import_id=run_id)

    skus = [str(r.get("sku", "")).strip() for r in rows]
    product_map = _resolve_product_ids(db, skus)

    valid_rows: list[dict] = []
    for i, row in enumerate(rows, start=2):
        errors: list[str] = []

        sku = str(row.get("sku", "")).strip()
        name = str(row.get("name", "")).strip()
        discount_raw = str(row.get("discount_percent", "")).strip()
        starts_raw = str(row.get("starts_at", "")).strip()
        ends_raw = str(row.get("ends_at", "")).strip()
        status = str(row.get("status", "draft")).strip().lower()

        product_id = product_map.get(sku)
        if not sku:
            errors.append(("sku", "sku is required"))
        elif product_id is None:
            errors.append(("sku", f"sku '{sku}' not found in products table"))

        if not name:
            errors.append(("name", "name is required"))

        discount = None
        try:
            discount = float(discount_raw)
            if not (0 <= discount <= 100):
                raise ValueError
        except (ValueError, TypeError):
            errors.append(("discount_percent",
                           f"discount_percent must be between 0 and 100, got '{discount_raw}'"))

        starts_dt = _parse_date(starts_raw) if starts_raw else None
        if not starts_raw:
            errors.append(("starts_at", "starts_at is required"))
        elif starts_dt is None:
            errors.append(("starts_at",
                           f"starts_at must be ISO 8601 datetime, got '{starts_raw}'"))

        ends_dt = _parse_date(ends_raw) if ends_raw else None
        if not ends_raw:
            errors.append(("ends_at", "ends_at is required"))
        elif ends_dt is None:
            errors.append(("ends_at",
                           f"ends_at must be ISO 8601 datetime, got '{ends_raw}'"))

        if starts_dt and ends_dt and ends_dt <= starts_dt:
            errors.append(("ends_at", "ends_at must be after starts_at"))

        if status not in VALID_PROMO_STATUSES:
            errors.append(("status",
                           f"status must be one of {sorted(VALID_PROMO_STATUSES)}, got '{status}'"))

        if errors:
            for field, msg in errors:
                result.errors.append(ImportError(row=i, field=field, message=msg))
            result.rejected += 1
            continue

        # Idempotency: skip if (store_id, product_id, name) already exists
        if product_id and name:
            try:
                existing = (
                    db.table("promotions")
                    .select("id")
                    .eq("store_id", store_id)
                    .eq("product_id", product_id)
                    .eq("name", name)
                    .execute()
                )
                if existing.data:
                    result.duplicates += 1
                    continue
            except Exception:
                pass

        db_row: dict = {
            "store_id": store_id,
            "product_id": product_id,
            "name": name,
            "discount_percent": discount,
            "starts_at": starts_dt.isoformat(),
            "ends_at": ends_dt.isoformat(),
            "status": status,
        }
        valid_rows.append(db_row)

    if valid_rows:
        try:
            resp = db.table("promotions").insert(valid_rows).execute()
            result.accepted = len(resp.data)
        except Exception as exc:
            result.errors.append(ImportError(row=0, field="db", message=f"Database error: {exc}"))
            result.rejected += len(valid_rows)
            _finish_import_run(db, run_id, result.accepted, result.rejected, "failed", str(exc))
            return result

    _finish_import_run(db, run_id, result.accepted, result.rejected)
    return result
