"""
Unified Demo Data Store for Freshwise Telegram Bot.

Provides multi-store coordinates, geographic distance calculations,
food rescue deals, donation partner routing, inventory batches, and
persistent in-memory reservation management.
"""

from __future__ import annotations

import logging
import math
import random
from datetime import date, datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger("freshwise.telegram.demo_store")


# ---------------------------------------------------------------------------
# Geographic Distance (Haversine Formula)
# ---------------------------------------------------------------------------

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in km."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


# Locality & PIN Code Geocoding Directory (Demo Bengaluru)
LOCALITY_COORDINATES = {
    "560001": (12.9716, 77.5946, "Central Bengaluru"),
    "central": (12.9716, 77.5946, "Central Bengaluru"),
    "mg road": (12.9756, 77.6066, "MG Road"),
    "cbd": (12.9716, 77.5946, "Central Business District"),
    "560038": (12.9784, 77.6408, "Indiranagar"),
    "indiranagar": (12.9784, 77.6408, "Indiranagar"),
    "domlur": (12.9609, 77.6387, "Domlur"),
    "560034": (12.9352, 77.6245, "Koramangala"),
    "koramangala": (12.9352, 77.6245, "Koramangala"),
    "hsr": (12.9121, 77.6446, "HSR Layout"),
    "560066": (12.9698, 77.7499, "Whitefield"),
    "whitefield": (12.9698, 77.7499, "Whitefield"),
    "itpl": (12.9863, 77.7381, "ITPL / Whitefield"),
}


def geocode_locality(query: str) -> tuple[float, float, str] | None:
    """Resolve a PIN code or locality name to latitude and longitude."""
    cleaned = query.strip().lower()
    for key, (lat, lon, name) in LOCALITY_COORDINATES.items():
        if key in cleaned or cleaned in key:
            return lat, lon, name
    return None


# ---------------------------------------------------------------------------
# Multi-Store Demo Fixtures
# ---------------------------------------------------------------------------

DEMO_STORES = [
    {
        "id": "27934f1c-f6cb-4731-a419-570b18e39f0a",
        "code": "DEMO-STORE-001",
        "name": "[DEMO] Freshwise Central",
        "address": "1 Demo Lane, MG Road, Bengaluru 560001",
        "locality": "Central Bengaluru",
        "pincode": "560001",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "timezone": "Asia/Kolkata",
        "pickup_hours": "08:00 AM – 09:30 PM",
        "contact_phone": "+91 80 2558 0001",
        "is_active": True,
    },
    {
        "id": "store-demo-002",
        "code": "DEMO-STORE-002",
        "name": "[DEMO] Freshwise Indiranagar",
        "address": "100 Feet Road, HAL 2nd Stage, Indiranagar, Bengaluru 560038",
        "locality": "Indiranagar",
        "pincode": "560038",
        "latitude": 12.9784,
        "longitude": 77.6408,
        "timezone": "Asia/Kolkata",
        "pickup_hours": "08:30 AM – 10:00 PM",
        "contact_phone": "+91 80 2520 0002",
        "is_active": True,
    },
    {
        "id": "store-demo-003",
        "code": "DEMO-STORE-003",
        "name": "[DEMO] Freshwise Koramangala",
        "address": "80 Feet Road, 4th Block, Koramangala, Bengaluru 560034",
        "locality": "Koramangala",
        "pincode": "560034",
        "latitude": 12.9352,
        "longitude": 77.6245,
        "timezone": "Asia/Kolkata",
        "pickup_hours": "09:00 AM – 09:30 PM",
        "contact_phone": "+91 80 2553 0003",
        "is_active": True,
    },
    {
        "id": "store-demo-004",
        "code": "DEMO-STORE-004",
        "name": "[DEMO] Freshwise Whitefield",
        "address": "ITPL Main Road, Whitefield, Bengaluru 560066",
        "locality": "Whitefield",
        "pincode": "560066",
        "latitude": 12.9698,
        "longitude": 77.7499,
        "timezone": "Asia/Kolkata",
        "pickup_hours": "08:00 AM – 10:00 PM",
        "contact_phone": "+91 80 2841 0004",
        "is_active": True,
    },
]

