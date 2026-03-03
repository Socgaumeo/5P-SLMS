"""
Rate file upload API — parse Excel/CSV rate sheets and bulk import rates.
Endpoints:
  POST /api/admin/rates/upload-file   → parse file, return preview
  POST /api/admin/rates/confirm-import → bulk create rates from preview
"""

import logging
import tempfile
import os
from datetime import date, datetime
from typing import Optional, List

import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from app.db.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/rates", tags=["Rate File Upload"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class RateRow(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    vehicle_type: Optional[str] = None
    price: float
    unit: str = "TRIP"
    notes: Optional[str] = None
    is_surcharge: bool = False


class ConfirmImportRequest(BaseModel):
    file_ref_id: Optional[int] = None
    rate_type: str  # "buying" or "selling"
    vendor_id: Optional[int] = None
    customer_id: Optional[int] = None
    service_type_code: Optional[str] = None
    rates: List[RateRow]


# ---------------------------------------------------------------------------
# Helpers — parse Vietnamese trucking rate sheets
# ---------------------------------------------------------------------------

import re

# Keywords to identify header row containing origin/destination columns
HEADER_KEYWORDS = ["stt", "từ", "đến", "tuyến", "origin", "destination", "no."]

# Patterns that identify vehicle/container type columns
VEHICLE_PATTERNS = [
    r"\d+\.?\d*\s*t\b",       # 1.25T, 2.5T, 5T, 14T
    r"truck\s*\d",             # Truck 1.25T, Truck 5T
    r"cont\s*\d",             # CONT 20', CONT 40'
    r"\d+\s*ft",               # 20ft, 40ft
    r"\d+\s*hc",               # 40HC
    r"\d+['']",                # 20', 40'
]

# Rows containing these keywords are surcharges, not route rates
SURCHARGE_KEYWORDS = [
    "chờ giờ", "lưu ca", "hủy chuyến", "huỷ chuyến", "bốc xếp",
    "phụ phí", "lưu ý", "dịch vụ khác", "thanh lý", "ghi chú",
    "note", "remark", "lưu kho",
]


def _is_vehicle_col(col_name: str) -> bool:
    """Check if column header looks like a vehicle/container type."""
    s = str(col_name).lower().strip()
    return any(re.search(p, s) for p in VEHICLE_PATTERNS)


def _is_surcharge_row(row_values: list) -> bool:
    """Check if a row is a surcharge/note row (not a route rate)."""
    text = " ".join(str(v).lower() for v in row_values if pd.notna(v))
    return any(kw in text for kw in SURCHARGE_KEYWORDS)


def _find_header_row(df_raw: pd.DataFrame) -> Optional[int]:
    """
    Scan first 20 rows of raw DataFrame (no header) to find the row
    that contains column headers like STT, TỪ, ĐẾN, and vehicle types.
    """
    for idx in range(min(20, len(df_raw))):
        row_vals = [str(v).lower().strip() for v in df_raw.iloc[idx] if pd.notna(v)]
        row_text = " ".join(row_vals)
        # Must contain origin/destination keywords AND at least 1 vehicle column
        has_header = any(kw in row_text for kw in ["từ", "đến", "origin", "destination", "stt"])
        has_vehicle = any(_is_vehicle_col(v) for v in df_raw.iloc[idx] if pd.notna(v))
        if has_header and has_vehicle:
            return idx
    return None


