# backend/app/db/supabase_client.py
"""
Supabase client for database operations.
Provides both sync and async clients.
"""

from supabase import create_client, Client
from app.core.config import settings


# Singleton Supabase client
_supabase_client: Client | None = None


def get_supabase() -> Client:
    """
    Get Supabase client instance (singleton pattern).
    Uses service_role key for full database access.
    """
    global _supabase_client

    if _supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment"
            )

        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )

    return _supabase_client


def get_supabase_anon() -> Client:
    """
    Get Supabase client with anon key (for public/RLS-restricted access).
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment"
        )

    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY
    )


# Convenience alias
supabase = get_supabase


# ==== 10/10/2026: trạng thái job SUY RA từ các dịch vụ (không chép 1 dịch vụ lên cả job) ====
_STATUS_RANK = {"PENDING": 0, "DRAFT": 0, "CONFIRMED": 1, "ASSIGNED": 1, "DISPATCHED": 2,
                "IN_TRANSIT": 2, "IN_PROGRESS": 2, "CUS_SUBMITTED": 2, "CUS_PROCESSING": 2,
                "WHS_RECEIVED": 2, "WHS_PROCESSING": 2, "CUS_APPROVED": 3, "WHS_RELEASED": 3,
                "DELIVERED": 3, "COMPLETED": 4}


def derive_job_status(client, job_id):
    """Job = mức THẤP NHẤT của các dịch vụ chưa hủy.
    Mọi dịch vụ COMPLETED -> COMPLETED; mọi dịch vụ đã giao/xong -> DELIVERED;
    có dịch vụ đang chạy -> IN_PROGRESS; còn lại -> PENDING. Mọi dịch vụ hủy -> CANCELLED."""
    rows = client.table("job_services").select("status_code").eq("job_id", job_id).execute().data or []
    st = [(r.get("status_code") or "PENDING").upper() for r in rows]
    live = [s for s in st if s != "CANCELLED"]
    if not live:
        return "CANCELLED" if st else None
    low = min(_STATUS_RANK.get(s, 0) for s in live)
    hi = max(_STATUS_RANK.get(s, 0) for s in live)
    if low >= 4:
        return "COMPLETED"
    if low >= 3:
        return "DELIVERED"
    if hi >= 1:
        return "IN_PROGRESS"
    return "PENDING"


def sync_job_status_from_services(client, job_id, now_iso=None, user_id=None):
    from datetime import datetime as _dt
    new = derive_job_status(client, job_id)
    if not new:
        return None
    cur = client.table("jobs").select("status_code").eq("job_id", job_id).limit(1).execute().data
    if cur and (cur[0].get("status_code") or "").upper() == new:
        return new
    upd = {"status_code": new, "updated_at": now_iso or _dt.now().isoformat()}
    if user_id:
        upd["updated_by"] = user_id
    client.table("jobs").update(upd).eq("job_id", job_id).execute()
    return new
