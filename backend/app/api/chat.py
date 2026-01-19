"""
Chat API - Main endpoints for Chat UI
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import logging
import traceback

from app.services.ai_service import get_ai_service
from app.services.data_service import get_data_service

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models

class ChatContext(BaseModel):
    source_type: Optional[str] = None  # CUSTOMER, VENDOR
    source_id: Optional[str] = None    # DRT1, Tam Bao, etc.
    job_id: Optional[int] = None


class ChatRequest(BaseModel):
    content: str
    content_type: str = "TEXT"  # TEXT, EXCEL, PDF, IMAGE_OCR
    context: Optional[ChatContext] = None


class ChatResponse(BaseModel):
    intent: str
    confidence: float
    entities: Dict[str, Any]
    enriched_data: Optional[Dict[str, Any]] = None
    suggested_action: str
    form_data: Optional[Dict[str, Any]] = None
    generated_message: Optional[str] = None
    summary: Optional[str] = None


# Endpoints

@router.get("/search-customers")
async def search_customers(q: str = ""):
    """
    Search customers by keyword for autocomplete
    """
    from app.services.data_service import get_data_service
    
    data_service = get_data_service()
    conn = data_service._get_connection()
    cursor = conn.cursor()
    
    try:
        if q:
            cursor.execute("""
                SELECT customer_id, customer_code, short_name, company_name
                FROM customers 
                WHERE customer_code ILIKE %s 
                   OR short_name ILIKE %s 
                   OR company_name ILIKE %s
                ORDER BY short_name
                LIMIT 50
            """, (f"%{q}%", f"%{q}%", f"%{q}%"))
        else:
            cursor.execute("""
                SELECT customer_id, customer_code, short_name, company_name
                FROM customers 
                WHERE is_active = TRUE
                ORDER BY short_name
                LIMIT 50
            """)
        
        customers = cursor.fetchall()
        return {
            "customers": [
                {
                    "id": c["customer_id"],
                    "code": c["customer_code"],
                    "name": c["short_name"] or c["company_name"]
                }
                for c in customers
            ]
        }
    finally:
        cursor.close()
        conn.close()


@router.get("/search-jobs")
async def search_jobs(q: str = ""):
    """
    Search pending jobs for vehicle assignment
    Search by: job_no, customer_code, invoice, date
    """
    from app.services.data_service import get_data_service
    
    data_service = get_data_service()
    conn = data_service._get_connection()
    cursor = conn.cursor()
    
    try:
        if q:
            cursor.execute("""
                SELECT j.job_id, j.job_no, j.description, j.etd,
                       c.customer_code, c.short_name as customer_name,
                       js.scheduled_time, js.service_details
                FROM jobs j
                LEFT JOIN customers c ON j.customer_id = c.customer_id
                LEFT JOIN job_services js ON j.job_id = js.job_id
                WHERE j.status_code IN ('PENDING', 'CONFIRMED', 'DRAFT')
                  AND (
                    j.job_no ILIKE %s 
                    OR c.customer_code ILIKE %s 
                    OR c.short_name ILIKE %s
                    OR j.description ILIKE %s
                    OR CAST(j.etd AS TEXT) LIKE %s
                  )
                ORDER BY j.created_at DESC
                LIMIT 20
            """, (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"))
        else:
            cursor.execute("""
                SELECT j.job_id, j.job_no, j.description, j.etd, j.status_code,
                       c.customer_code, c.short_name as customer_name,
                       js.scheduled_time, js.service_details, js.vendor_text_input
                FROM jobs j
                LEFT JOIN customers c ON j.customer_id = c.customer_id
                LEFT JOIN job_services js ON j.job_id = js.job_id
                WHERE j.status_code IN ('PENDING', 'CONFIRMED', 'DRAFT', 'DISPATCHED')
                ORDER BY j.created_at DESC
                LIMIT 20
            """)
        
        jobs = cursor.fetchall()
        result = []
        for job in jobs:
            # Parse service_details if available
            invoice = ""
            pickup_time = ""
            if job.get("scheduled_time"):
                pickup_time = str(job["scheduled_time"])[:5]  # HH:MM format
            if job.get("service_details"):
                details = job["service_details"]
                if isinstance(details, str):
                    import json
                    details = json.loads(details)
                invoice = details.get("invoice_numbers", "")
            
            # Parse vendor_text_input for vehicle info
            license_plate = ""
            if job.get("vendor_text_input"):
                vendor_data = job["vendor_text_input"]
                if isinstance(vendor_data, str):
                    import json
                    try:
                        vendor_data = json.loads(vendor_data)
                        license_plate = vendor_data.get("license_plate", "")
                    except:
                        pass
                elif isinstance(vendor_data, dict):
                    license_plate = vendor_data.get("license_plate", "")
            
            result.append({
                "id": job["job_id"],
                "job_no": job["job_no"],
                "customer": job["customer_code"] or job["customer_name"],
                "date": str(job["etd"]) if job.get("etd") else "",
                "time": pickup_time,
                "invoice": invoice,
                "description": job.get("description", "")[:50],
                "has_vehicle": bool(license_plate),
                "license_plate": license_plate,
                "status": job.get("status_code", "PENDING")
            })
        
        return {"jobs": result}
    finally:
        cursor.close()
        conn.close()

@router.post("/process", response_model=ChatResponse)
async def process_chat_message(request: ChatRequest):
    """
    Main endpoint for Chat UI text processing
    """
    
    logger.info(f"Processing chat: {request.content[:200]}...")
    
    # Step 1: AI Processing
    ai_service = get_ai_service()
    ai_result = await ai_service.process(
        content=request.content,
        content_type=request.content_type,
        context=request.context.model_dump() if request.context else None
    )
    
    logger.info(f"AI result: intent={ai_result.get('intent')}, confidence={ai_result.get('confidence')}")
    
    # Step 2: Data Enrichment
    data_service = get_data_service()
    enriched = await data_service.enrich_entities(
        intent=ai_result.get("intent"),
        entities=ai_result.get("entities", {})
    )
    
    # Step 3: Generate form data
    form_data = generate_form_data(ai_result.get("intent"), enriched)
    
    # Step 4: Suggested action
    suggested_action = get_suggested_action(ai_result.get("intent"))
    
    return ChatResponse(
        intent=ai_result.get("intent", "GENERAL_QUERY"),
        confidence=ai_result.get("confidence", 0.0),
        entities=ai_result.get("entities", {}),
        enriched_data=enriched,
        suggested_action=suggested_action,
        form_data=form_data,
        summary=ai_result.get("summary")
    )


@router.post("/process-file")
async def process_file(
    file: UploadFile = File(...),
    context: str = Form(default="{}")
):
    """
    Process uploaded Excel/PDF file
    """
    try:
        context_dict = json.loads(context)
        
        # Detect file type and extract content
        filename = file.filename.lower()
        logger.info(f"Processing file: {filename}")
        
        if filename.endswith(('.xlsx', '.xls')):
            content = await extract_excel_content_structured(file)
            content_type = "EXCEL"
        elif filename.endswith('.pdf'):
            content = await extract_pdf_content(file)
            content_type = "PDF"
        else:
            raise HTTPException(400, f"Unsupported file type: {filename}")
        
        # Prepend additional text context (e.g., "khách MEIKO") to help AI understand
        additional_text = context_dict.get("additional_text", "")
        if additional_text:
            content = f"[USER CONTEXT: {additional_text}]\n\n{content}"
            logger.info(f"Added user context: {additional_text}")
        
        logger.info(f"Extracted content length: {len(content)} chars")
        logger.info(f"Content preview: {content[:500]}...")
        
        # Process extracted content
        return await process_chat_message(ChatRequest(
            content=content,
            content_type=content_type,
            context=None
        ))
    except Exception as e:
        logger.error(f"File processing error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(500, f"File processing error: {str(e)}")


@router.post("/process-image")
async def process_image(
    image: UploadFile = File(...),
    context: str = Form(default="{}")
):
    """
    Process uploaded image (screenshot) with OCR
    """
    try:
        context_dict = json.loads(context)
        logger.info(f"Processing image: {image.filename}")
        
        # OCR with Gemini Vision - extract structured data directly
        image_bytes = await image.read()
        ai_result = await ocr_and_extract(image_bytes, context_dict)
        
        # Return result directly
        return ChatResponse(
            intent=ai_result.get("intent", "GENERAL_QUERY"),
            confidence=ai_result.get("confidence", 0.0),
            entities=ai_result.get("entities", {}),
            enriched_data=ai_result.get("entities", {}),
            suggested_action=get_suggested_action(ai_result.get("intent")),
            form_data=generate_form_data(ai_result.get("intent"), ai_result.get("entities", {})),
            summary=ai_result.get("summary")
        )
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(500, f"Image processing error: {str(e)}")


# Helper functions

def get_suggested_action(intent: str) -> str:
    """Get suggested action based on intent"""
    actions = {
        "CREATE_JOB": "Review and create new job",
        "ASSIGN_VEHICLE": "Review and assign vehicle to job",
        "UPDATE_JOB": "Review and update job details",
        "COMPLETE_JOB": "Confirm job completion",
        "CANCEL_JOB": "Confirm job cancellation",
        "QUERY_STATUS": "View job status",
        "GENERAL_QUERY": "No specific action",
    }
    return actions.get(intent, "No specific action")


def generate_form_data(intent: str, enriched: Dict) -> Dict:
    """Generate form data for review based on intent"""
    
    if intent in ["CREATE_JOB", "UPDATE_JOB"]:
        return {
            "form_type": "create_job",
            "fields": [
                {"name": "customer_id", "label": "Khách hàng", "type": "select", "value": enriched.get("customer_id"), "display": enriched.get("customer_name") or enriched.get("customer_code")},
                {"name": "booking_date", "label": "Ngày", "type": "date", "value": enriched.get("booking_date")},
                {"name": "pickup_time", "label": "Giờ lấy hàng", "type": "time", "value": enriched.get("pickup_time")},
                {"name": "route_id", "label": "Tuyến", "type": "select", "value": enriched.get("route_id"), "display": enriched.get("route_name")},
                {"name": "vehicle_type", "label": "Loại xe", "type": "select", "value": enriched.get("vehicle_type")},
                {"name": "vendor_id", "label": "Nhà xe", "type": "select", "value": enriched.get("vendor_id"), "display": enriched.get("vendor_name")},
                {"name": "invoice_numbers", "label": "Invoice", "type": "text", "value": enriched.get("invoice_numbers")},
                {"name": "cargo_type", "label": "Loại hàng", "type": "text", "value": enriched.get("cargo_type")},
                {"name": "package_info", "label": "Số lượng", "type": "text", "value": enriched.get("package_info")},
                {"name": "delivery_details", "label": "Chi tiết giao hàng", "type": "text", "value": enriched.get("delivery_details")},
            ],
            "pricing": enriched.get("pricing", {})
        }
    
    elif intent == "ASSIGN_VEHICLE":
        return {
            "form_type": "assign_vehicle",
            "fields": [
                {"name": "job_id", "label": "Job", "type": "select", "value": enriched.get("job_id"), "display": enriched.get("job_number")},
                {"name": "license_plate", "label": "Biển số", "type": "text", "value": enriched.get("license_plate")},
                {"name": "driver_name", "label": "Tên lái xe", "type": "text", "value": enriched.get("driver_name")},
                {"name": "driver_phone", "label": "SĐT", "type": "text", "value": enriched.get("driver_phone")},
                {"name": "driver_id_card", "label": "CCCD", "type": "text", "value": enriched.get("driver_id_card")},
            ]
        }
    
    return {"form_type": "none"}


async def extract_excel_content_structured(file: UploadFile) -> str:
    """Extract structured text content from Excel file for logistics booking"""
    import openpyxl
    from io import BytesIO
    
    content = await file.read()
    wb = openpyxl.load_workbook(BytesIO(content), data_only=True)
    
    text_parts = []
    text_parts.append("=== BOOKING REQUEST FROM EXCEL ===")
    
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        text_parts.append(f"\n--- Sheet: {sheet_name} ---")
        
        # Get headers from first non-empty row
        headers = []
        header_row = None
        for row_idx, row in enumerate(ws.iter_rows(max_row=10), start=1):
            row_values = [str(cell.value).strip() if cell.value else "" for cell in row]
            non_empty = [v for v in row_values if v]
            if len(non_empty) >= 3:  # Likely header row
                headers = row_values
                header_row = row_idx
                break
        
        if not headers:
            # Fallback to simple extraction
            for row in ws.iter_rows(max_row=50):
                row_text = " | ".join([
                    str(cell.value)[:150] if cell.value else ""
                    for cell in row
                ])
                if row_text.strip(" |"):
                    text_parts.append(row_text)
            continue
        
        text_parts.append(f"Headers: {' | '.join(headers)}")
        
        # Extract data rows with header context
        for row in ws.iter_rows(min_row=header_row + 1, max_row=100):
            row_data = []
            for idx, cell in enumerate(row):
                header = headers[idx] if idx < len(headers) else f"Col{idx}"
                value = str(cell.value).strip() if cell.value else ""
                if value and value.lower() not in ['none', 'nan', '']:
                    row_data.append(f"{header}: {value}")
            
            if row_data:
                text_parts.append(" | ".join(row_data))
    
    result = "\n".join(text_parts)
    logger.info(f"Extracted Excel content:\n{result}")
    return result


async def extract_pdf_content(file: UploadFile) -> str:
    """Extract text content from PDF file"""
    from pypdf import PdfReader
    from io import BytesIO
    
    content = await file.read()
    reader = PdfReader(BytesIO(content))
    
    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    
    return "\n".join(text_parts)


async def ocr_and_extract(image_bytes: bytes, context: dict = None) -> Dict:
    """OCR image and extract structured logistics data using Gemini Vision"""
    import google.generativeai as genai
    from PIL import Image
    from io import BytesIO
    import re
    
    from app.core.config import settings
    
    try:
        genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        img = Image.open(BytesIO(image_bytes))
        
        # Enhanced prompt for logistics data extraction
        prompt = """Analyze this logistics/booking image and extract all information.