def _parse_pivot_sheet(df: pd.DataFrame) -> dict:
    """
    Parse a DataFrame that's already re-indexed with the correct header row.
    Handles pivot-style rate tables (vehicle types as column headers).
    Carries forward origin for multi-destination rows.
    Returns dict with rates and surcharges lists.
    """
    # Identify vehicle columns and text columns
    vehicle_cols = [c for c in df.columns if _is_vehicle_col(c)]
    if len(vehicle_cols) < 2:
        return {"rates": [], "surcharges": [], "data_rows": 0}

    # Text columns: everything except vehicle cols (skip STT-like first col)
    text_cols = [c for c in df.columns if c not in vehicle_cols]
    # Find origin and destination columns (usually first two text cols after STT)
    stt_col = None
    origin_col = None
    dest_col = None
    for tc in text_cols:
        tc_lower = str(tc).lower().strip()
        if tc_lower in ["stt", "no.", "no", "tt"]:
            stt_col = tc
        elif "từ" in tc_lower or "origin" in tc_lower or "from" in tc_lower:
            origin_col = tc
        elif "đến" in tc_lower or "destination" in tc_lower or "to" in tc_lower:
            dest_col = tc

    # Fallback: first non-STT text col = origin, second = destination
    non_stt_text = [c for c in text_cols if c != stt_col]
    if not origin_col and len(non_stt_text) >= 1:
        origin_col = non_stt_text[0]
    if not dest_col and len(non_stt_text) >= 2:
        dest_col = non_stt_text[1]

    rates = []
    surcharges = []
    last_origin = None
    data_rows = 0

    for _, row in df.iterrows():
        # Count rows with at least one price value
        has_price = any(
            pd.notna(row.get(vc)) and _is_numeric_price(row.get(vc))
            for vc in vehicle_cols
        )
        if has_price:
            data_rows += 1

        # Get origin/destination values
        raw_origin = str(row[origin_col]).strip() if origin_col and pd.notna(row.get(origin_col)) else None
        raw_dest = str(row[dest_col]).strip() if dest_col and pd.notna(row.get(dest_col)) else None

        # Carry forward origin for multi-destination rows
        if raw_origin and raw_origin.lower() not in ["nan", ""]:
            last_origin = raw_origin
        origin = last_origin

        # Collect surcharge rows instead of skipping
        if _is_surcharge_row(row.values):
            text = " | ".join(str(v) for v in row.values if pd.notna(v) and str(v).strip())
            for vc in vehicle_cols:
                price_val = row.get(vc)
                if pd.notna(price_val):
                    try:
                        price = float(price_val)
                        if price >= 10000:
                            surcharges.append({
                                "origin": None,
                                "destination": None,
                                "vehicle_type": str(vc).strip(),
                                "price": price,
                                "unit": "TRIP",
                                "notes": f"PHỤ PHÍ: {text.strip()}"[:200],
                                "is_surcharge": True,
                            })
                    except (ValueError, TypeError):
                        continue
            continue

        # Skip rows without destination
        if not raw_dest or raw_dest.lower() in ["nan", ""]:
            continue

        # Extract prices for each vehicle type
        for vc in vehicle_cols:
            price_val = row.get(vc)
            if pd.notna(price_val):
                try:
                    price = float(price_val)
                    # Minimum price threshold to filter noise (> 10,000 VND)
                    if price >= 10000:
                        rates.append({
                            "origin": origin,
                            "destination": raw_dest,
                            "vehicle_type": str(vc).strip(),
                            "price": price,
                            "unit": "TRIP",
                            "notes": None,
                            "is_surcharge": False,
                        })
                except (ValueError, TypeError):
                    continue

    return {"rates": rates, "surcharges": surcharges, "data_rows": data_rows}


def _is_numeric_price(val) -> bool:
    """Check if a value can be a valid price number."""
    try:
        return float(val) >= 10000
    except (ValueError, TypeError):
        return False


# Keywords for list-style header detection (packing, customs, warehouse)
LIST_SERVICE_KEYWORDS = ["dịch vụ", "services", "nội dung", "hạng mục", "diễn giải"]
LIST_PRICE_KEYWORDS = ["đơn giá", "unit price", "price"]
LIST_UNIT_KEYWORDS = ["đvt", "đơn vị", "unit"]


def _find_list_header_row(df_raw: pd.DataFrame) -> Optional[int]:
    """Find header row for list-style rate sheets (STT | Service | Unit | Price)."""
    for idx in range(min(20, len(df_raw))):
        row_vals = [str(v).lower().strip() for v in df_raw.iloc[idx] if pd.notna(v)]
        # Need at least 3 columns to be a valid header
        if len(row_vals) < 3:
            continue
        row_text = " ".join(row_vals)
        has_stt = any(kw in row_text for kw in ["stt", "no."])
        has_service = any(kw in row_text for kw in LIST_SERVICE_KEYWORDS)
        has_price = any(kw in row_text for kw in LIST_PRICE_KEYWORDS)
        has_unit = any(kw in row_text for kw in LIST_UNIT_KEYWORDS)
        # Require STT + (service or unit) + price
        if has_stt and has_price and (has_service or has_unit):
            return idx
    return None