DEMO_STORE = DEMO_STORES[0]  # Default store


# ---------------------------------------------------------------------------
# Products Catalogue
# ---------------------------------------------------------------------------

DEMO_PRODUCTS = {
    "DEMO-MILK-1L": {
        "id": "p-milk-01",
        "sku": "DEMO-MILK-1L",
        "name": "[DEMO] Whole Milk 1L",
        "category": "dairy",
        "unit": "each",
        "selling_price": 68.00,
        "unit_cost": 48.00,
        "is_perishable": True,
    },
    "DEMO-STRAW-250": {
        "id": "p-straw-01",
        "sku": "DEMO-STRAW-250",
        "name": "[DEMO] Strawberries 250g",
        "category": "produce",
        "unit": "each",
        "selling_price": 89.00,
        "unit_cost": 55.00,
        "is_perishable": True,
    },
    "DEMO-YOGURT-500": {
        "id": "p-yogurt-01",
        "sku": "DEMO-YOGURT-500",
        "name": "[DEMO] Greek Yogurt 500g",
        "category": "dairy",
        "unit": "each",
        "selling_price": 95.00,
        "unit_cost": 62.00,
        "is_perishable": True,
    },
    "DEMO-BREAD-WW": {
        "id": "p-bread-01",
        "sku": "DEMO-BREAD-WW",
        "name": "[DEMO] Whole Wheat Bread",
        "category": "bakery",
        "unit": "each",
        "selling_price": 48.00,
        "unit_cost": 28.00,
        "is_perishable": True,
    },
    "DEMO-SPINACH-200": {
        "id": "p-spinach-01",
        "sku": "DEMO-SPINACH-200",
        "name": "[DEMO] Baby Spinach 200g",
        "category": "produce",
        "unit": "each",
        "selling_price": 55.00,
        "unit_cost": 32.00,
        "is_perishable": True,
    },
    "DEMO-EGG-12": {
        "id": "p-egg-01",
        "sku": "DEMO-EGG-12",
        "name": "[DEMO] Free Range Eggs 12pk",
        "category": "dairy",
        "unit": "each",
        "selling_price": 120.00,
        "unit_cost": 82.00,
        "is_perishable": True,
    },
    "DEMO-OATS-500": {
        "id": "p-oats-01",
        "sku": "DEMO-OATS-500",
        "name": "[DEMO] Rolled Oats 500g",
        "category": "grains",
        "unit": "each",
        "selling_price": 78.00,
        "unit_cost": 45.00,
        "is_perishable": False,
    },
    "DEMO-PASTA-500": {
        "id": "p-pasta-01",
        "sku": "DEMO-PASTA-500",
        "name": "[DEMO] Whole Grain Pasta 500g",
        "category": "grains",
        "unit": "each",
        "selling_price": 62.00,
        "unit_cost": 38.00,
        "is_perishable": False,
    },
}


# ---------------------------------------------------------------------------
# Food Rescue Deals (Dynamic Deals Available for Customer Reservation)
# ---------------------------------------------------------------------------

