"""
Smart Service Type Detector
===========================
Analyzes content (file data, text) to determine appropriate service type.

Categories and Service Codes:
- TRUCKING: TRUCKING_DOM (domestic), TRUCKING_LONG
- BORDER: BORDER_IMP (border import by road from China)
- AIR: AIR_IMP, AIR_EXP
- SEA: SEA_IMP, SEA_EXP, SEA_DOM
- WAREHOUSE: WHS_STORAGE, WHS_HANDLE, WHS_VAS
- CUSTOMS: CUS_IMPORT, CUS_EXPORT, CUS_TRANSIT, CUS_CO
- PACKING: SVC_PACK, SVC_FUMI, SVC_VACUUM, SVC_SHRINK, SVC_LASHING_TRUCK, SVC_LASHING_CONT, SVC_LASHING_FR
- CONTAINER: LIFT_ON, LIFT_OFF
- OTHER: SVC_OTHER
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


# Map category to default service_code in DB
CATEGORY_TO_DEFAULT_CODE = {
    "TRUCKING": "TRUCKING_DOM",
    "BORDER": "BORDER_IMP",
    "AIR": "AIR_IMP",
    "SEA": "SEA_IMP",
    "PACKING": "SVC_PACK",
    "WAREHOUSE": "WHS_STORAGE",
    "CUSTOMS": "CUS_IMPORT",
    "CONTAINER": "LIFT_ON",
    "OTHER": "SVC_OTHER",
}

# All valid service codes in DB
VALID_SERVICE_CODES = {
    # Trucking (domestic only)
    "TRUCKING_DOM",
    # Border (cross-border by road)
    "BORDER_IMP",
    # Air freight
    "AIR_IMP", "AIR_EXP",
    # Sea freight
    "SEA_IMP", "SEA_EXP", "SEA_DOM",
    # Warehouse
    "WHS_STORAGE", "WHS_HANDLE", "WHS_VAS",
    # Customs
    "CUS_IMPORT", "CUS_EXPORT", "CUS_TRANSIT", "CUS_CO",
    # Packing
    "SVC_PACK", "SVC_FUMI", "SVC_VACUUM", "SVC_SHRINK",
    "SVC_LASHING", "SVC_LASHING_TRUCK", "SVC_LASHING_CONT", "SVC_LASHING_FR",
    # Container handling
    "LIFT_ON", "LIFT_OFF",
    # Other
    "SVC_OTHER",
    # Legacy codes (mapped to TRUCKING_DOM for backward compatibility)
    "TRUCKING_SHORT", "TRUCKING_LONG", "TRUCKING_CONT",
}

# Keywords and patterns for detecting service categories
CATEGORY_PATTERNS = {
    "PACKING": {
        "keywords": [
            # General packing
            "đóng gói", "dong goi", "packing", "đóng kiện", "dong kien",
            "đóng pallet", "dong pallet", "palletize", "palletizing",
            "đóng hộp", "dong hop", "carton", "đóng thùng", "dong thung",
            "crating", "đóng khung", "wooden case", "thùng gỗ",
            "đóng cont", "đóng container", "stuff", "stuffing",
            # Fumigation
            "fumigation", "hun trùng", "hun trung", "khử trùng",
            # Vacuum
            "hút chân không", "hut chan khong", "vacuum",
            # Shrink wrap
            "màng co", "mang co", "shrink wrap", "shrink", "cuốn màng",
            "bọc màng", "boc mang", "wrap", "wrapping",
            # Lashing
            "chằng buộc", "chang buoc", "lashing", "ràng buộc",
            "neo hàng", "cố định hàng",
            # Excel-specific
            "estimate", "quotation", "debit", "báo giá đóng gói",
            "packing list",
        ],
        "filename_patterns": [
            r"quotation", r"debit", r"estimate", r"packing",
            r"đóng\s*gói", r"dong\s*goi",
        ],
        "sheet_names": ["debit", "estimate", "packing", "quotation"],
        "weight": 1.0,
    },
    "CONTAINER": {
        "keywords": [
            # Container
            "lift on", "lift off", "nâng cont", "hạ cont",
            "nâng container", "hạ container", "lifting",
            "cẩu cont", "cau cont", "crane",
            # Cargo items (kiện hàng)
            "nâng hàng", "hạ hàng", "nang hang", "ha hang",
            "nâng kiện", "hạ kiện", "nâng máy", "hạ máy",
            "cẩu hàng", "cau hang", "cẩu kiện",
        ],
        "weight": 0.95,
    },
    "WAREHOUSE": {
        "keywords": [
            "lưu kho", "luu kho", "storage", "gửi kho", "gui kho",
            "nhập kho", "nhap kho", "xuất kho", "xuat kho",
            "tồn kho", "ton kho", "inventory", "warehousing",
            "thuê kho", "thue kho", "rent warehouse",
            "bảo quản", "bao quan", "lưu trữ", "luu tru",
            "bốc xếp", "boc xep", "loading", "unloading",
            "xếp dỡ", "xep do", "handling", "nâng hạ", "nang ha",
            "forklift", "xe nâng", "xe nang",
        ],
        "filename_patterns": [
            r"storage", r"warehouse", r"kho", r"lưu\s*kho",
            r"handling", r"bốc\s*xếp",
        ],
        "weight": 0.9,
    },
    "CUSTOMS": {
        "keywords": [
            # General customs
            "hải quan", "hai quan", "customs", "thông quan", "thong quan",
            "khai báo", "khai bao", "declaration", "tờ khai", "to khai",
            "clearance", "giải phóng hàng",
            # Import
            "nhập khẩu", "nhap khau", "import", "thủ tục nhập",
            # Export
            "xuất khẩu", "xuat khau", "export", "thủ tục xuất",
            # C/O
            "c/o", "co", "certificate of origin", "chứng nhận xuất xứ",
            "giấy chứng nhận", "form e", "form d", "form ak",
        ],
        "filename_patterns": [
            r"customs", r"hải\s*quan", r"clearance",
            r"export", r"import", r"c[/\-]?o",
        ],
        "weight": 0.95,
    },
    "TRUCKING": {
        "keywords": [
            # General trucking
            "vận chuyển", "van chuyen", "trucking", "transport",
            "giao hàng", "giao hang", "delivery",
            "xe tải", "xe tai", "truck",
            "book xe", "đặt xe", "dat xe", "điều xe", "dieu xe",
            "pickup", "lấy hàng", "lay hang", "nhận hàng", "nhan hang",
            # Domestic/Short-haul
            "nội thành", "noi thanh", "nội địa", "noi dia",
            # Long-haul
            "liên tỉnh", "lien tinh", "đường dài", "duong dai",
        ],
        "filename_patterns": [
            r"book\s*xe", r"booking", r"phiếu\s*book",
            r"trucking", r"delivery",
        ],
        "weight": 0.5,  # Lower weight - default fallback
    },
    "BORDER": {
        "keywords": [
            # Border/cross-border transport
            "nhập khẩu đường bộ", "nhap khau duong bo",
            "biên giới", "bien gioi", "border",
            "cửa khẩu", "cua khau", "biên mậu", "bien mau",
            "sang tải", "sang tai", "transload",
            "xe trung quốc", "xe tq", "biển số tq",
            "china truck", "xe trung", "hữu nghị", "huu nghi",
            "tân thanh", "tan thanh", "lạng sơn", "lang son",
            "móng cái", "mong cai", "lào cai", "lao cai",
        ],
        "filename_patterns": [
            r"border", r"biên\s*giới", r"cửa\s*khẩu",
            r"bảng\s*kê\s*im", r"bang\s*ke\s*im",
        ],
        "sheet_names": ["bảng kê im", "border", "im"],
        "weight": 1.0,
    },
    "AIR": {
        "keywords": [
            # Air freight
            "hàng không", "hang khong", "air", "airfreight",
            "máy bay", "may bay", "flight", "airline",
            "awb", "air waybill", "mawb", "hawb",
            "sân bay", "san bay", "airport",
            "tân sơn nhất", "tan son nhat", "nội bài", "noi bai",
        ],
        "filename_patterns": [
            r"air", r"hàng\s*không", r"awb",
        ],
        "weight": 1.0,
    },
    "SEA": {
        "keywords": [
            # Sea freight
            "đường biển", "duong bien", "sea", "seafreight", "ocean",
            "container", "cont 20", "cont 40", "cont20", "cont40",
            "fcl", "lcl", "full container",
            "cảng", "cang", "port", "tàu", "tau", "vessel", "ship",
            "b/l", "bill of lading", "vận đơn", "van don",
            "cát lái", "cat lai", "hải phòng", "hai phong",
        ],
        "filename_patterns": [
            r"sea", r"ocean", r"đường\s*biển", r"container",
        ],
        "weight": 0.95,
    },
}

# Sub-type patterns for specific service detection
SPECIFIC_SERVICE_PATTERNS = {
    # Customs sub-types
    "CUS_IMPORT": ["nhập khẩu", "nhap khau", "import", "thủ tục nhập"],
    "CUS_EXPORT": ["xuất khẩu", "xuat khau", "export", "thủ tục xuất"],
    "CUS_CO": ["c/o", "certificate of origin", "chứng nhận xuất xứ", "form e", "form d", "form ak"],

    # Packing sub-types
    "SVC_FUMI": ["fumigation", "hun trùng", "hun trung", "khử trùng", "diệt côn trùng"],
    "SVC_VACUUM": ["vacuum", "hút chân không", "hut chan khong", "chân không"],
    "SVC_SHRINK": ["shrink", "màng co", "mang co", "cuốn màng", "bọc màng"],
    "SVC_LASHING_TRUCK": ["lashing xe", "chằng buộc xe tải", "chang buoc xe"],
    "SVC_LASHING_CONT": ["lashing cont", "chằng buộc container", "chang buoc cont"],
    "SVC_LASHING_FR": ["lashing flatrack", "chằng buộc flatrack", "flat rack", "flatrack", "fr"],

    # Container/Cargo handling
    "LIFT_ON": ["lift on", "nâng cont", "nâng container", "cẩu lên", "nâng hàng", "nâng kiện", "nâng máy"],
    "LIFT_OFF": ["lift off", "hạ cont", "hạ container", "cẩu xuống", "hạ hàng", "hạ kiện", "hạ máy"],

    # Air freight sub-types
    "AIR_IMP": ["air import", "nhập hàng không", "nhap hang khong"],
    "AIR_EXP": ["air export", "xuất hàng không", "xuat hang khong"],

    # Sea freight sub-types
    "SEA_IMP": ["sea import", "nhập đường biển", "nhap duong bien"],
    "SEA_EXP": ["sea export", "xuất đường biển", "xuat duong bien"],
    "SEA_DOM": ["sea domestic", "đường biển nội địa", "duong bien noi dia", "vận tải biển nội địa", "coastal", "ven biển", "nội địa đường biển"],
}


def detect_service_type(
    content: Dict[str, Any] = None,
    text: str = None,
    filename: str = None,
    sheet_names: List[str] = None,
) -> Tuple[str, float, str]:
    """
    Detect service type from various inputs.

    Returns:
        Tuple of (service_code, confidence, reason)
    """
    scores = {cat: 0.0 for cat in CATEGORY_PATTERNS.keys()}
    reasons = {cat: [] for cat in CATEGORY_PATTERNS.keys()}
    specific_matches = {}

    # 1. Check content dict for explicit service_type
    if content:
        if explicit_type := content.get("service_type"):
            normalized = normalize_service_code(explicit_type)
            logger.info(f"[ServiceDetector] Explicit service_type: {explicit_type} → {normalized}")
            return (normalized, 1.0, "Explicit in parsed content")

        # Check content type field
        if content_type := content.get("type"):
            if "quotation" in content_type.lower() or "packing" in content_type.lower():
                scores["PACKING"] += 0.8
                reasons["PACKING"].append(f"Content type: {content_type}")

    # 2. Check filename
    if filename:
        filename_lower = filename.lower()
        for cat, patterns in CATEGORY_PATTERNS.items():
            for pattern in patterns.get("filename_patterns", []):
                if re.search(pattern, filename_lower, re.IGNORECASE):
                    scores[cat] += 0.5
                    reasons[cat].append(f"Filename: {pattern}")

    # 3. Check sheet names
    if sheet_names:
        sheet_names_lower = [s.lower() for s in sheet_names]
        for cat, patterns in CATEGORY_PATTERNS.items():
            for expected_sheet in patterns.get("sheet_names", []):
                if expected_sheet.lower() in sheet_names_lower:
                    scores[cat] += 0.4
                    reasons[cat].append(f"Sheet: {expected_sheet}")

    # 4. Check text content for category keywords
    if text:
        text_lower = text.lower()
        for cat, patterns in CATEGORY_PATTERNS.items():
            for kw in patterns.get("keywords", []):
                if kw.lower() in text_lower:
                    scores[cat] += 0.15
                    if len(reasons[cat]) < 5:
                        reasons[cat].append(f"Keyword: {kw}")

        # Also check for specific service patterns
        for svc_code, patterns in SPECIFIC_SERVICE_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    specific_matches[svc_code] = specific_matches.get(svc_code, 0) + 1

    # Apply weights
    for cat in scores:
        scores[cat] *= CATEGORY_PATTERNS[cat].get("weight", 1.0)

    # Find best category
    best_cat = max(scores, key=scores.get)
    best_score = scores[best_cat]

    # Default to TRUCKING if no strong signal
    # Threshold lowered to 0.1 to catch single keyword matches
    if best_score < 0.1:
        logger.info("[ServiceDetector] No strong signal, defaulting to TRUCKING")
        return ("TRUCKING_SHORT", 0.5, "Mặc định - vận chuyển")

    # Determine specific service code within category
    service_code = _get_specific_code(best_cat, specific_matches, text)

    # Calculate confidence
    confidence = min(1.0, best_score / 1.5)
    reason = "; ".join(reasons[best_cat][:3]) if reasons[best_cat] else "Pattern matching"

    logger.info(f"[ServiceDetector] Detected: {best_cat} → {service_code} (confidence: {confidence:.2f})")

    return (service_code, confidence, reason)


def _get_specific_code(category: str, specific_matches: dict, text: str = None) -> str:
    """Get the most specific service code within a category based on matches."""

    # Map category to its possible specific codes
    category_codes = {
        "CUSTOMS": ["CUS_CO", "CUS_EXPORT", "CUS_IMPORT"],
        "PACKING": ["SVC_FUMI", "SVC_VACUUM", "SVC_SHRINK", "SVC_LASHING_FR", "SVC_LASHING_CONT", "SVC_LASHING_TRUCK", "SVC_PACK"],
        "CONTAINER": ["LIFT_OFF", "LIFT_ON"],
        "TRUCKING": ["TRUCKING_DOM"],
        "BORDER": ["BORDER_IMP"],
        "AIR": ["AIR_EXP", "AIR_IMP"],
        "SEA": ["SEA_DOM", "SEA_EXP", "SEA_IMP"],
        "WAREHOUSE": ["WHS_HANDLE", "WHS_STORAGE"],
    }

    codes = category_codes.get(category, [])

    # Find best matching specific code
    best_code = None
    best_count = 0

    for code in codes:
        if code in specific_matches and specific_matches[code] > best_count:
            best_code = code
            best_count = specific_matches[code]

    if best_code:
        return best_code

    # Return default for category
    return CATEGORY_TO_DEFAULT_CODE.get(category, "TRUCKING_SHORT")


def detect_from_excel_data(
    parsed_data: Dict[str, Any],
    filename: str = None,
    sheet_names: List[str] = None,
) -> Dict[str, Any]:
    """
    Detect service type from Excel parser output.

    Returns:
        Dict with service_type, confidence, reason
    """
    # Build text from parsed data
    text_parts = []

    if notes := parsed_data.get("notes"):
        text_parts.append(notes)
    if cargo := parsed_data.get("cargo_type"):
        text_parts.append(cargo)
    if desc := parsed_data.get("description"):
        text_parts.append(desc)

    for addr_key in ["pickup_address", "delivery_address", "origin_address", "dest_address"]:
        if addr := parsed_data.get(addr_key):
            text_parts.append(addr)

    text = " ".join(text_parts)

    service_code, confidence, reason = detect_service_type(
        content=parsed_data,
        text=text,
        filename=filename,
        sheet_names=sheet_names,
    )

    return {
        "service_type": service_code,
        "confidence": confidence,
        "reason": reason,
    }


def normalize_service_code(code: str) -> str:
    """
    Normalize any service type input to a valid DB service_code.

    Handles:
    - Valid codes (pass through)
    - Category names → default codes
    - Legacy/alias codes → valid codes
    """
    if not code:
        return "TRUCKING_DOM"

    code_upper = code.upper().strip()

    # Direct valid codes - pass through
    if code_upper in VALID_SERVICE_CODES:
        # Map legacy codes to TRUCKING_DOM
        if code_upper in ("TRUCKING_SHORT", "TRUCKING_LONG", "TRUCKING_CONT"):
            return "TRUCKING_DOM"
        return code_upper

    # Category names → default codes
    if code_upper in CATEGORY_TO_DEFAULT_CODE:
        return CATEGORY_TO_DEFAULT_CODE[code_upper]

    # Legacy/alias mapping
    legacy = {
        # Packing aliases
        "PACKING": "SVC_PACK",
        "PACK": "SVC_PACK",
        "ĐÓNG GÓI": "SVC_PACK",
        "FUMIGATION": "SVC_FUMI",
        "FUMI": "SVC_FUMI",
        "HUN TRÙNG": "SVC_FUMI",
        "VACUUM": "SVC_VACUUM",
        "HÚT CHÂN KHÔNG": "SVC_VACUUM",
        "SHRINK": "SVC_SHRINK",
        "SHRINK_WRAP": "SVC_SHRINK",
        "MÀNG CO": "SVC_SHRINK",
        "LASHING": "SVC_LASHING_TRUCK",
        "CHẰNG BUỘC": "SVC_LASHING_TRUCK",

        # Customs aliases
        "CUSTOMS": "CUS_IMPORT",
        "HẢI QUAN": "CUS_IMPORT",
        "IMPORT": "CUS_IMPORT",
        "NHẬP KHẨU": "CUS_IMPORT",
        "EXPORT": "CUS_EXPORT",
        "XUẤT KHẨU": "CUS_EXPORT",
        "CO": "CUS_CO",
        "C/O": "CUS_CO",

        # Warehouse aliases
        "WAREHOUSE": "WHS_STORAGE",
        "STORAGE": "WHS_STORAGE",
        "LƯU KHO": "WHS_STORAGE",
        "HANDLING": "WHS_HANDLE",
        "BỐC XẾP": "WHS_HANDLE",

        # Container handling aliases
        "LIFT": "LIFT_ON",
        "LIFTON": "LIFT_ON",
        "LIFT_ON": "LIFT_ON",
        "LIFTOFF": "LIFT_OFF",
        "LIFT_OFF": "LIFT_OFF",

        # Trucking aliases - all map to TRUCKING_DOM
        "TRUCKING": "TRUCKING_DOM",
        "TRUCK": "TRUCKING_DOM",
        "DELIVERY": "TRUCKING_DOM",
        "TRANSPORT": "TRUCKING_DOM",
        "VẬN CHUYỂN": "TRUCKING_DOM",
        "GIAO HÀNG": "TRUCKING_DOM",
        "NỘI ĐỊA": "TRUCKING_DOM",
        "LIÊN TỈNH": "TRUCKING_DOM",
        "ĐƯỜNG DÀI": "TRUCKING_DOM",
        "TRUCKING_SHORT": "TRUCKING_DOM",
        "TRUCKING_LONG": "TRUCKING_DOM",

        # Border aliases
        "BORDER": "BORDER_IMP",
        "BIÊN GIỚI": "BORDER_IMP",
        "CỬA KHẨU": "BORDER_IMP",
        "NHẬP KHẨU ĐƯỜNG BỘ": "BORDER_IMP",

        # Air freight aliases
        "AIR": "AIR_IMP",
        "HÀNG KHÔNG": "AIR_IMP",
        "AIR FREIGHT": "AIR_IMP",
        "AIRFREIGHT": "AIR_IMP",

        # Sea freight aliases
        "SEA": "SEA_IMP",
        "ĐƯỜNG BIỂN": "SEA_IMP",
        "SEA FREIGHT": "SEA_IMP",
        "SEAFREIGHT": "SEA_IMP",
        "CONTAINER": "SEA_IMP",
        "TRUCKING_CONT": "SEA_IMP",
    }

    return legacy.get(code_upper, "TRUCKING_DOM")


def simplify_service_code(code: str) -> str:
    """
    Simplify service code for display purposes.
    TRUCKING_DOM/TRUCKING_LONG → TRUCKING
    SVC_PACK/SVC_FUMI → PACKING
    etc.
    """
    if not code:
        return "TRUCKING"

    code_upper = code.upper().strip()

    # Map detailed codes to simple display names
    display_map = {
        # Trucking (all legacy codes map to TRUCKING)
        "TRUCKING_DOM": "TRUCKING",
        "TRUCKING_SHORT": "TRUCKING",  # Legacy
        "TRUCKING_LONG": "TRUCKING",   # Legacy
        "TRUCKING_CONT": "TRUCKING",   # Legacy
        # Border
        "BORDER_IMP": "BORDER_IMPORT",
        # Air freight
        "AIR_IMP": "AIR_IMPORT",
        "AIR_EXP": "AIR_EXPORT",
        # Sea freight
        "SEA_IMP": "SEA_IMPORT",
        "SEA_EXP": "SEA_EXPORT",
        "SEA_DOM": "SEA_DOMESTIC",
        # Packing
        "SVC_PACK": "PACKING",
        "SVC_FUMI": "FUMIGATION",
        "SVC_VACUUM": "VACUUM",
        "SVC_SHRINK": "SHRINK_WRAP",
        "SVC_LASHING": "LASHING",
        "SVC_LASHING_TRUCK": "LASHING",
        "SVC_LASHING_CONT": "LASHING",
        "SVC_LASHING_FR": "LASHING",
        # Warehouse
        "WHS_STORAGE": "WAREHOUSE",
        "WHS_HANDLE": "HANDLING",
        "WHS_VAS": "VAS",
        # Customs
        "CUS_IMPORT": "CUSTOMS_IMPORT",
        "CUS_EXPORT": "CUSTOMS_EXPORT",
        "CUS_TRANSIT": "CUSTOMS_TRANSIT",
        "CUS_CO": "C/O",
        # Container
        "LIFT_ON": "LIFT_ON",
        "LIFT_OFF": "LIFT_OFF",
        # Other
        "SVC_OTHER": "OTHER",
    }

    return display_map.get(code_upper, code_upper)


def get_all_service_codes() -> List[str]:
    """Return all valid service codes."""
    return list(VALID_SERVICE_CODES)


def get_category_for_code(code: str) -> Optional[str]:
    """Get the category for a service code."""
    code_upper = code.upper().strip()

    code_to_category = {
        # Trucking (all legacy codes map to TRUCKING category)
        "TRUCKING_DOM": "TRUCKING",
        "TRUCKING_SHORT": "TRUCKING",  # Legacy
        "TRUCKING_LONG": "TRUCKING",   # Legacy
        "TRUCKING_CONT": "TRUCKING",   # Legacy
        # Border
        "BORDER_IMP": "BORDER",
        # Air freight
        "AIR_IMP": "AIR",
        "AIR_EXP": "AIR",
        # Sea freight
        "SEA_IMP": "SEA",
        "SEA_EXP": "SEA",
        "SEA_DOM": "SEA",
        # Warehouse
        "WHS_STORAGE": "WAREHOUSE",
        "WHS_HANDLE": "WAREHOUSE",
        "WHS_VAS": "WAREHOUSE",
        # Customs
        "CUS_IMPORT": "CUSTOMS",
        "CUS_EXPORT": "CUSTOMS",
        "CUS_TRANSIT": "CUSTOMS",
        "CUS_CO": "CUSTOMS",
        # Packing
        "SVC_PACK": "PACKING",
        "SVC_FUMI": "PACKING",
        "SVC_VACUUM": "PACKING",
        "SVC_SHRINK": "PACKING",
        "SVC_LASHING": "PACKING",
        "SVC_LASHING_TRUCK": "PACKING",
        "SVC_LASHING_CONT": "PACKING",
        "SVC_LASHING_FR": "PACKING",
        # Container
        "LIFT_ON": "CONTAINER",
        "LIFT_OFF": "CONTAINER",
        # Other
        "SVC_OTHER": "OTHER",
    }

    return code_to_category.get(code_upper)
