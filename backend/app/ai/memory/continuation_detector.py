# backend/app/ai/memory/continuation_detector.py

from typing import Optional, Tuple, Any
import re
import json

from .conversation_state import ConversationState, ContinuationType, TaskState

# Use Any for circular import avoidance if needed, but we can import AIClientManager in type hint
# from app.ai.clients import AIClientManager


class ContinuationDetector:
    """
    Detect loại continuation của message
    """
    
    # Keywords cho cancellation
    CANCEL_KEYWORDS = [
        "hủy", "bỏ", "cancel", "thôi", "không cần", "dừng",
        "bỏ qua", "skip", "quên đi", "forget"
    ]
    
    # Keywords cho confirmation
    CONFIRM_KEYWORDS = [
        "ok", "được", "confirm", "xác nhận", "đồng ý", "yes",
        "đúng rồi", "chính xác", "tạo đi", "tạo luôn", "làm đi",
        "luôn", "làm luôn", "gán luôn", "thực hiện", "đi",
        "ừ", "uh", "vâng", "dạ", "oke", "okie",
    ]
    
    # Keywords cho correction
    CORRECTION_KEYWORDS = [
        "sửa", "đổi", "thay", "không phải", "nhầm", "fix",
        "correct", "change", "update", "sai rồi", "sửa lại"
    ]
    
    # Keywords cho reference
    REFERENCE_KEYWORDS = [
        "giống", "như", "tương tự", "copy", "theo",
        "job", "booking", "hôm qua", "lần trước"
    ]
    
    # Intent keywords (để detect new task)
    INTENT_KEYWORDS = {
        "create_booking": ["đặt xe", "book", "booking", "tạo job", "cần xe", "lấy hàng"],
        "update_job": ["cập nhật", "update", "sửa job", "thay đổi"],
        "check_status": ["check", "kiểm tra", "status", "tình trạng", "đang ở đâu"],
        "assign_vehicle": ["gán xe", "assign", "phân xe", "điều xe"],
        "cancel_job": ["hủy job", "cancel job", "bỏ job"],
    }
    
    def __init__(self, ai_client: Any = None):
        self.ai = ai_client
    
    def detect(
        self,
        state: ConversationState,
        message: str
    ) -> Tuple[ContinuationType, Optional[str]]:
        """
        Detect continuation type

        Args:
            state: Current conversation state
            message: New user message

        Returns:
            Tuple of (ContinuationType, detected_intent or None)
        """
        import logging
        logger = logging.getLogger(__name__)

        message_lower = message.lower().strip()

        # Debug: Log state info
        is_confirm_msg = self._is_confirmation(message_lower)
        logger.info(f"[DETECTOR] task.state={state.task.state.value}")
        logger.info(f"[DETECTOR] task.intent={state.task.intent}")
        logger.info(f"[DETECTOR] has_entities={bool(state.task.entities)}")
        logger.info(f"[DETECTOR] is_confirmation_msg={is_confirm_msg}")

        # 1. Check cancellation
        if self._is_cancellation(message_lower):
            return ContinuationType.CANCELLATION, None

        # 2. Check confirmation (ONLY when in CONFIRMING state - ready to execute)
        # Do NOT return CONFIRMATION for COLLECTING state (e.g., awaiting customer selection)
        if state.task.state == TaskState.CONFIRMING:
            if is_confirm_msg and state.task.entities:
                logger.info(f"[DETECTOR] Returning CONFIRMATION (state=CONFIRMING)")
                return ContinuationType.CONFIRMATION, state.task.intent
        elif is_confirm_msg and state.task.is_active():
            # User sent confirmation while task is COLLECTING (not yet CONFIRMING)
            # If task has entities but is missing some fields, treat as "skip missing, confirm now"
            # e.g. "gán xe luôn nhé" when CCCD is optional
            if state.task.state == TaskState.COLLECTING and state.task.entities:
                logger.info(f"[DETECTOR] User confirms during COLLECTING, promoting to CONFIRMATION")
                return ContinuationType.CONFIRMATION, state.task.intent
            elif state.task.state != TaskState.COLLECTING:
                logger.warning(
                    f"[DETECTOR] User sent confirmation '{message_lower}' but task.state is {state.task.state.value}! "
                    f"Session may have been lost. session_id={state.session_id[:8]}..."
                )

        # 3. Check correction
        correction_field = self._is_correction(message_lower, state)
        if correction_field:
            return ContinuationType.CORRECTION, correction_field

        # 4. Check reference to past job
        if self._is_reference(message_lower):
            return ContinuationType.REFERENCE, None

        # 5. Check if new task (has clear intent keywords)
        new_intent = self._detect_intent(message_lower)
        if new_intent:
            # If task is active with same intent and message has confirm signal, treat as continuation
            if state.task.is_active() and new_intent == state.task.intent:
                if is_confirm_msg:
                    logger.info(f"[DETECTOR] Same intent + confirm signal → CONFIRMATION")
                    return ContinuationType.CONFIRMATION, state.task.intent
                # Same intent, no confirm signal → continue collecting
                return ContinuationType.CONTINUATION, state.task.intent
            # Different intent or no active task → new task
            if not state.task.is_active() or new_intent != state.task.intent:
                return ContinuationType.NEW_TASK, new_intent

        # 6. Default: continuation if there's active task
        if state.task.is_active():
            return ContinuationType.CONTINUATION, state.task.intent

        # 7. If no active task and no clear intent, treat as new task
        # (will need to classify intent in next step)
        return ContinuationType.NEW_TASK, None
    
    def _is_cancellation(self, message: str) -> bool:
        """Check if message is cancellation"""
        for keyword in self.CANCEL_KEYWORDS:
            if keyword in message:
                # Make sure it's not "cancel job" (which is a task)
                if "job" not in message or keyword not in ["hủy", "cancel"]:
                    return True
        return False
    
    def _is_confirmation(self, message: str) -> bool:
        """Check if message is confirmation"""
        # Short messages with confirm keywords
        if len(message.split()) <= 5:
            for keyword in self.CONFIRM_KEYWORDS:
                if keyword in message:
                    return True
        return False
    
    def _is_correction(
        self, 
        message: str, 
        state: ConversationState
    ) -> Optional[str]:
        """
        Check if message is correction
        Returns the field being corrected if detected
        """
        # Check correction keywords
        has_correction_keyword = any(kw in message for kw in self.CORRECTION_KEYWORDS)
        
        if not has_correction_keyword:
            return None
        
        # Try to identify which field is being corrected
        field_patterns = {
            "customer_code": ["khách", "kh", "customer"],
            "date": ["ngày", "date", "hôm"],
            "time": ["giờ", "time", "lúc"],
            "vehicle_type": ["xe", "vehicle", "tải"],
            "destination": ["đến", "destination", "giao"],
            "origin": ["lấy", "origin", "pickup"],
        }
        
        for field, patterns in field_patterns.items():
            for pattern in patterns:
                if pattern in message:
                    return field
        
        # Generic correction - will need context to determine field
        return "unknown"
    
    def _is_reference(self, message: str) -> bool:
        """
        Check if message references past job/booking.
        Be strict to avoid false positives on Excel content.
        """
        msg_lower = message.lower()

        # First check: if message has UPDATE_JOB signals, it's NOT a reference
        # These signals indicate user wants to modify a job, not copy/reference it
        update_job_signals = [
            "đổi khách", "sửa", "thay đổi", "thêm dịch vụ", "sửa địa chỉ",
            "ghi chú", "yêu cầu", "chờ hàng", "phí chờ", "phí huỷ", "phí hủy",
            "phí phát sinh", "hoàn thành", "done", "xong", "hủy", "cancel",
            "trạng thái", "status", "đổi kh", "them phi", "phi cho"
        ]
        for signal in update_job_signals:
            if signal in msg_lower:
                return False  # Not a reference, likely UPDATE_JOB

        # Only trigger on clear reference patterns with job numbers
        # Pattern: contains job ID format like "JOB-", "TRK-", or "job nào/số job"
        reference_patterns = [
            r"giống\s+(?:job|đơn|booking)",  # "giống job..."
            r"như\s+(?:lần|hôm|ngày)\s+trước",  # "như lần trước"
            r"copy\s+(?:job|đơn|booking)",  # "copy job..."
            r"tương tự\s+(?:với|job|đơn|như)",  # "tương tự với..."
            r"(?:theo|dựa theo)\s+(?:job|đơn|mẫu)",  # "theo job..."
        ]

        for pattern in reference_patterns:
            if re.search(pattern, msg_lower):
                return True

        return False
    
    def _detect_intent(self, message: str) -> Optional[str]:
        """Detect intent from message"""
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message:
                    return intent
        return None
    
    async def detect_with_ai(
        self, 
        state: ConversationState, 
        message: str
    ) -> Tuple[ContinuationType, Optional[str]]:
        """
        Use AI for more accurate detection (when rule-based is uncertain)
        """
        if not self.ai:
            return self.detect(state, message)
        
        # Build context
        conversation_text = state.get_conversation_text(n=3)
        task_context = ""
        if state.task.is_active():
            task_context = f"""
Current task: {state.task.intent}
Collected data: {state.task.entities}
Missing fields: {state.task.missing_fields}
"""
        
        prompt = f"""Analyze this message in the context of a logistics chat system.

CONVERSATION HISTORY:
{conversation_text}

{task_context}

NEW MESSAGE: "{message}"

Determine the type of this message:
1. NEW_TASK - User wants to start a completely new task
2. CONTINUATION - User is providing more info for current task
3. CORRECTION - User wants to fix/change something they said
4. CONFIRMATION - User is confirming the pending action
5. CANCELLATION - User wants to cancel current task
6. REFERENCE - User is referencing a past job/booking

Also identify the intent if it's a NEW_TASK:
- create_booking: Create new booking/job
- update_job: Update existing job
- check_status: Check job status
- assign_vehicle: Assign vehicle to job

Respond in JSON format:
{{
    "continuation_type": "NEW_TASK|CONTINUATION|CORRECTION|CONFIRMATION|CANCELLATION|REFERENCE",
    "intent": "intent_name or null",
    "confidence": 0.95,
    "reasoning": "brief explanation"
}}
"""
        
        try:
            response = await self.ai.generate(
                prompt=prompt,
                system_prompt="You are analyzing conversation flow in a logistics system.",
                temperature=0.1
            )
            
            # Simple cleanup of code blocks if AI returns markdown
            clean_res = response.strip()
            if clean_res.startswith("```json"):
                clean_res = clean_res[7:]
            if clean_res.endswith("```"):
                clean_res = clean_res[:-3]
            
            result = json.loads(clean_res)
            
            cont_type = ContinuationType(result["continuation_type"].lower())
            intent = result.get("intent")
            
            return cont_type, intent
            
        except Exception as e:
            print(f"AI detection failed, falling back to rules: {e}")
            return self.detect(state, message)