_DEMO_RESCUE_DEALS = {
    "deal-milk-01": {
        "id": "deal-milk-01",
        "store_id": "27934f1c-f6cb-4731-a419-570b18e39f0a",
        "store_name": "[DEMO] Freshwise Central",
        "product_id": "p-milk-01",
        "product_name": "[DEMO] Whole Milk 1L",
        "sku": "DEMO-MILK-1L",
        "category": "dairy",
        "original_price": 68.00,
        "discount_percent": 25,
        "rescue_price": 51.00,
        "quantity_available": 14,
        "days_left": 1,
        "expiry_date": (date.today() + timedelta(days=1)).isoformat(),
        "pickup_window": "Today, 04:00 PM – 09:30 PM",
        "is_active": True,
    },
    "deal-straw-01": {
        "id": "deal-straw-01",
        "store_id": "27934f1c-f6cb-4731-a419-570b18e39f0a",
        "store_name": "[DEMO] Freshwise Central",
        "product_id": "p-straw-01",
        "product_name": "[DEMO] Strawberries 250g",
        "sku": "DEMO-STRAW-250",
        "category": "produce",
        "original_price": 89.00,
        "discount_percent": 20,
        "rescue_price": 71.20,
        "quantity_available": 10,
        "days_left": 2,
        "expiry_date": (date.today() + timedelta(days=2)).isoformat(),
        "pickup_window": "Today, 02:00 PM – 09:00 PM",
        "is_active": True,
    },
    "deal-bread-02": {
        "id": "deal-bread-02",
        "store_id": "store-demo-002",
        "store_name": "[DEMO] Freshwise Indiranagar",
        "product_id": "p-bread-01",
        "product_name": "[DEMO] Whole Wheat Bread",
        "sku": "DEMO-BREAD-WW",
        "category": "bakery",
        "original_price": 48.00,
        "discount_percent": 30,
        "rescue_price": 33.60,
        "quantity_available": 16,
        "days_left": 2,
        "expiry_date": (date.today() + timedelta(days=2)).isoformat(),
        "pickup_window": "Today, 03:00 PM – 10:00 PM",
        "is_active": True,
    },
    "deal-yogurt-03": {
        "id": "deal-yogurt-03",
        "store_id": "store-demo-003",
        "store_name": "[DEMO] Freshwise Koramangala",
        "product_id": "p-yogurt-01",
        "product_name": "[DEMO] Greek Yogurt 500g",
        "sku": "DEMO-YOGURT-500",
        "category": "dairy",
        "original_price": 95.00,
        "discount_percent": 30,
        "rescue_price": 66.50,
        "quantity_available": 20,
        "days_left": 3,
        "expiry_date": (date.today() + timedelta(days=3)).isoformat(),
        "pickup_window": "Today, 01:00 PM – 09:30 PM",
        "is_active": True,
    },
    "deal-spinach-04": {
        "id": "deal-spinach-04",
        "store_id": "store-demo-004",
        "store_name": "[DEMO] Freshwise Whitefield",
        "product_id": "p-spinach-01",
        "product_name": "[DEMO] Baby Spinach 200g",
        "sku": "DEMO-SPINACH-200",
        "category": "produce",
        "original_price": 55.00,
        "discount_percent": 40,
        "rescue_price": 33.00,
        "quantity_available": 8,
        "days_left": 1,
        "expiry_date": (date.today() + timedelta(days=1)).isoformat(),
        "pickup_window": "Today, 02:00 PM – 09:30 PM",
        "is_active": True,
    },
}


# ---------------------------------------------------------------------------
# NGO Food Donations Fixtures
# ---------------------------------------------------------------------------

DEMO_DONATIONS = [
    {
        "id": "don-001",
        "store_id": "27934f1c-f6cb-4731-a419-570b18e39f0a",
        "store_name": "[DEMO] Freshwise Central",
        "product_name": "[DEMO] Baby Spinach 200g",
        "sku": "DEMO-SPINACH-200",
        "category": "produce",
        "quantity": 3,
        "partner_name": "Robin Hood Army (Central Bengaluru)",
        "partner_contact": "+91 98800 12345",
        "status": "ready_for_dispatch",
        "expiry_date": (date.today() + timedelta(days=1)).isoformat(),
        "pickup_deadline": "Today by 08:00 PM",
        "eligibility_basis": "Food Safety Grade A - 100% wholesome for immediate meal prep",
    },
    {
        "id": "don-002",
        "store_id": "store-demo-002",
        "store_name": "[DEMO] Freshwise Indiranagar",
        "product_name": "[DEMO] Whole Wheat Bread",
        "sku": "DEMO-BREAD-WW",
        "category": "bakery",
        "quantity": 6,
        "partner_name": "Feeding India (Indiranagar)",
        "partner_contact": "+91 98800 67890",
        "status": "ready_for_dispatch",
        "expiry_date": (date.today() + timedelta(days=1)).isoformat(),
        "pickup_deadline": "Today by 09:00 PM",
        "eligibility_basis": "Day-surplus bakery stock, sealed and hygienic",
    },
    {
        "id": "don-003",
        "store_id": "store-demo-003",
        "store_name": "[DEMO] Freshwise Koramangala",
        "product_name": "[DEMO] Greek Yogurt 500g",
        "sku": "DEMO-YOGURT-500",
        "category": "dairy",
        "quantity": 5,
        "partner_name": "Akshaya Patra Community Kitchen",
        "partner_contact": "+91 80 2345 6789",
        "status": "partner_notified",
        "expiry_date": (date.today() + timedelta(days=2)).isoformat(),
        "pickup_deadline": "Tomorrow by 11:00 AM",
        "eligibility_basis": "Cold-chain verified dairy surplus",
    },
]


