"""
Unit tests for the CSV ingestion service.

All Supabase calls are mocked — no real database connections are made.
"""

import io
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.ingestion_service import (
    ImportResult,
    parse_and_validate_csv,
    upsert_inventory,
    upsert_products,
    upsert_promotions,
    upsert_sales,
)


# ---------------------------------------------------------------------------
# Helpers to build mock Supabase clients
# ---------------------------------------------------------------------------

def _mock_db(
    products_data: list[dict] | None = None,
    upsert_data: list[dict] | None = None,
    insert_data: list[dict] | None = None,
    existing_sales: list[dict] | None = None,
    existing_promo: list[dict] | None = None,
    ai_runs_insert: list[dict] | None = None,
):
    """Return a MagicMock that mimics supabase-py's chained query API."""
    db = MagicMock()

    # Default responses
    _products = products_data if products_data is not None else [
        {"id": "prod-uuid-1", "sku": "SKU-001"},
        {"id": "prod-uuid-2", "sku": "SKU-002"},
    ]
    _upsert = upsert_data if upsert_data is not None else [
        {"id": "row-uuid-1"}, {"id": "row-uuid-2"}
    ]
    _insert = insert_data if insert_data is not None else [
        {"id": "row-uuid-1"}, {"id": "row-uuid-2"}, {"id": "row-uuid-3"}
    ]
    _ex_sales = existing_sales if existing_sales is not None else []
    _ex_promo = existing_promo if existing_promo is not None else []
    _ai = ai_runs_insert if ai_runs_insert is not None else [{"id": "run-uuid-1"}]

    # ai_runs insert
    ai_table = MagicMock()
    ai_table.insert.return_value.execute.return_value = SimpleNamespace(data=_ai)
    ai_table.update.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[])

    # products table
    prod_table = MagicMock()
    prod_table.select.return_value.in_.return_value.execute.return_value = SimpleNamespace(data=_products)
    prod_table.upsert.return_value.execute.return_value = SimpleNamespace(data=_upsert)

    # inventory_batches table
    inv_table = MagicMock()
    inv_table.upsert.return_value.execute.return_value = SimpleNamespace(data=_upsert)

    # sales_records table
    sales_check = MagicMock()
    sales_check.execute.return_value = SimpleNamespace(data=_ex_sales)
    sales_table = MagicMock()
    # Chain for existence check: .select().eq().eq().eq().eq().execute()
    sales_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=_ex_sales)
    sales_table.insert.return_value.execute.return_value = SimpleNamespace(data=_insert)

    # promotions table
    promo_table = MagicMock()
    promo_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=_ex_promo)
    promo_table.insert.return_value.execute.return_value = SimpleNamespace(data=[{"id": "promo-1"}])

    # stores table
    stores_table = MagicMock()
    stores_table.select.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[{"id": "store-1"}])

    def _table(name: str):
        if name == "ai_runs":
            return ai_table
        if name == "products":
            return prod_table
        if name == "inventory_batches":
            return inv_table
        if name == "sales_records":
            return sales_table
        if name == "promotions":
            return promo_table
        if name == "stores":
            return stores_table
        return MagicMock()

    db.table.side_effect = _table
    return db


# ---------------------------------------------------------------------------
# parse_and_validate_csv tests
# ---------------------------------------------------------------------------

def test_valid_products_csv_accepted():
    """Valid products CSV with required columns passes validation."""
    csv = (
        "sku,name,category,selling_price,unit_cost\n"
        "SKU-001,Whole Milk 1L,dairy,68.00,48.00\n"
        "SKU-002,Rolled Oats,grains,78.00,45.00\n"
    ).encode()
    rows, errors = parse_and_validate_csv(csv, "products")
    assert len(errors) == 0
    assert len(rows) == 2


def test_missing_required_column():
    """CSV missing a required column returns a file-level error naming the column."""
    csv = (
        "sku,name,category,unit_cost\n"   # missing selling_price
        "SKU-001,Milk,dairy,48.00\n"
    ).encode()
    rows, errors = parse_and_validate_csv(csv, "products")
    assert len(rows) == 0
    assert any("selling_price" in e.field for e in errors)


def test_empty_csv():
    """CSV with headers only (no data rows) returns an appropriate error."""
    csv = b"sku,name,category,selling_price,unit_cost\n"
    rows, errors = parse_and_validate_csv(csv, "products")
    assert len(rows) == 0
    assert len(errors) > 0
    assert any("no data" in e.message.lower() for e in errors)


# ---------------------------------------------------------------------------
# upsert_products tests
# ---------------------------------------------------------------------------

def test_products_upsert_valid():
    """Two valid product rows → accepted=2, rejected=0."""
    rows = [
        {"sku": "SKU-001", "name": "Milk", "category": "dairy",
         "selling_price": "68", "unit_cost": "48"},
        {"sku": "SKU-002", "name": "Oats", "category": "grains",
         "selling_price": "78", "unit_cost": "45"},
    ]
    db = _mock_db(upsert_data=[{"id": "1", "sku": "SKU-001"}, {"id": "2", "sku": "SKU-002"}])
    result = upsert_products(rows, db)
    assert result.accepted == 2
    assert result.rejected == 0
    assert len(result.errors) == 0


