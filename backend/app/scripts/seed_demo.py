"""
Idempotent demo data seeder for Zero-Waste Grocery.

Run command:
    cd backend
    .venv/Scripts/python.exe app/scripts/seed_demo.py

Seeds one demo store, 8 products (4 scenarios), inventory batches,
sales records, and 1 promotion. All records are labelled with [DEMO].
Safe to re-run: uses upsert on natural keys; never overwrites real records.
"""

import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Allow running from the backend directory directly
# parents[0]=scripts, parents[1]=app, parents[2]=backend, parents[3]=project root
BACKEND_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

load_dotenv(BACKEND_DIR / ".env")

from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    sys.exit("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in backend/.env")

db = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

today = date.today()
now_utc = datetime.now(timezone.utc)


def utc_iso(dt: datetime) -> str:
    return dt.isoformat()


def date_iso(d: date) -> str:
    return d.isoformat()


# ---------------------------------------------------------------------------
# 1. Upsert demo store
# ---------------------------------------------------------------------------
store_row = {
    "code": "DEMO-STORE-001",
    "name": "[DEMO] Freshwise Central",
    "address": "1 Demo Lane, Bengaluru 560001",
    "timezone": "Asia/Kolkata",
    "is_active": True,
}
resp = db.table("stores").upsert(store_row, on_conflict="code").execute()
store = resp.data[0]
store_id = store["id"]
print(f"✓ Store upserted  id={store_id}")

# ---------------------------------------------------------------------------
# 2. Upsert 8 demo products
# ---------------------------------------------------------------------------
products_data = [
    # (sku, name, category, shelf_life, selling_price, unit_cost, is_perishable, scenario)
    ("DEMO-MILK-1L",    "[DEMO] Whole Milk 1L",          "dairy",   7,   68.00, 48.00, True,  "expiring_soon"),
    ("DEMO-STRAW-250",  "[DEMO] Strawberries 250g",      "produce", 4,   89.00, 55.00, True,  "expiring_soon"),
    ("DEMO-YOGURT-500", "[DEMO] Greek Yogurt 500g",      "dairy",  14,   95.00, 62.00, True,  "excess_inventory"),
    ("DEMO-BREAD-WW",   "[DEMO] Whole Wheat Bread",      "bakery",  5,   48.00, 28.00, True,  "excess_inventory"),
    ("DEMO-SPINACH-200","[DEMO] Baby Spinach 200g",      "produce", 5,   55.00, 32.00, True,  "stockout_risk"),
    ("DEMO-EGG-12",     "[DEMO] Free Range Eggs 12pk",  "dairy",  21,  120.00, 82.00, True,  "stockout_risk"),
    ("DEMO-OATS-500",   "[DEMO] Rolled Oats 500g",       "grains", 365,  78.00, 45.00, False, "healthy"),
    ("DEMO-PASTA-500",  "[DEMO] Whole Grain Pasta 500g", "grains", 730,  62.00, 38.00, False, "healthy"),
]

product_rows = [
    {
        "sku": sku,
        "name": name,
        "category": category,
        "unit": "each",
        "default_shelf_life_days": shelf_life,
        "selling_price": selling_price,
        "unit_cost": unit_cost,
        "is_perishable": is_perishable,
        "is_active": True,
    }
    for sku, name, category, shelf_life, selling_price, unit_cost, is_perishable, _ in products_data
]

resp = db.table("products").upsert(product_rows, on_conflict="sku").execute()
print(f"✓ {len(resp.data)} products upserted")

# Build sku → id lookup
product_lookup: dict[str, str] = {}
for p in resp.data:
    product_lookup[p["sku"]] = p["id"]

# Fetch any that already existed (upsert returns all touched rows; but on conflict=update
# it should return them — verify we have all 8).
if len(product_lookup) < 8:
    existing = db.table("products").select("id,sku").in_("sku", [r["sku"] for r in product_rows]).execute()
    for p in existing.data:
        product_lookup[p["sku"]] = p["id"]

# ---------------------------------------------------------------------------
# 3. Upsert inventory batches
# ---------------------------------------------------------------------------
batch_configs = [
    # (sku, batch_code, days_ago_received, days_to_expiry, qty_received, qty_on_hand)
    ("DEMO-MILK-1L",     "DEMO-B-MILK-01",  6,  1, 20, 20),
    ("DEMO-STRAW-250",   "DEMO-B-STRAW-01", 2,  2, 14, 14),
    ("DEMO-YOGURT-500",  "DEMO-B-YOURT-01", 3, 10, 80, 75),
    ("DEMO-BREAD-WW",    "DEMO-B-BREAD-01", 1,  4, 60, 58),
    ("DEMO-SPINACH-200", "DEMO-B-SPIN-01",  4,  1, 12,  3),
    ("DEMO-EGG-12",      "DEMO-B-EGG-01",   5, 14, 24,  4),
    ("DEMO-OATS-500",    "DEMO-B-OATS-01", 10,355, 40, 38),
    ("DEMO-PASTA-500",   "DEMO-B-PASTA-01",10,720, 35, 33),
]