# ---------------------------------------------------------------------------
# Persistent In-Memory Reservations State
# ---------------------------------------------------------------------------

_DEMO_RESERVATIONS: dict[str, dict] = {}
_DEMO_RECOMMENDATIONS = {
    "rec-demo-001": {
        "id": "rec-demo-001",
        "store_id": DEMO_STORE["id"],
        "product_id": "p-milk-01",
        "sku": "DEMO-MILK-1L",
        "product_name": "[DEMO] Whole Milk 1L",
        "action": "markdown",
        "status": "proposed",
        "discount_percent": 20,
        "proposed_quantity": 20,
        "confidence": 0.88,
        "rationale": "Expires in 1 day with 20 units on hand. High risk of complete write-off without immediate 20% discount.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reviewed_by": None,
        "reviewed_at": None,
        "review_note": None,
    },
    "rec-demo-002": {
        "id": "rec-demo-002",
        "store_id": DEMO_STORE["id"],
        "product_id": "p-straw-01",
        "sku": "DEMO-STRAW-250",
        "product_name": "[DEMO] Strawberries 250g",
        "action": "markdown",
        "status": "proposed",
        "discount_percent": 15,
        "proposed_quantity": 14,
        "confidence": 0.82,
        "rationale": "Expires in 2 days. 15% discount recommended to accelerate sales before quality degrades.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reviewed_by": None,
        "reviewed_at": None,
        "review_note": None,
    },
    "rec-demo-003": {
        "id": "rec-demo-003",
        "store_id": DEMO_STORE["id"],
        "product_id": "p-spinach-01",
        "sku": "DEMO-SPINACH-200",
        "product_name": "[DEMO] Baby Spinach 200g",
        "action": "donate",
        "status": "proposed",
        "discount_percent": None,
        "proposed_quantity": 3,
        "confidence": 0.92,
        "rationale": "Critical stock (3 units) expiring tomorrow. Route to Robin Hood Army partner for same-day meal prep.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reviewed_by": None,
        "reviewed_at": None,
        "review_note": None,
    },
}

_DEMO_DECISION_LOGS: list[dict] = []


# ---------------------------------------------------------------------------
# Query & Reservation Operations
# ---------------------------------------------------------------------------

def get_all_demo_stores() -> list[dict]:
    """Return all available demo stores."""
    return [dict(s) for s in DEMO_STORES]


def get_demo_store_by_id(store_id_or_code: str) -> dict | None:
    """Retrieve a store by UUID or code."""
    cleaned = store_id_or_code.strip().lower()
    for s in DEMO_STORES:
        if s["id"].lower() == cleaned or s["code"].lower() == cleaned:
            return dict(s)
        if cleaned in s["locality"].lower() or cleaned in s["name"].lower():
            return dict(s)
    return None


def get_nearby_stores(lat: float, lon: float, max_radius_km: float = 30.0) -> list[dict]:
    """
    Find demo stores ordered by distance from given coordinates.
    """
    stores_with_distance = []
    for s in DEMO_STORES:
        dist = calculate_distance_km(lat, lon, s["latitude"], s["longitude"])
        if dist <= max_radius_km:
            active_deals = [d for d in _DEMO_RESCUE_DEALS.values() if d["store_id"] == s["id"] and d["quantity_available"] > 0]
            store_copy = dict(s)
            store_copy["distance_km"] = dist
            store_copy["active_deals_count"] = len(active_deals)
            stores_with_distance.append(store_copy)

    return sorted(stores_with_distance, key=lambda x: x["distance_km"])


def get_all_rescue_deals(store_id: str = "") -> list[dict]:
    """Return active food rescue deals, optionally filtered by store."""
    deals = [dict(d) for d in _DEMO_RESCUE_DEALS.values() if d["is_active"] and d["quantity_available"] > 0]
    if store_id:
        deals = [d for d in deals if d["store_id"] == store_id]
    return sorted(deals, key=lambda x: (x["days_left"], -x["discount_percent"]))


