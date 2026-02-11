"""
Audit Logs API endpoints
- Query activity logs for tracking user actions
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Request

from app.db.supabase_client import get_supabase as get_supabase_client
from app.api.dependencies import require_admin

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.get("/logs")
async def get_activity_logs(
    request: Request,
    user_id: Optional[int] = None,
    action_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    from_date: Optional[str] = None,  # YYYY-MM-DD
    to_date: Optional[str] = None,    # YYYY-MM-DD
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """
    Get activity logs with filters (ADMIN only)
    """
    await require_admin(request)
    client = get_supabase_client()

    # Build query
    query = client.table('activity_logs').select(
        '''
        log_id,
        user_id,
        action_type,
        entity_type,
        entity_id,
        entity_ref,
        old_value,
        new_value,
        description,
        ip_address,
        created_at,
        users!activity_logs_user_id_fkey(user_code, full_name)
        '''
    )

    # Apply filters
    if user_id:
        query = query.eq('user_id', user_id)

    if action_type:
        query = query.eq('action_type', action_type)

    if entity_type:
        query = query.eq('entity_type', entity_type)

    if entity_id:
        query = query.eq('entity_id', entity_id)

    if from_date:
        query = query.gte('created_at', f"{from_date}T00:00:00")

    if to_date:
        query = query.lte('created_at', f"{to_date}T23:59:59")

    if search:
        query = query.or_(
            f"entity_ref.ilike.%{search}%,"
            f"description.ilike.%{search}%"
        )

    # Order and paginate
    query = query.order('created_at', desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    # Transform user data for easier frontend use
    logs = []
    for log in result.data:
        user_info = log.pop('users', None)
        if user_info:
            log['user_code'] = user_info.get('user_code')
            log['user_name'] = user_info.get('full_name')
        logs.append(log)

    return {
        "success": True,
        "logs": logs,
        "total": len(logs),
        "offset": offset,
        "limit": limit
    }


@router.get("/logs/summary")
async def get_logs_summary(request: Request, days: int = 7):
    """
    Get summary of activity logs for dashboard (ADMIN only)
    """
    await require_admin(request)
    client = get_supabase_client()

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get counts by action type
    result = client.table('activity_logs').select(
        'action_type'
    ).gte('created_at', start_date.isoformat()).execute()

    # Count by action type
    action_counts = {}
    for log in result.data:
        action = log['action_type']
        action_counts[action] = action_counts.get(action, 0) + 1

    # Get recent activities
    recent = client.table('activity_logs').select(
        '''
        log_id,
        action_type,
        entity_type,
        entity_ref,
        description,
        created_at,
        users!activity_logs_user_id_fkey(user_code, full_name)
        '''
    ).order('created_at', desc=True).limit(10).execute()

    recent_logs = []
    for log in recent.data:
        user_info = log.pop('users', None)
        if user_info:
            log['user_code'] = user_info.get('user_code')
            log['user_name'] = user_info.get('full_name')
        recent_logs.append(log)

    return {
        "success": True,
        "period_days": days,
        "total_actions": len(result.data),
        "by_action_type": action_counts,
        "recent_activities": recent_logs
    }


@router.get("/users")
async def get_users_for_filter(request: Request):
    """
    Get list of users who have activity logs (for filter dropdown)
    """
    await require_admin(request)
    client = get_supabase_client()

    # Get distinct user_ids from logs
    logs = client.table('activity_logs').select(
        'user_id'
    ).execute()

    user_ids = list(set(log['user_id'] for log in logs.data if log.get('user_id')))

    if not user_ids:
        return {"success": True, "users": []}

    # Get user info
    users = client.table('users').select(
        'user_id, user_code, full_name'
    ).in_('user_id', user_ids).execute()

    return {
        "success": True,
        "users": users.data
    }


@router.get("/action-types")
async def get_action_types(request: Request):
    """
    Get list of action types for filter dropdown
    """
    await require_admin(request)

    return {
        "success": True,
        "action_types": [
            {"value": "LOGIN", "label": "Đăng nhập"},
            {"value": "LOGOUT", "label": "Đăng xuất"},
            {"value": "CREATE", "label": "Tạo mới"},
            {"value": "UPDATE", "label": "Cập nhật"},
            {"value": "DELETE", "label": "Xóa"},
        ]
    }


@router.get("/entity-types")
async def get_entity_types(request: Request):
    """
    Get list of entity types for filter dropdown
    """
    await require_admin(request)

    return {
        "success": True,
        "entity_types": [
            {"value": "JOB", "label": "Job"},
            {"value": "USER", "label": "Người dùng"},
            {"value": "CUSTOMER", "label": "Khách hàng"},
            {"value": "VENDOR", "label": "Nhà cung cấp"},
            {"value": "SERVICE", "label": "Loại dịch vụ"},
        ]
    }