def test_products_invalid_price():
    """Row with negative selling_price is rejected; valid row is accepted."""
    rows = [
        {"sku": "SKU-001", "name": "Milk", "category": "dairy",
         "selling_price": "-5", "unit_cost": "48"},
        {"sku": "SKU-002", "name": "Oats", "category": "grains",
         "selling_price": "78", "unit_cost": "45"},
    ]
    db = _mock_db(upsert_data=[{"id": "2", "sku": "SKU-002"}])
    result = upsert_products(rows, db)
    assert result.rejected == 1
    assert any(e.field == "selling_price" for e in result.errors)
    assert result.accepted == 1


# ---------------------------------------------------------------------------
# upsert_inventory tests
# ---------------------------------------------------------------------------

def test_invalid_date_format():
    """Row with an unparseable expiry_date is rejected with a date error."""
    rows = [
        {
            "sku": "SKU-001",
            "batch_code": "B-001",
            "received_at": "2025-01-10",
            "expiry_date": "not-a-date",
            "quantity_received": "50",
            "quantity_on_hand": "48",
        }
    ]
    db = _mock_db(products_data=[{"id": "prod-1", "sku": "SKU-001"}])
    result = upsert_inventory(rows, db, "store-1")
    assert result.rejected == 1
    assert any(e.field == "expiry_date" for e in result.errors)


def test_qty_on_hand_exceeds_received():
    """quantity_on_hand > quantity_received is a validation error."""
    rows = [
        {
            "sku": "SKU-001",
            "batch_code": "B-001",
            "received_at": "2025-01-10",
            "expiry_date": "2025-01-20",
            "quantity_received": "50",
            "quantity_on_hand": "100",
        }
    ]
    db = _mock_db(products_data=[{"id": "prod-1", "sku": "SKU-001"}])
    result = upsert_inventory(rows, db, "store-1")
    assert result.rejected == 1
    assert any("quantity_on_hand" in e.field for e in result.errors)


def test_inventory_unknown_sku():
    """Unknown SKU (not in products) is rejected with a sku error."""
    rows = [
        {
            "sku": "UNKNOWN-SKU",
            "batch_code": "B-001",
            "received_at": "2025-01-10",
            "expiry_date": "2025-01-20",
            "quantity_received": "50",
            "quantity_on_hand": "48",
        }
    ]
    db = _mock_db(products_data=[])  # empty — no products found
    result = upsert_inventory(rows, db, "store-1")
    assert result.rejected == 1
    assert any(e.field == "sku" for e in result.errors)


# ---------------------------------------------------------------------------
# upsert_sales tests
# ---------------------------------------------------------------------------

def test_sales_valid_csv():
    """Three valid sales rows → accepted=3, rejected=0."""
    rows = [
        {"sku": "SKU-001", "sold_at": "2025-01-12T10:00:00",
         "quantity": "3", "unit_price": "68.00"},
        {"sku": "SKU-001", "sold_at": "2025-01-13T10:00:00",
         "quantity": "2", "unit_price": "68.00"},
        {"sku": "SKU-002", "sold_at": "2025-01-12T11:00:00",
         "quantity": "1", "unit_price": "78.00"},
    ]
    db = _mock_db(
        insert_data=[{"id": "s1"}, {"id": "s2"}, {"id": "s3"}],
    )
    result = upsert_sales(rows, db, "store-1")
    assert result.accepted == 3
    assert result.rejected == 0


def test_sales_duplicate_skipped():
    """When existence check returns a row, the sale is counted as duplicate not rejected."""
    rows = [
        {"sku": "SKU-001", "sold_at": "2025-01-12T10:00:00",
         "quantity": "3", "unit_price": "68.00", "source_ref": "REF-001"},
    ]
    # Existence check returns an existing row → duplicate
    db = _mock_db(existing_sales=[{"id": "existing-sale-id"}])
    result = upsert_sales(rows, db, "store-1")
    assert result.duplicates == 1
    assert result.accepted == 0
    assert result.rejected == 0


# ---------------------------------------------------------------------------
# upsert_promotions tests
# ---------------------------------------------------------------------------

def test_promotions_invalid_discount():
    """discount_percent=150 is rejected with a discount_percent error."""
    rows = [
        {
            "sku": "SKU-001",
            "name": "Summer Sale",
            "discount_percent": "150",
            "starts_at": "2025-06-01T00:00:00",
            "ends_at": "2025-06-30T23:59:59",
        }
    ]
    db = _mock_db(products_data=[{"id": "prod-1", "sku": "SKU-001"}])
    result = upsert_promotions(rows, db, "store-1")
    assert result.rejected == 1
    assert any(e.field == "discount_percent" for e in result.errors)


def test_duplicate_import_uses_upsert():
    """Calling upsert_products twice with the same data does not raise; accepted > 0."""
    rows = [
        {"sku": "SKU-001", "name": "Milk", "category": "dairy",
         "selling_price": "68", "unit_cost": "48"},
    ]
    db = _mock_db(upsert_data=[{"id": "1", "sku": "SKU-001"}])
    result1 = upsert_products(rows, db)
    result2 = upsert_products(rows, db)
    assert result1.accepted > 0
    assert result2.accepted > 0
    # No exceptions raised
