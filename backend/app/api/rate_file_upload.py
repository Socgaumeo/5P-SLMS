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


class ConfirmImportRequest(BaseModel):
    file_ref_id: Optional[int] = None
    rate_type: str  # "buying" or "selling"
    vendor_id: Optional[int] = None
    customer_id: Optional[int] = None
    service_type_code: Optional[str] = None
    rates: List[RateRow]


# ---------------------------------------------------------------------------
# Helpers — auto-detect columns in a DataFrame
# ---------------------------------------------------------------------------

# Vietnamese + English keywords for column detection
ORIGIN_KEYWORDS = ["điểm đi", "nơi đi", "origin", "from", "đi từ", "xuất phát", "điểm lấy hàng"]
DEST_KEYWORDS = ["điểm đến", "nơi đến", "destination", "to", "đến", "giao hàng", "điểm trả hàng"]
PRICE_KEYWORDS = ["giá", "price", "đơn giá", "cước", "phí", "cost", "rate", "amount"]
VEHICLE_KEYWORDS = ["loại xe", "vehicle", "xe", "tải trọng", "tonnage", "truck", "container"]
UNIT_KEYWORDS = ["đơn vị", "unit", "dvt"]
NOTES_KEYWORDS = ["ghi chú", "note", "remark", "mô tả", "description"]


def _match_column(col_name: str, keywords: list) -> bool:
    """Check if column name matches any keyword (case-insensitive)."""
    col_lower = str(col_name).lower().strip()
    return any(kw in col_lower for kw in keywords)


def _detect_columns(df: pd.DataFrame) -> dict:
    """Auto-detect which DataFrame columns map to rate fields."""
    mapping = {}
    for col in df.columns:
        if not mapping.get("origin") and _match_column(col, ORIGIN_KEYWORDS):
            mapping["origin"] = col
        elif not mapping.get("destination") and _match_column(col, DEST_KEYWORDS):
            mapping["destination"] = col
        elif not mapping.get("vehicle_type") and _match_column(col, VEHICLE_KEYWORDS):
            mapping["vehicle_type"] = col
        elif not mapping.get("price") and _match_column(col, PRICE_KEYWORDS):
            mapping["price"] = col
        elif not mapping.get("unit") and _match_column(col, UNIT_KEYWORDS):
            mapping["unit"] = col
        elif not mapping.get("notes") and _match_column(col, NOTES_KEYWORDS):
            mapping["notes"] = col
    return mapping


def _detect_pivot_table(df: pd.DataFrame) -> list:
    """
    Detect pivot-style rate tables where vehicle types are column headers
    and prices are cell values. Common format for Vietnamese trucking rates.
    Layout: Origin | Destination | 1.5T | 2.5T | 3.5T | 5T | ...
    """
    # Heuristic: if >3 columns contain numbers and headers look like vehicle types
    vehicle_pattern = [
        "0.5t", "1t", "1.25t", "1.5t", "2t", "2.5t", "3t", "3.5t",
        "5t", "7t", "8t", "10t", "15t", "20t", "25t", "30t",
        "20ft", "40ft", "40hc", "cont 20", "cont 40",
    ]
    header_strs = [str(c).lower().strip() for c in df.columns]

    # Find columns that look like vehicle types
    vehicle_cols = []
    for i, h in enumerate(header_strs):
        if any(vt in h for vt in vehicle_pattern):
            vehicle_cols.append(df.columns[i])

    if len(vehicle_cols) < 2:
        return []

    # First 1-2 text columns are likely origin/destination
    text_cols = [c for c in df.columns if c not in vehicle_cols]
    origin_col = text_cols[0] if len(text_cols) >= 1 else None
    dest_col = text_cols[1] if len(text_cols) >= 2 else None

    rates = []
    for _, row in df.iterrows():
        origin = str(row[origin_col]).strip() if origin_col and pd.notna(row[origin_col]) else None
        dest = str(row[dest_col]).strip() if dest_col and pd.notna(row[dest_col]) else None

        if not origin or origin.lower() in ["nan", ""]:
            continue

        for vc in vehicle_cols:
            price_val = row[vc]
            if pd.notna(price_val):
                try:
                    price = float(price_val)
                    if price > 0:
                        rates.append({
                            "origin": origin,
                            "destination": dest,
                            "vehicle_type": str(vc).strip(),
                            "price": price,
                            "unit": "TRIP",
                            "notes": None,
                        })
                except (ValueError, TypeError):
                    continue
    return rates