def get_rescue_deal_by_id(deal_id: str) -> dict | None:
    """Retrieve a specific deal by ID."""
    if deal_id in _DEMO_RESCUE_DEALS:
        return dict(_DEMO_RESCUE_DEALS[deal_id])
    return None


def get_all_donations(store_id: str = "") -> list[dict]:
    """Return NGO food donation items."""
    donations = [dict(d) for d in DEMO_DONATIONS]
    if store_id:
        donations = [d for d in donations if d["store_id"] == store_id]
    return donations


def create_demo_reservation(
    user_id: int,
    deal_id: str,
    quantity: int = 1,
    actor_name: str = "",
) -> tuple[bool, str, dict | None]:
    """
    Create an in-memory demo reservation for a rescue deal.
    Enforces availability, prevents duplicate active reservations, and prevents over-reservation.
    """
    if deal_id not in _DEMO_RESCUE_DEALS:
        return False, "❌ Deal offer not found or has expired.", None

    deal = _DEMO_RESCUE_DEALS[deal_id]
    if deal["quantity_available"] < quantity:
        return (
            False,
            f"❌ Not enough items left to reserve. Available: {deal['quantity_available']} unit(s).",
            None,
        )

    # Check for existing active reservation for the same deal by this user
    for res in _DEMO_RESERVATIONS.values():
        if res["user_id"] == user_id and res["deal_id"] == deal_id and res["status"] == "confirmed":
            return (
                False,
                f"⚠️ You already have an active reservation for **{deal['product_name']}** (Code: `{res['reservation_code']}`).",
                dict(res),
            )

    # Decrement available quantity in demo state
    deal["quantity_available"] -= quantity

    res_id = f"res-demo-{len(_DEMO_RESERVATIONS) + 1:04d}"
    res_code = f"FW-RES-{random.randint(1000, 9999)}"
    now_str = datetime.now(timezone.utc).isoformat()

    reservation_record = {
        "id": res_id,
        "reservation_code": res_code,
        "user_id": user_id,
        "actor_name": actor_name or str(user_id),
        "deal_id": deal_id,
        "product_name": deal["product_name"],
        "store_id": deal["store_id"],
        "store_name": deal["store_name"],
        "quantity": quantity,
        "unit_price": deal["rescue_price"],
        "total_amount": round(deal["rescue_price"] * quantity, 2),
        "pickup_window": deal["pickup_window"],
        "status": "confirmed",  # confirmed, cancelled, collected
        "created_at": now_str,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat(),
    }

    _DEMO_RESERVATIONS[res_id] = reservation_record
    logger.info("Demo reservation %s created for user %d (Deal: %s)", res_id, user_id, deal_id)

    msg = (
        f"🎉 **Demo Reservation Confirmed!**\n\n"
        f"🏷️ **Item:** {deal['product_name']}\n"
        f"🏬 **Store:** {deal['store_name']}\n"
        f"📦 **Quantity:** {quantity} unit(s) @ ₹{deal['rescue_price']:.2f}\n"
        f"🔖 **Reservation Code:** `{res_code}`\n"
        f"🕒 **Pickup Window:** {deal['pickup_window']}\n\n"
        f"*(Demo mode: Show this code at the store pickup counter. No payment charged.)*"
    )
    return True, msg, dict(reservation_record)


def cancel_demo_reservation(res_id: str, user_id: int) -> tuple[bool, str, dict | None]:
    """
    Cancel an existing demo reservation and restore the deal's available stock.
    """
    if res_id not in _DEMO_RESERVATIONS:
        # Check by reservation code
        for r in _DEMO_RESERVATIONS.values():
            if r["reservation_code"] == res_id:
                res_id = r["id"]
                break

    if res_id not in _DEMO_RESERVATIONS:
        return False, "❌ Reservation not found.", None

    res = _DEMO_RESERVATIONS[res_id]
    if res["user_id"] != user_id:
        return False, "🔒 Unauthorized: You can only cancel your own reservations.", None

    if res["status"] == "cancelled":
        return False, "⚠️ This reservation is already cancelled.", dict(res)

    res["status"] = "cancelled"
    deal_id = res["deal_id"]
    if deal_id in _DEMO_RESCUE_DEALS:
        _DEMO_RESCUE_DEALS[deal_id]["quantity_available"] += res["quantity"]

    msg = f"✅ Reservation `{res['reservation_code']}` for **{res['product_name']}** has been cancelled."
    return True, msg, dict(res)