def _parse_list_sheet(df: pd.DataFrame) -> dict:
    """
    Parse list-style rate tables (packing, customs, warehouse).
    Format: STT | Service name | Unit | Price
    """
    rates = []
    # Identify columns by header content
    service_col = None
    unit_col = None
    price_col = None

    for c in df.columns:
        cl = str(c).lower().strip()
        if cl in ["stt", "no.", "no", "tt"]:
            continue
        elif any(kw in cl for kw in LIST_PRICE_KEYWORDS):
            price_col = c
        elif any(kw in cl for kw in LIST_UNIT_KEYWORDS):
            unit_col = c
        elif service_col is None:
            # First non-STT, non-price, non-unit column = service name
            service_col = c

    if not price_col:
        return {"rates": [], "surcharges": [], "data_rows": 0}

    data_rows = 0
    last_group = None  # Track section headers (e.g. "Phí đóng kiện gỗ")

    for _, row in df.iterrows():
        price_val = row.get(price_col)
        service_name = str(row.get(service_col, "")).strip() if service_col and pd.notna(row.get(service_col)) else None
        unit_val = str(row.get(unit_col, "")).strip() if unit_col and pd.notna(row.get(unit_col)) else None

        # Section header row (has service name but no price)
        if service_name and service_name.lower() not in ["nan", ""] and (not pd.notna(price_val) or not _is_numeric_price(price_val)):
            last_group = service_name
            continue

        if pd.notna(price_val) and _is_numeric_price(price_val):
            data_rows += 1
            # Build descriptive vehicle_type from group + service name
            label = f"{last_group} - {service_name}" if last_group and service_name else (service_name or last_group or "")
            rates.append({
                "origin": None,
                "destination": None,
                "vehicle_type": label.strip()[:150] if label else None,
                "price": float(price_val),
                "unit": unit_val or "TRIP",
                "notes": None,
                "is_surcharge": False,
            })

    return {"rates": rates, "surcharges": [], "data_rows": data_rows}


