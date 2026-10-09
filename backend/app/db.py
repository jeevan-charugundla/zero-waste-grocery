from functools import lru_cache
from supabase import create_client, Client
from app.config import get_settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    s = get_settings()
    if not s.supabase_url or not s.supabase_service_role_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in backend/.env"
        )
    return create_client(s.supabase_url, s.supabase_service_role_key)
