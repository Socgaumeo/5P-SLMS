"""
Authentication API endpoints
- Login/logout
- Get current user info
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr

from app.core.config import settings

from app.db.supabase_client import get_supabase as get_supabase_client
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
)

from app.middleware.rate_limiter import limiter

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# Request/Response models
class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


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
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest):
    """
    Authenticate user and return JWT token
    """
    client = get_supabase_client()

    try:
        # Find user by email
        result = client.table('users').select(
            'user_id, user_code, full_name, email, password_hash, role, is_active'
        ).eq('email', login_data.email).limit(1).execute()

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

        if not verify_password(login_data.password, password_hash):
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
                'ip_address': request.client.host if request.client else None,
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
async def change_password(req: Request, body: ChangePasswordRequest):
    """
    Change current user's password
    """
    from app.api.dependencies import get_current_user

    current_password = body.current_password
    new_password = body.new_password

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

    # Validate new password (độ mạnh: >=8, có chữ + số)
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải có ít nhất 8 ký tự")
    if not any(c.isalpha() for c in new_password) or not any(c.isdigit() for c in new_password):
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải gồm cả chữ và số")
    if new_password == current_password:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải khác mật khẩu hiện tại")

    # Update password
    new_hash = get_password_hash(new_password)
    client.table('users').update({
        'password_hash': new_hash,
        'updated_at': datetime.utcnow().isoformat()
    }).eq('user_id', user['user_id']).execute()

    return {"success": True, "message": "Đã đổi mật khẩu thành công"}


# ============================================================
# FORGOT / RESET PASSWORD
# ============================================================

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _send_reset_email(to_email: str, full_name: str, reset_link: str) -> Optional[str]:
    """Gửi email reset qua Gmail API. Trả None nếu OK, hoặc chuỗi lỗi."""
    import httpx
    import base64
    from email.message import EmailMessage
    gcid = getattr(settings, "GMAIL_CLIENT_ID", None)
    gcs = getattr(settings, "GMAIL_CLIENT_SECRET", None)
    grt = getattr(settings, "GMAIL_REFRESH_TOKEN", None)
    email_from = getattr(settings, "EMAIL_FROM", None) or getattr(settings, "GMAIL_SENDER", None) or "5pvietnam.tas@gmail.com"
    if not (gcid and gcs and grt):
        return "gmail_not_configured"
    try:
        with httpx.Client(timeout=20) as cli:
            tr = cli.post("https://oauth2.googleapis.com/token", data={
                "client_id": gcid, "client_secret": gcs,
                "refresh_token": grt, "grant_type": "refresh_token"})
            at = tr.json().get("access_token")
            if not at:
                return f"token: {tr.text[:150]}"
            body = (
                f"Xin chào {full_name},\n\n"
                f"Bạn (hoặc ai đó) đã yêu cầu đặt lại mật khẩu tài khoản 5P SLMS.\n"
                f"Nhấn vào link dưới đây để đặt mật khẩu mới (hết hạn sau 30 phút):\n\n"
                f"{reset_link}\n\n"
                f"Nếu không phải bạn yêu cầu, hãy bỏ qua email này.\n\n— 5P Vietnam SLMS"
            )
            msg = EmailMessage()
            msg["To"] = to_email
            msg["From"] = email_from
            msg["Subject"] = "[5P SLMS] Đặt lại mật khẩu"
            msg.set_content(body)
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            sr = cli.post("https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers={"Authorization": f"Bearer {at}"}, json={"raw": raw})
        return None if sr.status_code == 200 else f"Gmail {sr.status_code}: {sr.text[:150]}"
    except Exception as e:
        return str(e)


def _send_reset_telegram(telegram_id, reset_link: str) -> Optional[str]:
    """Gửi link reset qua Telegram bot. Trả None nếu OK, hoặc chuỗi lỗi."""
    import httpx
    tok = getattr(settings, "TELEGRAM_BOT_TOKEN", None) or getattr(settings, "TELEGRAM_DOC_BOT_TOKEN", None)
    if not tok or not telegram_id:
        return "telegram_not_configured"
    try:
        text = (
            "🔑 *Đặt lại mật khẩu 5P SLMS*\n\n"
            "Bạn vừa yêu cầu đặt lại mật khẩu. Nhấn link dưới đây (hết hạn sau 30 phút):\n\n"
            f"{reset_link}\n\n"
            "Nếu không phải bạn, hãy bỏ qua tin này."
        )
        with httpx.Client(timeout=15) as cli:
            r = cli.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                json={"chat_id": telegram_id, "text": text, "parse_mode": "Markdown",
                      "disable_web_page_preview": True})
        return None if r.status_code == 200 else f"TG {r.status_code}: {r.text[:120]}"
    except Exception as e:
        return str(e)


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, body: ForgotPasswordRequest):
    """
    Yêu cầu đặt lại mật khẩu. Luôn trả về success chung (chống dò tài khoản).
    Gửi link reset qua email (Gmail) và/hoặc Telegram.
    """
    generic = {"success": True,
               "message": "Nếu email tồn tại trong hệ thống, hướng dẫn đặt lại mật khẩu đã được gửi."}
    email = (body.email or "").strip().lower()
    if not email:
        return generic

    client = get_supabase_client()
    res = client.table('users').select(
        'user_id, full_name, email, telegram_id, is_active'
    ).eq('email', email).limit(1).execute()

    if not res.data:
        return generic
    user = res.data[0]
    if not user.get('is_active'):
        return generic

    # Tạo token + lưu hash (hết hạn 30 phút)
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires = datetime.utcnow() + timedelta(minutes=30)
    ip = request.client.host if request.client else None
    try:
        client.table('password_resets').insert({
            'user_id': user['user_id'],
            'token_hash': token_hash,
            'expires_at': expires.isoformat(),
            'request_ip': ip,
        }).execute()
    except Exception:
        return generic

    reset_link = f"{settings.FRONTEND_URL.rstrip('/')}/?reset_token={raw_token}"

    # Gửi qua cả email + telegram (best effort)
    email_err = _send_reset_email(user['email'], user.get('full_name') or '', reset_link)
    tg_err = _send_reset_telegram(user.get('telegram_id'), reset_link)

    # Log (không lộ token)
    try:
        client.table('activity_logs').insert({
            'user_id': user['user_id'],
            'action_type': 'PASSWORD_RESET_REQUEST',
            'entity_type': 'USER',
            'entity_id': user['user_id'],
            'entity_ref': email,
            'description': f"Yêu cầu reset MK (email:{'ok' if not email_err else email_err}; tg:{'ok' if not tg_err else tg_err})",
            'ip_address': ip,
        }).execute()
    except Exception:
        pass

    return generic


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, body: ResetPasswordRequest):
    """Đặt mật khẩu mới bằng token reset."""
    new_password = body.new_password or ""
    token = body.token or ""

    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải có ít nhất 8 ký tự")
    if not any(c.isalpha() for c in new_password) or not any(c.isdigit() for c in new_password):
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải gồm cả chữ và số")

    client = get_supabase_client()
    token_hash = _hash_token(token)
    res = client.table('password_resets').select(
        'id, user_id, expires_at, used_at'
    ).eq('token_hash', token_hash).limit(1).execute()

    if not res.data:
        raise HTTPException(status_code=400, detail="Link đặt lại không hợp lệ")
    rec = res.data[0]
    if rec.get('used_at'):
        raise HTTPException(status_code=400, detail="Link đặt lại đã được sử dụng")
    try:
        exp = datetime.fromisoformat(str(rec['expires_at']).replace('Z', '+00:00')).replace(tzinfo=None)
    except Exception:
        exp = datetime.utcnow() - timedelta(seconds=1)
    if datetime.utcnow() > exp:
        raise HTTPException(status_code=400, detail="Link đặt lại đã hết hạn, vui lòng yêu cầu lại")

    new_hash = get_password_hash(new_password)
    client.table('users').update({
        'password_hash': new_hash,
        'updated_at': datetime.utcnow().isoformat()
    }).eq('user_id', rec['user_id']).execute()
    client.table('password_resets').update({
        'used_at': datetime.utcnow().isoformat()
    }).eq('id', rec['id']).execute()

    try:
        client.table('activity_logs').insert({
            'user_id': rec['user_id'],
            'action_type': 'PASSWORD_RESET',
            'entity_type': 'USER',
            'entity_id': rec['user_id'],
            'description': "Đặt lại mật khẩu thành công qua link",
            'ip_address': request.client.host if request.client else None,
        }).execute()
    except Exception:
        pass

    return {"success": True, "message": "Đã đặt lại mật khẩu thành công. Vui lòng đăng nhập lại."}
