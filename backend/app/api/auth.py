"""
Authentication API endpoints
- Login/logout
- Get current user info
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr

from app.db.supabase_client import get_supabase as get_supabase_client
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# Request/Response models
class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user: Optional[dict] = None
    message: Optional[str] = None


class UserResponse(BaseModel):
    user_id: int
    user_code: str
    full_name: str
    email: Optional[str]
    role: str
    is_active: bool


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, req: Request):
    """
    Authenticate user and return JWT token
    """
    client = get_supabase_client()

    try:
        # Find user by email
        result = client.table('users').select(
            'user_id, user_code, full_name, email, password_hash, role, is_active'
        ).eq('email', request.email).limit(1).execute()

        if not result.data:
            return LoginResponse(
                success=False,
                message="Email hoặc mật khẩu không đúng"
            )

        user = result.data[0]

        # Check if user is active
        if not user.get('is_active', True):
            return LoginResponse(
                success=False,
                message="Tài khoản đã bị vô hiệu hóa"
            )

        # Verify password
        password_hash = user.get('password_hash')
        if not password_hash:
            return LoginResponse(
                success=False,
                message="Tài khoản chưa được thiết lập mật khẩu"
            )

        if not verify_password(request.password, password_hash):
            return LoginResponse(
                success=False,
                message="Email hoặc mật khẩu không đúng"
            )

        # Create JWT token
        token_data = {
            "user_id": user['user_id'],
            "user_code": user['user_code'],
            "role": user['role'],
        }
        token = create_access_token(token_data)

        # Update last_login
        client.table('users').update({
            'last_login': datetime.utcnow().isoformat()
        }).eq('user_id', user['user_id']).execute()

        # Log login action (if activity_logs table exists)
        try:
            client.table('activity_logs').insert({
                'user_id': user['user_id'],
                'action_type': 'LOGIN',
                'entity_type': 'USER',
                'entity_id': user['user_id'],
                'entity_ref': user['user_code'],
                'description': f"User {user['user_code']} logged in",
                'ip_address': req.client.host if req.client else None,
            }).execute()
        except Exception:
            pass  # Ignore if table doesn't exist yet

        return LoginResponse(
            success=True,
            token=token,
            user={
                "user_id": user['user_id'],
                "user_code": user['user_code'],
                "full_name": user['full_name'],
                "email": user.get('email'),
                "role": user['role'],
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me")
async def get_current_user_info(req: Request):
    """
    Get current user info from token
    Requires Authorization header: Bearer <token>
    """
    from app.api.dependencies import get_current_user

    try:
        user = await get_current_user(req)
        return {
            "success": True,
            "user": user
        }
    except HTTPException as e:
        return {
            "success": False,
            "message": e.detail
        }


@router.post("/logout")
async def logout(req: Request):
    """
    Logout user (invalidate session on client side)
    Server-side: log the logout action
    """
    from app.api.dependencies import get_current_user_optional

    try:
        user = await get_current_user_optional(req)
        if user:
            client = get_supabase_client()
            # Log logout action
            try:
                client.table('activity_logs').insert({
                    'user_id': user['user_id'],
                    'action_type': 'LOGOUT',
                    'entity_type': 'USER',
                    'entity_id': user['user_id'],
                    'entity_ref': user['user_code'],
                    'description': f"User {user['user_code']} logged out",
                    'ip_address': req.client.host if req.client else None,
                }).execute()
            except Exception:
                pass

        return {"success": True, "message": "Đã đăng xuất"}
    except Exception:
        return {"success": True, "message": "Đã đăng xuất"}


@router.post("/change-password")
async def change_password(
    req: Request,
    current_password: str,
    new_password: str
):
    """
    Change current user's password
    """
    from app.api.dependencies import get_current_user

    user = await get_current_user(req)
    client = get_supabase_client()

    # Get current password hash
    result = client.table('users').select('password_hash').eq(
        'user_id', user['user_id']
    ).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify current password
    if not verify_password(current_password, result.data['password_hash']):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không đúng")

    # Validate new password
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải có ít nhất 6 ký tự")

    # Update password
    new_hash = get_password_hash(new_password)
    client.table('users').update({
        'password_hash': new_hash,
        'updated_at': datetime.utcnow().isoformat()
    }).eq('user_id', user['user_id']).execute()

    return {"success": True, "message": "Đã đổi mật khẩu thành công"}
