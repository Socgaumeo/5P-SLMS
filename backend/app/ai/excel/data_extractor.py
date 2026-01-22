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
