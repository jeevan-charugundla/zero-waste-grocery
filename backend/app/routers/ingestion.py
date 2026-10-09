"""
Ingestion router — CSV upload endpoints for products, inventory, sales, and promotions.

[DEV/DEMO ONLY — No store-level authentication is enforced. Do not promote to
production without adding proper auth and row-level security.]
"""

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import Response

from app.db import get_supabase
from app.services.ingestion_service import (
    ImportResult,
    parse_and_validate_csv,
    upsert_inventory,
    upsert_products,
    upsert_promotions,
    upsert_sales,
)

router = APIRouter(tags=["ingestion"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# ---------------------------------------------------------------------------
# Sample CSV templates
# ---------------------------------------------------------------------------

SAMPLE_CSVS: dict[str, str] = {
    "products": (
        "sku,name,category,unit,selling_price,unit_cost,default_shelf_life_days,is_perishable\n"
        "SKU-001,Whole Milk 1L,dairy,each,68.00,48.00,7,true\n"
        "SKU-002,Rolled Oats 500g,grains,each,78.00,45.00,365,false\n"
    ),
    "inventory": (
        "sku,batch_code,received_at,expiry_date,quantity_received,quantity_on_hand,source_receipt_ref\n"
        "SKU-001,BATCH-001,2025-01-10T08:00:00,2025-01-17,50,48,REC-001\n"
        "SKU-002,BATCH-002,2025-01-05T08:00:00,2026-01-05,100,95,REC-002\n"
    ),
    "sales": (
        "sku,sold_at,quantity,unit_price,source_ref,batch_code\n"
        "SKU-001,2025-01-12T10:00:00,3,68.00,SALE-2025-01-12,BATCH-001\n"
        "SKU-002,2025-01-12T11:00:00,2,78.00,SALE-2025-01-12-2,BATCH-002\n"
    ),
    "promotions": (
        "sku,name,discount_percent,starts_at,ends_at,status\n"
        "SKU-001,Milk Weekend Deal,10,2025-01-11T00:00:00,2025-01-13T23:59:59,approved\n"
    ),
}


def _check_file_size(file_bytes: bytes) -> None:
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)} MB.",
        )


# ---------------------------------------------------------------------------
# Sample download endpoints
# ---------------------------------------------------------------------------

@router.get("/ingestion/products/sample")
def sample_products():
    """Download a sample CSV template for the products dataset."""
    return Response(
        content=SAMPLE_CSVS["products"],
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_products.csv"},
    )


@router.get("/ingestion/inventory/sample")
def sample_inventory():
    """Download a sample CSV template for the inventory dataset."""
    return Response(
        content=SAMPLE_CSVS["inventory"],
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_inventory.csv"},
    )


@router.get("/ingestion/sales/sample")
def sample_sales():
    """Download a sample CSV template for the sales dataset."""
    return Response(
        content=SAMPLE_CSVS["sales"],
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_sales.csv"},
    )


@router.get("/ingestion/promotions/sample")
def sample_promotions():
    """Download a sample CSV template for the promotions dataset."""
    return Response(
        content=SAMPLE_CSVS["promotions"],
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_promotions.csv"},
    )


# ---------------------------------------------------------------------------
# Upload endpoints
# ---------------------------------------------------------------------------

@router.post("/ingestion/products", response_model=ImportResult)
async def ingest_products(file: UploadFile = File(...)):
    """[DEV/DEMO ONLY - No auth] Import products from CSV."""
    file_bytes = await file.read()
    _check_file_size(file_bytes)

    rows, parse_errors = parse_and_validate_csv(file_bytes, "products")
    if parse_errors:
        raise HTTPException(
            status_code=422,
            detail=[e.model_dump() for e in parse_errors],
        )

    try:
        db = get_supabase()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        return upsert_products(rows, db)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.post("/ingestion/inventory", response_model=ImportResult)
async def ingest_inventory(
    file: UploadFile = File(...),
    store_id: str = Query(..., description="UUID of the target store"),
):
    """[DEV/DEMO ONLY - No auth] Import inventory batches from CSV."""
    file_bytes = await file.read()
    _check_file_size(file_bytes)

    rows, parse_errors = parse_and_validate_csv(file_bytes, "inventory")
    if parse_errors:
        raise HTTPException(
            status_code=422,
            detail=[e.model_dump() for e in parse_errors],
        )

    try:
        db = get_supabase()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # Verify store exists
    try:
        store_check = db.table("stores").select("id").eq("id", store_id).execute()
        if not store_check.data:
            raise HTTPException(status_code=404, detail=f"Store '{store_id}' not found.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc

    try:
        return upsert_inventory(rows, db, store_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.post("/ingestion/sales", response_model=ImportResult)
async def ingest_sales(
    file: UploadFile = File(...),
    store_id: str = Query(..., description="UUID of the target store"),
):
    """[DEV/DEMO ONLY - No auth] Import sales records from CSV."""
    file_bytes = await file.read()
    _check_file_size(file_bytes)

    rows, parse_errors = parse_and_validate_csv(file_bytes, "sales")
    if parse_errors:
        raise HTTPException(
            status_code=422,
            detail=[e.model_dump() for e in parse_errors],
        )

    try:
        db = get_supabase()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        store_check = db.table("stores").select("id").eq("id", store_id).execute()
        if not store_check.data:
            raise HTTPException(status_code=404, detail=f"Store '{store_id}' not found.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc

    try:
        return upsert_sales(rows, db, store_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.post("/ingestion/promotions", response_model=ImportResult)
async def ingest_promotions(
    file: UploadFile = File(...),
    store_id: str = Query(..., description="UUID of the target store"),
):
    """[DEV/DEMO ONLY - No auth] Import promotions from CSV."""
    file_bytes = await file.read()
    _check_file_size(file_bytes)

    rows, parse_errors = parse_and_validate_csv(file_bytes, "promotions")
    if parse_errors:
        raise HTTPException(
            status_code=422,
            detail=[e.model_dump() for e in parse_errors],
        )

    try:
        db = get_supabase()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        store_check = db.table("stores").select("id").eq("id", store_id).execute()
        if not store_check.data:
            raise HTTPException(status_code=404, detail=f"Store '{store_id}' not found.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc

    try:
        return upsert_promotions(rows, db, store_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc
