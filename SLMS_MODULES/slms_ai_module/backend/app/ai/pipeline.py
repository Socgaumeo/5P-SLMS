"""
SLMS AI Pipeline - Main Orchestrator
====================================

Multi-stage AI processing pipeline:
1. Preprocessor: Convert input (text/image/excel) to text
2. IntentClassifier: Classify user intent
3. ContextLoader: Load relevant context from database
4. EntityExtractor: Extract entities based on intent
5. Validator: Validate and identify missing fields
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
import logging

from .preprocessor import Preprocessor
from .intent_classifier import IntentClassifier
from .context_loader import ContextLoader
from .entity_extractor import EntityExtractor
from .validator import Validator, ValidationResult

logger = logging.getLogger(__name__)


class Intent(str, Enum):
    """Supported user intents"""
    CREATE_BOOKING = "create_booking"
    ASSIGN_VEHICLE = "assign_vehicle"
    UPDATE_STATUS = "update_status"
    QUERY_INFO = "query_info"
    GENERAL_CHAT = "general_chat"
    UNKNOWN = "unknown"


class InputType(str, Enum):
    """Supported input types"""
    TEXT = "text"
    IMAGE = "image"
    EXCEL = "excel"
    PDF = "pdf"


class PipelineInput(BaseModel):
    """Input for AI Pipeline"""
    content: str
    input_type: InputType = InputType.TEXT
    file_data: Optional[bytes] = None
    file_name: Optional[str] = None
    user_context: Optional[Dict] = None
    session_id: Optional[str] = None
    
    class Config:
        use_enum_values = True


class PipelineOutput(BaseModel):
    """Output from AI Pipeline"""
    # Core results
    intent: str
    confidence: float
    entities: Dict[str, Any]
    
    # Validation
    missing_fields: List[str]
    validation_errors: List[str]
    is_valid: bool
    
    # Action guidance
    suggested_action: str  # show_form, ask_clarification, cannot_understand
    clarification_question: Optional[str] = None
    input_suggestions: Optional[List[str]] = None
    
    # Message generation
    generated_message: Optional[str] = None
    message_template_code: Optional[str] = None
    
    # Metadata
    processing_time_ms: int
    stages_completed: List[str]
    
    class Config:
        use_enum_values = True


class AIPipeline:
    """
    Multi-stage AI processing pipeline
    
    Usage:
        pipeline = AIPipeline(db_session, ai_client)
        result = await pipeline.process(PipelineInput(
            content="Ngày mai 22h cần xe 1.25T cho DRT1",
            input_type=InputType.TEXT
        ))
    """
    
    # Confidence thresholds
    THRESHOLD_HIGH = 0.85      # Auto show form
    THRESHOLD_MEDIUM = 0.65    # Show form with warnings
    THRESHOLD_LOW = 0.40       # Ask clarification
    
    def __init__(self, db_session, ai_client):
        """
        Initialize pipeline with database session and AI client
        
        Args:
            db_session: Async database session (SQLAlchemy or databases)
            ai_client: AI client (GeminiClient or DeepSeekClient)
        """
        self.db = db_session
        self.ai = ai_client
        
        # Initialize stages
        self.preprocessor = Preprocessor(ai_client)
        self.intent_classifier = IntentClassifier(ai_client)
        self.context_loader = ContextLoader(db_session)
        self.entity_extractor = EntityExtractor(ai_client)
        self.validator = Validator()
    
    async def process(self, input_data: PipelineInput) -> PipelineOutput:
        """
        Main processing pipeline
        
        Args:
            input_data: PipelineInput with content, type, and optional context
            
        Returns:
            PipelineOutput with intent, entities, validation, and action guidance
        """
        start_time = datetime.now()
        stages_completed = []
        
        try:
            # ══════════════════════════════════════════════════════════════
            # STAGE 1: PREPROCESS INPUT
            # ══════════════════════════════════════════════════════════════
            logger.info(f"Stage 1: Preprocessing {input_data.input_type} input")
            
            processed_text = await self.preprocessor.process(
                content=input_data.content,
                input_type=input_data.input_type,
                file_data=input_data.file_data,
                file_name=input_data.file_name
            )
            stages_completed.append("preprocessor")
            
            logger.debug(f"Preprocessed text: {processed_text[:200]}...")
            
            # ══════════════════════════════════════════════════════════════
            # STAGE 2: CLASSIFY INTENT
            # ══════════════════════════════════════════════════════════════
            logger.info("Stage 2: Classifying intent")
            
            intent_result = await self.intent_classifier.classify(
                text=processed_text
            )
            intent = intent_result["intent"]
            intent_confidence = intent_result["confidence"]
            intent_signals = intent_result.get("key_signals", [])
            
            stages_completed.append("intent_classifier")
            
            logger.info(f"Intent: {intent} (confidence: {intent_confidence})")
            
            # ══════════════════════════════════════════════════════════════
            # STAGE 3: LOAD CONTEXT FROM DATABASE
            # ══════════════════════════════════════════════════════════════
            logger.info("Stage 3: Loading context from database")
            
            context = await self.context_loader.load(
                intent=intent,
                user_context=input_data.user_context
            )
            stages_completed.append("context_loader")
            
            logger.debug(f"Loaded context keys: {list(context.keys())}")
            
            # ══════════════════════════════════════════════════════════════
            # STAGE 4: EXTRACT ENTITIES
            # ══════════════════════════════════════════════════════════════
            logger.info("Stage 4: Extracting entities")
            
            extraction_result = await self.entity_extractor.extract(
                text=processed_text,
                intent=intent,
                context=context
            )
            entities = extraction_result["entities"]
            extraction_confidence = extraction_result["confidence"]
            
            stages_completed.append("entity_extractor")
            
            logger.info(f"Extracted entities: {list(entities.keys())}")
            
            # ══════════════════════════════════════════════════════════════
            # STAGE 5: VALIDATE
            # ══════════════════════════════════════════════════════════════
            logger.info("Stage 5: Validating extracted entities")
            
            validation: ValidationResult = await self.validator.validate(
                intent=intent,
                entities=entities,
                context=context
            )
            stages_completed.append("validator")
            
            logger.info(f"Validation: valid={validation.is_valid}, missing={validation.missing_fields}")
            
            # ══════════════════════════════════════════════════════════════
            # DETERMINE ACTION
            # ══════════════════════════════════════════════════════════════
            overall_confidence = min(intent_confidence, extraction_confidence)
            
            action, clarification, suggestions = self._determine_action(
                intent=intent,
                confidence=overall_confidence,
                validation=validation,
                context=context
            )
            
            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return PipelineOutput(
                intent=intent,
                confidence=overall_confidence,
                entities=entities,
                missing_fields=validation.missing_fields,
                validation_errors=validation.errors,
                is_valid=validation.is_valid,
                suggested_action=action,
                clarification_question=clarification,
                input_suggestions=suggestions,
                generated_message=None,
                message_template_code=None,
                processing_time_ms=processing_time,
                stages_completed=stages_completed
            )
            
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}", exc_info=True)
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return PipelineOutput(
                intent=Intent.UNKNOWN.value,
                confidence=0.0,
                entities={},
                missing_fields=[],
                validation_errors=[str(e)],
                is_valid=False,
                suggested_action="error",
                clarification_question="Đã xảy ra lỗi khi xử lý. Vui lòng thử lại.",
                input_suggestions=None,
                generated_message=None,
                message_template_code=None,
                processing_time_ms=processing_time,
                stages_completed=stages_completed
            )
    
    def _determine_action(
        self,
        intent: str,
        confidence: float,
        validation: ValidationResult,
        context: Dict
    ) -> tuple[str, Optional[str], Optional[List[str]]]:
        """
        Determine what action to take based on confidence and validation
        
        Returns:
            tuple of (action, clarification_question, suggestions)
        """
        
        # High confidence + valid = show form
        if confidence >= self.THRESHOLD_HIGH and validation.is_valid:
            return "show_form", None, None
        
        # High confidence but missing fields = show form with warnings
        if confidence >= self.THRESHOLD_HIGH and not validation.is_valid:
            question = self._generate_clarification(intent, validation.missing_fields)
            return "show_form_incomplete", question, None
        
        # Medium confidence = show form with warnings
        if confidence >= self.THRESHOLD_MEDIUM:
            if validation.missing_fields:
                question = self._generate_clarification(intent, validation.missing_fields)
                return "ask_clarification", question, self._generate_suggestions(intent, context)
            return "show_form_uncertain", None, None
        
        # Low confidence = ask clarification
        if confidence >= self.THRESHOLD_LOW:
            question = self._generate_clarification(intent, validation.missing_fields)
            suggestions = self._generate_suggestions(intent, context)
            return "ask_clarification", question, suggestions
        
        # Very low confidence = cannot understand
        suggestions = self._generate_general_suggestions()
        return "cannot_understand", "Xin lỗi, tôi không hiểu yêu cầu. Bạn có thể thử các mẫu sau:", suggestions
    
    def _generate_clarification(self, intent: str, missing: List[str]) -> str:
        """Generate clarification question based on missing fields"""
        
        questions = {
            Intent.CREATE_BOOKING.value: {
                "customer": "Khách hàng là ai? (VD: DRT1, SEVT, HSDN)",
                "customer_code": "Khách hàng là ai? (VD: DRT1, SEVT, HSDN)",
                "date": "Ngày lấy hàng là khi nào? (VD: ngày mai, 20/1)",
                "booking_date": "Ngày lấy hàng là khi nào? (VD: ngày mai, 20/1)",
                "time": "Giờ lấy hàng? (VD: 22h, 10:00)",
                "pickup_time": "Giờ lấy hàng? (VD: 22h, 10:00)",
                "vehicle_type": "Loại xe cần dùng? (VD: 1.25T, 2.5T, 5T)",
            },
            Intent.ASSIGN_VEHICLE.value: {
                "license_plate": "Biển số xe là gì?",
                "driver_name": "Tên lái xe?",
                "driver_phone": "Số điện thoại lái xe?",
                "job_number": "Điều xe cho job nào?",
            },
            Intent.UPDATE_STATUS.value: {
                "job_number": "Số job cần cập nhật? (VD: TRK-2601-089)",
                "status": "Trạng thái mới? (hoàn thành, hủy, đang giao...)",
                "new_status": "Trạng thái mới? (hoàn thành, hủy, đang giao...)",
            },
        }
        
        intent_questions = questions.get(intent, {})
        
        # Return first missing field question
        for field in missing:
            if field in intent_questions:
                return intent_questions[field]
        
        # Default question
        if missing:
            return f"Vui lòng cung cấp thêm: {', '.join(missing)}"
        
        return "Vui lòng cung cấp thêm thông tin chi tiết."
    
    def _generate_suggestions(self, intent: str, context: Dict) -> List[str]:
        """Generate input suggestions based on intent and context"""
        
        suggestions = {
            Intent.CREATE_BOOKING.value: [
                "Book xe 1.25T ngày mai 22h cho DRT1",
                "Cần xe 2.5T chở hàng, giao Nội Bài ngày 20/1",
                "DRT1 - 2 kiện PCB - giao sân bay ngày mai 10h",
            ],
            Intent.ASSIGN_VEHICLE.value: [
                "BKS 29H 76514 - Nguyễn Văn A - 0912345678",
                "Xe 29H-76514, lái xe Đức, sdt 0912345678",
                "Đã điều xe 76514, tài xế Minh 0987654321",
            ],
            Intent.UPDATE_STATUS.value: [
                "Job TRK-2601-089 đã giao xong",
                "Hoàn thành đơn DRT1 hôm nay",
                "Hủy job 089 do khách cancel",
            ],
        }
        
        return suggestions.get(intent, self._generate_general_suggestions())
    
    def _generate_general_suggestions(self) -> List[str]:
        """Generate general suggestions when intent is unclear"""
        return [
            "📦 Book xe: 'Ngày mai 22h cần xe 1.25T cho DRT1'",
            "🚗 Điều xe: 'BKS 29H 76514 - Nguyễn Văn A - 0912345678'",
            "✅ Cập nhật: 'Job TRK-2601-089 đã hoàn thành'",
            "❓ Hỏi: 'Trạng thái job 089?'",
        ]


# ══════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def create_pipeline(db_session, ai_client) -> AIPipeline:
    """
    Factory function to create AIPipeline instance
    
    Args:
        db_session: Database session
        ai_client: AI client (Gemini or DeepSeek)
        
    Returns:
        Configured AIPipeline instance
    """
    return AIPipeline(db_session, ai_client)
