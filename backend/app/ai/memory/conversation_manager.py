# backend/app/ai/memory/conversation_manager.py

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .conversation_state import (
    ConversationState, 
    Message, 
    TaskState, 
    ContinuationType
)
from .session_store import SessionStore, InMemorySessionStore
from .continuation_detector import ContinuationDetector
from .entity_accumulator import EntityAccumulator, AccumulationResult

from typing import Any
# To avoid circular imports, we use Any for classes not defined in this module
# from app.ai.clients import AIClientManager
# from app.ai.pipeline.intent_classifier import IntentClassifier
# from app.ai.pipeline.entity_extractor import EntityExtractor


@dataclass
class ProcessResult:
    """Kết quả xử lý message"""
    response: str
    state: ConversationState
    action: Optional[Dict[str, Any]] = None  # Action to execute
    needs_confirmation: bool = False
    confirmation_data: Optional[Dict] = None


class ConversationManager:
    """
    Main manager cho conversation với memory
    """
    
    def __init__(
        self,
        ai_client: Any,
        session_store: Optional[SessionStore] = None,
        db_session = None
    ):
        self.ai = ai_client
        self.store = session_store or InMemorySessionStore()
        self.db = db_session
        
        # Initialize components
        self.detector = ContinuationDetector(ai_client)
        self.accumulator = EntityAccumulator()
        
        # Lazy import or passed-in instances for pipeline components to avoid circular deps
        # For now, we'll assume they are instantiated here or passed in.
        # Since the original design called for using the pipeline classes, let's try to import them inside methods 
        # or use the ones from app.ai.pipeline if available.
        # For this implementation, I will import them here assuming the paths exist.
        
        from app.ai.intent_classifier import IntentClassifier
        from app.ai.entity_extractor import EntityExtractor
        
        self.intent_classifier = IntentClassifier(ai_client)
        self.entity_extractor = EntityExtractor(ai_client)
    
    async def process(
        self,
        session_id: str,
        message: str,
        user_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> ProcessResult:
        """
        Process a user message
        
        Args:
            session_id: Session identifier
            message: User message
            user_id: Optional user ID
            context: Additional context (e.g., from frontend)
        
        Returns:
            ProcessResult
        """
        # 1. Get or create session
        state = await self.store.get_or_create(session_id, user_id)
        
        # 2. Add user message to history
        state.add_message(Message.user(message))
        
        # 3. Detect continuation type
        cont_type, detected_intent = self.detector.detect(state, message)
        
        # 4. Process based on continuation type
        if cont_type == ContinuationType.CANCELLATION:
            result = await self._handle_cancellation(state)
        
        elif cont_type == ContinuationType.CONFIRMATION:
            result = await self._handle_confirmation(state)
        
        elif cont_type == ContinuationType.CORRECTION:
            result = await self._handle_correction(state, message, detected_intent)
        
        elif cont_type == ContinuationType.REFERENCE:
            result = await self._handle_reference(state, message)
        
        elif cont_type == ContinuationType.NEW_TASK:
            result = await self._handle_new_task(state, message, detected_intent, context)
        
        else:  # CONTINUATION
            result = await self._handle_continuation(state, message, context)
        
        # 5. Add assistant response to history
        state.add_message(Message.assistant(result.response))
        
        # 6. Save state
        await self.store.save(state)
        
        return result
    
    async def _handle_cancellation(self, state: ConversationState) -> ProcessResult:
        """Handle task cancellation"""
        had_task = state.task.is_active()
        state.reset_task()
        
        if had_task:
            response = "Đã hủy. Bạn cần gì khác không?"
        else:
            response = "Không có gì để hủy. Bạn cần giúp gì?"
        
        return ProcessResult(response=response, state=state)
    
    async def _handle_confirmation(self, state: ConversationState) -> ProcessResult:
        """Handle task confirmation - actually execute the action"""
        if state.task.state != TaskState.CONFIRMING:
            return ProcessResult(
                response="Không có gì để xác nhận.",
                state=state
            )
        
        # Build action data
        action = {
            "type": state.task.intent,
            "data": state.task.entities,
            "confirmation_data": state.task.confirmation_data
        }
        
        # Actually execute the action based on intent
        execution_result = None
        response = ""
        
        try:
            if state.task.intent == "create_booking":
                # Call job creation API
                execution_result = await self._execute_create_booking(state.task.entities)
                if execution_result.get("success"):
                    # API returns 'job_number' not 'job_no'
                    job_number = execution_result.get("job_number") or execution_result.get("job_no", "N/A")
                    job_id = execution_result.get("job_id")
                    response = f"✅ Đã tạo Job **{job_number}** thành công!"
                    
                    # Add summary of entities
                    entities = state.task.entities
                    if entities.get("customer_code"):
                        response += f"\n• Khách hàng: {entities['customer_code']}"
                    if entities.get("booking_date"):
                        response += f"\n• Ngày: {entities['booking_date']}"
                    if entities.get("pickup_time"):
                        response += f"\n• Giờ lấy: {entities['pickup_time']}"
                    if entities.get("invoices"):
                        inv = entities['invoices']
                        inv_str = ', '.join(inv) if isinstance(inv, list) else inv
                        response += f"\n• Invoices: {inv_str}"
                    if entities.get("dest_address") or entities.get("delivery_address"):
                        dest = entities.get("dest_address") or entities.get("delivery_address")
                        response += f"\n• Giao tại: {dest}"
                    
                    # Generate vendor message
                    vendor_msg = self._generate_vendor_message(entities, job_number)
                    response += f"\n\n📋 **Tin nhắn gửi vendor:**\n```\n{vendor_msg}\n```"
                else:
                    response = f"❌ Lỗi tạo job: {execution_result.get('message', 'Unknown error')}"
            
            elif state.task.intent == "assign_vehicle":
                execution_result = await self._execute_assign_vehicle(state.task.entities)
                if execution_result.get("success"):
                    entities = state.task.entities
                    job_number = execution_result.get("job_number") or entities.get("job_number", "")
                    job_details = execution_result.get("job_details", {})

                    response = f"✅ Đã gán xe cho Job **{job_number}** thành công!"

                    # Add vehicle details - bolder
                    if entities.get("license_plate"):
                        response += f"\n• **Biển số:** {entities['license_plate']}"
                    if entities.get("driver_name"):
                        response += f"\n• **Tài xế:** {entities['driver_name']}"
                    if entities.get("driver_phone"):
                        response += f"\n• **SĐT:** {entities['driver_phone']}"
                    if entities.get("driver_cccd"):
                        response += f"\n• **CCCD:** {entities['driver_cccd']}"

                    # Generate customer confirmation message with job details
                    confirm_msg = self._generate_vehicle_confirm_message(entities, job_number, job_details)
                    response += f"\n\n📋 **Tin nhắn xác nhận gửi khách hàng:**\n```\n{confirm_msg}\n```"
                else:
                    response = f"❌ Lỗi gán xe: {execution_result.get('message', 'Unknown error')}"
            
            else:
                response = self._generate_execution_response(state.task.intent, state.task.entities)
        
        except Exception as e:
            import logging
            logging.error(f"Execution error: {e}")
            response = f"❌ Đã xảy ra lỗi khi thực hiện: {str(e)}"
        
        # Mark as executed
        state.task.state = TaskState.EXECUTED
        
        # Reset for next task
        state.reset_task()
        
        return ProcessResult(
            response=response,
            state=state,
            action=action
        )
    
    async def _execute_create_booking(self, entities: Dict) -> Dict:
        """Execute job creation via jobs API"""
        import httpx
        
        try:
            # Call the internal jobs API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/api/jobs/create",
                    json={
                        "session_id": "internal",
                        "entities": entities,
                        "enriched_data": entities  # Use entities as enriched data too
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result
                else:
                    return {"success": False, "message": f"API error: {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def _execute_assign_vehicle(self, entities: Dict) -> Dict:
        """Execute vehicle assignment"""
        import httpx
        
        try:
            job_id = entities.get("job_id")
            job_number = entities.get("job_number") or entities.get("matched_job_no")
            
            # If we have job_number but not job_id, look it up
            if not job_id and job_number:
                async with httpx.AsyncClient() as client:
                    # Look up job by job_number
                    lookup_response = await client.get(
                        f"http://localhost:8000/api/jobs/by-number/{job_number}",
                        timeout=10.0
                    )
                    if lookup_response.status_code == 200:
                        job_data = lookup_response.json()
                        job_id = job_data.get("job_id") or job_data.get("id")
            
            if not job_id:
                return {"success": False, "message": f"Không tìm thấy job '{job_number}'. Vui lòng cho biết mã job hợp lệ."}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://localhost:8000/api/jobs/{job_id}/assign-vehicle",
                    json={
                        "license_plate": entities.get("license_plate"),
                        "driver_name": entities.get("driver_name"),
                        "driver_phone": entities.get("driver_phone"),
                        "driver_id_card": entities.get("driver_cccd") or entities.get("driver_id_card")
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    result["job_number"] = job_number
                    
                    # Fetch job details for invoice/date/time
                    try:
                        details_response = await client.get(
                            f"http://localhost:8000/api/jobs/{job_id}/details",
                            timeout=10.0
                        )
                        if details_response.status_code == 200:
                            job_data = details_response.json()
                            result["job_details"] = {
                                "scheduled_date": job_data.get("booking_date") or job_data.get("etd"),
                                "scheduled_time": job_data.get("pickup_time"),
                                "invoice_numbers": job_data.get("invoice_numbers"),
                                "pickup_address": job_data.get("pickup_address"),
                                "delivery_address": job_data.get("delivery_address"),
                                "package_quantity": job_data.get("package_quantity"),
                                "package_display": job_data.get("package_display"),
                            }
                            # Also check service_details
                            if job_data.get("services"):
                                svc = job_data["services"][0] if job_data["services"] else {}
                                svc_details = svc.get("service_details") or {}
                                if not result["job_details"]["invoice_numbers"]:
                                    result["job_details"]["invoice_numbers"] = svc_details.get("invoice_numbers")
                                if not result["job_details"]["scheduled_date"]:
                                    result["job_details"]["scheduled_date"] = svc.get("scheduled_date")
                                if not result["job_details"]["scheduled_time"]:
                                    result["job_details"]["scheduled_time"] = svc.get("scheduled_time")
                                if not result["job_details"]["package_quantity"]:
                                    result["job_details"]["package_quantity"] = svc_details.get("package_quantity") or svc_details.get("package_display")
                    except Exception as e:
                        import logging
                        logging.warning(f"Could not fetch job details: {e}")
                    
                    return result
                else:
                    return {"success": False, "message": f"API error: {response.status_code} - {response.text}"}
        except Exception as e:
            import logging
            logging.error(f"Assign vehicle error: {e}")
            return {"success": False, "message": str(e)}
    
    def _generate_vendor_message(self, entities: Dict, job_number: str) -> str:
        """Generate vendor booking message with all relevant details"""
        # Build vendor message
        lines = []
        lines.append(f"📦 YÊU CẦU BOOK XE")
        lines.append(f"Job: {job_number}")
        lines.append("")
        
        # Customer
        if entities.get("customer_code"):
            lines.append(f"🏢 Khách hàng: {entities['customer_code']}")
        
        # Date/Time
        if entities.get("booking_date"):
            lines.append(f"📅 Ngày: {entities['booking_date']}")
        if entities.get("pickup_time"):
            lines.append(f"⏰ Giờ lấy: {entities['pickup_time']}")
        
        # Locations
        if entities.get("pickup_address") or entities.get("origin_address"):
            pickup = entities.get("pickup_address") or entities.get("origin_address")
            lines.append(f"📍 Lấy tại: {pickup}")
        
        if entities.get("delivery_address") or entities.get("dest_address"):
            dest = entities.get("delivery_address") or entities.get("dest_address")
            lines.append(f"🎯 Giao tại: {dest}")
        
        # Cargo info
        if entities.get("cargo_type"):
            lines.append(f"📦 Hàng hóa: {entities['cargo_type']}")
        
        if entities.get("package_quantity_raw") or entities.get("package_quantity"):
            qty = entities.get("package_quantity_raw") or f"{entities.get('package_quantity', '')} {entities.get('package_unit', '')}"
            lines.append(f"📊 Số lượng: {qty}")
        
        # Invoices
        if entities.get("invoices"):
            inv = entities['invoices']
            inv_str = ', '.join(inv) if isinstance(inv, list) else inv
            lines.append(f"📄 Invoice: {inv_str}")
        
        # Notes
        if entities.get("notes"):
            lines.append(f"📝 Ghi chú: {entities['notes']}")
        
        lines.append("")
        lines.append("✅ Vui lòng xác nhận!")
        
        return "\n".join(lines)
    
    def _generate_vehicle_confirm_message(self, entities: Dict, job_number: str, job_details: Dict = None) -> str:
        """Generate vehicle assignment confirmation message for customer"""
        job_details = job_details or {}
        lines = []
        lines.append(f"🚚 **XÁC NHẬN GÁN XE**")
        lines.append(f"**Job:** {job_number}")
        lines.append("")

        # Job info (from job_details)
        if job_details.get("scheduled_date") or job_details.get("pickup_date"):
            date = job_details.get("scheduled_date") or job_details.get("pickup_date")
            lines.append(f"📅 **Ngày:** {date}")

        if job_details.get("scheduled_time") or job_details.get("pickup_time"):
            time = job_details.get("scheduled_time") or job_details.get("pickup_time")
            lines.append(f"⏰ **Giờ:** {time}")

        # Invoices
        if job_details.get("invoice_numbers") or job_details.get("invoices"):
            inv = job_details.get("invoice_numbers") or job_details.get("invoices")
            if isinstance(inv, list):
                inv = ', '.join(str(i) for i in inv)
            lines.append(f"📄 **Invoice:** {inv}")

        # Quantity/Package info - now below invoice
        pkg_qty = job_details.get("package_quantity") or job_details.get("package_display")
        pkg_unit = job_details.get("package_unit") or ""
        if pkg_qty:
            qty_str = f"{pkg_qty}"
            if pkg_unit:
                qty_str = f"{pkg_qty} {pkg_unit}"
            lines.append(f"📦 **Số lượng:** {qty_str}")

        lines.append("")

        # Vehicle info - bolder
        if entities.get("license_plate"):
            lines.append(f"🚗 **Biển số:** {entities['license_plate']}")

        if entities.get("driver_name"):
            lines.append(f"👤 **Tài xế:** {entities['driver_name']}")

        if entities.get("driver_phone"):
            lines.append(f"📞 **SĐT:** {entities['driver_phone']}")

        if entities.get("driver_cccd") or entities.get("driver_id_card"):
            cccd = entities.get("driver_cccd") or entities.get("driver_id_card")
            lines.append(f"🆔 **CCCD:** {cccd}")

        lines.append("")
        lines.append("✅ Xe đã được gán. Vui lòng xác nhận!")

        return "\n".join(lines)
    
    async def _handle_correction(
        self, 
        state: ConversationState, 
        message: str,
        field: Optional[str]
    ) -> ProcessResult:
        """Handle correction of existing data"""
        if not state.task.is_active():
            return ProcessResult(
                response="Không có thông tin nào để sửa. Bạn muốn bắt đầu task mới?",
                state=state
            )
        
        # Extract the correction from message
        # Use entity extractor focused on the specific field
        # Note: The original EntityExtractor might not support 'context' parameter fully yet, 
        # but we follow the design.
        extracted = await self.entity_extractor.extract(
            text=message,
            intent=state.task.intent,
            context={"focus_field": field}
        )
        
        if not extracted.get("entities"):
            return ProcessResult(
                response="Tôi không hiểu bạn muốn sửa gì. Vui lòng nói rõ hơn.",
                state=state
            )
        
        # Apply correction
        result = self.accumulator.accumulate(state.task, extracted["entities"])
        
        # Update task
        state.task.entities = result.entities
        state.task.missing_fields = result.missing_fields
        
        # Generate response
        if result.is_complete:
            state.task.state = TaskState.CONFIRMING
            state.task.confirmation_data = result.entities
            response = self._generate_confirmation_request(state.task)
        else:
            response = f"Đã cập nhật.\n\n"
            response += self.accumulator.get_summary(state.task)
            if result.missing_fields:
                response += f"\n\n{self.accumulator.get_missing_fields_message(state.task.intent, result.missing_fields)}"
        
        return ProcessResult(
            response=response,
            state=state,
            needs_confirmation=result.is_complete,
            confirmation_data=result.entities if result.is_complete else None
        )
    
    async def _handle_reference(
        self, 
        state: ConversationState, 
        message: str
    ) -> ProcessResult:
        """Handle reference to past job/booking"""
        # Extract job reference
        # Could be: "giống job hôm qua", "như booking 2501001", etc.
        
        # For now, simple implementation
        # TODO: Load referenced job and use as template
        
        return ProcessResult(
            response="Tính năng tham chiếu job cũ đang được phát triển. Vui lòng nhập thông tin booking mới.",
            state=state
        )
    
    async def _handle_new_task(
        self,
        state: ConversationState,
        message: str,
        detected_intent: Optional[str],
        context: Optional[Dict]
    ) -> ProcessResult:
        """Handle new task"""
        # Reset any previous task
        state.reset_task()
        
        # Classify intent if not detected
        if not detected_intent:
            intent_result = await self.intent_classifier.classify(message)
            detected_intent = intent_result["intent"]
        
        # Extract entities
        extracted = await self.entity_extractor.extract(
            text=message,
            intent=detected_intent,
            context=context
        )
        
        # Start new task
        state.task.start_task(detected_intent, extracted["entities"])
        
        # Accumulate and check completeness
        result = self.accumulator.accumulate(state.task, {})  # Already have entities
        state.task.missing_fields = result.missing_fields
        
        # Generate response
        if result.is_complete:
            state.task.state = TaskState.CONFIRMING
            state.task.confirmation_data = state.task.entities
            response = self._generate_confirmation_request(state.task)
            needs_confirmation = True
        else:
            response = f"Đã nhận thông tin:\n\n"
            response += self.accumulator.get_summary(state.task)
            response += f"\n\n{self.accumulator.get_missing_fields_message(state.task.intent, result.missing_fields)}"
            needs_confirmation = False
        
        return ProcessResult(
            response=response,
            state=state,
            needs_confirmation=needs_confirmation,
            confirmation_data=state.task.entities if needs_confirmation else None
        )
    
    async def _handle_continuation(
        self,
        state: ConversationState,
        message: str,
        context: Optional[Dict]
    ) -> ProcessResult:
        """Handle continuation of current task"""
        if not state.task.is_active():
            # No active task, treat as new
            return await self._handle_new_task(state, message, None, context)
        
        # Extract new entities
        extracted = await self.entity_extractor.extract(
            text=message,
            intent=state.task.intent,
            context=context
        )
        
        # Accumulate
        result = self.accumulator.accumulate(state.task, extracted["entities"])
        
        # Update task
        state.task.entities = result.entities
        state.task.missing_fields = result.missing_fields
        
        # Generate response
        if result.is_complete:
            state.task.state = TaskState.CONFIRMING
            state.task.confirmation_data = result.entities
            response = self._generate_confirmation_request(state.task)
            needs_confirmation = True
        else:
            # Acknowledge changes
            if result.changes:
                response = "Đã cập nhật: " + ", ".join(result.changes) + "\n\n"
            else:
                # If nothing changed effectively, re-ask missing
                response = ""
            
            response += self.accumulator.get_summary(state.task)
            
            if result.missing_fields:
                response += f"\n\n{self.accumulator.get_missing_fields_message(state.task.intent, result.missing_fields)}"
            
            needs_confirmation = False
        
        return ProcessResult(
            response=response,
            state=state,
            needs_confirmation=needs_confirmation,
            confirmation_data=result.entities if needs_confirmation else None
        )
    
    def _generate_confirmation_request(self, task: Any) -> str:
        """Generate confirmation request message"""
        summary = self.accumulator.get_summary(task)
        
        intent_names = {
            "create_booking": "tạo booking",
            "update_job": "cập nhật job",
            "assign_vehicle": "gán xe",
            "cancel_job": "hủy job",
        }
        
        action = intent_names.get(task.intent, task.intent)
        
        return f"""✅ Đã đủ thông tin để {action}:

{summary}

Xác nhận thực hiện? (Gõ "ok" để xác nhận hoặc sửa thông tin)"""
    
    def _generate_execution_response(
        self, 
        intent: str, 
        entities: Dict[str, Any]
    ) -> str:
        """Generate response after execution"""
        if intent == "create_booking":
            return f"""🎉 Đã tạo booking thành công!

• Khách hàng: {entities.get('customer_code')}
• Ngày: {entities.get('date')}
• Giờ: {entities.get('time', 'Chưa xác định')}
• Giao tại: {entities.get('destination')}
• Loại xe: {entities.get('vehicle_type', 'Chưa xác định')}

Bạn cần gì khác không?"""
        
        elif intent == "assign_vehicle":
            return f"""✅ Đã gán xe thành công!

• Job: {entities.get('job_id')}
• Biển số: {entities.get('license_plate')}
• Tài xế: {entities.get('driver_name', 'Chưa có')}

Bạn cần gì khác không?"""
        
        else:
            return f"✅ Đã thực hiện {intent} thành công!"
    
    async def get_session_stats(self) -> Dict:
        """Get session statistics"""
        if hasattr(self.store, 'get_stats'):
            return self.store.get_stats()
        return {}
