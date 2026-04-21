"""
Vietnamese customs declaration codes (mã loại hình HQ) — whitelist + validator.

Single source of truth for:
- Which service_type_code values count as customs (require loai_hinh).
- Which loai_hinh codes are valid.
- Human-readable label for each code (used in error UX + AI prompt).

Kept deliberately small (~18 most common codes per TT 38/2015, TT 39/2018).
Add codes as needed when new customer types appear.

Import via importlib (kebab-case filename):
    import importlib
    customs = importlib.import_module("app.core.vietnamese-customs-declaration-codes-and-validator")
    err = customs.validate_loai_hinh_for_service(svc_code, loai_hinh)
"""

from typing import Dict, List, Optional, Tuple


# Service types that require loai_hinh — customs declaration services.
# Matched as prefix (svc_code.startswith(prefix)) OR exact equality.
# CUS_CO is EXCLUDED: CO (Certificate of Origin) is a separate service that does
# not need a customs declaration code.
CUSTOMS_SERVICE_PREFIXES: Tuple[str, ...] = ("CUS_IMPORT", "CUS_EXPORT")
CUSTOMS_SERVICE_EXACT: Tuple[str, ...] = ("CUS",)


# Common Vietnamese customs declaration codes.
# Source: Tổng cục Hải quan — Thông tư 38/2015, 39/2018.
CUSTOMS_CODE_LABELS: Dict[str, str] = {
    "A11": "Nhập kinh doanh tiêu dùng",
    "A12": "Nhập kinh doanh SX",
    "A41": "Nhập kinh doanh tại chỗ",
    "A42": "Chuyển tiêu thụ nội địa",
    "B11": "Xuất kinh doanh",
    "B12": "Xuất sau khi đã tạm xuất",
    "B13": "Xuất kinh doanh tại chỗ",
    "E11": "Nhập nguyên liệu để gia công",
    "E21": "Nhập nguyên liệu để SXXK",
    "E31": "Nhập sản phẩm gia công",
    "E42": "Xuất sản phẩm SXXK",
    "E52": "Xuất sản phẩm gia công",
    "E62": "Xuất sản phẩm sau khi sửa chữa, bảo hành",
    "G14": "Tạm xuất máy móc, thiết bị",
    "G24": "Tái xuất máy móc, thiết bị",
    "G51": "Tái xuất hàng KD tạm nhập tái xuất",
    "H11": "Hàng nhập khẩu khác",
    "H21": "Hàng xuất khẩu khác",
}


def is_customs_service(service_type_code: Optional[str]) -> bool:
    """Return True if the service requires a loai_hinh (customs declaration code)."""
    if not service_type_code:
        return False
    code = service_type_code.upper().strip()
    if code in CUSTOMS_SERVICE_EXACT:
        return True
    return any(code.startswith(p) for p in CUSTOMS_SERVICE_PREFIXES)


def normalize_loai_hinh(value: Optional[str]) -> str:
    """Upper-case, strip whitespace. Returns '' when empty/None."""
    return (value or "").strip().upper()


def is_valid_loai_hinh(value: Optional[str]) -> bool:
    """Check against the whitelist. Unknown codes rejected to avoid typos like 'A1' or 'XX11'."""
    norm = normalize_loai_hinh(value)
    return norm in CUSTOMS_CODE_LABELS


def build_missing_loai_hinh_error(invalid_value: Optional[str] = None) -> Dict:
    """
    Structured error payload for missing/invalid loai_hinh.
    Returned by both REST endpoint validator and service-layer validator so the
    frontend can render suggestion chips uniformly.
    """
    if invalid_value:
        # User/AI provided something, but it's not in the whitelist
        message = (
            f"Mã loại hình '{invalid_value}' không hợp lệ. "
            "Vui lòng dùng một trong các mã chuẩn của Tổng cục Hải quan."
        )
        error_code = "invalid_loai_hinh"
    else:
        message = (
            "Job tờ khai bắt buộc phải có 'Loại hình' (mã loại hình hải quan). "
            "Vui lòng bổ sung trường này — một trong các mã chuẩn dưới đây."
        )
        error_code = "missing_loai_hinh"

    return {
        "success": False,
        "error": error_code,
        "message": message,
        "suggestions": [
            {"code": code, "label": label}
            for code, label in CUSTOMS_CODE_LABELS.items()
        ],
    }


def validate_loai_hinh_for_service(
    service_type_code: Optional[str],
    loai_hinh: Optional[str],
) -> Optional[Dict]:
    """
    Single entry-point validator.

    Returns None when valid (or when the service doesn't require loai_hinh).
    Returns an error dict (same shape as build_missing_loai_hinh_error) otherwise.
    """
    if not is_customs_service(service_type_code):
        return None

    norm = normalize_loai_hinh(loai_hinh)
    if not norm:
        return build_missing_loai_hinh_error(None)
    if not is_valid_loai_hinh(norm):
        return build_missing_loai_hinh_error(norm)
    return None


def format_codes_for_prompt() -> str:
    """Render the code table for inclusion in the AI extraction prompt."""
    lines: List[str] = []
    for code, label in CUSTOMS_CODE_LABELS.items():
        lines.append(f"  * {code}: {label}")
    return "\n".join(lines)