def get_user_reservations(user_id: int) -> list[dict]:
    """Return all active and past demo reservations for a user."""
    user_res = [dict(r) for r in _DEMO_RESERVATIONS.values() if r["user_id"] == user_id]
    return sorted(user_res, key=lambda x: x["created_at"], reverse=True)


# ---------------------------------------------------------------------------
# Manager Functions
# ---------------------------------------------------------------------------

def get_demo_store() -> dict:
    return dict(DEMO_STORE)


def get_demo_inventory_batches() -> list[dict]:
    today = date.today()
    batch_defs = [
        ("DEMO-MILK-1L",     "DEMO-B-MILK-01",  1,   20, 20),
        ("DEMO-STRAW-250",   "DEMO-B-STRAW-01", 2,   14, 14),
        ("DEMO-YOGURT-500",  "DEMO-B-YOURT-01", 10,  80, 75),
        ("DEMO-BREAD-WW",    "DEMO-B-BREAD-01", 4,   60, 58),
        ("DEMO-SPINACH-200", "DEMO-B-SPIN-01",  1,   12,  3),
        ("DEMO-EGG-12",      "DEMO-B-EGG-01",   14,  24,  4),
        ("DEMO-OATS-500",    "DEMO-B-OATS-01",  355, 40, 38),
        ("DEMO-PASTA-500",   "DEMO-B-PASTA-01", 720, 35, 33),
    ]

    batches = []
    for idx, (sku, batch_code, days_to_exp, qty_recv, qty_oh) in enumerate(batch_defs, 1):
        prod = DEMO_PRODUCTS[sku]
        exp_date = today + timedelta(days=days_to_exp)
        batches.append({
            "batch_id": f"b-demo-{idx:03d}",
            "batch_code": batch_code,
            "product_id": prod["id"],
            "product_name": prod["name"],
            "sku": sku,
            "category": prod["category"],
            "selling_price": prod["selling_price"],
            "quantity_received": qty_recv,
            "quantity_on_hand": qty_oh,
            "expiry_date": exp_date.isoformat(),
            "days_left": days_to_exp,
        })
    return batches


def get_demo_store_summary() -> dict:
    batches = get_demo_inventory_batches()
    total_batches = len(batches)
    total_units_on_hand = sum(b["quantity_on_hand"] for b in batches)
    expiring_soon_count = sum(1 for b in batches if 0 <= b["days_left"] <= 3)
    expired_count = sum(1 for b in batches if b["days_left"] < 0)
    open_recs_count = sum(1 for r in _DEMO_RECOMMENDATIONS.values() if r["status"] == "proposed")

    return {
        "store_id": DEMO_STORE["id"],
        "store_name": DEMO_STORE["name"],
        "store_code": DEMO_STORE["code"],
        "total_batches": total_batches,
        "total_units_on_hand": total_units_on_hand,
        "expiring_soon_count": expiring_soon_count,
        "expired_count": expired_count,
        "open_recommendations_count": open_recs_count,
        "sales_units_7d": 105,
    }


def get_demo_expiring_batches(days_threshold: int = 7) -> list[dict]:
    batches = get_demo_inventory_batches()
    filtered = [b for b in batches if b["days_left"] <= days_threshold]
    return sorted(filtered, key=lambda x: x["days_left"])


def get_demo_stockout_risks(max_units_threshold: int = 5) -> list[dict]:
    batches = get_demo_inventory_batches()
    low_stock = [b for b in batches if b["quantity_on_hand"] <= max_units_threshold]
    results = []
    for b in low_stock:
        results.append({
            "batch_id": b["batch_id"],
            "batch_code": b["batch_code"],
            "product_name": b["product_name"],
            "sku": b["sku"],
            "category": b["category"],
            "quantity_on_hand": b["quantity_on_hand"],
            "urgency": "CRITICAL" if b["quantity_on_hand"] <= 2 else "LOW",
        })
    return sorted(results, key=lambda x: x["quantity_on_hand"])


