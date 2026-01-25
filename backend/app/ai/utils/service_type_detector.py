"""
Smart Service Type Detector
===========================
Analyzes content (file data, text) to determine appropriate service type.

Service Codes (matching master_service_types table):
- TRUCKING_SHORT: Vận chuyển nội thành
- TRUCKING_LONG: Vận chuyển liên tỉnh
- TRUCKING_CONT: Vận chuyển container
- WHS_STORAGE: Lưu kho
- WHS_HANDLE: Bốc xếp
- WHS_VAS: Dịch vụ giá trị gia tăng
- CUS_IMPORT: Thủ tục nhập khẩu
- CUS_EXPORT: Thủ tục xuất khẩu
- CUS_TRANSIT: Quá cảnh
- SVC_PACK: Đóng gói
- SVC_VACUUM: Hút chân không
- SVC_LASHING: Chằng buộc
- SVC_FUMI: Hun trùng
- SVC_OTHER: Dịch vụ khác
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


# Keywords and patterns for each service type
# Keys must match service_code in master_service_types table
SERVICE_PATTERNS = {
    "SVC_PACK": {  # Đóng gói - main packing service
        "keywords": [
            # Vietnamese
            "đóng gói", "dong goi", "packing", "đóng kiện", "dong kien",
            "đóng pallet", "dong pallet", "palletize", "palletizing",
            "đóng hộp", "dong hop", "carton", "đóng thùng", "dong thung",
            "bọc màng", "boc mang", "shrink wrap", "wrap", "wrapping",
            "đóng cont", "đóng container", "stuff", "stuffing",
            "crating", "đóng khung", "wooden case", "thùng gỗ",
            # Excel-specific
            "estimate", "quotation", "debit", "báo giá đóng gói",
            "packing list", "danh sách đóng gói",
        ],
        "filename_patterns": [
            r"quotation", r"debit", r"estimate", r"packing",
            r"đóng\s*gói", r"dong\s*goi",
        ],
        "sheet_names": ["debit", "estimate", "packing", "quotation"],
        "weight": 1.0,
    },
    "SVC_FUMI": {  # Hun trùng
        "keywords": [
            "fumigation", "hun trùng", "hun trung", "khử trùng", "khu trung",
            "diệt côn trùng", "diet con trung", "phun thuốc",
        ],
        "weight": 0.95,
    },
    "SVC_VACUUM": {  # Hút chân không
        "keywords": [
            "hút chân không", "hut chan khong", "vacuum", "vacuum pack",
            "chân không", "chan khong",
        ],
        "weight": 0.9,
    },
    "SVC_LASHING": {  # Chằng buộc
        "keywords": [
            "chằng buộc", "chang buoc", "lashing", "ràng buộc", "rang buoc",
            "neo hàng", "neo hang", "cố định", "co dinh",
        ],
        "weight": 0.9,
    },
    "WHS_STORAGE": {  # Lưu kho
        "keywords": [
            "lưu kho", "luu kho", "storage", "gửi kho", "gui kho",
            "nhập kho", "nhap kho", "xuất kho", "xuat kho",
            "tồn kho", "ton kho", "inventory", "warehousing",
            "thuê kho", "thue kho", "rent warehouse",
            "bảo quản", "bao quan", "lưu trữ", "luu tru",
        ],
        "filename_patterns": [
            r"storage", r"warehouse", r"kho", r"lưu\s*kho", r"luu\s*kho",
        ],
        "weight": 0.9,
    },
    "WHS_HANDLE": {  # Bốc xếp
        "keywords": [
            "bốc xếp", "boc xep", "loading", "unloading",
            "xếp dỡ", "xep do", "handling", "nâng hạ", "nang ha",
            "forklift", "xe nâng", "xe nang", "bốc vác", "boc vac",
            "dỡ hàng", "do hang", "chất hàng", "chat hang",
        ],
        "filename_patterns": [
            r"handling", r"bốc\s*xếp", r"boc\s*xep",
        ],
        "weight": 0.85,
    },
    "CUS_EXPORT": {  # Thủ tục xuất khẩu
        "keywords": [
            "xuất khẩu", "xuat khau", "export", "thủ tục xuất",
            "khai báo xuất", "customs export",
        ],
        "filename_patterns": [
            r"export", r"xuất\s*khẩu", r"xuat\s*khau",
        ],
        "weight": 0.95,
    },
    "CUS_IMPORT": {  # Thủ tục nhập khẩu
        "keywords": [
            "nhập khẩu", "nhap khau", "import", "thủ tục nhập",
            "khai báo nhập", "customs import",
            "hải quan", "hai quan", "customs", "thông quan", "thong quan",
            "khai báo", "khai bao", "declaration", "tờ khai", "to khai",
            "clearance", "giải phóng", "giai phong",
        ],
        "filename_patterns": [
            r"customs", r"hải\s*quan", r"hai\s*quan", r"clearance",
            r"import", r"nhập\s*khẩu", r"nhap\s*khau",
        ],
        "weight": 0.95,
    },
    "TRUCKING_CONT": {  # Vận chuyển container
        "keywords": [
            "container", "cont 20", "cont 40", "cont20", "cont40",
            "fcl", "lcl", "full container", "vận chuyển container",
        ],
        "filename_patterns": [
            r"container", r"cont\d+",
        ],
        "weight": 0.85,
    },
    "TRUCKING_LONG": {  # Vận chuyển liên tỉnh
        "keywords": [
            "liên tỉnh", "lien tinh", "long haul", "đường dài", "duong dai",
            # Province names (long distance indicators)
            "hà nội", "ha noi", "hải phòng", "hai phong", "đà nẵng", "da nang",
            "hồ chí minh", "ho chi minh", "hcm", "sài gòn", "sai gon",
            "bình dương", "binh duong", "đồng nai", "dong nai",
            "cần thơ", "can tho", "vũng tàu", "vung tau",
        ],
        "route_patterns": [
            r"(hà nội|hn).*(hcm|sài gòn|sai gon)",
            r"(hcm|sài gòn|sai gon).*(hà nội|hn)",
            r"(bình dương|binh duong).*(hà nội|hn)",
            r"liên\s*tỉnh",
        ],
        "weight": 0.8,
    },
    "TRUCKING_SHORT": {  # Vận chuyển nội thành - DEFAULT
        "keywords": [
            "nội thành", "noi thanh", "nội địa", "noi dia",
            "giao hàng", "giao hang", "delivery", "vận chuyển", "van chuyen",
            "xe tải", "xe tai", "truck", "trucking",
            "book xe", "đặt xe", "dat xe", "điều xe", "dieu xe",
            "pickup", "lấy hàng", "lay hang", "nhận hàng", "nhan hang",
        ],
        "filename_patterns": [
            r"book\s*xe", r"booking", r"phiếu\s*book",
        ],
        "weight": 0.5,  # Lower weight - this is the default fallback
    },
}


def detect_service_type(
    content: Dict[str, Any] = None,
    text: str = None,
    filename: str = None,
    sheet_names: List[str] = None,
) -> Tuple[str, float, str]:
    """
    Detect service type from various inputs.

    Args:
        content: Parsed content from file (booking_form_parser or quotation_parser)
        text: Raw text input
        filename: Original filename
        sheet_names: List of sheet names in Excel file

    Returns:
        Tuple of (service_type, confidence, reason)
    """
    scores = {stype: 0.0 for stype in SERVICE_PATTERNS.keys()}
    reasons = {stype: [] for stype in SERVICE_PATTERNS.keys()}

    # 1. Check content dict for explicit service_type
    if content:
        if explicit_type := content.get("service_type"):
            if explicit_type in SERVICE_PATTERNS:
                logger.info(f"[ServiceDetector] Explicit service_type in content: {explicit_type}")
                return (explicit_type, 1.0, "Explicit in parsed content")

        # Check content type field
        if content_type := content.get("type"):
            if "quotation" in content_type.lower() or "packing" in content_type.lower():
                scores["PACKING"] += 0.8
                reasons["PACKING"].append(f"Content type: {content_type}")

        # Check items for packing-related fields
        items = content.get("items", [])
        for item in items[:5]:  # Check first 5 items
            item_str = str(item).lower()
            for stype, patterns in SERVICE_PATTERNS.items():
                for kw in patterns.get("keywords", [])[:10]:  # Check top 10 keywords
                    if kw.lower() in item_str:
                        scores[stype] += 0.1
                        if len(reasons[stype]) < 3:
                            reasons[stype].append(f"Item contains '{kw}'")

    # 2. Check filename
    if filename:
        filename_lower = filename.lower()
        for stype, patterns in SERVICE_PATTERNS.items():
            for pattern in patterns.get("filename_patterns", []):
                if re.search(pattern, filename_lower, re.IGNORECASE):
                    scores[stype] += 0.5
                    reasons[stype].append(f"Filename matches '{pattern}'")

    # 3. Check sheet names
    if sheet_names:
        sheet_names_lower = [s.lower() for s in sheet_names]
        for stype, patterns in SERVICE_PATTERNS.items():
            for expected_sheet in patterns.get("sheet_names", []):
                if expected_sheet.lower() in sheet_names_lower:
                    scores[stype] += 0.4
                    reasons[stype].append(f"Sheet name: {expected_sheet}")

    # 4. Check text content
    if text:
        text_lower = text.lower()
        for stype, patterns in SERVICE_PATTERNS.items():
            # Check keywords
            for kw in patterns.get("keywords", []):
                if kw.lower() in text_lower:
                    scores[stype] += 0.15
                    if len(reasons[stype]) < 5:
                        reasons[stype].append(f"Keyword: {kw}")

            # Check route patterns for trucking
            for route_pattern in patterns.get("route_patterns", []):
                if re.search(route_pattern, text_lower, re.IGNORECASE):
                    scores[stype] += 0.3
                    reasons[stype].append(f"Route pattern matched")

    # Apply weights
    for stype in scores:
        scores[stype] *= SERVICE_PATTERNS[stype].get("weight", 1.0)

    # Find best match
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    # Default to TRUCKING_SHORT if no strong signal
    if best_score < 0.2:
        logger.info("[ServiceDetector] No strong signal, defaulting to TRUCKING_SHORT")
        return ("TRUCKING_SHORT", 0.5, "Mặc định - không tìm thấy dấu hiệu dịch vụ cụ thể")

    # Calculate confidence (normalize score)
    confidence = min(1.0, best_score / 1.5)
    reason = "; ".join(reasons[best_type][:3]) if reasons[best_type] else "Pattern matching"

    logger.info(f"[ServiceDetector] Detected: {best_type} (confidence: {confidence:.2f}, reason: {reason})")

    return (best_type, confidence, reason)


def detect_from_excel_data(
    parsed_data: Dict[str, Any],
    filename: str = None,
    sheet_names: List[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to detect service type from Excel parser output.

    Args:
        parsed_data: Output from booking_form_parser or quotation_parser
        filename: Original filename
        sheet_names: List of sheet names

    Returns:
        Dict with service_type, confidence, reason
    """
    # Build text from parsed data for additional analysis
    text_parts = []

    if notes := parsed_data.get("notes"):
        text_parts.append(notes)
    if cargo := parsed_data.get("cargo_type"):
        text_parts.append(cargo)
    if desc := parsed_data.get("description"):
        text_parts.append(desc)

    # Add addresses
    for addr_key in ["pickup_address", "delivery_address", "origin_address", "dest_address"]:
        if addr := parsed_data.get(addr_key):
            text_parts.append(addr)

    text = " ".join(text_parts)

    service_type, confidence, reason = detect_service_type(
        content=parsed_data,
        text=text,
        filename=filename,
        sheet_names=sheet_names,
    )

    return {
        "service_type": service_type,
        "confidence": confidence,
        "reason": reason,
    }


