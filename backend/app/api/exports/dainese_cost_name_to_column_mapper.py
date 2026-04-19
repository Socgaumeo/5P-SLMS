"""
Maps DAINESE `job_costs.cost_name` strings to Bảng kê column keys.

The mapping is fuzzy (case-insensitive substring) because cost names entered
in the UI are free-text. Patterns ordered specific-first.

Output keys correspond to columns in the SEA/AIR import statement:
  K=phi_mtk, L=phi_kh, M=phi_vc, N=phi_lh, O=phi_psk,
  P=phi_dnn, Q=cuoc_qt, R=thc, S=cfs, T=do, U=dly      (own services)
  W=local, X=csht, Y=kho                                (reimbursable)

Anything unmatched falls back to:
  - 'phi_psk' (Phí phát sinh khác) for own services
  - 'kho'     (Lưu kho) for reimbursable rows
"""

import re
from typing import Dict, List, Optional


# Substring patterns → column key. First match wins.
# Use lowercase with diacritics removed in matching.
_PATTERNS_OWN: List[tuple[str, str]] = [
    # Customs declaration fee (very specific first to avoid catching "phí" only)
    (r"(mở|mo) (tờ|to) khai", "phi_mtk"),
    (r"kiểm hóa|kiem hoa", "phi_kh"),
    # International freight (must come BEFORE "vận chuyển" since it contains it)
    (r"cước (vận|van) tải quốc tế|cuoc van tai quoc te|international freight", "cuoc_qt"),
    # THC (handling/loading at port)
    (r"\bthc\b|xếp dỡ|xep do", "thc"),
    # CFS / CIC / LSS (consolidation/origin charges)
    (r"\bcfs\b|cic|lss|gom hàng|gom hang", "cfs"),
    # D/O (delivery order)
    (r"d/?o\b|lấy lệnh|lay lenh|delivery order", "do"),
    # Foreign-end fee
    (r"đầu nước ngoài|dau nuoc ngoai|overseas fee", "phi_dnn"),
    # Handling fee at our side
    (r"làm hàng|lam hang|handling", "phi_lh"),
    # Agency fee
    (r"đại lý|dai ly|agency", "dly"),
    # Local trucking / local transport (FALLBACK for trucking inland)
    (r"vận chuyển|van chuyen|truck|cước|cuoc", "phi_vc"),
    # Surcharges (fuel etc) → "phát sinh"
    (r"phụ phí|phu phi|surcharge|phát sinh|phat sinh|xăng|xang", "phi_psk"),
]

_PATTERNS_REIMBURSE: List[tuple[str, str]] = [
    (r"local charge|\blcc\b", "local"),
    (r"csht|cơ sở hạ tầng|co so ha tang|thuế|thue|vé bãi|ve bai", "csht"),
    (r"lưu kho|luu kho|hạ hàng|ha hang|nâng vỏ|nang vo|bốc xếp|boc xep|nâng hạ|nang ha|storage|warehouse", "kho"),
    # "Thu hộ" entries → CSHT bucket (legal/customs fees)
    (r"thu hộ|thu ho|lệ phí hải quan|le phi hai quan|biên lai|bien lai", "csht"),
]


def _norm(s: str) -> str:
    """Lowercase + collapse whitespace. Diacritics kept (regex handles both forms)."""
    return re.sub(r"\s+", " ", s.lower().strip())


def map_cost_name_to_column(cost_name: str, is_reimbursement: bool) -> str:
    """Return the column key (e.g. 'phi_mtk') for one job_costs row."""
    if not cost_name:
        return "kho" if is_reimbursement else "phi_psk"
    norm = _norm(cost_name)
    patterns = _PATTERNS_REIMBURSE if is_reimbursement else _PATTERNS_OWN
    for pat, key in patterns:
        if re.search(pat, norm):
            return key
    # Fallback bucket
    return "kho" if is_reimbursement else "phi_psk"


def aggregate_costs_into_columns(cost_rows: List[Dict]) -> Dict[str, float]:
    """
    Sum selling_amount per column key for one service's cost rows.
    Returns dict {column_key: total_amount, 'vat_total': ..., 'total_with_vat': ...}.
    """
    out: Dict[str, float] = {
        "phi_mtk": 0.0, "phi_kh": 0.0, "phi_vc": 0.0, "phi_lh": 0.0, "phi_psk": 0.0,
        "phi_dnn": 0.0, "cuoc_qt": 0.0, "thc": 0.0, "cfs": 0.0, "do": 0.0, "dly": 0.0,
        "local": 0.0, "csht": 0.0, "kho": 0.0,
        "vat_total": 0.0, "subtotal_own": 0.0, "subtotal_reimburse": 0.0,
    }
    for row in cost_rows:
        amount = float(row.get("selling_amount") or 0)
        if amount == 0:
            continue
        is_reim = bool(row.get("is_reimbursement"))
        key = map_cost_name_to_column(row.get("cost_name", ""), is_reim)
        out[key] = out.get(key, 0.0) + amount
        if is_reim:
            out["subtotal_reimburse"] += amount
        else:
            out["subtotal_own"] += amount
        # Accumulate VAT (only on own/non-reimbursement rows usually)
        vat_rate = float(row.get("vat_rate") or 0)
        if vat_rate and not is_reim:
            out["vat_total"] += amount * (vat_rate / 100.0)
    return out
