"""
Intelligence router — expiry risk and recalculate endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db import get_supabase
from app.services.intelligence_service import get_batch_risks, recalculate_store

router = APIRouter(tags=["intelligence"])


class RecalculateRequest(BaseModel):
    store_id: str


@router.get("/intelligence/risk")
def risk_endpoint(
    store_id: str = Query(None, description="UUID of the store to analyse"),
):
    """
    Return batch-level expiry risk for a store.

    If store_id is omitted the endpoint returns an empty list with a message.
    """
    if not store_id:
        return {"data": [], "message": "Provide store_id query parameter to see risk data."}

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
        risks = get_batch_risks(store_id, db)
        return {"data": risks, "message": None}
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/intelligence/recalculate")
def recalculate_endpoint(request: RecalculateRequest):
    """
    Recalculate demand forecasts and recommendations for a store.
    """
    store_id = request.store_id

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
        result = recalculate_store(store_id, db)
        return result
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