def suggest_service_types(
    content: Dict[str, Any] = None,
    text: str = None,
    filename: str = None,
    top_n: int = 3,
) -> List[Dict[str, Any]]:
    """
    Suggest multiple possible service types with confidence scores.

    Returns:
        List of dicts with service_type, confidence, reason (sorted by confidence)
    """
    scores = {stype: 0.0 for stype in SERVICE_PATTERNS.keys()}
    reasons = {stype: [] for stype in SERVICE_PATTERNS.keys()}

    # Run detection logic (same as detect_service_type)
    if filename:
        filename_lower = filename.lower()
        for stype, patterns in SERVICE_PATTERNS.items():
            for pattern in patterns.get("filename_patterns", []):
                if re.search(pattern, filename_lower, re.IGNORECASE):
                    scores[stype] += 0.5
                    reasons[stype].append(f"Filename: {pattern}")

    if text:
        text_lower = text.lower()
        for stype, patterns in SERVICE_PATTERNS.items():
            for kw in patterns.get("keywords", []):
                if kw.lower() in text_lower:
                    scores[stype] += 0.15
                    if len(reasons[stype]) < 3:
                        reasons[stype].append(f"Keyword: {kw}")

    if content:
        if content_type := content.get("type"):
            if "quotation" in content_type.lower():
                scores["SVC_PACK"] += 0.8
                reasons["SVC_PACK"].append("Quotation file")
            elif "booking" in content_type.lower():
                scores["TRUCKING_SHORT"] += 0.3
                reasons["TRUCKING_SHORT"].append("Booking form")

    # Apply weights and sort
    for stype in scores:
        scores[stype] *= SERVICE_PATTERNS[stype].get("weight", 1.0)

    sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    suggestions = []
    for stype, score in sorted_types[:top_n]:
        if score > 0:
            suggestions.append({
                "service_type": stype,
                "confidence": min(1.0, score / 1.5),
                "reason": "; ".join(reasons[stype][:2]) if reasons[stype] else "Pattern match",
            })

    # Always include at least TRUCKING_SHORT as fallback
    if not suggestions:
        suggestions.append({
            "service_type": "TRUCKING_SHORT",
            "confidence": 0.5,
            "reason": "Default option",
        })

    return suggestions
