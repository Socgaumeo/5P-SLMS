"""
AI-powered rate sheet parser using Gemini/DeepSeek/Anthropic.
Fallback when regex-based parser fails to extract rates.
Handles any Excel format: trucking, customs, warehouse, packing.
"""

import json
import logging
from typing import List, Dict, Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Prompt template for AI rate extraction
RATE_EXTRACTION_PROMPT = """Bạn là chuyên gia phân tích bảng giá logistics Việt Nam.
Phân tích dữ liệu Excel bên dưới và trích xuất TẤT CẢ các mục báo giá/giá cước.

Loại dịch vụ gợi ý: {service_type_hint}

Quy tắc:
1. Mỗi dòng giá = 1 mục trong mảng kết quả
2. Nếu bảng có dạng pivot (loại xe/container là header cột), tách mỗi cột giá thành 1 mục riêng
3. Giá phải > 0 và là số thực (bỏ qua dòng tổng, dòng ghi chú, phụ phí)
4. Nếu nhiều điểm đến chung 1 điểm đi, sử dụng điểm đi gần nhất ở trên
5. Đơn vị mặc định: TRIP (chuyến). Nếu file ghi đơn vị khác thì dùng đơn vị đó
6. Với dịch vụ CUSTOMS/PACKING/WAREHOUSE: không cần origin/destination, đặt tên dịch vụ vào vehicle_type

Trả về ĐÚNG JSON array, KHÔNG markdown, KHÔNG giải thích:
[
  {{
    "origin": "điểm đi hoặc null",
    "destination": "điểm đến hoặc null",
    "vehicle_type": "loại xe/container/dịch vụ",
    "price": 1500000,
    "unit": "TRIP",
    "notes": "ghi chú nếu có hoặc null"
  }}
]

Dữ liệu Excel:
{sheet_content}"""


def _sheet_to_text(df_raw: pd.DataFrame, max_rows: int = 60) -> str:
    """Convert raw DataFrame to readable text for AI prompt."""
    lines = []
    for idx in range(min(max_rows, len(df_raw))):
        row_vals = []
        for val in df_raw.iloc[idx]:
            if pd.notna(val):
                s = str(val).strip()
                if s and s.lower() != "nan":
                    row_vals.append(s)
        if row_vals:
            lines.append(" | ".join(row_vals))
    return "\n".join(lines)


async def parse_rates_with_ai(
    file_path: str,
    service_type_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse rate file using AI. Called when regex parser fails.
    Returns same format as parse_excel_rates().
    """
    import os
    from app.ai.clients import get_ai_client

    file_name = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()

    # Map service type to hint for AI
    service_hints = {
        "TRUCKING_DOM": "Vận chuyển nội địa (có tuyến đường, loại xe)",
        "TRUCKING_INTL": "Vận chuyển quốc tế (có tuyến đường, container)",
        "CUSTOMS": "Thủ tục hải quan (phí dịch vụ, tờ khai, loại hình)",
        "PACKING": "Đóng gói (phí đóng gói, loại bao bì)",
        "WAREHOUSE": "Kho bãi (phí lưu kho, diện tích, thời gian)",
    }
    hint = service_hints.get(service_type_code, "Logistics (tự phát hiện loại dịch vụ)")

    all_rates = []
    sheet_info = []

    try:
        # Read sheets
        if ext == ".csv":
            raw_sheets = {"Sheet1": pd.read_csv(file_path, header=None)}
        else:
            xls = pd.ExcelFile(file_path)
            raw_sheets = {}
            for sheet in xls.sheet_names:
                try:
                    raw_sheets[sheet] = pd.read_excel(
                        file_path, sheet_name=sheet, header=None
                    )
                except Exception:
                    continue

        # Get AI client
        ai_client = get_ai_client()

        for sheet_name, df_raw in raw_sheets.items():
            if df_raw.empty or len(df_raw) < 2:
                continue

            # Convert sheet to text
            sheet_text = _sheet_to_text(df_raw)
            if not sheet_text.strip():
                continue

            # Build prompt
            prompt = RATE_EXTRACTION_PROMPT.format(
                service_type_hint=hint,
                sheet_content=sheet_text,
            )

            # Call AI
            try:
                response = await ai_client.generate(
                    prompt=prompt,
                    response_format="json",
                    temperature=0.1,
                )

                # Parse response
                rates = _parse_ai_response(response)
                if rates:
                    all_rates.extend(rates)
                    sheet_info.append({
                        "sheet": sheet_name,
                        "type": "ai_parsed",
                        "count": len(rates),
                    })
                else:
                    sheet_info.append({
                        "sheet": sheet_name,
                        "type": "ai_no_rates",
                        "count": 0,
                    })

            except Exception as e:
                logger.error(f"AI parse error for sheet {sheet_name}: {e}")
                sheet_info.append({
                    "sheet": sheet_name,
                    "type": "ai_error",
                    "count": 0,
                })

    except Exception as e:
        logger.error(f"Error in AI rate parsing: {e}")
        return {
            "file_name": file_name,
            "parsed_rates": [],
            "error": str(e),
            "parse_method": "ai",
        }

    return {
        "file_name": file_name,
        "parsed_rates": all_rates,
        "sheet_info": sheet_info,
        "total_rates": len(all_rates),
        "parse_method": "ai",
    }


def _parse_ai_response(response) -> List[Dict[str, Any]]:
    """Parse AI response into list of rate dicts. Handles various formats."""
    # If already a list (AI client returned parsed JSON)
    if isinstance(response, list):
        return _validate_rates(response)

    # If dict with a rates key
    if isinstance(response, dict):
        if "rates" in response:
            return _validate_rates(response["rates"])
        # Maybe the dict itself is a single rate
        if "price" in response:
            return _validate_rates([response])
        return []

    # If string, try to parse JSON
    if isinstance(response, str):
        text = response.strip()
        # Remove markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(text)
            if isinstance(data, list):
                return _validate_rates(data)
            if isinstance(data, dict) and "rates" in data:
                return _validate_rates(data["rates"])
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse AI response as JSON: {text[:200]}")

    return []


def _validate_rates(rates: list) -> List[Dict[str, Any]]:
    """Validate and normalize rate items from AI response."""
    valid = []
    for r in rates:
        if not isinstance(r, dict):
            continue
        try:
            price = float(r.get("price", 0))
            if price <= 0:
                continue
            valid.append({
                "origin": r.get("origin") or None,
                "destination": r.get("destination") or None,
                "vehicle_type": r.get("vehicle_type") or r.get("service") or None,
                "price": price,
                "unit": r.get("unit", "TRIP") or "TRIP",
                "notes": r.get("notes") or None,
            })
        except (ValueError, TypeError):
            continue
    return valid