def get_demo_proposed_recommendations(limit: int = 5) -> list[dict]:
    recs = [r for r in _DEMO_RECOMMENDATIONS.values() if r["status"] == "proposed"]
    return recs[:limit]


def get_demo_recommendation_by_id(rec_id: str) -> dict | None:
    if rec_id in _DEMO_RECOMMENDATIONS:
        return dict(_DEMO_RECOMMENDATIONS[rec_id])
    return None


def review_demo_recommendation(
    rec_id: str,
    decision: str,
    actor_id: str,
    note: str = "",
) -> tuple[bool, str, dict | None]:
    if rec_id not in _DEMO_RECOMMENDATIONS:
        return False, f"Recommendation '{rec_id}' not found in demo database.", None

    rec = _DEMO_RECOMMENDATIONS[rec_id]
    current_status = rec["status"]
    if current_status != "proposed":
        return (
            False,
            f"Recommendation has already been {current_status} by {rec.get('reviewed_by') or 'manager'}.",
            dict(rec),
        )

    now_str = datetime.now(timezone.utc).isoformat()
    rec["status"] = decision
    rec["reviewed_by"] = actor_id
    rec["reviewed_at"] = now_str
    rec["review_note"] = note or f"Reviewed in Demo Mode by {actor_id}"

    _DEMO_DECISION_LOGS.append({
        "id": f"log-demo-{len(_DEMO_DECISION_LOGS) + 1:03d}",
        "recommendation_id": rec_id,
        "actor_id": actor_id,
        "event_type": f"recommendation_{decision}",
        "before_state": "proposed",
        "after_state": decision,
        "note": note,
        "created_at": now_str,
    })

    action_verb = "approved" if decision == "approved" else "rejected"
    msg = (
        f"✅ Recommendation for **{rec['product_name']}** ({rec['action'].upper()}) "
        f"has been **{action_verb}** *(Demo Decision)*.\n\n"
        f"*(Manager sign-off recorded in demo state. No live ERP actions dispatched.)*"
    )
    return True, msg, dict(rec)


def build_demo_copilot_context() -> tuple[str, str]:
    batches = get_demo_inventory_batches()
    recs = [r for r in _DEMO_RECOMMENDATIONS.values() if r["status"] == "proposed"]
    deals = [d for d in _DEMO_RESCUE_DEALS.values() if d["quantity_available"] > 0]
    donations = DEMO_DONATIONS

    lines = [
        "=== Freshwise Demo Multi-Store Network ===",
    ]
    for s in DEMO_STORES:
        lines.append(f"  • {s['name']} ({s['code']}) | Address: {s['address']} | Hours: {s['pickup_hours']}")

    lines.append("\n=== Active Food Rescue Deals ===")
    for d in deals:
        lines.append(
            f"  • {d['product_name']} @ {d['store_name']} | Rescue Price: ₹{d['rescue_price']} ({d['discount_percent']}% off, was ₹{d['original_price']}) | "
            f"Qty left: {d['quantity_available']} | Expiry: {d['expiry_date']} | Pickup: {d['pickup_window']}"
        )

    lines.append("\n=== NGO Food Rescue Donations ===")
    for don in donations:
        lines.append(
            f"  • {don['product_name']} ({don['quantity']} units) @ {don['store_name']} | Partner: {don['partner_name']} | "
            f"Deadline: {don['pickup_deadline']} | Safety: {don['eligibility_basis']}"
        )

    lines.append("\n=== Main Inventory Batches ===")
    for b in batches:
        lines.append(
            f"  • {b['product_name']} ({b['sku']}) | Batch: {b['batch_code']} | "
            f"Qty: {b['quantity_on_hand']} | Expiry: {b['expiry_date']} ({b['days_left']}d left) | Price: ₹{b['selling_price']}"
        )

    context_text = "\n".join(lines)
    summary = f"Loaded {len(DEMO_STORES)} stores, {len(deals)} rescue deals, and {len(donations)} donation batches."
    return context_text, summary
