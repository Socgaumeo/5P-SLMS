# backend/app/ai/excel/schema_detector.py

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
import re

from typing import Any


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
    
    def __init__(self, ai_client: Any):
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