batch_rows = []
for sku, batch_code, days_ago, days_to_exp, qty_recv, qty_oh in batch_configs:
    product_id = product_lookup.get(sku)
    if not product_id:
        print(f"  WARNING: product not found for sku={sku}, skipping batch")
        continue
    received_at = now_utc - timedelta(days=days_ago)
    expiry_date = today + timedelta(days=days_to_exp)
    batch_rows.append({
        "store_id": store_id,
        "product_id": product_id,
        "batch_code": batch_code,
        "received_at": utc_iso(received_at),
        "expiry_date": date_iso(expiry_date),
        "quantity_received": qty_recv,
        "quantity_on_hand": qty_oh,
        "source_receipt_ref": "DEMO",
    })

resp = db.table("inventory_batches").upsert(
    batch_rows, on_conflict="store_id,product_id,batch_code"
).execute()
print(f"✓ {len(resp.data)} inventory batches upserted")

# Build batch_code → id lookup
batch_lookup: dict[str, str] = {}
for b in resp.data:
    batch_lookup[b["batch_code"]] = b["id"]

if len(batch_lookup) < 8:
    codes = [r["batch_code"] for r in batch_rows]
    existing = db.table("inventory_batches").select("id,batch_code").in_("batch_code", codes).execute()
    for b in existing.data:
        batch_lookup[b["batch_code"]] = b["id"]

# ---------------------------------------------------------------------------
# 4. Sales records (7 days, skip if demo sales already exist)
# ---------------------------------------------------------------------------
existing_sales = (
    db.table("sales_records")
    .select("id", count="exact")
    .eq("store_id", store_id)
    .eq("source_ref", "DEMO")
    .execute()
)
sales_count = existing_sales.count if existing_sales.count is not None else len(existing_sales.data)

if sales_count > 0:
    print(f"✓ Sales records: skipped (already {sales_count} demo rows exist)")
else:
    # Sales pattern: (sku, units_per_day)
    sales_patterns = [
        ("DEMO-MILK-1L",     3),
        ("DEMO-STRAW-250",   2),
        ("DEMO-YOGURT-500",  1),
        ("DEMO-BREAD-WW",    2),
        ("DEMO-SPINACH-200", 3),
        ("DEMO-EGG-12",      4),
        ("DEMO-OATS-500",    1),
        ("DEMO-PASTA-500",   1),
    ]

    batch_code_for_sku = {
        "DEMO-MILK-1L":     "DEMO-B-MILK-01",
        "DEMO-STRAW-250":   "DEMO-B-STRAW-01",
        "DEMO-YOGURT-500":  "DEMO-B-YOURT-01",
        "DEMO-BREAD-WW":    "DEMO-B-BREAD-01",
        "DEMO-SPINACH-200": "DEMO-B-SPIN-01",
        "DEMO-EGG-12":      "DEMO-B-EGG-01",
        "DEMO-OATS-500":    "DEMO-B-OATS-01",
        "DEMO-PASTA-500":   "DEMO-B-PASTA-01",
    }

    # Selling prices from products_data
    price_for_sku = {r[0]: r[4] for r in products_data}

    sales_rows = []
    for day_offset in range(7):
        sale_day = now_utc - timedelta(days=day_offset)
        for sku, units in sales_patterns:
            product_id = product_lookup.get(sku)
            if not product_id:
                continue
            batch_code = batch_code_for_sku.get(sku)
            batch_id = batch_lookup.get(batch_code) if batch_code else None
            sales_rows.append({
                "store_id": store_id,
                "product_id": product_id,
                "batch_id": batch_id,
                "sold_at": utc_iso(sale_day.replace(hour=10, minute=0, second=0)),
                "quantity": units,
                "unit_price": price_for_sku[sku],
                "source_ref": "DEMO",
            })

    resp = db.table("sales_records").insert(sales_rows).execute()
    print(f"✓ {len(resp.data)} sales records inserted")

# ---------------------------------------------------------------------------
# 5. Promotion — Milk Markdown
# ---------------------------------------------------------------------------
milk_product_id = product_lookup.get("DEMO-MILK-1L")
if milk_product_id:
    milk_expiry = today + timedelta(days=1)
    promo_name = "[DEMO] Milk Markdown — Expiry Alert"

    existing_promo = (
        db.table("promotions")
        .select("id")
        .eq("store_id", store_id)
        .eq("product_id", milk_product_id)
        .eq("name", promo_name)
        .execute()
    )

    if existing_promo.data:
        print(f"✓ Promotion: skipped (already exists)")
    else:
        promo_row = {
            "store_id": store_id,
            "product_id": milk_product_id,
            "name": promo_name,
            "discount_percent": 15.00,
            "starts_at": utc_iso(now_utc),
            "ends_at": utc_iso(
                datetime(milk_expiry.year, milk_expiry.month, milk_expiry.day,
                         23, 59, 59, tzinfo=timezone.utc)
            ),
            "status": "approved",
        }
        resp = db.table("promotions").insert([promo_row]).execute()
        print(f"✓ Promotion upserted  id={resp.data[0]['id']}")
else:
    print("  WARNING: DEMO-MILK-1L product not found, skipping promotion")

print("\n✓ Demo seeding complete.")
print(f"  Store ID  : {store_id}")
print(f"  Store code: DEMO-STORE-001")
print("  Set VITE_DEMO_STORE_ID in frontend/.env to this store ID to see live data.")