This is likely a screenshot from Zalo or an Excel booking sheet from a Vietnamese logistics company.

Extract and return as JSON:
{
    "intent": "CREATE_JOB" or "ASSIGN_VEHICLE" or "UPDATE_JOB" or "QUERY_STATUS",
    "confidence": 0.95,
    "entities": {
        "customer_code": "customer code like DRT, SEVT, HSDN",
        "booking_date": "YYYY-MM-DD format",
        "pickup_time": "HH:mm format",
        "vehicle_type": "1.25T, 2.5T, 5T, etc",
        "invoice_numbers": ["list of invoice numbers"],
        "cargo_type": "type of cargo like PCB, FPC, etc",
        "package_info": "1 pallet, 2 box, etc",
        "delivery_details": "workshop/location info like Xưởng 1, Xưởng 2",
        "license_plate": "if visible, e.g. 29H 76514",
        "driver_name": "if visible",
        "driver_phone": "if visible"
    },
    "summary": "Brief Vietnamese summary of what this booking contains"
}

IMPORTANT:
- Extract ALL invoice numbers visible
- Note which invoices go to which workshop/location (e.g., "260116DRT-F17: Xưởng 1")
- Include delivery_details with workshop assignments
- If this is a table, extract each row's data
- Return ONLY valid JSON, no markdown

RESPOND IN JSON FORMAT ONLY:"""
        
        response = model.generate_content([prompt, img])
        text = response.text.strip()
        
        logger.info(f"Gemini Vision response: {text[:500]}")
        
        # Parse JSON response
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        # Clean up JSON
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        
        result = json.loads(text)
        
        # Ensure confidence is a float
        result["confidence"] = float(result.get("confidence", 0.9))
        
        return result
        
    except Exception as e:
        logger.error(f"OCR error: {e}")
        logger.error(traceback.format_exc())
        return {
            "intent": "GENERAL_QUERY",
            "confidence": 0.0,
            "entities": {},
            "summary": f"Lỗi xử lý ảnh: {str(e)}"
        }
