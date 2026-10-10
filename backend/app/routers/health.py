from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
@router.get("/api/health")
def health():
    return {"status": "ok", "service": "zero-waste-grocery-api"}
