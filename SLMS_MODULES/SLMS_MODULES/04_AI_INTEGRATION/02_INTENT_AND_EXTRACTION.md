# 🎯 MODULE 4.2: INTENT DETECTION & ENTITY EXTRACTION

## 📋 Mục lục
1. [Intent Detection](#1-intent-detection)
2. [Entity Extraction](#2-entity-extraction)
3. [Document Parsing](#3-document-parsing)
4. [Message Generation](#4-message-generation)

---

## 1. Intent Detection

### 1.1 Intent Categories

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         INTENT CATEGORIES                                        │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                      JOB MANAGEMENT                                     │   │
│   │                                                                          │   │
│   │  create_job         - Tạo booking/job mới                               │   │
│   │  update_job         - Cập nhật thông tin job                            │   │
│   │  cancel_job         - Hủy job                                           │   │
│   │  search_job         - Tìm kiếm job theo tiêu chí                        │   │
│   │  assign_vehicle     - Gán xe/lái xe cho job                             │   │
│   │  complete_job       - Hoàn thành job                                    │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                      PRICING & QUOTES                                   │   │
│   │                                                                          │   │
│   │  create_vendor_quote     - Tạo báo giá mua từ vendor                    │   │
│   │  update_vendor_quote     - Cập nhật báo giá vendor                      │   │
│   │  create_customer_quote   - Tạo báo giá bán cho khách                    │   │
│   │  search_rate             - Tra cứu giá                                  │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                      FINANCIAL                                          │   │
│   │                                                                          │   │
│   │  generate_statement      - Tạo bảng kê khách hàng/vendor               │   │
│   │  reconcile_statement     - Đối chiếu bảng kê                            │   │
│   │  query_balance           - Tra cứu công nợ                              │   │
│   │  generate_report         - Tạo báo cáo                                  │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                      GENERAL                                            │   │
│   │                                                                          │   │
│   │  query_status       - Hỏi trạng thái chung                              │   │
│   │  help               - Yêu cầu hướng dẫn                                 │   │
│   │  unknown            - Không xác định được intent                        │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Intent Detection Examples

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      INTENT DETECTION EXAMPLES                                   │
│                                                                                  │
│   Message                                    │ Intent            │ Confidence   │
│   ───────────────────────────────────────────┼───────────────────┼───────────── │
│   "Book xe 1.25T ngày mai 22h cho DREAMTECH" │ create_job        │ 0.95         │
│   "[File: Phiếu book xe.xlsx]"               │ create_job        │ 0.90         │
│   "BKS 29H 76514, Nguyễn Văn A, 0912345678"  │ assign_vehicle    │ 0.92         │
│   "Job TRK-2601-0001 đã giao xong"           │ complete_job      │ 0.88         │
│   "Tình trạng job hôm nay thế nào?"          │ query_status      │ 0.85         │
│   "Cập nhật giá mới cho tuyến MK-HP"         │ create_vendor_quote│ 0.87        │
│   "Tạo bảng kê tháng 1 cho DREAMTECH"        │ generate_statement│ 0.90         │
│   "Công nợ Tam Bảo bao nhiêu?"               │ query_balance     │ 0.88         │
│   "Làm sao để book xe?"                       │ help              │ 0.92         │
│   "Chào buổi sáng"                           │ unknown           │ 0.30         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Intent Detection Prompt

```python
INTENT_DETECTION_PROMPT = """Bạn là hệ thống phân loại intent cho ứng dụng quản lý logistics.

Phân loại tin nhắn sau vào một trong các intent:

JOB MANAGEMENT:
- create_job: Tạo booking/job mới (book xe, đặt xe, yêu cầu xe)
- update_job: Cập nhật job (sửa thông tin, thay đổi địa chỉ, đổi giờ)
- cancel_job: Hủy job (hủy, cancel, không cần nữa)
- search_job: Tìm job (tìm, tra cứu job, job nào)
- assign_vehicle: Gán xe (BKS, biển số, lái xe, thông tin xe)
- complete_job: Hoàn thành (giao xong, hoàn tất, đã nhận hàng)

PRICING:
- create_vendor_quote: Báo giá vendor (giá mua, cập nhật giá từ vendor)
- create_customer_quote: Báo giá khách (giá bán, báo giá cho khách)
- search_rate: Tra giá (giá bao nhiêu, giá tuyến)

FINANCIAL:
- generate_statement: Tạo bảng kê (bảng kê, statement, thanh toán)
- reconcile_statement: Đối chiếu (đối chiếu, reconcile)
- query_balance: Tra công nợ (công nợ, nợ, balance)
- generate_report: Tạo báo cáo (báo cáo, report)

GENERAL:
- query_status: Hỏi trạng thái (tình trạng, status, thế nào)
- help: Hướng dẫn (làm sao, cách nào, help)
- unknown: Không xác định

Tin nhắn: {message}

Context (nếu có): {context}

Trả lời theo format: intent|confidence
Ví dụ: create_job|0.92
"""
```

---

## 2. Entity Extraction

### 2.1 Entity Types by Intent

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      ENTITY TYPES BY INTENT                                      │
│                                                                                  │
│   Intent: CREATE_JOB                                                            │
│   ──────────────────                                                            │
│   • customer_code    : String    - Mã KH (DRT1, SEVT, HSDN)                    │
│   • customer_name    : String    - Tên KH (DREAMTECH VIETNAM)                  │
│   • booking_date     : Date      - Ngày lấy hàng                               │
│   • pickup_time      : Time      - Giờ lấy hàng                                │
│   • invoice_numbers  : String[]  - Danh sách invoice                           │
│   • cargo_type       : String    - Loại hàng (PCB, TEXTILE)                    │
│   • package_info     : String    - Đóng gói (8 box, 5 pallets)                 │
│   • vehicle_type     : String    - Loại xe (1.25T, 2.5T)                       │
│   • pickup_address   : String    - Địa chỉ lấy                                 │
│   • delivery_address : String    - Địa chỉ giao                                │
│   • contact_name     : String    - Người liên hệ                               │
│   • contact_phone    : String    - SĐT liên hệ                                 │
│                                                                                  │
│   Intent: ASSIGN_VEHICLE                                                        │
│   ──────────────────────                                                        │
│   • job_reference    : String    - Tham chiếu job (quote, invoice, date)       │
│   • license_plate    : String    - Biển số xe (29H 76514)                      │
│   • driver_name      : String    - Tên lái xe                                  │
│   • driver_phone     : String    - SĐT lái xe                                  │
│   • driver_id_card   : String    - Số CCCD                                     │
│   • vehicle_type     : String    - Loại xe                                     │
│                                                                                  │
│   Intent: CREATE_VENDOR_QUOTE                                                   │
│   ───────────────────────────                                                   │
│   • vendor_code      : String    - Mã vendor (TB, VT)                          │
│   • effective_date   : Date      - Ngày hiệu lực                               │
│   • items[]          : Object[]  - Danh sách item báo giá                      │
│     ├── route        : String    - Tuyến (MK-HN, MK-HP)                        │
│     ├── vehicle_type : String    - Loại xe                                     │
│     ├── price        : Number    - Giá                                         │
│     └── unit         : String    - Đơn vị (TRIP, KG)                           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Entity Extraction Examples

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ENTITY EXTRACTION EXAMPLES                                    │
│                                                                                  │
│   EXAMPLE 1: Create Job from Message                                            │
│   ─────────────────────────────────────                                         │
│   Input: "Book xe 1.25T cho DRT1 ngày 15/01, 22h, invoice 260115DRT-001,       │
│           hàng PCB 8 box, giao nội thành HN"                                    │
│                                                                                  │
│   Output:                                                                        │
│   {                                                                              │
│     "customer_code": "DRT1",                                                    │
│     "booking_date": "2026-01-15",                                              │
│     "pickup_time": "22:00",                                                    │
│     "vehicle_type": "1.25T",                                                   │
│     "invoice_numbers": ["260115DRT-001"],                                      │
│     "cargo_type": "PCB",                                                       │
│     "package_info": "8 box",                                                   │
│     "delivery_address": "Nội thành HN"                                         │
│   }                                                                              │
│                                                                                  │
│   ───────────────────────────────────────────────────────────────────────────   │
│                                                                                  │
│   EXAMPLE 2: Assign Vehicle from Vendor Response                                │
│   ──────────────────────────────────────────────                                │
│   Input: "MK-DRT2 / 13.01 / Invoice: 260113DRTV-08, 260113DRT-F10             │
│           BKS: 29H 88330 - Trần Việt Chung - SĐT 0359.018.595                  │
│           Số CCCD: 001089021335"                                                │
│                                                                                  │
│   Output:                                                                        │
│   {                                                                              │
│     "job_reference": {                                                          │
│       "route": "MK-DRT2",                                                      │
│       "date": "2026-01-13",                                                    │
│       "invoices": ["260113DRTV-08", "260113DRT-F10"]                          │
│     },                                                                          │
│     "license_plate": "29H 88330",                                              │
│     "driver_name": "Trần Việt Chung",                                          │
│     "driver_phone": "0359018595",                                              │
│     "driver_id_card": "001089021335"                                           │
│   }                                                                              │
│                                                                                  │
│   ───────────────────────────────────────────────────────────────────────────   │
│                                                                                  │
│   EXAMPLE 3: Vendor Quote                                                       │
│   ───────────────────────                                                       │
│   Input: "Báo giá Tam Bảo tháng 1/2026:                                        │
│           MK-HN: 1.25T=850K, 2.5T=1.2M, 5T=1.8M                                │
│           MK-HP: 1.25T=2.5M, 2.5T=3.2M                                         │
│           MK-BN: 1.25T=700K"                                                    │
│                                                                                  │
│   Output:                                                                        │
│   {                                                                              │
│     "vendor_code": "TB",                                                        │
│     "vendor_name": "Tam Bảo",                                                  │
│     "effective_date": "2026-01-01",                                            │
│     "items": [                                                                   │
│       {"route": "MK-HN", "vehicle_type": "1.25T", "price": 850000},           │
│       {"route": "MK-HN", "vehicle_type": "2.5T", "price": 1200000},           │
│       {"route": "MK-HN", "vehicle_type": "5T", "price": 1800000},             │
│       {"route": "MK-HP", "vehicle_type": "1.25T", "price": 2500000},          │
│       {"route": "MK-HP", "vehicle_type": "2.5T", "price": 3200000},           │
│       {"route": "MK-BN", "vehicle_type": "1.25T", "price": 700000}            │
│     ]                                                                            │
│   }                                                                              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Entity Extraction Code

```python
# entity_extraction.py

import re
from typing import Dict, Any, Optional
from datetime import datetime, date

class EntityExtractor:
    """Extract structured entities from text"""
    
    # Regex patterns for Vietnamese logistics data
    PATTERNS = {
        'license_plate': r'(?:BKS[:\s]*)?(\d{2}[A-Z]\s*[-\s]?\d{4,5})',
        'phone': r'(?:SĐT[:\s]*|SDT[:\s]*)?(\d{4}[.\s-]?\d{3}[.\s-]?\d{3})',
        'cccd': r'(?:CCCD[:\s]*|CMND[:\s]*)?(\d{9,12})',
        'date_dmy': r'(\d{1,2}[./]\d{1,2}(?:[./]\d{2,4})?)',
        'time': r'(\d{1,2}[:\.]?\d{2})\s*(?:h|H|giờ)?',
        'invoice': r'(\d{6}[A-Z]{2,4}[-]?[A-Z]?\d{1,3})',
        'price_vnd': r'(\d{1,3}(?:[.,]\d{3})*)\s*(?:K|k|VND|VNĐ|đ|đồng|M|m)?',
        'vehicle_type': r'(\d+(?:\.\d+)?[Tt]|CONT\d{2})',
        'route': r'([A-Z]{2,3}[-][A-Z]{2,3})',
        'customer_code': r'\b([A-Z]{2,5}\d?)\b',
    }
    
    def extract_vehicle_info(self, text: str) -> Dict[str, Any]:
        """Extract vehicle and driver info from vendor response"""
        result = {}
        
        # License plate
        match = re.search(self.PATTERNS['license_plate'], text, re.I)
        if match:
            result['license_plate'] = match.group(1).replace(' ', '').replace('-', ' ')
        
        # Phone number
        match = re.search(self.PATTERNS['phone'], text)
        if match:
            result['driver_phone'] = re.sub(r'[.\s-]', '', match.group(1))
        
        # CCCD
        match = re.search(self.PATTERNS['cccd'], text)
        if match:
            result['driver_id_card'] = match.group(1)
        
        # Driver name (text between plate and phone, or after "Lái xe:")
        name_patterns = [
            r'BKS[:\s]*\d{2}[A-Z]\s*\d{4,5}\s*[-–]\s*([^-–]+?)\s*[-–]\s*(?:SĐT|SDT|\d{4})',
            r'(?:Lái xe|LX)[:\s]*([^,\n]+)',
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                result['driver_name'] = match.group(1).strip()
                break
        
        return result
    
    def extract_job_reference(self, text: str) -> Dict[str, Any]:
        """Extract job reference from message context"""
        result = {}
        
        # Route (e.g., MK-DRT2)
        match = re.search(r'(MK[-]?[A-Z]{2,5}\d?)', text, re.I)
        if match:
            result['route'] = match.group(1).upper()
        
        # Date
        match = re.search(self.PATTERNS['date_dmy'], text)
        if match:
            result['date'] = self._parse_date(match.group(1))
        
        # Invoice numbers
        invoices = re.findall(self.PATTERNS['invoice'], text)
        if invoices:
            result['invoices'] = invoices
        
        return result
    
    def extract_booking_info(self, text: str) -> Dict[str, Any]:
        """Extract booking info from customer message"""
        result = {}
        
        # Customer code
        match = re.search(r'(?:cho|KH|khách)\s*([A-Z]{2,5}\d?)', text, re.I)
        if match:
            result['customer_code'] = match.group(1).upper()
        
        # Date
        match = re.search(self.PATTERNS['date_dmy'], text)
        if match:
            result['booking_date'] = self._parse_date(match.group(1))
        
        # Time
        match = re.search(self.PATTERNS['time'], text)
        if match:
            result['pickup_time'] = self._parse_time(match.group(1))
        
        # Vehicle type
        match = re.search(self.PATTERNS['vehicle_type'], text, re.I)
        if match:
            result['vehicle_type'] = match.group(1).upper()
        
        # Invoice
        invoices = re.findall(self.PATTERNS['invoice'], text)
        if invoices:
            result['invoice_numbers'] = invoices
        
        # Package info (e.g., "8 box", "5 pallets")
        match = re.search(r'(\d+\s*(?:box|thùng|pallet|kiện|bao))', text, re.I)
        if match:
            result['package_info'] = match.group(1)
        
        return result
    
    def extract_quote_info(self, text: str) -> Dict[str, Any]:
        """Extract vendor quote info"""
        result = {
            'items': []
        }
        
        # Vendor name/code
        vendor_patterns = [
            (r'(?:Báo giá|Quote)\s+([A-Za-z\s]+?)(?:\s+tháng|\s+\d)', 'vendor_name'),
            (r'\b(TB|VT|NB)\b', 'vendor_code'),
        ]
        for pattern, key in vendor_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                result[key] = match.group(1).strip()
        
        # Extract price items: route: vehicle=price
        item_pattern = r'([A-Z]{2,3}[-][A-Z]{2,3})[:\s]+(\d+(?:\.\d+)?[Tt])\s*[=:]\s*(\d{1,3}(?:[.,]\d{3})*)\s*([KkMm])?'
        for match in re.finditer(item_pattern, text, re.I):
            route, vehicle, price, unit = match.groups()
            price_val = float(re.sub(r'[.,]', '', price))
            if unit and unit.upper() == 'M':
                price_val *= 1000000
            elif unit and unit.upper() == 'K':
                price_val *= 1000
            
            result['items'].append({
                'route': route.upper(),
                'vehicle_type': vehicle.upper(),
                'price': int(price_val)
            })
        
        return result
    
    def _parse_date(self, date_str: str) -> str:
        """Parse Vietnamese date format to ISO"""
        parts = re.split(r'[./]', date_str)
        if len(parts) == 2:
            day, month = parts
            year = datetime.now().year
        else:
            day, month, year = parts
            if len(year) == 2:
                year = '20' + year
        
        return f"{year}-{int(month):02d}-{int(day):02d}"
    
    def _parse_time(self, time_str: str) -> str:
        """Parse Vietnamese time format to HH:MM"""
        clean = re.sub(r'[^\d]', '', time_str)
        if len(clean) <= 2:
            return f"{int(clean):02d}:00"
        else:
            return f"{clean[:2]}:{clean[2:4]}"
```

---

## 3. Document Parsing

### 3.1 Excel Booking File Parser

```python
# document_parser.py

import pandas as pd
from typing import Dict, Any, List
import re

class ExcelBookingParser:
    """Parse Excel booking files from customers"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """Parse Excel booking file and extract structured data"""
        
        # Read Excel file
        df = pd.read_excel(file_path, header=None)
        
        # Convert to text for AI processing
        text_content = self._df_to_text(df)
        
        # Extract data using patterns
        result = {
            'source_file': file_path,
            'raw_content': text_content,
            'extracted_data': {}
        }
        
        # Try pattern-based extraction first
        result['extracted_data'] = self._pattern_extract(text_content)
        
        return result
    
    def _df_to_text(self, df: pd.DataFrame) -> str:
        """Convert DataFrame to searchable text"""
        lines = []
        for idx, row in df.iterrows():
            line = ' | '.join([str(cell) for cell in row if pd.notna(cell)])
            if line.strip():
                lines.append(line)
        return '\n'.join(lines)
    
    def _pattern_extract(self, text: str) -> Dict[str, Any]:
        """Extract data using regex patterns"""
        result = {}
        
        # Customer name patterns
        customer_patterns = [
            r'(?:Công ty|CÔNG TY|Cty)[:\s]*(.+?)(?:\n|$)',
            r'(?:Khách hàng|KHÁCH HÀNG)[:\s]*(.+?)(?:\n|$)',
        ]
        for pattern in customer_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                result['customer_name'] = match.group(1).strip()
                break
        
        # Contact info
        contact_pattern = r'(?:Người book|Người đặt|Liên hệ)[:\s]*([^,\n]+)[,\s]*(\d{10,11})?'
        match = re.search(contact_pattern, text, re.I)
        if match:
            result['contact_name'] = match.group(1).strip()
            if match.group(2):
                result['contact_phone'] = match.group(2)
        
        # Date and time
        date_pattern = r'(?:Ngày|Date)[:\s]*(\d{1,2}[/.-]\d{1,2}[/.-]?\d{0,4})'
        match = re.search(date_pattern, text, re.I)
        if match:
            result['booking_date'] = match.group(1)
        
        time_pattern = r'(?:Giờ|Time|Thời gian)[:\s]*(\d{1,2}[:.h]\d{0,2})'
        match = re.search(time_pattern, text, re.I)
        if match:
            result['pickup_time'] = match.group(1)
        
        # Invoice numbers
        invoice_pattern = r'(\d{6}[A-Z]{2,4}[-]?[A-Z]?\d{1,3})'
        invoices = re.findall(invoice_pattern, text)
        if invoices:
            result['invoice_numbers'] = invoices
        
        # Cargo info
        cargo_pattern = r'(?:Hàng|Cargo|Loại hàng)[:\s]*([^\n]+)'
        match = re.search(cargo_pattern, text, re.I)
        if match:
            result['cargo_type'] = match.group(1).strip()
        
        # Package info
        package_pattern = r'(\d+)\s*(box|thùng|pallet|kiện|carton)'
        match = re.search(package_pattern, text, re.I)
        if match:
            result['package_info'] = f"{match.group(1)} {match.group(2)}"
        
        return result


class ImageDocumentParser:
    """Parse images using OCR + AI"""
    
    def __init__(self, ai_service):
        self.ai_service = ai_service
    
    async def parse(self, image_path: str, doc_type: str = 'general') -> Dict[str, Any]:
        """Parse image and extract structured data"""
        
        # Use Gemini Vision or Document AI for OCR
        ocr_text = await self._ocr_image(image_path)
        
        # Use AI to structure the extracted text
        structured_data = await self._structure_data(ocr_text, doc_type)
        
        return {
            'source_file': image_path,
            'ocr_text': ocr_text,
            'extracted_data': structured_data
        }
    
    async def _ocr_image(self, image_path: str) -> str:
        """Perform OCR on image"""
        import google.generativeai as genai
        from PIL import Image
        
        img = Image.open(image_path)
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content([
            "Đọc và trích xuất tất cả văn bản từ hình ảnh này. Giữ nguyên format.",
            img
        ])
        
        return response.text
    
    async def _structure_data(self, text: str, doc_type: str) -> Dict[str, Any]:
        """Structure OCR text based on document type"""
        
        prompts = {
            'invoice': """Trích xuất thông tin hóa đơn:
- invoice_number: Số hóa đơn
- date: Ngày
- customer_name: Tên khách hàng
- items: Danh sách hàng hóa
- total_amount: Tổng tiền""",
            
            'pod': """Trích xuất thông tin biên bản giao hàng:
- delivery_date: Ngày giao
- receiver_name: Người nhận
- signature: Có chữ ký không
- notes: Ghi chú""",
            
            'general': """Trích xuất các thông tin chính từ văn bản."""
        }
        
        prompt = f"""{prompts.get(doc_type, prompts['general'])}

Văn bản:
{text}

Trả lời dạng JSON."""
        
        response = await self.ai_service._call_gemini(prompt)
        
        import json
        try:
            return json.loads(response)
        except:
            return {'raw_text': text}
```

---

## 4. Message Generation

### 4.1 Message Templates

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       MESSAGE TEMPLATES                                          │
│                                                                                  │
│   TEMPLATE: VENDOR_DISPATCH_REQUEST                                             │
│   ─────────────────────────────────                                             │
│   🚛 YÊU CẦU XE - {customer_code}                                              │
│                                                                                  │
│   📅 Ngày: {booking_date}                                                       │
│   ⏰ Giờ: {pickup_time}                                                         │
│   📦 Invoice: {invoice_numbers}                                                 │
│   📋 Hàng: {cargo_type} - {package_info}                                       │
│   🚗 Loại xe: {vehicle_type}                                                   │
│   📍 Giao: {delivery_address}                                                  │
│                                                                                  │
│   Vui lòng điều xe và phản hồi thông tin lái xe.                               │
│                                                                                  │
│   ───────────────────────────────────────────────────────────────────────────   │
│                                                                                  │
│   TEMPLATE: CUSTOMER_VEHICLE_CONFIRMATION                                       │
│   ───────────────────────────────────────                                       │
│   {route} / {date} / {time} / Invoice: {invoices} / {cargo} / {package}        │
│   / {vehicle_type} / BKS: {license_plate} / {driver_name}                      │
│   - {driver_phone} - CCCD: {driver_id_card}                                    │
│                                                                                  │
│   ───────────────────────────────────────────────────────────────────────────   │
│                                                                                  │
│   TEMPLATE: JOB_STATUS_UPDATE                                                   │
│   ───────────────────────────                                                   │
│   📦 Job {job_number}                                                           │
│   🔄 Trạng thái: {old_status} → {new_status}                                   │
│   ⏰ Thời gian: {timestamp}                                                     │
│   📝 Ghi chú: {notes}                                                          │
│                                                                                  │
│   ───────────────────────────────────────────────────────────────────────────   │
│                                                                                  │
│   TEMPLATE: DAILY_SUMMARY                                                       │
│   ───────────────────────                                                       │
│   📊 BÁO CÁO NGÀY {date}                                                       │
│                                                                                  │
│   Tổng job: {total_jobs}                                                        │
│   ✅ Hoàn thành: {completed}                                                    │
│   🚚 Đang chạy: {in_transit}                                                   │
│   ⏳ Chờ xử lý: {pending}                                                       │
│                                                                                  │
│   Doanh thu: {revenue:,.0f} VND                                                 │
│   Chi phí: {cost:,.0f} VND                                                      │
│   Lợi nhuận: {profit:,.0f} VND ({margin:.1f}%)                                 │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Message Generator Code

```python
# message_generator.py

from typing import Dict, Any
from string import Template
import re

class MessageGenerator:
    """Generate messages from templates"""
    
    TEMPLATES = {
        'VENDOR_DISPATCH': """🚛 YÊU CẦU XE - $customer_code

📅 Ngày: $booking_date
⏰ Giờ: $pickup_time
📦 Invoice: $invoice_numbers
📋 Hàng: $cargo_type - $package_info
🚗 Loại xe: $vehicle_type
📍 Giao: $delivery_address

Vui lòng điều xe và phản hồi thông tin lái xe.""",

        'CUSTOMER_CONFIRM': """$route / $date / $time / Invoice: $invoices / $cargo / $package / $vehicle_type / BKS: $license_plate / $driver_name - $driver_phone - CCCD: $driver_id_card""",
        
        'STATUS_UPDATE': """📦 Job $job_number
🔄 Trạng thái: $old_status → $new_status
⏰ Thời gian: $timestamp
📝 Ghi chú: $notes""",

        'DAILY_SUMMARY': """📊 BÁO CÁO NGÀY $date

Tổng job: $total_jobs
✅ Hoàn thành: $completed
🚚 Đang chạy: $in_transit
⏳ Chờ xử lý: $pending

Doanh thu: $revenue VND
Chi phí: $cost VND
Lợi nhuận: $profit VND ($margin%)"""
    }
    
    def generate(self, template_name: str, data: Dict[str, Any]) -> str:
        """Generate message from template"""
        
        template_str = self.TEMPLATES.get(template_name)
        if not template_str:
            raise ValueError(f"Unknown template: {template_name}")
        
        # Format data
        formatted_data = self._format_data(data)
        
        # Generate message
        template = Template(template_str)
        
        try:
            message = template.substitute(formatted_data)
        except KeyError as e:
            # Use safe_substitute for partial data
            message = template.safe_substitute(formatted_data)
        
        return message
    
    def _format_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Format data values for template"""
        formatted = {}
        
        for key, value in data.items():
            if value is None:
                formatted[key] = 'N/A'
            elif isinstance(value, list):
                formatted[key] = ', '.join(str(v) for v in value)
            elif isinstance(value, (int, float)):
                if key in ['revenue', 'cost', 'profit']:
                    formatted[key] = f"{value:,.0f}"
                elif key == 'margin':
                    formatted[key] = f"{value:.1f}"
                else:
                    formatted[key] = str(value)
            else:
                formatted[key] = str(value)
        
        return formatted
    
    def generate_customer_confirm(self, job_data: Dict, vehicle_data: Dict) -> str:
        """Generate customer confirmation message"""
        
        data = {
            'route': f"MK-{job_data.get('customer_code', 'XX')}",
            'date': job_data.get('booking_date', ''),
            'time': job_data.get('pickup_time', ''),
            'invoices': job_data.get('invoice_numbers', ''),
            'cargo': job_data.get('cargo_type', ''),
            'package': job_data.get('package_info', ''),
            'vehicle_type': job_data.get('vehicle_type', ''),
            'license_plate': vehicle_data.get('license_plate', ''),
            'driver_name': vehicle_data.get('driver_name', ''),
            'driver_phone': vehicle_data.get('driver_phone', ''),
            'driver_id_card': vehicle_data.get('driver_id_card', ''),
        }
        
        return self.generate('CUSTOMER_CONFIRM', data)
```

---

## 📊 SUMMARY

### Key Components
1. **Intent Detection** - Classify user requests into action categories
2. **Entity Extraction** - Extract structured data from unstructured text
3. **Document Parsing** - Process Excel, PDF, images
4. **Message Generation** - Create formatted messages from templates

### Supported Intents
- Job Management: create, update, cancel, assign, complete, search
- Pricing: vendor quotes, customer quotes, rate lookup
- Financial: statements, reconciliation, reports
- General: status queries, help

### Entity Types
- Job entities: customer, date, time, invoice, cargo, vehicle
- Vehicle entities: license plate, driver name, phone, ID card
- Quote entities: vendor, route, vehicle type, price

### Integration
- **AI Service**: Gemini for detection and extraction
- **Database**: Store extracted entities
- **n8n**: Trigger workflows based on intents
