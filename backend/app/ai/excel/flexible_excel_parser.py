# backend/app/ai/excel/flexible_excel_parser.py

from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from datetime import date

# from app.db.session import get_db
# from ..client import AIClient
from .excel_reader import ExcelReader, ExcelReaderError
from .schema_detector import SchemaDetector
from .value_normalizer import ValueNormalizer
from .data_extractor import DataExtractor, ExtractionResult


@dataclass
class ParseResult:
    """Kết quả parse cuối cùng"""
    success: bool
    data: Optional[ExtractionResult]
    error: Optional[str]
    preview: List[Dict[str, Any]]  # Preview 5 dòng đầu cho UI


class FlexibleExcelParser:
    """
    Main orchestrator cho flexible Excel parsing.
    Workflow:
    1. Reader: Đọc file Excel -> Raw Data
    2. Schema Detector: Detect columns -> Schema Mapping
    3. Data Extractor: Extract & Normalize -> Clean Data
    """
    
    def __init__(self, ai_client: Any):
        self.reader = ExcelReader()
        self.schema_detector = SchemaDetector(ai_client)
        # Normalizer & Extractor sẽ init trong initialize() khi có db session
        self.normalizer = None
        self.extractor = None
        self._is_initialized = False
    
    async def initialize(self, db_session: Any):
        """Init các component cần DB connection"""
        if not self._is_initialized:
            self.normalizer = ValueNormalizer(db_session)
            await self.normalizer.initialize()
            self.extractor = DataExtractor(self.normalizer)
            self._is_initialized = True
    
    async def parse(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> ParseResult:
        """
        Parse Excel file
        
        Args:
            file_path: Path tới file Excel
            sheet_name: Tên sheet (optional)
            context: Context thêm (customer_id, user_preferences, etc.)
        
        Returns:
            ParseResult
        """
        if not self._is_initialized:
            return ParseResult(False, None, "Parser not initialized. Call initialize() first.", [])
            
        try:
            # Step 1: Read Excel
            raw_data = self.reader.read(file_path, sheet_name)
            
            # Step 2: Detect schema
            schema = await self.schema_detector.detect(
                headers=raw_data.headers or [],
                sample_rows=raw_data.rows[:5],
                context=context
            )
            
            # Step 3: Extract and normalize data
            extraction_result = await self.extractor.extract(raw_data, schema)
            
            # Step 4: Build preview for UI
            preview = self._build_preview(extraction_result)
            
            return ParseResult(
                success=True,
                data=extraction_result,
                error=None,
                preview=preview
            )
            
        except ExcelReaderError as e:
            return ParseResult(False, None, f"Error reading Excel: {str(e)}", [])
        except Exception as e:
            import traceback
            traceback.print_exc()
            return ParseResult(False, None, f"Unexpected error: {str(e)}", [])

    def _build_preview(self, result: ExtractionResult) -> List[Dict[str, Any]]:
        """Build preview data cho UI"""
        preview_rows = []
        # Lấy tối đa 5 dòng đầu
        for row in result.rows[:5]:
            preview_row = {
                'row_index': row.row_index,
                'data': {},
                'warnings': row.warnings,
                'errors': row.errors,
                'confidence': row.overall_confidence
            }
            
            # Flatten fields
            for field_name, field in row.fields.items():
                preview_row['data'][field_name] = {
                    'value': field.value,
                    'original': field.original_value,
                    'is_valid': field.warning is None,
                    'resolved_name': field.resolved_name
                }
            
            preview_rows.append(preview_row)
            
        return preview_rows

    def convert_to_jobs(self, extraction_result: ExtractionResult, default_customer_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Convert result sang format jobs để lưu DB
        """
        jobs = []
        for row in extraction_result.rows:
            # Skip invalid rows
            if row.errors:
                continue
                
            fields = {k: v.value for k, v in row.fields.items()}
            resolved = {k: v.resolved_id for k, v in row.fields.items() if v.resolved_id}
            
            # Determine customer_id
            customer_id = resolved.get('customer_code') or default_customer_id
            
            job = {
                'customer_id': customer_id,
                'pickup_date': fields.get('date'),
                'pickup_address': fields.get('origin') or fields.get('pickup_address'),
                'delivery_address': fields.get('destination') or fields.get('delivery_address'),
                'job_type': self._determine_job_type(fields),
                'vehicle_type_id': resolved.get('vehicle_type'),
                'quantity': fields.get('quantity'),
                'weight': fields.get('weight'),
                'cbm': fields.get('cbm'),
                'notes': fields.get('notes'),
                # Metadata
                'raw_data': row.to_dict()
            }
            jobs.append(job)
            
        return jobs
    
    def _determine_job_type(self, fields: Dict[str, Any]) -> str:
        """Helper để đoán job type"""
        # Logic đơn giản, có thể cải thiện sau
        if fields.get('trip_type'):
            return fields['trip_type']
        return 'delivery'  # Default
