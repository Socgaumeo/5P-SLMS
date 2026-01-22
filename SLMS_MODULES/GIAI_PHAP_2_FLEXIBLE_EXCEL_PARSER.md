# 🎯 GIẢI PHÁP 2: FLEXIBLE EXCEL PARSER

## Mục lục

1. [Tổng quan vấn đề](#1-tổng-quan-vấn-đề)
2. [Kiến trúc giải pháp](#2-kiến-trúc-giải-pháp)
3. [Chi tiết Implementation](#3-chi-tiết-implementation)
4. [Files cần tạo](#4-files-cần-tạo)
5. [Hướng dẫn từng bước](#5-hướng-dẫn-từng-bước)
6. [Test cases](#6-test-cases)
7. [Integration với hệ thống hiện tại](#7-integration-với-hệ-thống-hiện-tại)

---

## 1. TỔNG QUAN VẤN ĐỀ

### 1.1 Vấn đề với Excel Parser cứng

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    EXCEL PARSING PROBLEM                                         │
│                                                                                  │
│   Expected Format:          Actual Variations:                                  │
│   ─────────────────         ─────────────────                                   │
│                                                                                  │
│   Header: "Ngày"            → Date / Ngày lấy hàng / Pickup Date / Ngày LH     │
│   Value:  17/01/2026        → 17/1/26 / 2026-01-17 / 17-Jan / Jan 17           │
│                                                                                  │
│   Header: "Giờ"             → Time / Giờ lấy / Pickup Time / Giờ LH            │
│   Value:  22:00             → 22h / 10PM / 22:00:00 / 22h00                     │
│                                                                                  │
│   Header: "Khách hàng"      → Customer / KH / Tên KH / Công ty / Client        │
│   Value:  DREAMTECH         → DRT1 / Dreamtech Vietnam / DRT                   │
│                                                                                  │
│   Header: "Loại xe"         → Vehicle / Xe / Truck / Trọng tải / Tải           │
│   Value:  Xe 5 tấn          → 5T / 5 ton / xe tải 5T / cont 20                 │
│                                                                                  │
│   ❌ Fixed column mapping fails with variations!                                │
│   ❌ Mỗi khách hàng gửi Excel format khác nhau!                                 │
│   ❌ Code phải sửa liên tục khi có format mới!                                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Các dạng Excel thường gặp trong logistics

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    EXCEL FORMAT TYPES                                            │
│                                                                                  │
│   TYPE 1: Table Format (Dạng bảng)                                              │
│   ────────────────────────────────                                              │
│   ┌─────────┬─────────┬────────────┬─────────┬───────────┐                     │
│   │ Ngày    │ Giờ     │ Khách hàng │ Loại xe │ Điểm đến  │                     │
│   ├─────────┼─────────┼────────────┼─────────┼───────────┤                     │
│   │ 17/1/26 │ 22:00   │ DRT1       │ 5T      │ HP        │                     │
│   │ 18/1/26 │ 08:00   │ SEVT       │ 10T     │ QN        │                     │
│   └─────────┴─────────┴────────────┴─────────┴───────────┘                     │
│                                                                                  │
│   TYPE 2: Form Format (Dạng form key-value)                                     │
│   ─────────────────────────────────────────                                     │
│   ┌────────────────┬────────────────────────┐                                  │
│   │ Booking Date:  │ 17/01/2026             │                                  │
│   │ Customer:      │ DREAMTECH VIETNAM      │                                  │
│   │ Vehicle Type:  │ Container 20ft         │                                  │
│   │ Pickup:        │ KCN Bình Dương         │                                  │
│   │ Delivery:      │ Cảng Hải Phòng         │                                  │
│   └────────────────┴────────────────────────┘                                  │
│                                                                                  │
│   TYPE 3: Mixed Format (Header + Details)                                       │
│   ───────────────────────────────────────                                       │
│   ┌─────────────────────────────────────────┐                                  │
│   │ BOOKING FORM - DREAMTECH                │ ← Header info                    │
│   │ Date: 17/01/2026                        │                                  │
│   ├─────────────────────────────────────────┤                                  │
│   │ STT │ Hàng hóa │ SL │ Điểm giao         │ ← Table details                 │
│   │ 1   │ Linh kiện│ 50 │ HP                │                                  │
│   │ 2   │ Bao bì   │ 30 │ QN                │                                  │
│   └─────────────────────────────────────────┘                                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Giải pháp: AI-Powered Schema Detection

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    AI SCHEMA DETECTION FLOW                                      │
│                                                                                  │
│   Excel File                                                                     │
│       │                                                                          │
│       ▼                                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │ STAGE 1: Format Detection                                                │  │
│   │ ─────────────────────────                                                │  │
│   │ • Detect: Table / Form / Mixed                                          │  │
│   │ • Identify header row position                                          │  │
│   │ • Find data boundaries                                                  │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│       │                                                                          │
│       ▼                                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │ STAGE 2: Schema Detection (AI)                                          │  │
│   │ ─────────────────────────────                                           │  │
│   │ • AI analyzes headers + sample data                                     │  │
│   │ • Maps to standard fields (date, time, customer, etc.)                 │  │
│   │ • Detects date/time formats                                             │  │
│   │ • Returns confidence scores                                             │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│       │                                                                          │
│       ▼                                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │ STAGE 3: Data Extraction                                                │  │
│   │ ────────────────────────                                                │  │
│   │ • Parse values according to detected schema                            │  │
│   │ • Normalize dates, times, customer codes                               │  │
│   │ • Resolve customer/vehicle references from DB                          │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│       │                                                                          │
│       ▼                                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │ STAGE 4: Validation & Confirmation                                      │  │
│   │ ─────────────────────────────────                                       │  │
│   │ • Validate required fields                                              │  │
│   │ • Flag low-confidence mappings                                          │  │
│   │ • Request human confirmation if needed                                  │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│       │                                                                          │
│       ▼                                                                          │
│   Structured Jobs Data                                                          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. KIẾN TRÚC GIẢI PHÁP

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    FLEXIBLE EXCEL PARSER COMPONENTS                              │
│                                                                                  │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│   │  ExcelReader    │───▶│ SchemaDetector  │───▶│  DataExtractor  │            │
│   │                 │    │                 │    │                 │            │
│   │ • Read file     │    │ • AI analysis   │    │ • Parse values  │            │
│   │ • Preview data  │    │ • Field mapping │    │ • Normalize     │            │
│   │ • Detect format │    │ • Confidence    │    │ • Resolve refs  │            │
│   └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│           │                       │                      │                      │
│           │                       │                      │                      │
│           ▼                       ▼                      ▼                      │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                         ValueNormalizer                                  │  │
│   │ ──────────────────────────────────────────────────────────────────────  │  │
│   │ • DateNormalizer: 17/1/26, 2026-01-17, Jan 17 → datetime                │  │
│   │ • TimeNormalizer: 22h, 10PM, 22:00 → time                               │  │
│   │ • CustomerResolver: DRT1, Dreamtech → customer_id                       │  │
│   │ • VehicleTypeNormalizer: 5T, xe 5 tấn → vehicle_type_id                 │  │
│   │ • LocationResolver: HP, Hải Phòng → location info                       │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│           │                                                                      │
│           ▼                                                                      │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                         ValidationLayer                                  │  │
│   │ ──────────────────────────────────────────────────────────────────────  │  │
│   │ • Required fields check                                                  │  │
│   │ • Business rules validation                                              │  │
│   │ • Confidence threshold check                                             │  │
│   │ • Generate confirmation request                                          │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    DATA FLOW                                                     │
│                                                                                  │
│   1. User uploads Excel                                                         │
│      │                                                                          │
│      ▼                                                                          │
│   2. ExcelReader.read()                                                         │
│      • Output: RawExcelData(sheets, cells, merged_cells)                       │
│      │                                                                          │
│      ▼                                                                          │
│   3. ExcelReader.detect_format()                                               │
│      • Output: ExcelFormat(type="table"|"form"|"mixed", header_row, data_range)│
│      │                                                                          │
│      ▼                                                                          │
│   4. SchemaDetector.detect()                                                   │
│      • Input: headers + sample_rows (3-5 rows)                                 │
│      • AI Prompt: "Map these columns to standard fields..."                    │
│      • Output: SchemaMapping(field_mappings, confidence_scores)                │
│      │                                                                          │
│      ▼                                                                          │
│   5. DataExtractor.extract()                                                   │
│      • Apply schema mapping                                                     │
│      • Call ValueNormalizer for each field                                     │
│      • Output: List[ExtractedRow]                                              │
│      │                                                                          │
│      ▼                                                                          │
│   6. ValidationLayer.validate()                                                │
│      • Check required fields                                                    │
│      • Flag low confidence                                                      │
│      • Output: ValidationResult(rows, warnings, errors, needs_confirmation)    │
│      │                                                                          │
│      ▼                                                                          │
│   7. Return to user for confirmation                                           │
│      • Show parsed data                                                         │
│      • Highlight uncertain fields                                              │
│      • User confirms/edits                                                      │
│      │                                                                          │
│      ▼                                                                          │
│   8. Create jobs in database                                                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. CHI TIẾT IMPLEMENTATION

### 3.1 File: `excel_reader.py`

```python
# backend/app/ai/excel/excel_reader.py

import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import openpyxl
from openpyxl.utils import get_column_letter


class ExcelFormatType(Enum):
    """Loại format của Excel file"""
    TABLE = "table"       # Dạng bảng với header row
    FORM = "form"         # Dạng form key-value
    MIXED = "mixed"       # Dạng mixed (header + table)
    UNKNOWN = "unknown"   # Không xác định


@dataclass
class ExcelFormat:
    """Thông tin format của Excel file"""
    format_type: ExcelFormatType
    header_row: Optional[int]        # Row chứa header (0-indexed), None nếu form
    data_start_row: int              # Row bắt đầu data
    data_end_row: int                # Row kết thúc data
    data_columns: List[str]          # Các column có data (A, B, C...)
    has_merged_cells: bool           # Có merged cells không
    form_pairs: Optional[List[Tuple[str, str]]] = None  # Key-value pairs nếu là form


@dataclass  
class RawExcelData:
    """Raw data đọc từ Excel"""
    sheets: List[str]                # Tên các sheets
    active_sheet: str                # Sheet đang active
    headers: Optional[List[str]]     # Headers nếu có
    rows: List[List[Any]]            # Data rows
    format_info: ExcelFormat         # Format information
    raw_df: pd.DataFrame             # Raw pandas DataFrame


class ExcelReader:
    """
    Đọc và phân tích cấu trúc Excel file
    """
    
    def __init__(self):
        self.workbook = None
        self.active_sheet = None
    
    def read(self, file_path: str, sheet_name: Optional[str] = None) -> RawExcelData:
        """
        Đọc Excel file và trả về raw data
        
        Args:
            file_path: Đường dẫn file Excel
            sheet_name: Tên sheet cần đọc (None = active sheet)
        
        Returns:
            RawExcelData object
        """
        # Load workbook với openpyxl để có thêm metadata
        self.workbook = openpyxl.load_workbook(file_path, data_only=True)
        
        sheets = self.workbook.sheetnames
        self.active_sheet = sheet_name or self.workbook.active.title
        
        # Đọc với pandas
        df = pd.read_excel(file_path, sheet_name=self.active_sheet, header=None)
        
        # Detect format
        format_info = self._detect_format(df)
        
        # Extract headers và rows dựa trên format
        headers = None
        rows = []
        
        if format_info.format_type == ExcelFormatType.TABLE:
            if format_info.header_row is not None:
                headers = df.iloc[format_info.header_row].tolist()
                # Clean headers
                headers = [str(h).strip() if pd.notna(h) else f"Column_{i}" 
                          for i, h in enumerate(headers)]
            
            rows = df.iloc[format_info.data_start_row:format_info.data_end_row + 1].values.tolist()
        
        elif format_info.format_type == ExcelFormatType.FORM:
            # Form format - extract key-value pairs
            format_info.form_pairs = self._extract_form_pairs(df)
            rows = [[k, v] for k, v in format_info.form_pairs]
        
        elif format_info.format_type == ExcelFormatType.MIXED:
            # Mixed format - có cả header info và table
            # TODO: Handle mixed format
            pass
        
        return RawExcelData(
            sheets=sheets,
            active_sheet=self.active_sheet,
            headers=headers,
            rows=rows,
            format_info=format_info,
            raw_df=df
        )
    
    def _detect_format(self, df: pd.DataFrame) -> ExcelFormat:
        """
        Phát hiện format của Excel file
        
        Heuristics:
        - Table: Row đầu có nhiều giá trị text, các row sau có pattern tương tự
        - Form: Column A chứa labels, Column B chứa values
        - Mixed: Có section header + table bên dưới
        """
        if df.empty:
            return ExcelFormat(
                format_type=ExcelFormatType.UNKNOWN,
                header_row=None,
                data_start_row=0,
                data_end_row=0,
                data_columns=[],
                has_merged_cells=False
            )
        
        # Check for merged cells
        ws = self.workbook[self.active_sheet]
        has_merged = len(ws.merged_cells.ranges) > 0
        
        # Analyze structure
        num_rows, num_cols = df.shape
        
        # Check if it's a form (key-value pairs in columns A-B)
        if self._is_form_format(df):
            return ExcelFormat(
                format_type=ExcelFormatType.FORM,
                header_row=None,
                data_start_row=0,
                data_end_row=num_rows - 1,
                data_columns=['A', 'B'],
                has_merged_cells=has_merged
            )
        
        # Find header row for table format
        header_row = self._find_header_row(df)
        
        # Find data boundaries
        data_start, data_end = self._find_data_boundaries(df, header_row)
        
        # Get columns with data
        data_cols = self._get_data_columns(df)
        
        return ExcelFormat(
            format_type=ExcelFormatType.TABLE,
            header_row=header_row,
            data_start_row=data_start,
            data_end_row=data_end,
            data_columns=data_cols,
            has_merged_cells=has_merged
        )
    
    def _is_form_format(self, df: pd.DataFrame) -> bool:
        """
        Kiểm tra xem có phải dạng form key-value không
        
        Criteria:
        - Chủ yếu 2 columns
        - Column A chứa text labels (kết thúc bằng ":" hoặc là keyword)
        - Column B chứa values
        """
        if df.shape[1] < 2:
            return False
        
        # Chỉ check 2 columns đầu
        col_a = df.iloc[:, 0].dropna()
        col_b = df.iloc[:, 1].dropna()
        
        if len(col_a) < 3:
            return False
        
        # Check xem column A có pattern của labels không
        label_patterns = [':', 'date', 'time', 'customer', 'vehicle', 
                         'ngày', 'giờ', 'khách', 'xe', 'hàng']
        
        label_count = 0
        for val in col_a:
            val_str = str(val).lower().strip()
            if any(p in val_str for p in label_patterns):
                label_count += 1
        
        # Nếu >50% rows có label pattern -> form format
        return label_count / len(col_a) > 0.5
    
    def _find_header_row(self, df: pd.DataFrame) -> Optional[int]:
        """
        Tìm row chứa header
        
        Heuristics:
        - Row có nhiều giá trị text
        - Row có các keyword phổ biến (date, time, customer, etc.)
        - Row ngay trước các data rows
        """
        header_keywords = [
            'stt', 'no', 'ngày', 'date', 'giờ', 'time', 
            'khách', 'customer', 'xe', 'vehicle', 'hàng', 'cargo',
            'điểm', 'location', 'ghi chú', 'note', 'sl', 'qty'
        ]
        
        best_row = None
        best_score = 0
        
        # Check first 10 rows
        for i in range(min(10, len(df))):
            row = df.iloc[i]
            score = 0
            
            non_empty = row.dropna()
            if len(non_empty) < 2:
                continue
            
            # Check for keywords
            for val in non_empty:
                val_str = str(val).lower().strip()
                if any(kw in val_str for kw in header_keywords):
                    score += 2
                # Bonus nếu là text ngắn (likely header)
                if len(val_str) < 30 and not val_str.replace('.', '').replace(',', '').isdigit():
                    score += 1
            
            if score > best_score:
                best_score = score
                best_row = i
        
        return best_row if best_score >= 3 else 0
    
    def _find_data_boundaries(self, df: pd.DataFrame, header_row: Optional[int]) -> Tuple[int, int]:
        """Tìm row bắt đầu và kết thúc của data"""
        start_row = (header_row + 1) if header_row is not None else 0
        
        # Tìm row cuối có data
        end_row = len(df) - 1
        for i in range(len(df) - 1, start_row - 1, -1):
            if df.iloc[i].notna().any():
                end_row = i
                break
        
        return start_row, end_row
    
    def _get_data_columns(self, df: pd.DataFrame) -> List[str]:
        """Lấy danh sách columns có data"""
        cols = []
        for i in range(df.shape[1]):
            if df.iloc[:, i].notna().any():
                cols.append(get_column_letter(i + 1))
        return cols
    
    def _extract_form_pairs(self, df: pd.DataFrame) -> List[Tuple[str, str]]:
        """Extract key-value pairs từ form format"""
        pairs = []
        
        for i in range(len(df)):
            key = df.iloc[i, 0] if pd.notna(df.iloc[i, 0]) else None
            value = df.iloc[i, 1] if df.shape[1] > 1 and pd.notna(df.iloc[i, 1]) else None
            
            if key is not None:
                # Clean key
                key_str = str(key).strip().rstrip(':')
                value_str = str(value).strip() if value is not None else ""
                pairs.append((key_str, value_str))
        
        return pairs
    
    def get_preview(self, file_path: str, max_rows: int = 5) -> Dict[str, Any]:
        """
        Lấy preview data để hiển thị cho user xác nhận
        """
        data = self.read(file_path)
        
        preview_rows = data.rows[:max_rows]
        
        return {
            "format_type": data.format_info.format_type.value,
            "headers": data.headers,
            "sample_rows": preview_rows,
            "total_rows": len(data.rows),
            "sheets": data.sheets,
            "active_sheet": data.active_sheet
        }
```

### 3.2 File: `schema_detector.py`

```python
# backend/app/ai/excel/schema_detector.py

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
import re

from app.ai.clients import AIClientManager


@dataclass
class FieldMapping:
    """Mapping từ Excel column sang standard field"""
    excel_column: str           # Column trong Excel (header text)
    excel_column_index: int     # Column index (0-based)
    standard_field: str         # Standard field name (date, time, customer, etc.)
    confidence: float           # Confidence score 0-1
    detected_format: Optional[str] = None  # Format detected (e.g., "DD/MM/YYYY")
    sample_values: List[str] = field(default_factory=list)


@dataclass
class SchemaMapping:
    """Kết quả detect schema"""
    field_mappings: List[FieldMapping]
    unmapped_columns: List[str]     # Columns không map được
    overall_confidence: float        # Confidence tổng thể
    warnings: List[str] = field(default_factory=list)


class SchemaDetector:
    """
    AI-powered schema detection cho Excel files
    """
    
    # Standard fields cho logistics
    STANDARD_FIELDS = {
        "date": {
            "description": "Ngày lấy/giao hàng",
            "aliases": ["ngày", "date", "ngày lấy hàng", "pickup date", "ngày lh", 
                       "ngày giao", "delivery date", "ngày vận chuyển"],
            "required": True
        },
        "time": {
            "description": "Giờ lấy/giao hàng", 
            "aliases": ["giờ", "time", "giờ lấy", "pickup time", "giờ lh",
                       "giờ giao", "delivery time", "giờ yêu cầu"],
            "required": False
        },
        "customer_code": {
            "description": "Mã khách hàng",
            "aliases": ["khách hàng", "kh", "customer", "tên kh", "công ty", 
                       "client", "mã kh", "customer code", "cust"],
            "required": True
        },
        "vehicle_type": {
            "description": "Loại xe/trọng tải",
            "aliases": ["loại xe", "vehicle", "xe", "truck type", "loại",
                       "trọng tải", "tải", "container", "cont"],
            "required": True
        },
        "origin": {
            "description": "Điểm lấy hàng",
            "aliases": ["điểm lấy", "origin", "lấy tại", "pickup", "địa chỉ lấy",
                       "from", "lấy hàng", "điểm đi", "nơi lấy"],
            "required": False
        },
        "destination": {
            "description": "Điểm giao hàng",
            "aliases": ["điểm đến", "destination", "giao tại", "delivery", 
                       "địa chỉ giao", "to", "giao hàng", "điểm đến", "nơi giao"],
            "required": True
        },
        "cargo": {
            "description": "Mô tả hàng hóa",
            "aliases": ["hàng hóa", "cargo", "hàng", "goods", "mô tả hàng",
                       "description", "loại hàng", "tên hàng", "sản phẩm"],
            "required": False
        },
        "quantity": {
            "description": "Số lượng",
            "aliases": ["số lượng", "quantity", "qty", "sl", "kiện", 
                       "packages", "pcs", "thùng", "carton"],
            "required": False
        },
        "weight": {
            "description": "Trọng lượng",
            "aliases": ["trọng lượng", "weight", "kg", "khối lượng", "tl",
                       "ton", "tấn", "cbm", "khối"],
            "required": False
        },
        "invoice_number": {
            "description": "Số hóa đơn/Invoice",
            "aliases": ["invoice", "hóa đơn", "số hđ", "inv", "invoice no",
                       "mã hđ", "số invoice", "bill"],
            "required": False
        },
        "notes": {
            "description": "Ghi chú",
            "aliases": ["ghi chú", "notes", "note", "yêu cầu", "requirements",
                       "remark", "remarks", "comment"],
            "required": False
        },
        "po_number": {
            "description": "Số PO",
            "aliases": ["po", "po number", "số po", "purchase order", "đơn hàng"],
            "required": False
        },
        "route": {
            "description": "Tuyến đường",
            "aliases": ["tuyến", "route", "tuyến đường", "chặng", "line"],
            "required": False
        }
    }
    
    def __init__(self, ai_client: AIClientManager):
        self.ai = ai_client
    
    async def detect(
        self, 
        headers: List[str], 
        sample_rows: List[List[Any]],
        context: Optional[Dict] = None
    ) -> SchemaMapping:
        """
        Detect schema mapping từ headers và sample data
        
        Args:
            headers: List header texts từ Excel
            sample_rows: 3-5 sample data rows
            context: Additional context (customer list, vehicle types, etc.)
        
        Returns:
            SchemaMapping object
        """
        # Step 1: Try rule-based mapping first
        rule_based_mappings = self._rule_based_mapping(headers)
        
        # Step 2: Use AI for uncertain mappings
        uncertain_columns = [
            h for h in headers 
            if h not in [m.excel_column for m in rule_based_mappings if m.confidence > 0.8]
        ]
        
        ai_mappings = []
        if uncertain_columns:
            ai_mappings = await self._ai_based_mapping(
                headers, sample_rows, uncertain_columns, context
            )
        
        # Step 3: Merge mappings
        all_mappings = self._merge_mappings(rule_based_mappings, ai_mappings)
        
        # Step 4: Calculate overall confidence and warnings
        unmapped = [h for h in headers 
                   if h not in [m.excel_column for m in all_mappings]]
        
        overall_conf = self._calculate_overall_confidence(all_mappings)
        warnings = self._generate_warnings(all_mappings, unmapped)
        
        return SchemaMapping(
            field_mappings=all_mappings,
            unmapped_columns=unmapped,
            overall_confidence=overall_conf,
            warnings=warnings
        )
    
    def _rule_based_mapping(self, headers: List[str]) -> List[FieldMapping]:
        """
        Mapping dựa trên rules (exact match và fuzzy match với aliases)
        """
        mappings = []
        
        for i, header in enumerate(headers):
            header_lower = header.lower().strip()
            
            best_match = None
            best_score = 0
            
            for field_name, field_info in self.STANDARD_FIELDS.items():
                for alias in field_info["aliases"]:
                    alias_lower = alias.lower()
                    
                    # Exact match
                    if header_lower == alias_lower:
                        score = 1.0
                    # Contains match
                    elif alias_lower in header_lower or header_lower in alias_lower:
                        score = 0.8
                    # Partial match (at least 3 chars)
                    elif len(alias_lower) >= 3 and alias_lower[:3] in header_lower:
                        score = 0.6
                    else:
                        score = 0
                    
                    if score > best_score:
                        best_score = score
                        best_match = field_name
            
            if best_match and best_score >= 0.6:
                mappings.append(FieldMapping(
                    excel_column=header,
                    excel_column_index=i,
                    standard_field=best_match,
                    confidence=best_score,
                    detected_format=None,
                    sample_values=[]
                ))
        
        return mappings
    
    async def _ai_based_mapping(
        self,
        headers: List[str],
        sample_rows: List[List[Any]],
        uncertain_columns: List[str],
        context: Optional[Dict]
    ) -> List[FieldMapping]:
        """
        Sử dụng AI để mapping các columns không chắc chắn
        """
        # Prepare sample data for AI
        sample_data = []
        for row in sample_rows[:3]:  # Only first 3 rows
            row_dict = {}
            for i, h in enumerate(headers):
                if i < len(row):
                    row_dict[h] = str(row[i]) if row[i] is not None else ""
            sample_data.append(row_dict)
        
        # Build prompt
        prompt = f"""Analyze this Excel data and map columns to standard logistics fields.

STANDARD FIELDS (choose from these):
{json.dumps({k: v["description"] for k, v in self.STANDARD_FIELDS.items()}, ensure_ascii=False, indent=2)}

EXCEL HEADERS:
{json.dumps(headers, ensure_ascii=False)}

SAMPLE DATA (first 3 rows):
{json.dumps(sample_data, ensure_ascii=False, indent=2)}

COLUMNS TO ANALYZE (uncertain mapping):
{json.dumps(uncertain_columns, ensure_ascii=False)}

{f"CONTEXT (known customers, vehicle types, etc.): {json.dumps(context, ensure_ascii=False)}" if context else ""}

For each uncertain column, determine:
1. Which standard field it maps to (or "unmapped" if no match)
2. Confidence score (0-1)
3. Detected data format if applicable (e.g., date format "DD/MM/YYYY")

Respond in JSON format:
{{
    "mappings": [
        {{
            "excel_column": "column name",
            "standard_field": "field name or unmapped",
            "confidence": 0.95,
            "detected_format": "format or null",
            "reasoning": "brief explanation"
        }}
    ]
}}
"""

        response = await self.ai.generate(
            prompt=prompt,
            system_prompt="You are an expert at analyzing logistics data. Map Excel columns to standard fields accurately.",
            temperature=0.1
        )
        
        # Parse AI response
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                
                mappings = []
                for m in result.get("mappings", []):
                    if m.get("standard_field") != "unmapped":
                        col_idx = headers.index(m["excel_column"]) if m["excel_column"] in headers else -1
                        mappings.append(FieldMapping(
                            excel_column=m["excel_column"],
                            excel_column_index=col_idx,
                            standard_field=m["standard_field"],
                            confidence=float(m.get("confidence", 0.7)),
                            detected_format=m.get("detected_format"),
                            sample_values=[]
                        ))
                return mappings
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error parsing AI response: {e}")
        
        return []
    
    def _merge_mappings(
        self, 
        rule_based: List[FieldMapping], 
        ai_based: List[FieldMapping]
    ) -> List[FieldMapping]:
        """Merge rule-based và AI-based mappings"""
        merged = {}
        
        # Add rule-based first
        for m in rule_based:
            merged[m.excel_column] = m
        
        # Add/override with AI-based if higher confidence
        for m in ai_based:
            if m.excel_column not in merged or m.confidence > merged[m.excel_column].confidence:
                merged[m.excel_column] = m
        
        return list(merged.values())
    
    def _calculate_overall_confidence(self, mappings: List[FieldMapping]) -> float:
        """Calculate overall confidence score"""
        if not mappings:
            return 0.0
        
        # Weight required fields higher
        weighted_sum = 0
        total_weight = 0
        
        for m in mappings:
            field_info = self.STANDARD_FIELDS.get(m.standard_field, {})
            weight = 2.0 if field_info.get("required", False) else 1.0
            weighted_sum += m.confidence * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _generate_warnings(
        self, 
        mappings: List[FieldMapping], 
        unmapped: List[str]
    ) -> List[str]:
        """Generate warnings về mapping"""
        warnings = []
        
        # Check required fields
        mapped_fields = {m.standard_field for m in mappings}
        for field_name, field_info in self.STANDARD_FIELDS.items():
            if field_info.get("required") and field_name not in mapped_fields:
                warnings.append(f"Missing required field: {field_name} ({field_info['description']})")
        
        # Check low confidence mappings
        low_conf = [m for m in mappings if m.confidence < 0.7]
        for m in low_conf:
            warnings.append(f"Low confidence mapping: '{m.excel_column}' → {m.standard_field} ({m.confidence:.0%})")
        
        # Unmapped columns
        if unmapped:
            warnings.append(f"Unmapped columns will be ignored: {', '.join(unmapped)}")
        
        return warnings
```

### 3.3 File: `value_normalizer.py`

```python
# backend/app/ai/excel/value_normalizer.py

from typing import Optional, Any, List, Dict, Tuple
from datetime import datetime, date, time
from dataclasses import dataclass
import re

from app.db.session import get_db
from app.models import Customer, VehicleType


@dataclass
class NormalizedValue:
    """Kết quả normalize"""
    value: Any                      # Giá trị đã normalize
    original: Any                   # Giá trị gốc
    confidence: float               # Confidence score
    resolved_id: Optional[int] = None  # ID nếu resolve được từ DB
    resolved_name: Optional[str] = None  # Tên đầy đủ nếu resolve
    warning: Optional[str] = None   # Warning nếu có


class DateNormalizer:
    """Normalize các format ngày khác nhau"""
    
    # Các pattern ngày phổ biến
    DATE_PATTERNS = [
        # Vietnamese formats
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%d/%m/%Y'),  # 17/01/2026
        (r'(\d{1,2})/(\d{1,2})/(\d{2})', '%d/%m/%y'),  # 17/01/26
        (r'(\d{1,2})-(\d{1,2})-(\d{4})', '%d-%m-%Y'),  # 17-01-2026
        (r'(\d{1,2})-(\d{1,2})-(\d{2})', '%d-%m-%y'),  # 17-01-26
        # ISO format
        (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),      # 2026-01-17
        # English formats
        (r'(\d{1,2})\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', None),  # 17 Jan
        (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{1,2})', None),  # Jan 17
    ]
    
    MONTH_NAMES = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
        'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
        'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    RELATIVE_DATES = {
        'hôm nay': 0, 'today': 0,
        'ngày mai': 1, 'mai': 1, 'tomorrow': 1,
        'ngày kia': 2, 'mốt': 2,
        'hôm qua': -1, 'yesterday': -1,
    }
    
    def normalize(self, value: Any, base_date: Optional[date] = None) -> NormalizedValue:
        """
        Normalize date value
        
        Args:
            value: Raw date value
            base_date: Base date for relative dates (default: today)
        
        Returns:
            NormalizedValue with datetime.date
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            return NormalizedValue(None, value, 0.0, warning="Empty date value")
        
        original = value
        base = base_date or date.today()
        
        # If already a date/datetime
        if isinstance(value, datetime):
            return NormalizedValue(value.date(), original, 1.0)
        if isinstance(value, date):
            return NormalizedValue(value, original, 1.0)
        
        value_str = str(value).strip().lower()
        
        # Check relative dates
        for pattern, delta in self.RELATIVE_DATES.items():
            if pattern in value_str:
                from datetime import timedelta
                result_date = base + timedelta(days=delta)
                return NormalizedValue(result_date, original, 0.95)
        
        # Try date patterns
        for pattern, fmt in self.DATE_PATTERNS:
            match = re.search(pattern, value_str, re.IGNORECASE)
            if match:
                try:
                    if fmt:
                        parsed = datetime.strptime(match.group(), fmt).date()
                        return NormalizedValue(parsed, original, 0.95)
                    else:
                        # Handle month name formats
                        groups = match.groups()
                        day = None
                        month = None
                        for g in groups:
                            if g.isdigit():
                                day = int(g)
                            elif g.lower() in self.MONTH_NAMES:
                                month = self.MONTH_NAMES[g.lower()]
                        
                        if day and month:
                            year = base.year
                            parsed = date(year, month, day)
                            # If parsed date is in past, assume next year
                            if parsed < base:
                                parsed = date(year + 1, month, day)
                            return NormalizedValue(parsed, original, 0.85)
                except ValueError:
                    continue
        
        return NormalizedValue(None, original, 0.0, warning=f"Could not parse date: {value}")


class TimeNormalizer:
    """Normalize các format giờ khác nhau"""
    
    TIME_PATTERNS = [
        (r'(\d{1,2}):(\d{2}):(\d{2})', '%H:%M:%S'),    # 22:00:00
        (r'(\d{1,2}):(\d{2})', '%H:%M'),               # 22:00
        (r'(\d{1,2})h(\d{2})?', None),                 # 22h hoặc 22h00
        (r'(\d{1,2})\s*(AM|PM|am|pm)', None),          # 10PM
        (r'(\d{1,2})g(\d{2})?', None),                 # 22g hoặc 22g00
    ]
    
    def normalize(self, value: Any) -> NormalizedValue:
        """Normalize time value"""
        if value is None or (isinstance(value, str) and not value.strip()):
            return NormalizedValue(None, value, 0.5)  # Time often optional
        
        original = value
        
        # If already a time/datetime
        if isinstance(value, datetime):
            return NormalizedValue(value.time(), original, 1.0)
        if isinstance(value, time):
            return NormalizedValue(value, original, 1.0)
        
        value_str = str(value).strip().lower()
        
        # Try patterns
        for pattern, fmt in self.TIME_PATTERNS:
            match = re.search(pattern, value_str, re.IGNORECASE)
            if match:
                try:
                    if fmt:
                        parsed = datetime.strptime(match.group(), fmt).time()
                        return NormalizedValue(parsed, original, 0.95)
                    else:
                        # Handle special formats (22h, 10PM, etc.)
                        groups = match.groups()
                        hour = int(groups[0])
                        minute = int(groups[1]) if groups[1] and groups[1].isdigit() else 0
                        
                        # Handle AM/PM
                        if len(groups) > 1 and groups[-1] and groups[-1].lower() in ['pm', 'am']:
                            if groups[-1].lower() == 'pm' and hour < 12:
                                hour += 12
                            elif groups[-1].lower() == 'am' and hour == 12:
                                hour = 0
                        
                        parsed = time(hour, minute)
                        return NormalizedValue(parsed, original, 0.9)
                except ValueError:
                    continue
        
        return NormalizedValue(None, original, 0.0, warning=f"Could not parse time: {value}")


class CustomerResolver:
    """Resolve customer từ code/name"""
    
    def __init__(self, db_session=None):
        self.db = db_session
        self._cache = {}  # Cache để không query DB liên tục
    
    async def load_customers(self):
        """Load customers từ DB vào cache"""
        if self.db is None:
            return
        
        customers = self.db.query(Customer).filter(Customer.is_active == True).all()
        
        for c in customers:
            # Add exact code match
            self._cache[c.code.lower()] = {
                'id': c.id,
                'code': c.code,
                'name': c.name,
                'confidence': 1.0
            }
            # Add name variations
            if c.name:
                self._cache[c.name.lower()] = {
                    'id': c.id,
                    'code': c.code,
                    'name': c.name,
                    'confidence': 0.95
                }
                # Add first word of name
                first_word = c.name.split()[0].lower()
                if first_word not in self._cache:
                    self._cache[first_word] = {
                        'id': c.id,
                        'code': c.code,
                        'name': c.name,
                        'confidence': 0.7
                    }
    
    def resolve(self, value: Any) -> NormalizedValue:
        """Resolve customer từ code hoặc name"""
        if value is None or (isinstance(value, str) and not value.strip()):
            return NormalizedValue(None, value, 0.0, warning="Empty customer value")
        
        original = value
        value_str = str(value).strip().lower()
        
        # Try exact match first
        if value_str in self._cache:
            match = self._cache[value_str]
            return NormalizedValue(
                match['code'],
                original,
                match['confidence'],
                resolved_id=match['id'],
                resolved_name=match['name']
            )
        
        # Try partial match
        for key, match in self._cache.items():
            if key in value_str or value_str in key:
                return NormalizedValue(
                    match['code'],
                    original,
                    match['confidence'] * 0.8,  # Lower confidence for partial
                    resolved_id=match['id'],
                    resolved_name=match['name']
                )
        
        # Not found - return as-is with low confidence
        return NormalizedValue(
            value_str.upper(),
            original,
            0.3,
            warning=f"Customer not found in database: {value}"
        )


class VehicleTypeNormalizer:
    """Normalize và resolve vehicle types"""
    
    # Common aliases
    VEHICLE_ALIASES = {
        # Xe tải
        '500kg': ('xe_tai', '500KG'),
        '0.5t': ('xe_tai', '500KG'),
        '1t': ('xe_tai', '1T'),
        '1 tấn': ('xe_tai', '1T'),
        '1.5t': ('xe_tai', '1.5T'),
        '2t': ('xe_tai', '2T'),
        '2 tấn': ('xe_tai', '2T'),
        '3.5t': ('xe_tai', '3.5T'),
        '5t': ('xe_tai', '5T'),
        '5 tấn': ('xe_tai', '5T'),
        'xe 5 tấn': ('xe_tai', '5T'),
        '8t': ('xe_tai', '8T'),
        '10t': ('xe_tai', '10T'),
        '15t': ('xe_tai', '15T'),
        # Container
        'cont 20': ('container', '20FT'),
        'container 20': ('container', '20FT'),
        '20ft': ('container', '20FT'),
        '20 feet': ('container', '20FT'),
        'cont 40': ('container', '40FT'),
        'container 40': ('container', '40FT'),
        '40ft': ('container', '40FT'),
        '40hc': ('container', '40HC'),
        '40hq': ('container', '40HC'),
        # Xe đầu kéo
        'đầu kéo': ('dau_keo', 'DAU_KEO'),
        'mooc': ('dau_keo', 'MOOC'),
        'rơ mooc': ('dau_keo', 'MOOC'),
    }
    
    def __init__(self, db_session=None):
        self.db = db_session
        self._db_cache = {}
    
    async def load_vehicle_types(self):
        """Load vehicle types từ DB"""
        if self.db is None:
            return
        
        vehicle_types = self.db.query(VehicleType).filter(VehicleType.is_active == True).all()
        for vt in vehicle_types:
            self._db_cache[vt.code.lower()] = {
                'id': vt.id,
                'code': vt.code,
                'name': vt.name
            }
    
    def normalize(self, value: Any) -> NormalizedValue:
        """Normalize vehicle type"""
        if value is None or (isinstance(value, str) and not value.strip()):
            return NormalizedValue(None, value, 0.0, warning="Empty vehicle type")
        
        original = value
        value_str = str(value).strip().lower()
        
        # Clean up common variations
        value_str = value_str.replace('xe ', '').replace(' tấn', 't').replace('tấn', 't')
        value_str = re.sub(r'\s+', ' ', value_str).strip()
        
        # Try alias match
        for alias, (category, code) in self.VEHICLE_ALIASES.items():
            if alias in value_str or value_str in alias:
                # Try to find in DB
                if code.lower() in self._db_cache:
                    match = self._db_cache[code.lower()]
                    return NormalizedValue(
                        code,
                        original,
                        0.95,
                        resolved_id=match['id'],
                        resolved_name=match['name']
                    )
                return NormalizedValue(code, original, 0.85)
        
        # Try DB match
        for key, match in self._db_cache.items():
            if key in value_str or value_str in key:
                return NormalizedValue(
                    match['code'],
                    original,
                    0.8,
                    resolved_id=match['id'],
                    resolved_name=match['name']
                )
        
        # Not found
        return NormalizedValue(
            value_str.upper(),
            original,
            0.3,
            warning=f"Vehicle type not recognized: {value}"
        )


class ValueNormalizer:
    """
    Main class để normalize tất cả các loại giá trị
    """
    
    def __init__(self, db_session=None):
        self.date_normalizer = DateNormalizer()
        self.time_normalizer = TimeNormalizer()
        self.customer_resolver = CustomerResolver(db_session)
        self.vehicle_normalizer = VehicleTypeNormalizer(db_session)
    
    async def initialize(self):
        """Load data từ DB"""
        await self.customer_resolver.load_customers()
        await self.vehicle_normalizer.load_vehicle_types()
    
    def normalize(self, field_type: str, value: Any) -> NormalizedValue:
        """
        Normalize value dựa trên field type
        
        Args:
            field_type: Loại field (date, time, customer_code, vehicle_type, etc.)
            value: Raw value
        
        Returns:
            NormalizedValue
        """
        if field_type == 'date':
            return self.date_normalizer.normalize(value)
        elif field_type == 'time':
            return self.time_normalizer.normalize(value)
        elif field_type == 'customer_code':
            return self.customer_resolver.resolve(value)
        elif field_type == 'vehicle_type':
            return self.vehicle_normalizer.normalize(value)
        else:
            # Default: return as-is
            if value is None or (isinstance(value, str) and not value.strip()):
                return NormalizedValue(None, value, 0.5)
            return NormalizedValue(str(value).strip(), value, 0.9)
```

### 3.4 File: `data_extractor.py`

```python
# backend/app/ai/excel/data_extractor.py

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .excel_reader import RawExcelData, ExcelFormatType
from .schema_detector import SchemaMapping, FieldMapping
from .value_normalizer import ValueNormalizer, NormalizedValue


@dataclass
class ExtractedField:
    """Một field đã được extract và normalize"""
    field_name: str
    value: Any
    original_value: Any
    confidence: float
    resolved_id: Optional[int] = None
    resolved_name: Optional[str] = None
    warning: Optional[str] = None


@dataclass
class ExtractedRow:
    """Một row data đã được extract"""
    row_index: int
    fields: Dict[str, ExtractedField]
    overall_confidence: float
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary cho API response"""
        return {
            'row_index': self.row_index,
            'data': {k: v.value for k, v in self.fields.items()},
            'original': {k: v.original_value for k, v in self.fields.items()},
            'confidence': self.overall_confidence,
            'resolved': {
                k: {'id': v.resolved_id, 'name': v.resolved_name}
                for k, v in self.fields.items()
                if v.resolved_id is not None
            },
            'warnings': self.warnings,
            'errors': self.errors
        }


@dataclass
class ExtractionResult:
    """Kết quả extract toàn bộ file"""
    rows: List[ExtractedRow]
    schema: SchemaMapping
    summary: Dict[str, Any]
    needs_confirmation: bool
    confirmation_items: List[Dict[str, Any]] = field(default_factory=list)


class DataExtractor:
    """
    Extract và normalize data từ Excel dựa trên detected schema
    """
    
    # Required fields cho một job
    REQUIRED_FIELDS = ['date', 'customer_code', 'destination']
    
    # Confidence threshold for auto-accept
    AUTO_ACCEPT_THRESHOLD = 0.85
    
    def __init__(self, normalizer: ValueNormalizer):
        self.normalizer = normalizer
    
    async def extract(
        self,
        raw_data: RawExcelData,
        schema: SchemaMapping
    ) -> ExtractionResult:
        """
        Extract data từ raw Excel data theo schema
        
        Args:
            raw_data: Raw data từ ExcelReader
            schema: Schema mapping từ SchemaDetector
        
        Returns:
            ExtractionResult
        """
        extracted_rows = []
        all_warnings = []
        confirmation_items = []
        
        # Build mapping index -> field
        col_to_field = {
            m.excel_column_index: m
            for m in schema.field_mappings
        }
        
        # Process each row
        for row_idx, row in enumerate(raw_data.rows):
            extracted_fields = {}
            row_warnings = []
            row_errors = []
            
            # Extract each mapped field
            for col_idx, mapping in col_to_field.items():
                if col_idx >= len(row):
                    continue
                
                raw_value = row[col_idx]
                
                # Normalize value
                normalized = self.normalizer.normalize(
                    mapping.standard_field,
                    raw_value
                )
                
                extracted_fields[mapping.standard_field] = ExtractedField(
                    field_name=mapping.standard_field,
                    value=normalized.value,
                    original_value=normalized.original,
                    confidence=normalized.confidence * mapping.confidence,
                    resolved_id=normalized.resolved_id,
                    resolved_name=normalized.resolved_name,
                    warning=normalized.warning
                )
                
                if normalized.warning:
                    row_warnings.append(normalized.warning)
                
                # Check if needs confirmation
                combined_conf = normalized.confidence * mapping.confidence
                if combined_conf < self.AUTO_ACCEPT_THRESHOLD and normalized.value is not None:
                    confirmation_items.append({
                        'row': row_idx,
                        'field': mapping.standard_field,
                        'original': normalized.original,
                        'suggested': normalized.value,
                        'confidence': combined_conf,
                        'resolved_name': normalized.resolved_name
                    })
            
            # Check required fields
            for req_field in self.REQUIRED_FIELDS:
                if req_field not in extracted_fields:
                    row_errors.append(f"Missing required field: {req_field}")
                elif extracted_fields[req_field].value is None:
                    row_errors.append(f"Empty required field: {req_field}")
            
            # Calculate row confidence
            field_confs = [f.confidence for f in extracted_fields.values() if f.value is not None]
            row_confidence = sum(field_confs) / len(field_confs) if field_confs else 0
            
            extracted_rows.append(ExtractedRow(
                row_index=row_idx,
                fields=extracted_fields,
                overall_confidence=row_confidence,
                warnings=row_warnings,
                errors=row_errors
            ))
            
            all_warnings.extend(row_warnings)
        
        # Summary statistics
        summary = self._calculate_summary(extracted_rows, schema)
        
        # Determine if confirmation needed
        needs_confirmation = (
            len(confirmation_items) > 0 or
            schema.overall_confidence < self.AUTO_ACCEPT_THRESHOLD or
            any(row.errors for row in extracted_rows)
        )
        
        return ExtractionResult(
            rows=extracted_rows,
            schema=schema,
            summary=summary,
            needs_confirmation=needs_confirmation,
            confirmation_items=confirmation_items
        )
    
    def _calculate_summary(
        self,
        rows: List[ExtractedRow],
        schema: SchemaMapping
    ) -> Dict[str, Any]:
        """Calculate summary statistics"""
        total_rows = len(rows)
        valid_rows = len([r for r in rows if not r.errors])
        avg_confidence = sum(r.overall_confidence for r in rows) / total_rows if rows else 0
        
        # Count unique values per field
        field_stats = {}
        for row in rows:
            for field_name, field in row.fields.items():
                if field_name not in field_stats:
                    field_stats[field_name] = {
                        'count': 0,
                        'unique_values': set(),
                        'null_count': 0,
                        'low_confidence_count': 0
                    }
                
                stats = field_stats[field_name]
                stats['count'] += 1
                
                if field.value is None:
                    stats['null_count'] += 1
                else:
                    stats['unique_values'].add(str(field.value))
                
                if field.confidence < self.AUTO_ACCEPT_THRESHOLD:
                    stats['low_confidence_count'] += 1
        
        # Convert sets to counts
        for field_name in field_stats:
            field_stats[field_name]['unique_count'] = len(field_stats[field_name]['unique_values'])
            del field_stats[field_name]['unique_values']
        
        return {
            'total_rows': total_rows,
            'valid_rows': valid_rows,
            'error_rows': total_rows - valid_rows,
            'average_confidence': avg_confidence,
            'schema_confidence': schema.overall_confidence,
            'field_stats': field_stats,
            'unmapped_columns': schema.unmapped_columns,
            'schema_warnings': schema.warnings
        }
```

### 3.5 File: `flexible_excel_parser.py` (Main Entry Point)

```python
# backend/app/ai/excel/flexible_excel_parser.py

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import os

from .excel_reader import ExcelReader, RawExcelData
from .schema_detector import SchemaDetector, SchemaMapping
from .data_extractor import DataExtractor, ExtractionResult
from .value_normalizer import ValueNormalizer

from app.ai.clients import AIClientManager


@dataclass
class ParseResult:
    """Kết quả parse Excel cuối cùng"""
    success: bool
    data: Optional[ExtractionResult]
    error: Optional[str]
    preview: Optional[Dict[str, Any]]


class FlexibleExcelParser:
    """
    Main entry point cho Flexible Excel Parser
    
    Usage:
        parser = FlexibleExcelParser(ai_client, db_session)
        await parser.initialize()
        
        # Get preview first
        preview = await parser.preview(file_path)
        
        # Parse with full processing
        result = await parser.parse(file_path)
        
        if result.data.needs_confirmation:
            # Show confirmation UI
            pass
    """
    
    def __init__(self, ai_client: AIClientManager, db_session=None):
        self.ai_client = ai_client
        self.db_session = db_session
        
        # Initialize components
        self.reader = ExcelReader()
        self.schema_detector = SchemaDetector(ai_client)
        self.normalizer = ValueNormalizer(db_session)
        self.extractor = DataExtractor(self.normalizer)
        
        self._initialized = False
    
    async def initialize(self):
        """Initialize normalizer with DB data"""
        if not self._initialized:
            await self.normalizer.initialize()
            self._initialized = True
    
    async def preview(self, file_path: str, max_rows: int = 5) -> Dict[str, Any]:
        """
        Get preview của Excel file (format, headers, sample data)
        Dùng để show cho user xác nhận trước khi parse
        """
        if not os.path.exists(file_path):
            return {'error': f'File not found: {file_path}'}
        
        try:
            preview = self.reader.get_preview(file_path, max_rows)
            return {
                'success': True,
                'preview': preview
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def parse(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> ParseResult:
        """
        Parse Excel file với full AI processing
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name to parse (None = active sheet)
            context: Additional context (customer list, etc.)
        
        Returns:
            ParseResult
        """
        await self.initialize()
        
        if not os.path.exists(file_path):
            return ParseResult(
                success=False,
                data=None,
                error=f'File not found: {file_path}',
                preview=None
            )
        
        try:
            # Step 1: Read Excel
            raw_data = self.reader.read(file_path, sheet_name)
            
            if not raw_data.rows:
                return ParseResult(
                    success=False,
                    data=None,
                    error='Excel file is empty',
                    preview=None
                )
            
            # Step 2: Detect schema
            sample_rows = raw_data.rows[:5]  # First 5 rows for schema detection
            
            schema = await self.schema_detector.detect(
                headers=raw_data.headers or [],
                sample_rows=sample_rows,
                context=context
            )
            
            # Step 3: Extract and normalize data
            extraction_result = await self.extractor.extract(raw_data, schema)
            
            # Step 4: Build preview for confirmation
            preview = {
                'format': raw_data.format_info.format_type.value,
                'total_rows': len(raw_data.rows),
                'schema_confidence': schema.overall_confidence,
                'field_mappings': [
                    {
                        'excel_column': m.excel_column,
                        'standard_field': m.standard_field,
                        'confidence': m.confidence
                    }
                    for m in schema.field_mappings
                ],
                'unmapped_columns': schema.unmapped_columns,
                'warnings': schema.warnings,
                'sample_data': [
                    row.to_dict() for row in extraction_result.rows[:3]
                ]
            }
            
            return ParseResult(
                success=True,
                data=extraction_result,
                error=None,
                preview=preview
            )
            
        except Exception as e:
            import traceback
            return ParseResult(
                success=False,
                data=None,
                error=f'Parse error: {str(e)}\n{traceback.format_exc()}',
                preview=None
            )
    
    def convert_to_jobs(
        self,
        extraction_result: ExtractionResult,
        defaults: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Convert extraction result to job creation payloads
        
        Args:
            extraction_result: Result from parse()
            defaults: Default values for missing fields
        
        Returns:
            List of job dictionaries ready for creation
        """
        defaults = defaults or {}
        jobs = []
        
        for row in extraction_result.rows:
            # Skip rows with errors
            if row.errors:
                continue
            
            job = {
                # Map extracted fields to job fields
                'pickup_date': row.fields.get('date', {}).value,
                'pickup_time': row.fields.get('time', {}).value,
                'customer_id': row.fields.get('customer_code', {}).resolved_id,
                'vehicle_type_id': row.fields.get('vehicle_type', {}).resolved_id,
                'origin_address': row.fields.get('origin', {}).value,
                'destination_address': row.fields.get('destination', {}).value,
                'cargo_description': row.fields.get('cargo', {}).value,
                'quantity': row.fields.get('quantity', {}).value,
                'weight': row.fields.get('weight', {}).value,
                'invoice_number': row.fields.get('invoice_number', {}).value,
                'notes': row.fields.get('notes', {}).value,
                
                # Metadata
                '_source': 'excel_import',
                '_row_index': row.row_index,
                '_confidence': row.overall_confidence
            }
            
            # Apply defaults
            for key, value in defaults.items():
                if job.get(key) is None:
                    job[key] = value
            
            # Clean None values
            job = {k: v for k, v in job.items() if v is not None}
            
            jobs.append(job)
        
        return jobs
```

---

## 4. FILES CẦN TẠO

### 4.1 Directory Structure

```
backend/app/ai/excel/
├── __init__.py
├── excel_reader.py           # Đọc và detect format Excel
├── schema_detector.py        # AI-powered schema detection
├── value_normalizer.py       # Normalize dates, times, resolve references
├── data_extractor.py         # Extract data theo schema
└── flexible_excel_parser.py  # Main entry point

backend/app/api/v1/endpoints/
└── excel_import.py           # API endpoint cho Excel import

frontend/src/components/excel/
├── ExcelUploader.tsx         # Upload component
├── SchemaPreview.tsx         # Preview schema mapping
├── DataConfirmation.tsx      # Confirm parsed data
└── ImportProgress.tsx        # Import progress indicator
```

### 4.2 `__init__.py`

```python
# backend/app/ai/excel/__init__.py

from .excel_reader import ExcelReader, RawExcelData, ExcelFormat, ExcelFormatType
from .schema_detector import SchemaDetector, SchemaMapping, FieldMapping
from .value_normalizer import (
    ValueNormalizer, 
    DateNormalizer, 
    TimeNormalizer,
    CustomerResolver,
    VehicleTypeNormalizer,
    NormalizedValue
)
from .data_extractor import DataExtractor, ExtractedRow, ExtractionResult
from .flexible_excel_parser import FlexibleExcelParser, ParseResult

__all__ = [
    'ExcelReader',
    'RawExcelData',
    'ExcelFormat',
    'ExcelFormatType',
    'SchemaDetector',
    'SchemaMapping',
    'FieldMapping',
    'ValueNormalizer',
    'DateNormalizer',
    'TimeNormalizer',
    'CustomerResolver',
    'VehicleTypeNormalizer',
    'NormalizedValue',
    'DataExtractor',
    'ExtractedRow',
    'ExtractionResult',
    'FlexibleExcelParser',
    'ParseResult'
]
```

---

## 5. HƯỚNG DẪN TỪNG BƯỚC

### 5.1 Task List

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION TASKS                                          │
│                                                                                  │
│   ☐ Task 4.1: Tạo directory structure và __init__.py                           │
│                                                                                  │
│   ☐ Task 4.2: Implement excel_reader.py                                        │
│      • ExcelReader class                                                        │
│      • Format detection (table/form/mixed)                                      │
│      • Header row detection                                                     │
│      • get_preview() method                                                     │
│                                                                                  │
│   ☐ Task 4.3: Implement schema_detector.py                                     │
│      • Rule-based mapping với FIELD_ALIASES                                    │
│      • AI-based mapping cho uncertain columns                                  │
│      • Confidence scoring                                                       │
│                                                                                  │
│   ☐ Task 4.4: Implement value_normalizer.py                                    │
│      • DateNormalizer với các Vietnam/English formats                          │
│      • TimeNormalizer                                                          │
│      • CustomerResolver với DB lookup                                          │
│      • VehicleTypeNormalizer                                                   │
│                                                                                  │
│   ☐ Task 4.5: Implement data_extractor.py                                      │
│      • Extract data theo schema                                                 │
│      • Validation và error handling                                            │
│      • Summary statistics                                                       │
│                                                                                  │
│   ☐ Task 4.6: Implement flexible_excel_parser.py                               │
│      • Main entry point                                                         │
│      • preview() method                                                         │
│      • parse() method                                                           │
│      • convert_to_jobs() method                                                 │
│                                                                                  │
│   ☐ Task 4.7: Create API endpoint excel_import.py                              │
│      • POST /api/v1/excel/preview                                              │
│      • POST /api/v1/excel/parse                                                │
│      • POST /api/v1/excel/import                                               │
│                                                                                  │
│   ☐ Task 4.8: Create frontend components                                       │
│      • ExcelUploader                                                            │
│      • SchemaPreview                                                            │
│      • DataConfirmation                                                         │
│                                                                                  │
│   ☐ Task 4.9: Integration testing                                              │
│      • Test với các Excel format khác nhau                                     │
│      • Test với real customer data                                             │
│      • Test edge cases                                                          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Step-by-Step Guide

#### Step 1: Setup Directory

```bash
mkdir -p backend/app/ai/excel
touch backend/app/ai/excel/__init__.py
```

#### Step 2: Install Dependencies

```bash
pip install openpyxl pandas xlrd
```

Thêm vào `requirements.txt`:
```
openpyxl>=3.1.0
pandas>=2.0.0
xlrd>=2.0.0
```

#### Step 3: Implement từng file theo thứ tự

1. `excel_reader.py` - Không dependency
2. `value_normalizer.py` - Cần DB models
3. `schema_detector.py` - Cần AI client
4. `data_extractor.py` - Cần normalizer
5. `flexible_excel_parser.py` - Main orchestrator

---

## 6. TEST CASES

### 6.1 Unit Tests

```python
# tests/test_excel_parser.py

import pytest
from datetime import date, time
from app.ai.excel import (
    DateNormalizer,
    TimeNormalizer,
    ExcelReader,
    SchemaDetector
)


class TestDateNormalizer:
    """Test date normalization"""
    
    def setup_method(self):
        self.normalizer = DateNormalizer()
    
    def test_standard_format(self):
        """Test DD/MM/YYYY format"""
        result = self.normalizer.normalize("17/01/2026")
        assert result.value == date(2026, 1, 17)
        assert result.confidence >= 0.9
    
    def test_short_year(self):
        """Test DD/MM/YY format"""
        result = self.normalizer.normalize("17/01/26")
        assert result.value == date(2026, 1, 17)
    
    def test_iso_format(self):
        """Test YYYY-MM-DD format"""
        result = self.normalizer.normalize("2026-01-17")
        assert result.value == date(2026, 1, 17)
    
    def test_relative_tomorrow(self):
        """Test 'ngày mai' / 'mai'"""
        result = self.normalizer.normalize("ngày mai")
        from datetime import timedelta
        assert result.value == date.today() + timedelta(days=1)
    
    def test_month_name(self):
        """Test '17 Jan' format"""
        result = self.normalizer.normalize("17 Jan")
        assert result.value.month == 1
        assert result.value.day == 17


class TestTimeNormalizer:
    """Test time normalization"""
    
    def setup_method(self):
        self.normalizer = TimeNormalizer()
    
    def test_standard_format(self):
        """Test HH:MM format"""
        result = self.normalizer.normalize("22:00")
        assert result.value == time(22, 0)
    
    def test_hour_only(self):
        """Test '22h' format"""
        result = self.normalizer.normalize("22h")
        assert result.value == time(22, 0)
    
    def test_with_minutes(self):
        """Test '22h30' format"""
        result = self.normalizer.normalize("22h30")
        assert result.value == time(22, 30)
    
    def test_pm_format(self):
        """Test '10PM' format"""
        result = self.normalizer.normalize("10PM")
        assert result.value == time(22, 0)


class TestExcelReader:
    """Test Excel reading"""
    
    def test_table_format_detection(self, sample_table_excel):
        """Test detection of table format"""
        reader = ExcelReader()
        data = reader.read(sample_table_excel)
        assert data.format_info.format_type.value == "table"
        assert data.headers is not None
    
    def test_form_format_detection(self, sample_form_excel):
        """Test detection of form format"""
        reader = ExcelReader()
        data = reader.read(sample_form_excel)
        assert data.format_info.format_type.value == "form"


class TestSchemaDetector:
    """Test schema detection"""
    
    @pytest.mark.asyncio
    async def test_rule_based_mapping(self, mock_ai_client):
        """Test rule-based column mapping"""
        detector = SchemaDetector(mock_ai_client)
        
        headers = ["Ngày", "Giờ", "Khách hàng", "Loại xe", "Điểm đến"]
        sample = [["17/01/26", "22:00", "DRT1", "5T", "Hải Phòng"]]
        
        result = await detector.detect(headers, sample)
        
        # Check mappings
        field_names = {m.standard_field for m in result.field_mappings}
        assert "date" in field_names
        assert "time" in field_names
        assert "customer_code" in field_names
```

### 6.2 Integration Test

```python
# tests/test_excel_integration.py

import pytest
from app.ai.excel import FlexibleExcelParser


class TestFlexibleExcelParser:
    """Integration tests for full parsing flow"""
    
    @pytest.fixture
    def parser(self, ai_client, db_session):
        return FlexibleExcelParser(ai_client, db_session)
    
    @pytest.mark.asyncio
    async def test_full_parse_flow(self, parser, sample_booking_excel):
        """Test complete parsing flow"""
        await parser.initialize()
        
        result = await parser.parse(sample_booking_excel)
        
        assert result.success
        assert result.data is not None
        assert len(result.data.rows) > 0
    
    @pytest.mark.asyncio
    async def test_convert_to_jobs(self, parser, sample_booking_excel):
        """Test conversion to job payloads"""
        await parser.initialize()
        
        result = await parser.parse(sample_booking_excel)
        jobs = parser.convert_to_jobs(result.data)
        
        assert len(jobs) > 0
        assert all('pickup_date' in j or 'customer_id' in j for j in jobs)
```

### 6.3 Sample Test Files

Tạo các file Excel mẫu để test:

```python
# tests/fixtures/create_test_excels.py

import pandas as pd
from openpyxl import Workbook


def create_table_format():
    """Create sample table format Excel"""
    data = {
        'Ngày': ['17/01/2026', '18/01/2026', '19/01/2026'],
        'Giờ': ['22:00', '08:00', '14:30'],
        'Khách hàng': ['DRT1', 'SEVT', 'HSDN'],
        'Loại xe': ['5T', '10T', 'Cont 20'],
        'Điểm đến': ['HP', 'QN', 'SG']
    }
    df = pd.DataFrame(data)
    df.to_excel('tests/fixtures/sample_table.xlsx', index=False)


def create_form_format():
    """Create sample form format Excel"""
    wb = Workbook()
    ws = wb.active
    
    ws['A1'] = 'Booking Date:'
    ws['B1'] = '17/01/2026'
    ws['A2'] = 'Customer:'
    ws['B2'] = 'DREAMTECH VIETNAM'
    ws['A3'] = 'Vehicle Type:'
    ws['B3'] = 'Container 20ft'
    ws['A4'] = 'Pickup:'
    ws['B4'] = 'KCN Bình Dương'
    ws['A5'] = 'Delivery:'
    ws['B5'] = 'Cảng Hải Phòng'
    
    wb.save('tests/fixtures/sample_form.xlsx')


def create_mixed_format():
    """Create sample mixed format Excel"""
    wb = Workbook()
    ws = wb.active
    
    # Header section
    ws['A1'] = 'BOOKING FORM - DREAMTECH'
    ws['A2'] = 'Date: 17/01/2026'
    
    # Table section
    ws['A4'] = 'STT'
    ws['B4'] = 'Hàng hóa'
    ws['C4'] = 'SL'
    ws['D4'] = 'Điểm giao'
    
    ws['A5'] = 1
    ws['B5'] = 'Linh kiện điện tử'
    ws['C5'] = 50
    ws['D5'] = 'HP'
    
    ws['A6'] = 2
    ws['B6'] = 'Bao bì'
    ws['C6'] = 30
    ws['D6'] = 'QN'
    
    wb.save('tests/fixtures/sample_mixed.xlsx')


if __name__ == '__main__':
    create_table_format()
    create_form_format()
    create_mixed_format()
    print("Test Excel files created!")
```

---

## 7. INTEGRATION VỚI HỆ THỐNG HIỆN TẠI

### 7.1 API Endpoint

```python
# backend/app/api/v1/endpoints/excel_import.py

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import tempfile
import os

from app.db.session import get_db
from app.ai.clients import get_ai_client
from app.ai.excel import FlexibleExcelParser, ParseResult
from app.core.auth import get_current_user
from app.models import User


router = APIRouter(prefix="/excel", tags=["Excel Import"])


@router.post("/preview")
async def preview_excel(
    file: UploadFile = File(...),
    sheet_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Preview Excel file structure và sample data
    """
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        ai_client = get_ai_client()
        parser = FlexibleExcelParser(ai_client, db)
        
        preview = await parser.preview(tmp_path)
        return preview
    finally:
        os.unlink(tmp_path)


@router.post("/parse")
async def parse_excel(
    file: UploadFile = File(...),
    sheet_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Parse Excel file với AI schema detection
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        ai_client = get_ai_client()
        parser = FlexibleExcelParser(ai_client, db)
        await parser.initialize()
        
        result = await parser.parse(tmp_path, sheet_name)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)
        
        return {
            "success": True,
            "preview": result.preview,
            "summary": result.data.summary,
            "needs_confirmation": result.data.needs_confirmation,
            "confirmation_items": result.data.confirmation_items,
            "data": [row.to_dict() for row in result.data.rows]
        }
    finally:
        os.unlink(tmp_path)


@router.post("/import")
async def import_excel_jobs(
    file: UploadFile = File(...),
    confirmed_mappings: Optional[dict] = None,
    defaults: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import jobs từ Excel file
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        ai_client = get_ai_client()
        parser = FlexibleExcelParser(ai_client, db)
        await parser.initialize()
        
        result = await parser.parse(tmp_path)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)
        
        # Convert to jobs
        jobs = parser.convert_to_jobs(result.data, defaults)
        
        # TODO: Create jobs in database
        # created_jobs = await job_service.bulk_create(jobs, db)
        
        return {
            "success": True,
            "jobs_to_create": len(jobs),
            "jobs": jobs  # Preview - thực tế sẽ tạo trong DB
        }
    finally:
        os.unlink(tmp_path)
```

### 7.2 Frontend Integration

```typescript
// frontend/src/components/excel/ExcelImportDialog.tsx

import React, { useState } from 'react';
import { Upload, CheckCircle, AlertCircle } from 'lucide-react';

interface ExcelImportDialogProps {
  onImport: (jobs: any[]) => void;
  onClose: () => void;
}

export const ExcelImportDialog: React.FC<ExcelImportDialogProps> = ({
  onImport,
  onClose
}) => {
  const [step, setStep] = useState<'upload' | 'preview' | 'confirm'>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any>(null);
  const [parseResult, setParseResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = e.target.files?.[0];
    if (!uploadedFile) return;
    
    setFile(uploadedFile);
    setLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);
      
      const response = await fetch('/api/v1/excel/parse', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (data.success) {
        setPreview(data.preview);
        setParseResult(data);
        setStep('preview');
      }
    } catch (error) {
      console.error('Parse error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    // Import jobs
    onImport(parseResult.data);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[80vh] overflow-auto">
        <h2 className="text-xl font-bold mb-4">Import Excel</h2>
        
        {step === 'upload' && (
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2">Kéo thả file Excel hoặc click để chọn</p>
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={handleUpload}
              className="hidden"
              id="excel-upload"
            />
            <label
              htmlFor="excel-upload"
              className="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded cursor-pointer"
            >
              Chọn file
            </label>
          </div>
        )}
        
        {step === 'preview' && preview && (
          <div>
            <h3 className="font-semibold mb-2">Schema Mapping</h3>
            <div className="bg-gray-50 rounded p-4 mb-4">
              {preview.field_mappings?.map((m: any, i: number) => (
                <div key={i} className="flex items-center gap-2 py-1">
                  <span className="font-mono">{m.excel_column}</span>
                  <span>→</span>
                  <span className="text-blue-600">{m.standard_field}</span>
                  <span className={`text-sm ${m.confidence >= 0.85 ? 'text-green-600' : 'text-yellow-600'}`}>
                    ({(m.confidence * 100).toFixed(0)}%)
                  </span>
                </div>
              ))}
            </div>
            
            {parseResult?.confirmation_items?.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded p-4 mb-4">
                <h4 className="font-semibold text-yellow-800 flex items-center gap-2">
                  <AlertCircle className="h-5 w-5" />
                  Cần xác nhận
                </h4>
                {parseResult.confirmation_items.map((item: any, i: number) => (
                  <div key={i} className="mt-2 text-sm">
                    Row {item.row + 1}: "{item.original}" → {item.suggested}
                  </div>
                ))}
              </div>
            )}
            
            <h3 className="font-semibold mb-2">Preview Data</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full border">
                <thead>
                  <tr className="bg-gray-100">
                    {Object.keys(parseResult?.data[0]?.data || {}).map(key => (
                      <th key={key} className="border px-2 py-1 text-left text-sm">
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {parseResult?.data.slice(0, 5).map((row: any, i: number) => (
                    <tr key={i}>
                      {Object.values(row.data).map((val: any, j: number) => (
                        <td key={j} className="border px-2 py-1 text-sm">
                          {String(val)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={onClose}
                className="px-4 py-2 border rounded"
              >
                Hủy
              </button>
              <button
                onClick={handleConfirm}
                className="px-4 py-2 bg-blue-600 text-white rounded flex items-center gap-2"
              >
                <CheckCircle className="h-4 w-4" />
                Import {parseResult?.summary?.valid_rows} jobs
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
```

### 7.3 Tích hợp với Chat UI

```python
# backend/app/ai/chat/excel_handler.py

from app.ai.excel import FlexibleExcelParser


class ExcelChatHandler:
    """
    Handle Excel file trong chat context
    """
    
    def __init__(self, ai_client, db_session):
        self.parser = FlexibleExcelParser(ai_client, db_session)
    
    async def handle_excel_upload(self, file_path: str, user_message: str):
        """
        Handle khi user upload Excel trong chat
        """
        await self.parser.initialize()
        
        # Parse file
        result = await self.parser.parse(file_path)
        
        if not result.success:
            return {
                "type": "error",
                "message": f"Không thể đọc file Excel: {result.error}"
            }
        
        # Build response
        summary = result.data.summary
        
        response_text = f"""Tôi đã phân tích file Excel của bạn:

📊 **Tổng quan:**
- Số dòng: {summary['total_rows']}
- Dòng hợp lệ: {summary['valid_rows']}
- Độ tin cậy: {summary['average_confidence']:.0%}

📋 **Các trường nhận diện được:**
"""
        for mapping in result.data.schema.field_mappings:
            response_text += f"- {mapping.excel_column} → {mapping.standard_field}\n"
        
        if summary['unmapped_columns']:
            response_text += f"\n⚠️ Cột không nhận diện: {', '.join(summary['unmapped_columns'])}"
        
        if result.data.needs_confirmation:
            response_text += "\n\n🔍 Một số giá trị cần xác nhận. Bạn có muốn xem chi tiết không?"
        else:
            response_text += "\n\n✅ Sẵn sàng import. Bạn có muốn tạo jobs từ file này không?"
        
        return {
            "type": "excel_parsed",
            "message": response_text,
            "data": {
                "summary": summary,
                "preview": result.preview,
                "needs_confirmation": result.data.needs_confirmation,
                "jobs": self.parser.convert_to_jobs(result.data) if not result.data.needs_confirmation else None
            }
        }
```

---

## 8. SUMMARY

### Các điểm chính của Giải pháp 2:

1. **AI-Powered Schema Detection**: Tự động nhận diện cấu trúc Excel, không cần fix format
2. **Multi-format Support**: Hỗ trợ table, form, và mixed formats
3. **Smart Value Normalization**: Normalize dates, times, customer codes với nhiều variations
4. **Confidence Scoring**: Đánh giá độ tin cậy, yêu cầu confirm khi cần
5. **Database Integration**: Resolve references từ DB (customers, vehicle types)
6. **Human in the Loop**: Preview và confirm trước khi import

### Timeline Implementation:

- **Tuần 1**: excel_reader.py + value_normalizer.py
- **Tuần 2**: schema_detector.py + data_extractor.py
- **Tuần 3**: flexible_excel_parser.py + API endpoints
- **Tuần 4**: Frontend components + Integration testing

---

**Tài liệu tiếp theo:**
- GIẢI PHÁP 3: Conversation Memory
- GIẢI PHÁP 4: Smart Fallback & Clarification
