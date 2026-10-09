from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import health, copilot

settings = get_settings()
app = FastAPI(title="Zero-Waste Grocery API", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"], allow_headers=["Authorization", "Content-Type"]
)
app.include_router(health.router)
app.include_router(copilot.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"service": "zero-waste-grocery-api", "docs": "/docs"}