def parse_excel_rates(file_path: str) -> dict:
    """
    Parse an Excel/CSV file and extract rate rows.
    Returns { file_name, parsed_rates: [...], column_mapping, sheet_name }.
    """
    file_name = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()

    all_rates = []
    sheet_info = []

    try:
        if ext == ".csv":
            dfs = {"Sheet1": pd.read_csv(file_path)}
        else:
            xls = pd.ExcelFile(file_path)
            dfs = {}
            for sheet in xls.sheet_names:
                try:
                    dfs[sheet] = pd.read_excel(file_path, sheet_name=sheet)
                except Exception:
                    continue

        for sheet_name, df in dfs.items():
            if df.empty:
                continue

            # Drop fully empty rows/columns
            df = df.dropna(how="all").dropna(axis=1, how="all")
            if df.empty:
                continue

            # Try 1: pivot table detection (vehicle types as column headers)
            pivot_rates = _detect_pivot_table(df)
            if pivot_rates:
                all_rates.extend(pivot_rates)
                sheet_info.append({"sheet": sheet_name, "type": "pivot", "count": len(pivot_rates)})
                continue

            # Try 2: column-based detection
            mapping = _detect_columns(df)
            if not mapping.get("price"):
                # Try with first row as header (sometimes header is in row 1)
                if len(df) > 1:
                    df2 = df.iloc[1:].copy()
                    df2.columns = df.iloc[0]
                    mapping = _detect_columns(df2)
                    if mapping.get("price"):
                        df = df2

            if mapping.get("price"):
                price_col = mapping["price"]
                for _, row in df.iterrows():
                    price_val = row[price_col]
                    if pd.notna(price_val):
                        try:
                            price = float(price_val)
                            if price <= 0:
                                continue
                        except (ValueError, TypeError):
                            continue

                        rate = {
                            "origin": str(row[mapping["origin"]]).strip() if mapping.get("origin") and pd.notna(row.get(mapping["origin"])) else None,
                            "destination": str(row[mapping["destination"]]).strip() if mapping.get("destination") and pd.notna(row.get(mapping["destination"])) else None,
                            "vehicle_type": str(row[mapping["vehicle_type"]]).strip() if mapping.get("vehicle_type") and pd.notna(row.get(mapping["vehicle_type"])) else None,
                            "price": price,
                            "unit": str(row[mapping["unit"]]).strip() if mapping.get("unit") and pd.notna(row.get(mapping["unit"])) else "TRIP",
                            "notes": str(row[mapping["notes"]]).strip() if mapping.get("notes") and pd.notna(row.get(mapping["notes"])) else None,
                        }
                        all_rates.append(rate)

                sheet_info.append({"sheet": sheet_name, "type": "columnar", "count": len(all_rates)})

    except Exception as e:
        logger.error(f"Error parsing rate file: {e}")
        return {"file_name": file_name, "parsed_rates": [], "error": str(e)}

    return {
        "file_name": file_name,
        "parsed_rates": all_rates,
        "sheet_info": sheet_info,
        "total_rates": len(all_rates),
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

        # Parse
        result = parse_excel_rates(tmp_path)

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

            if rate.notes:
                row["notes"] = rate.notes
            if rate.vehicle_type:
                row["vehicle_type"] = rate.vehicle_type
            if request.file_ref_id:
                row["file_reference_id"] = request.file_ref_id

            if request.rate_type == "buying":
                row["vendor_id"] = request.vendor_id
                if rate.origin:
                    row["origin_province"] = rate.origin
                if rate.destination:
                    row["destination_province"] = rate.destination
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