def parse_excel_rates(file_path: str) -> dict:
    """
    Parse an Excel/CSV rate file and extract rate rows.
    Handles Vietnamese trucking rate sheet formats:
    - Pivot tables (vehicle types as column headers)
    - Header rows buried below company info
    - Multi-destination rows sharing same origin
    """
    file_name = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()

    all_rates = []
    all_surcharges = []
    sheet_info = []

    try:
        if ext == ".csv":
            raw_sheets = {"Sheet1": pd.read_csv(file_path, header=None)}
        else:
            xls = pd.ExcelFile(file_path)
            raw_sheets = {}
            for sheet in xls.sheet_names:
                try:
                    raw_sheets[sheet] = pd.read_excel(file_path, sheet_name=sheet, header=None)
                except Exception:
                    continue

        for sheet_name, df_raw in raw_sheets.items():
            if df_raw.empty or len(df_raw) < 3:
                continue

            # Step 1: Try pivot-style parser (trucking with vehicle columns)
            header_idx = _find_header_row(df_raw)
            if header_idx is not None:
                df = df_raw.iloc[header_idx + 1:].copy()
                df.columns = df_raw.iloc[header_idx]
                df = df.loc[:, df.columns.notna()]
                df = df.dropna(how="all")

                if not df.empty:
                    parsed = _parse_pivot_sheet(df)
                    if parsed["rates"] or parsed["surcharges"]:
                        all_rates.extend(parsed["rates"])
                        all_surcharges.extend(parsed["surcharges"])
                        sheet_info.append({
                            "sheet": sheet_name, "type": "pivot",
                            "count": len(parsed["rates"]),
                            "data_rows": parsed["data_rows"],
                        })
                        continue

            # Step 2: Try list-style parser (packing, customs, warehouse)
            list_header_idx = _find_list_header_row(df_raw)
            if list_header_idx is not None:
                df = df_raw.iloc[list_header_idx + 1:].copy()
                df.columns = df_raw.iloc[list_header_idx]
                df = df.loc[:, df.columns.notna()]
                df = df.dropna(how="all")

                if not df.empty:
                    parsed = _parse_list_sheet(df)
                    if parsed["rates"]:
                        all_rates.extend(parsed["rates"])
                        sheet_info.append({
                            "sheet": sheet_name, "type": "list",
                            "count": len(parsed["rates"]),
                            "data_rows": parsed["data_rows"],
                        })
                        continue

            sheet_info.append({"sheet": sheet_name, "type": "no_header", "count": 0})

    except Exception as e:
        logger.error(f"Error parsing rate file: {e}")
        import traceback
        traceback.print_exc()
        return {"file_name": file_name, "parsed_rates": [], "error": str(e)}

    # Merge surcharges into parsed_rates so frontend can preview them
    combined_rates = all_rates + all_surcharges

    return {
        "file_name": file_name,
        "parsed_rates": combined_rates,
        "surcharges": all_surcharges,
        "sheet_info": sheet_info,
        "total_rates": len(combined_rates),
    }


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@router.post("/upload-file")
async def upload_rate_file(
    file: UploadFile = File(...),
    rate_type: str = Form("buying"),
    vendor_id: Optional[int] = Form(None),
    customer_id: Optional[int] = Form(None),
    service_type_code: Optional[str] = Form(None),
):
    """
    Upload an Excel/CSV rate file, parse it, and return a preview.
    The user can then confirm the import via /confirm-import.
    """
    # Validate file type
    allowed_ext = {".xlsx", ".xls", ".csv"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed_ext:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: {', '.join(allowed_ext)}")

    # Save to temp file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Step 1: Try fast regex parser
        result = parse_excel_rates(tmp_path)

        # Step 2: Confidence check — call AI if regex extracted too few rates
        regex_count = len(result.get("parsed_rates", []))
        total_data_rows = sum(
            info.get("data_rows", 0) for info in result.get("sheet_info", [])
        )
        confidence = regex_count / max(total_data_rows, 1)

        if regex_count == 0 or confidence < 0.6:
            try:
                import importlib
                ai_parser = importlib.import_module("app.ai.excel.rate-sheet-ai-parser")
                ai_result = await ai_parser.parse_rates_with_ai(
                    tmp_path, service_type_code=service_type_code
                )
                if ai_result.get("parsed_rates") and len(ai_result["parsed_rates"]) > regex_count:
                    result = ai_result
                    result["parse_method"] = "ai"
                    result["confidence"] = 1.0
                else:
                    result["parse_method"] = "regex"
                    result["confidence"] = confidence
            except Exception as ai_err:
                logger.warning(f"AI parser fallback failed: {ai_err}")
                result["parse_method"] = "regex"
                result["confidence"] = confidence
        else:
            result["parse_method"] = "regex"
            result["confidence"] = confidence

        # Create file reference in DB
        file_ref_id = None
        try:
            client = get_supabase()
            ref_result = client.table("rate_file_references").insert({
                "file_name": file.filename,
                "uploaded_at": datetime.now().isoformat(),
                "notes": f"rate_type={rate_type}, vendor_id={vendor_id}, customer_id={customer_id}, service_type={service_type_code}",
            }).execute()
            if ref_result.data:
                file_ref_id = ref_result.data[0]["id"]
        except Exception as e:
            logger.warning(f"Failed to create file reference: {e}")

        result["file_ref_id"] = file_ref_id
        result["rate_type"] = rate_type
        result["vendor_id"] = vendor_id
        result["customer_id"] = customer_id
        result["service_type_code"] = service_type_code

        return result

    finally:
        # Cleanup temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@router.post("/confirm-import")
async def confirm_rate_import(request: ConfirmImportRequest):
    """
    Bulk create rates from the parsed preview data.
    """
    if not request.rates:
        raise HTTPException(400, "No rates to import")

    if request.rate_type == "buying" and not request.vendor_id:
        raise HTTPException(400, "vendor_id is required for buying rates")
    if request.rate_type == "selling" and not request.customer_id:
        raise HTTPException(400, "customer_id is required for selling rates")

    try:
        client = get_supabase()
        table = "vendor_rates" if request.rate_type == "buying" else "customer_rates"

        rows = []
        for rate in request.rates:
            row = {
                "price": rate.price,
                "currency": "VND",
                "unit": rate.unit or "TRIP",
                "effective_date": date.today().isoformat(),
                "is_active": True,
                "service_type_code": request.service_type_code,
            }

            if rate.vehicle_type:
                # DB column is varchar(20) — truncate and put full name in notes
                vt = rate.vehicle_type.strip()
                row["vehicle_type"] = vt[:20]
                if len(vt) > 20:
                    row["notes"] = f"{vt} | {rate.notes}" if rate.notes else vt
                elif rate.notes:
                    row["notes"] = rate.notes
            elif rate.notes:
                row["notes"] = rate.notes
            if request.file_ref_id:
                row["file_reference_id"] = request.file_ref_id

            if rate.origin:
                row["origin_province"] = rate.origin
            if rate.destination:
                row["destination_province"] = rate.destination

            if request.rate_type == "buying":
                row["vendor_id"] = request.vendor_id
            else:
                row["customer_id"] = request.customer_id

            rows.append(row)

        # Batch insert
        result = client.table(table).insert(rows).execute()

        return {
            "success": True,
            "created_count": len(result.data),
            "table": table,
            "file_ref_id": request.file_ref_id,
        }

    except Exception as e:
        logger.error(f"Error importing rates: {e}")
        raise HTTPException(500, f"Import failed: {str(e)}")
