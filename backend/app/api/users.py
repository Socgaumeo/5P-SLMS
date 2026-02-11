"""
User Management API endpoints
- CRUD operations for users
- Password reset functionality
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel, EmailStr

from app.db.supabase_client import get_supabase as get_supabase_client
from app.core.security import get_password_hash, generate_random_password
from app.api.dependencies import require_admin, require_manager_or_admin, get_current_user

router = APIRouter(prefix="/api/users", tags=["Users"])


# Request/Response models
class UserCreate(BaseModel):
    user_code: str
    full_name: str
    email: str
    password: Optional[str] = None  # If not provided, generate random
    role: str = "STAFF"  # ADMIN, MANAGER, STAFF


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    user_id: int
    user_code: str
    full_name: str
    email: Optional[str]
    role: str
    is_active: bool
    last_login: Optional[str]
    created_at: Optional[str]


class PasswordResetResponse(BaseModel):
    success: bool
    new_password: Optional[str] = None
    message: str


@router.get("")
async def list_users(
    request: Request,
    include_inactive: bool = False,
    search: Optional[str] = None,
    role: Optional[str] = None,
    limit: int = 100,
):
    """
    List all users (ADMIN/MANAGER only)
    """
    user = await require_manager_or_admin(request)
    client = get_supabase_client()

    query = client.table('users').select(
        'user_id, user_code, full_name, email, role, is_active, last_login, created_at'
    )

    if not include_inactive:
        query = query.eq('is_active', True)

    if role:
        query = query.eq('role', role)

    if search:
        query = query.or_(
            f"user_code.ilike.%{search}%,"
            f"full_name.ilike.%{search}%,"
            f"email.ilike.%{search}%"
        )

    query = query.order('user_code').limit(limit)
    result = query.execute()

    return {
        "success": True,
        "users": result.data,
        "total": len(result.data)
    }


@router.get("/{user_id}")
async def get_user(request: Request, user_id: int):
    """
    Get user details by ID (ADMIN/MANAGER only)
    """
    await require_manager_or_admin(request)
    client = get_supabase_client()

    result = client.table('users').select(
        'user_id, user_code, full_name, email, role, is_active, last_login, created_at, created_by'
    ).eq('user_id', user_id).limit(1).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    return {
        "success": True,
        "user": result.data[0]
    }


@router.post("")
async def create_user(request: Request, user_data: UserCreate):
    """
    Create new user (ADMIN only)
    """
    admin = await require_admin(request)
    client = get_supabase_client()

    # Validate role
    valid_roles = ['ADMIN', 'MANAGER', 'STAFF']
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Role không hợp lệ. Chọn: {', '.join(valid_roles)}"
        )

    # Check duplicate user_code
    existing = client.table('users').select('user_id').eq(
        'user_code', user_data.user_code.upper()
    ).limit(1).execute()

    if existing.data:
        raise HTTPException(
            status_code=400,
            detail=f"Mã người dùng '{user_data.user_code}' đã tồn tại"
        )

    # Check duplicate email
    if user_data.email:
        existing_email = client.table('users').select('user_id').eq(
            'email', user_data.email.lower()
        ).limit(1).execute()

        if existing_email.data:
            raise HTTPException(
                status_code=400,
                detail=f"Email '{user_data.email}' đã được sử dụng"
            )

    # Generate password if not provided
    password = user_data.password or generate_random_password()
    password_hash = get_password_hash(password)

    # Create user
    new_user = {
        'user_code': user_data.user_code.upper(),
        'full_name': user_data.full_name,
        'email': user_data.email.lower() if user_data.email else None,
        'password_hash': password_hash,
        'role': user_data.role,
        'is_active': True,
        'created_by': admin['user_id'],
        'created_at': datetime.utcnow().isoformat(),
    }

    result = client.table('users').insert(new_user).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Không thể tạo người dùng")

    created_user = result.data[0]

    # Log action
    try:
        client.table('activity_logs').insert({
            'user_id': admin['user_id'],
            'action_type': 'CREATE',
            'entity_type': 'USER',
            'entity_id': created_user['user_id'],
            'entity_ref': created_user['user_code'],
            'new_value': {'user_code': created_user['user_code'], 'role': user_data.role},
            'description': f"Created user {created_user['user_code']}",
        }).execute()
    except Exception:
        pass

    return {
        "success": True,
        "user": {
            "user_id": created_user['user_id'],
            "user_code": created_user['user_code'],
            "full_name": created_user['full_name'],
            "email": created_user.get('email'),
            "role": created_user['role'],
        },
        "generated_password": password if not user_data.password else None,
        "message": "Tạo người dùng thành công"
    }


@router.put("/{user_id}")
async def update_user(request: Request, user_id: int, user_data: UserUpdate):
    """
    Update user (ADMIN only)
    """
    admin = await require_admin(request)
    client = get_supabase_client()

    # Get existing user
    existing = client.table('users').select('*').eq('user_id', user_id).limit(1).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    old_user = existing.data[0]

    # Prepare update data
    update_data = {'updated_at': datetime.utcnow().isoformat()}

    if user_data.full_name is not None:
        update_data['full_name'] = user_data.full_name

    if user_data.email is not None:
        # Check duplicate email
        email_check = client.table('users').select('user_id').eq(
            'email', user_data.email.lower()
        ).neq('user_id', user_id).limit(1).execute()

        if email_check.data:
            raise HTTPException(status_code=400, detail="Email đã được sử dụng")

        update_data['email'] = user_data.email.lower()

    if user_data.role is not None:
        valid_roles = ['ADMIN', 'MANAGER', 'STAFF']
        if user_data.role not in valid_roles:
            raise HTTPException(status_code=400, detail="Role không hợp lệ")
        update_data['role'] = user_data.role

    if user_data.is_active is not None:
        update_data['is_active'] = user_data.is_active

    # Update user
    result = client.table('users').update(update_data).eq('user_id', user_id).execute()

    # Log action
    try:
        client.table('activity_logs').insert({
            'user_id': admin['user_id'],
            'action_type': 'UPDATE',
            'entity_type': 'USER',
            'entity_id': user_id,
            'entity_ref': old_user['user_code'],
            'old_value': {k: old_user.get(k) for k in update_data.keys() if k != 'updated_at'},
            'new_value': {k: v for k, v in update_data.items() if k != 'updated_at'},
            'description': f"Updated user {old_user['user_code']}",
        }).execute()
    except Exception:
        pass

    return {
        "success": True,
        "message": "Cập nhật người dùng thành công"
    }


@router.delete("/{user_id}")
async def delete_user(request: Request, user_id: int, hard_delete: bool = False):
    """
    Deactivate or delete user (ADMIN only)
    Default: soft delete (set is_active=False)
    """
    admin = await require_admin(request)
    client = get_supabase_client()

    # Prevent self-deletion
    if user_id == admin['user_id']:
        raise HTTPException(status_code=400, detail="Không thể xóa chính mình")

    # Get existing user
    existing = client.table('users').select('user_code').eq('user_id', user_id).limit(1).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    user_code = existing.data[0]['user_code']

    if hard_delete:
        # Hard delete
        client.table('users').delete().eq('user_id', user_id).execute()
        action_desc = f"Deleted user {user_code}"
    else:
        # Soft delete
        client.table('users').update({
            'is_active': False,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('user_id', user_id).execute()
        action_desc = f"Deactivated user {user_code}"

    # Log action
    try:
        client.table('activity_logs').insert({
            'user_id': admin['user_id'],
            'action_type': 'DELETE',
            'entity_type': 'USER',
            'entity_id': user_id,
            'entity_ref': user_code,
            'description': action_desc,
        }).execute()
    except Exception:
        pass

    return {
        "success": True,
        "message": "Xóa người dùng thành công" if hard_delete else "Vô hiệu hóa người dùng thành công"
    }


@router.post("/{user_id}/reset-password", response_model=PasswordResetResponse)
async def reset_user_password(request: Request, user_id: int):
    """
    Reset user password (ADMIN only)
    Generates a random password and returns it once
    """
    admin = await require_admin(request)
    client = get_supabase_client()

    # Get existing user
    existing = client.table('users').select('user_code, full_name').eq(
        'user_id', user_id
    ).limit(1).execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    user_info = existing.data[0]

    # Generate new random password
    new_password = generate_random_password(12)
    password_hash = get_password_hash(new_password)

    # Update password
    client.table('users').update({
        'password_hash': password_hash,
        'updated_at': datetime.utcnow().isoformat()
    }).eq('user_id', user_id).execute()

    # Log action
    try:
        client.table('activity_logs').insert({
            'user_id': admin['user_id'],
            'action_type': 'UPDATE',
            'entity_type': 'USER',
            'entity_id': user_id,
            'entity_ref': user_info['user_code'],
            'description': f"Reset password for user {user_info['user_code']}",
        }).execute()
    except Exception:
        pass

    return PasswordResetResponse(
        success=True,
        new_password=new_password,
        message=f"Đã reset mật khẩu cho {user_info['full_name']} ({user_info['user_code']})"
    )


@router.post("/{user_id}/activate")
async def activate_user(request: Request, user_id: int):
    """
    Reactivate a deactivated user (ADMIN only)
    """
    admin = await require_admin(request)
    client = get_supabase_client()

    # Get existing user
    existing = client.table('users').select('user_code, is_active').eq(
        'user_id', user_id
    ).limit(1).execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    if existing.data[0]['is_active']:
        return {"success": True, "message": "Người dùng đã hoạt động"}

    # Activate user
    client.table('users').update({
        'is_active': True,
        'updated_at': datetime.utcnow().isoformat()
    }).eq('user_id', user_id).execute()

    # Log action
    try:
        client.table('activity_logs').insert({
            'user_id': admin['user_id'],
            'action_type': 'UPDATE',
            'entity_type': 'USER',
            'entity_id': user_id,
            'entity_ref': existing.data[0]['user_code'],
            'description': f"Activated user {existing.data[0]['user_code']}",
        }).execute()
    except Exception:
        pass

    return {
        "success": True,
        "message": "Kích hoạt người dùng thành công"
    }
