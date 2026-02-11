"""
FastAPI dependencies for authentication and authorization
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Request

from app.core.security import decode_token
from app.db.supabase_client import get_supabase as get_supabase_client


async def get_token_from_request(request: Request) -> Optional[str]:
    """Extract Bearer token from Authorization header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Get current authenticated user from token.
    Raises HTTPException if not authenticated.
    """
    token = await get_token_from_request(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chưa đăng nhập",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch fresh user data from database
    client = get_supabase_client()
    result = client.table('users').select(
        'user_id, user_code, full_name, email, role, is_active'
    ).eq('user_id', user_id).limit(1).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại",
        )

    user = result.data[0]

    if not user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản đã bị vô hiệu hóa",
        )

    return user


async def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated, otherwise return None.
    Does not raise exception for unauthenticated requests.
    """
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


async def require_admin(request: Request) -> Dict[str, Any]:
    """Require ADMIN role"""
    user = await get_current_user(request)

    if user.get('role') != 'ADMIN':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Admin mới có quyền thực hiện thao tác này",
        )

    return user


async def require_manager_or_admin(request: Request) -> Dict[str, Any]:
    """Require MANAGER or ADMIN role"""
    user = await get_current_user(request)

    if user.get('role') not in ['ADMIN', 'MANAGER']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Manager hoặc Admin mới có quyền thực hiện thao tác này",
        )

    return user


def check_permission(user: Dict[str, Any], permission: str) -> bool:
    """
    Check if user has specific permission.

    Permission format: "entity:action" (e.g., "jobs:create", "users:delete")

    Role permissions:
    - ADMIN: all permissions
    - MANAGER: jobs:*, customers:*, vendors:*, users:read
    - STAFF: jobs:read, jobs:update_own, customers:read, vendors:read
    """
    role = user.get('role', 'STAFF')

    # Admin has all permissions
    if role == 'ADMIN':
        return True

    # Define role permissions
    role_permissions = {
        'MANAGER': [
            'jobs:*', 'customers:*', 'vendors:*',
            'users:read', 'users:create_staff',
            'reports:read', 'services:*'
        ],
        'STAFF': [
            'jobs:read', 'jobs:update_own',
            'customers:read', 'vendors:read',
            'services:read', 'services:update_own'
        ]
    }

    user_perms = role_permissions.get(role, [])

    # Check exact match or wildcard
    entity, action = permission.split(':') if ':' in permission else (permission, '*')

    for perm in user_perms:
        perm_entity, perm_action = perm.split(':') if ':' in perm else (perm, '*')

        # Match entity
        if perm_entity != entity and perm_entity != '*':
            continue

        # Match action
        if perm_action == '*' or perm_action == action:
            return True

    return False
