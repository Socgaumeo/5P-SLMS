# backend/app/ai/memory/conversation_manager.py

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import os
import logging

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
from app.ai.context_loader import ContextLoader
from app.core.config import settings

# API base URL - configurable via environment variable
API_BASE_URL = os.getenv("SLMS_API_URL", "http://localhost:8000")

logger = logging.getLogger(__name__)
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

        # Check conversation mode from config
        self.conversation_mode = getattr(settings, 'AI_CONVERSATION_MODE', 'classic')
        logger.info(f"[ConversationManager] AI_CONVERSATION_MODE = {self.conversation_mode}")

        # Initialize unified processor if using unified mode
        self.unified_processor = None
        if self.conversation_mode == "unified":
            from app.ai.unified_processor import UnifiedProcessor
            self.unified_processor = UnifiedProcessor(ai_client, db_session)
            logger.info("[ConversationManager] Using UNIFIED conversation mode")
        else:
            logger.info("[ConversationManager] Using CLASSIC conversation mode")

        # Initialize classic mode components
        self.detector = ContinuationDetector(ai_client)
        self.accumulator = EntityAccumulator()

        # Initialize context loader for database context
        self.context_loader = ContextLoader(db_session) if db_session else None

        # Lazy import or passed-in instances for pipeline components to avoid circular deps
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
        # Route to unified processor if configured
        if self.conversation_mode == "unified" and self.unified_processor:
            logger.info(f"[PROCESS] Routing to UNIFIED processor, session={session_id[:8]}")
            unified_result = await self.unified_processor.process(session_id, message, context)
            # Convert UnifiedResult to ProcessResult
            return ProcessResult(
                response=unified_result.response,
                state=None,  # Unified mode manages its own state
                action=unified_result.action,
                needs_confirmation=unified_result.ready_to_execute
            )

        # Classic mode processing below
        logger.info(f"[PROCESS] Using CLASSIC processor, session={session_id[:8]}")

        # 1. Get or create session
        state = await self.store.get_or_create(session_id, user_id)

        # Debug: Log state BEFORE processing
        logger.info(f"[PROCESS] session_id={session_id}")
        logger.info(f"[PROCESS] task.state={state.task.state.value}, intent={state.task.intent}")
        logger.info(f"[PROCESS] entities keys={list(state.task.entities.keys())}")
        logger.info(f"[PROCESS] message={message[:100]}...")

        # 2. Add user message to history
        state.add_message(Message.user(message))

        # 3. Detect continuation type
        cont_type, detected_intent = self.detector.detect(state, message)

        # Debug: Log detected continuation type
        logger.info(f"[PROCESS] cont_type={cont_type.value}, detected_intent={detected_intent}")
        
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
                    response = f"✅ Đã tạo Job {job_number} thành công!"

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
                    response += f"\n\n📋 Tin nhắn gửi vendor:\n```\n{vendor_msg}\n```"
                else:
                    response = f"❌ Lỗi tạo job: {execution_result.get('message', 'Unknown error')}"
            
            elif state.task.intent == "assign_vehicle":
                execution_result = await self._execute_assign_vehicle(state.task.entities)
                if execution_result.get("success"):
                    entities = state.task.entities
                    job_number = execution_result.get("job_number") or entities.get("job_number", "")
                    job_details = execution_result.get("job_details", {})

                    response = f"✅ Đã gán xe cho Job {job_number} thành công!"

                    # Add vehicle details with tonnage
                    if entities.get("license_plate"):
                        plate_str = entities['license_plate']
                        if entities.get("vehicle_type"):
                            plate_str = f"{plate_str} - {entities['vehicle_type']}"
                        response += f"\n• Biển số: {plate_str}"
                    if entities.get("driver_name"):
                        response += f"\n• Tài xế: {entities['driver_name']}"
                    if entities.get("driver_phone"):
                        response += f"\n• SĐT: {entities['driver_phone']}"
                    if entities.get("driver_cccd"):
                        response += f"\n• CCCD: {entities['driver_cccd']}"

                    # Generate customer confirmation message with job details
                    confirm_msg = self._generate_vehicle_confirm_message(entities, job_number, job_details)
                    response += f"\n\n📋 Tin nhắn xác nhận gửi khách hàng:\n```\n{confirm_msg}\n```"
                else:
                    response = f"❌ Lỗi gán xe: {execution_result.get('message', 'Unknown error')}"

            elif state.task.intent == "create_customer":
                execution_result = await self._execute_create_customer(state.task.entities)
                if execution_result.get("success"):
                    response = f"✅ Đã tạo khách hàng {execution_result.get('customer_code')} thành công!"
                    entities = state.task.entities
                    if entities.get("company_name"):
                        response += f"\n• Tên công ty: {entities['company_name']}"
                    if entities.get("tax_code"):
                        response += f"\n• MST: {entities['tax_code']}"
                    if entities.get("address"):
                        response += f"\n• Địa chỉ: {entities['address']}"
                else:
                    response = f"❌ Lỗi tạo khách hàng: {execution_result.get('message', 'Unknown error')}"

            elif state.task.intent == "create_vendor":
                execution_result = await self._execute_create_vendor(state.task.entities)
                if execution_result.get("success"):
                    response = f"✅ Đã tạo nhà cung cấp {execution_result.get('vendor_code')} thành công!"
                    entities = state.task.entities
                    if entities.get("vendor_name"):
                        response += f"\n• Tên NCC: {entities['vendor_name']}"
                    if entities.get("phone"):
                        response += f"\n• SĐT: {entities['phone']}"
                else:
                    response = f"❌ Lỗi tạo NCC: {execution_result.get('message', 'Unknown error')}"

            elif state.task.intent == "create_quotation":
                execution_result = await self._execute_create_quotation(state.task.entities)
                if execution_result.get("success"):
                    entities = state.task.entities
                    quote_type = "mua vào" if entities.get("quote_type") == "buying" else "bán ra"
                    response = f"✅ Đã tạo báo giá {quote_type} thành công!"
                    if entities.get("origin_province") and entities.get("destination_province"):
                        response += f"\n• Tuyến: {entities['origin_province']} → {entities['destination_province']}"
                    if entities.get("vehicle_type"):
                        response += f"\n• Loại xe: {entities['vehicle_type']}"
                    if entities.get("price"):
                        response += f"\n• Giá: {entities['price']:,.0f} {entities.get('currency', 'VND')}"
                    response += f"\n\n💡 Bạn có thể chỉnh sửa giá trong Admin Panel."
                else:
                    response = f"❌ Lỗi tạo báo giá: {execution_result.get('message', 'Unknown error')}"

            elif state.task.intent == "update_status":
                execution_result = await self._execute_update_status(state.task.entities)
                if execution_result.get("success"):
                    entities = state.task.entities
                    job_number = execution_result.get("job_number") or entities.get("job_number", "")
                    new_status = entities.get("new_status", "").upper()

                    # Vietnamese status names
                    status_names = {
                        "COMPLETED": "Hoàn thành",
                        "IN_TRANSIT": "Đang vận chuyển",
                        "DISPATCHED": "Đã điều xe",
                        "CANCELLED": "Đã hủy",
                        "PENDING": "Chờ xử lý",
                        "CONFIRMED": "Đã xác nhận"
                    }
                    status_vi = status_names.get(new_status, new_status)

                    response = f"✅ Đã cập nhật Job {job_number} → {status_vi}"
                    if entities.get("notes"):
                        response += f"\n• Ghi chú: {entities['notes']}"
                else:
                    response = f"❌ Lỗi cập nhật trạng thái: {execution_result.get('message', 'Unknown error')}"

            elif state.task.intent == "update_job":
                execution_result = await self._execute_update_job(state.task.entities)
                if execution_result.get("success"):
                    entities = state.task.entities
                    job_number = execution_result.get("job_number") or entities.get("job_number", "")
                    changes = execution_result.get("changes", [])

                    response = f"✅ Đã cập nhật Job {job_number} thành công!"
                    if changes:
                        response += "\n\nThay đổi:"
                        for change in changes:
                            response += f"\n• {change}"
                    if entities.get("new_customer_code"):
                        response += f"\n• Khách hàng mới: {entities['new_customer_code']}"
                    if entities.get("new_service_type"):
                        response += f"\n• Dịch vụ mới: {entities['new_service_type']}"
                else:
                    response = f"❌ Lỗi cập nhật job: {execution_result.get('message', 'Unknown error')}"

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
                    f"{API_BASE_URL}/api/jobs/create",
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
                        f"{API_BASE_URL}/api/jobs/by-number/{job_number}",
                        timeout=10.0
                    )
                    if lookup_response.status_code == 200:
                        job_data = lookup_response.json()
                        # Check success field - API returns 200 with success=False when not found
                        if job_data.get("success"):
                            job_id = job_data.get("job_id") or job_data.get("id")

            if not job_id:
                return {"success": False, "message": f"Không tìm thấy job '{job_number}'. Vui lòng cho biết mã job hợp lệ."}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/api/jobs/{job_id}/assign-vehicle",
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
                            f"{API_BASE_URL}/api/jobs/{job_id}/details",
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

    async def _execute_create_customer(self, entities: Dict) -> Dict:
        """Execute customer creation via admin API"""
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/api/admin/customers",
                    json={
                        "customer_code": entities.get("customer_code", "").upper(),
                        "company_name": entities.get("company_name"),
                        "short_name": entities.get("short_name"),
                        "address": entities.get("address"),
                        "contact_phone": entities.get("contact_phone"),
                        "contact_email": entities.get("contact_email"),
                        "tax_code": entities.get("tax_code"),
                        "is_active": True
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "customer_code": result.get("data", {}).get("customer_code"),
                        "customer_id": result.get("data", {}).get("customer_id")
                    }
                else:
                    error = response.json()
                    return {"success": False, "message": error.get("detail", f"API error: {response.status_code}")}
        except Exception as e:
            import logging
            logging.error(f"Create customer error: {e}")
            return {"success": False, "message": str(e)}

    async def _execute_create_vendor(self, entities: Dict) -> Dict:
        """Execute vendor creation via admin API"""
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/api/admin/vendors",
                    json={
                        "vendor_code": entities.get("vendor_code", "").upper(),
                        "vendor_name": entities.get("vendor_name"),
                        "short_name": entities.get("short_name"),
                        "address": entities.get("address"),
                        "phone": entities.get("phone"),
                        "email": entities.get("email"),
                        "tax_code": entities.get("tax_code"),
                        "is_active": True
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "vendor_code": result.get("data", {}).get("vendor_code"),
                        "vendor_id": result.get("data", {}).get("vendor_id")
                    }
                else:
                    error = response.json()
                    return {"success": False, "message": error.get("detail", f"API error: {response.status_code}")}
        except Exception as e:
            import logging
            logging.error(f"Create vendor error: {e}")
            return {"success": False, "message": str(e)}

    async def _execute_create_quotation(self, entities: Dict) -> Dict:
        """Execute quotation creation via admin API"""
        import httpx

        try:
            quote_type = entities.get("quote_type", "buying")

            # Find vendor/customer ID by name
            vendor_id = None
            customer_id = None

            async with httpx.AsyncClient() as client:
                if quote_type == "buying" and entities.get("vendor_name"):
                    # Lookup vendor by name
                    vendor_resp = await client.get(
                        f"{API_BASE_URL}/api/admin/vendors",
                        timeout=10.0
                    )
                    if vendor_resp.status_code == 200:
                        vendors = vendor_resp.json().get("data", [])
                        vendor_name_lower = entities["vendor_name"].lower()
                        for v in vendors:
                            if vendor_name_lower in (v.get("vendor_name") or "").lower() or \
                               vendor_name_lower in (v.get("short_name") or "").lower():
                                vendor_id = v.get("vendor_id")
                                break

                elif quote_type == "selling" and entities.get("customer_name"):
                    # Lookup customer by name
                    customer_resp = await client.get(
                        f"{API_BASE_URL}/api/admin/customers",
                        timeout=10.0
                    )
                    if customer_resp.status_code == 200:
                        customers = customer_resp.json().get("data", [])
                        customer_name_lower = entities["customer_name"].lower()
                        for c in customers:
                            if customer_name_lower in (c.get("company_name") or "").lower() or \
                               customer_name_lower in (c.get("short_name") or "").lower() or \
                               customer_name_lower in (c.get("customer_code") or "").lower():
                                customer_id = c.get("customer_id")
                                break

                # Create the rate
                endpoint = "buying-rates" if quote_type == "buying" else "selling-rates"
                payload = {
                    "price": entities.get("price"),
                    "currency": entities.get("currency", "VND"),
                    "unit": entities.get("unit", "TRIP"),
                    "vehicle_type": entities.get("vehicle_type"),
                    "origin_province": entities.get("origin_province"),
                    "destination_province": entities.get("destination_province"),
                    "notes": entities.get("sub_route") or entities.get("notes"),
                    "rate_type": entities.get("rate_type", "STANDARD"),
                    "is_active": True
                }

                if quote_type == "buying":
                    if not vendor_id:
                        return {"success": False, "message": f"Không tìm thấy NCC '{entities.get('vendor_name')}'. Vui lòng tạo NCC trước."}
                    payload["vendor_id"] = vendor_id
                else:
                    if not customer_id:
                        return {"success": False, "message": f"Không tìm thấy KH '{entities.get('customer_name')}'. Vui lòng tạo KH trước."}
                    payload["customer_id"] = customer_id

                response = await client.post(
                    f"{API_BASE_URL}/api/admin/{endpoint}",
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 200:
                    return {"success": True, "rate_id": response.json().get("data", {}).get("id")}
                else:
                    error = response.json()
                    return {"success": False, "message": error.get("detail", f"API error: {response.status_code}")}

        except Exception as e:
            import logging
            logging.error(f"Create quotation error: {e}")
            return {"success": False, "message": str(e)}

    async def _execute_update_status(self, entities: Dict) -> Dict:
        """Execute job status update via jobs API"""
        import httpx

        try:
            # Normalize status keywords to standard codes
            new_status = entities.get("new_status", "")
            if new_status:
                new_status = self._normalize_status(new_status)
                entities["new_status"] = new_status

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/api/jobs/update",
                    json={"entities": entities},
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        return {
                            "success": True,
                            "job_number": result.get("job_number") or result.get("job_no") or entities.get("job_number")
                        }
                    else:
                        return {"success": False, "message": result.get("message", "Update failed")}
                else:
                    error = response.json()
                    return {"success": False, "message": error.get("detail", f"API error: {response.status_code}")}
        except Exception as e:
            import logging
            logging.error(f"Update status error: {e}")
            return {"success": False, "message": str(e)}

    def _normalize_status(self, status: str) -> str:
        """Normalize various status keywords to standard codes"""
        status_lower = status.lower().strip()

        # COMPLETED mappings
        completed_keywords = [
            "completed", "complete", "hoàn thành", "hoan thanh",
            "xong", "done", "finish", "finished",
            "giao xong", "giao hàng xong", "giao hang xong",
            "đã xong", "da xong", "thành công", "thanh cong"
        ]
        if any(kw in status_lower for kw in completed_keywords):
            return "COMPLETED"

        # "đã giao" → COMPLETED (DELIVERED removed, use COMPLETED instead)
        delivered_keywords = [
            "delivered", "đã giao", "da giao", "giao rồi", "giao roi"
        ]
        if any(kw in status_lower for kw in delivered_keywords):
            return "COMPLETED"

        # IN_TRANSIT mappings
        transit_keywords = [
            "in_transit", "in transit", "đang giao", "dang giao",
            "đang đi", "dang di", "trên đường", "tren duong",
            "đang vận chuyển", "dang van chuyen", "on the way"
        ]
        if any(kw in status_lower for kw in transit_keywords):
            return "IN_TRANSIT"

        # DISPATCHED mappings
        dispatched_keywords = [
            "dispatched", "đã điều xe", "da dieu xe",
            "xe đã đi", "xe da di", "xuất phát", "xuat phat"
        ]
        if any(kw in status_lower for kw in dispatched_keywords):
            return "DISPATCHED"

        # CANCELLED mappings
        cancelled_keywords = [
            "cancelled", "canceled", "cancel", "hủy", "huy",
            "bỏ", "bo", "không đi", "khong di"
        ]
        if any(kw in status_lower for kw in cancelled_keywords):
            return "CANCELLED"

        # If already a valid status code, return uppercase
        valid_statuses = ["PENDING", "CONFIRMED", "DISPATCHED", "IN_TRANSIT", "COMPLETED", "CANCELLED"]
        if status.upper() in valid_statuses:
            return status.upper()

        # Default: return as-is uppercase
        return status.upper()

    async def _execute_update_job(self, entities: Dict) -> Dict:
        """Execute job update (change customer, add service, add note, add fee)"""
        import httpx

        try:
            job_id = entities.get("job_id")
            job_number = entities.get("job_number") or entities.get("matched_job_no")
            action_type = entities.get("action_type", "")
            changes = []

            # If we have job_number but not job_id, look it up
            if not job_id and job_number:
                async with httpx.AsyncClient() as client:
                    lookup_response = await client.get(
                        f"{API_BASE_URL}/api/jobs/by-number/{job_number}",
                        timeout=10.0
                    )
                    if lookup_response.status_code == 200:
                        job_data = lookup_response.json()
                        # Check success field - API returns 200 with success=False when not found
                        if job_data.get("success"):
                            job_id = job_data.get("job_id") or job_data.get("id")

            if not job_id:
                return {"success": False, "message": f"Không tìm thấy job '{job_number}'. Vui lòng cho biết mã job hợp lệ."}

            async with httpx.AsyncClient() as client:
                # Handle add_note action
                if action_type == "add_note":
                    notes = entities.get("notes", "")
                    if not notes:
                        return {"success": False, "message": "Thiếu nội dung ghi chú."}

                    # Get job services to find the first (main) service
                    job_resp = await client.get(
                        f"{API_BASE_URL}/api/jobs/{job_id}/details",
                        timeout=10.0
                    )
                    if job_resp.status_code == 200:
                        job_data = job_resp.json()
                        services = job_data.get("services", [])
                        if services:
                            svc_id = services[0].get("svc_id")
                            # Get existing notes and append
                            existing_notes = services[0].get("special_requirements") or ""
                            if existing_notes:
                                new_notes = f"{existing_notes}\n{notes}"
                            else:
                                new_notes = notes

                            # Update notes via API (endpoint is under /api/jobs router)
                            notes_resp = await client.put(
                                f"{API_BASE_URL}/api/jobs/services/{svc_id}/notes",
                                json={"notes": new_notes},
                                timeout=30.0
                            )
                            if notes_resp.status_code == 200:
                                result = notes_resp.json()
                                if result.get("success"):
                                    changes.append(f"Thêm ghi chú: {notes}")
                                else:
                                    return {"success": False, "message": result.get("message", "Add note failed")}
                            else:
                                return {"success": False, "message": f"API error: {notes_resp.status_code}"}
                        else:
                            return {"success": False, "message": "Job không có dịch vụ nào."}
                    else:
                        return {"success": False, "message": f"Không thể lấy thông tin job: {job_resp.status_code}"}

                # Handle add_fee action
                elif action_type == "add_fee":
                    fee_type = entities.get("fee_type", "SVC_SURCHARGE")
                    fee_amount = entities.get("fee_amount", 0)
                    fee_notes = entities.get("notes", "")

                    # Validate fee type
                    valid_fee_types = ["SVC_WAITING", "SVC_CANCEL_FEE", "SVC_SURCHARGE"]
                    if fee_type not in valid_fee_types:
                        fee_type = "SVC_SURCHARGE"

                    # Create fee service
                    fee_payload = {
                        "service_type_code": fee_type,
                        "special_requirements": fee_notes,
                        "service_details": {
                            "fee_amount": fee_amount,
                            "notes": fee_notes
                        }
                    }

                    response = await client.post(
                        f"{API_BASE_URL}/api/jobs/{job_id}/services",
                        json=fee_payload,
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            fee_labels = {
                                "SVC_WAITING": "Phí chờ giờ",
                                "SVC_CANCEL_FEE": "Phí huỷ chuyến",
                                "SVC_SURCHARGE": "Phí phát sinh"
                            }
                            fee_label = fee_labels.get(fee_type, fee_type)
                            amount_str = f"{fee_amount:,.0f} VND" if fee_amount else ""
                            changes.append(f"Thêm {fee_label}: {amount_str}")
                        else:
                            return {"success": False, "message": result.get("message", "Add fee failed")}
                    else:
                        return {"success": False, "message": f"API error: {response.status_code}"}

                # Change customer if requested
                elif entities.get("new_customer_id") or entities.get("new_customer_code"):
                    customer_payload = {
                        "customer_id": entities.get("new_customer_id"),
                        "customer_code": entities.get("new_customer_code"),
                        "reason": entities.get("change_reason", "Updated via chat")
                    }

                    # Lookup customer_id by code if only code is provided
                    if not customer_payload["customer_id"] and customer_payload["customer_code"]:
                        cust_resp = await client.get(
                            f"{API_BASE_URL}/api/customers",
                            timeout=10.0
                        )
                        if cust_resp.status_code == 200:
                            customers = cust_resp.json().get("customers", [])
                            for c in customers:
                                if c.get("customer_code", "").upper() == customer_payload["customer_code"].upper():
                                    customer_payload["customer_id"] = c.get("customer_id")
                                    break

                    if customer_payload["customer_id"]:
                        response = await client.put(
                            f"{API_BASE_URL}/api/jobs/{job_id}/customer",
                            json=customer_payload,
                            timeout=30.0
                        )
                        if response.status_code == 200:
                            result = response.json()
                            if result.get("success"):
                                changes.append(f"Đổi khách hàng → {customer_payload['customer_code']}")
                            else:
                                return {"success": False, "message": result.get("message", "Customer change failed")}
                        else:
                            return {"success": False, "message": f"API error: {response.status_code}"}

                # Add new service if requested
                elif entities.get("new_service_type"):
                    service_payload = {
                        "service_type_code": entities.get("new_service_type"),
                        "scheduled_date": entities.get("service_date"),
                        "origin_address": entities.get("origin_address"),
                        "dest_address": entities.get("dest_address"),
                        "cargo_type": entities.get("cargo_type"),
                        "package_quantity": entities.get("package_quantity"),
                        "package_unit": entities.get("package_unit"),
                    }

                    response = await client.post(
                        f"{API_BASE_URL}/api/jobs/{job_id}/services",
                        json=service_payload,
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            changes.append(f"Thêm dịch vụ: {entities['new_service_type']}")
                        else:
                            return {"success": False, "message": result.get("message", "Add service failed")}
                    else:
                        return {"success": False, "message": f"API error: {response.status_code}"}

                # Handle add_cost / add_revenue / add_cost_revenue / multi_cost / multi_cost_revenue actions
                elif action_type in ["add_cost", "add_revenue", "add_cost_revenue", "multi_cost", "multi_cost_revenue"]:
                    # Get job services to find the first (main) service
                    job_resp = await client.get(
                        f"{API_BASE_URL}/api/jobs/{job_id}/details",
                        timeout=10.0
                    )
                    if job_resp.status_code != 200:
                        return {"success": False, "message": f"Không thể lấy thông tin job: {job_resp.status_code}"}

                    job_data = job_resp.json()
                    services = job_data.get("services", [])
                    if not services:
                        return {"success": False, "message": "Job không có dịch vụ nào để thêm chi phí/doanh thu."}

                    svc_id = services[0].get("svc_id")
                    existing_details = services[0].get("service_details") or {}

                    # Build quotation payload - PRESERVE existing data
                    quotation_payload = {
                        "buying_rate_id": existing_details.get("buying_rate_id"),
                        "buying_price": existing_details.get("buying_price"),
                        "selling_rate_id": existing_details.get("selling_rate_id"),
                        "selling_price": existing_details.get("selling_price"),
                        "extra_costs": existing_details.get("extra_costs") or [],
                        "extra_revenues": existing_details.get("extra_revenues") or []
                    }

                    # Add cost - store in extra_costs with full structure
                    if action_type in ["add_cost", "add_cost_revenue"]:
                        cost_qty = entities.get("cost_qty", 1)
                        cost_unit_price = entities.get("cost_unit_price", 0)
                        cost_amount = cost_qty * cost_unit_price
                        cost_source = entities.get("cost_source", "manual")
                        vendor_name = entities.get("vendor_name", "")
                        cost_name = entities.get("cost_name", "")
                        cost_unit = entities.get("cost_unit", "ca")

                        # Build cost name: use extracted name, or build from vendor/source
                        if not cost_name:
                            if vendor_name:
                                cost_name = f"Chi phí từ {vendor_name}"
                            else:
                                cost_name = f"Chi phí ({cost_source})"

                        # Add new cost with full structure (including vendor)
                        quotation_payload["extra_costs"].append({
                            "name": cost_name,
                            "qty": cost_qty,
                            "unit_price": cost_unit_price,
                            "unit": cost_unit,
                            "amount": cost_amount,
                            "vendor": vendor_name
                        })
                        changes.append(f"Chi phí: {cost_qty} {cost_unit} × {cost_unit_price:,.0f} = {cost_amount:,.0f} VND - {cost_name}")

                    # Add revenue - store in extra_revenues with full structure
                    if action_type in ["add_revenue", "add_cost_revenue"]:
                        revenue_qty = entities.get("revenue_qty", 1)
                        revenue_unit_price = entities.get("revenue_unit_price", 0)
                        revenue_amount = revenue_qty * revenue_unit_price
                        revenue_name = entities.get("revenue_name", "")
                        revenue_unit = entities.get("revenue_unit", "chuyến")

                        # Build revenue name: use extracted name or default
                        if not revenue_name:
                            revenue_name = "Doanh thu dịch vụ"

                        # Add new revenue with full structure
                        quotation_payload["extra_revenues"].append({
                            "name": revenue_name,
                            "qty": revenue_qty,
                            "unit_price": revenue_unit_price,
                            "unit": revenue_unit,
                            "amount": revenue_amount
                        })
                        changes.append(f"Doanh thu: {revenue_qty} {revenue_unit} × {revenue_unit_price:,.0f} = {revenue_amount:,.0f} VND - {revenue_name}")

                    # Handle multi_cost / multi_cost_revenue - process arrays
                    if action_type in ["multi_cost", "multi_cost_revenue"]:
                        # Process multiple costs
                        costs_array = entities.get("costs", [])
                        for cost_item in costs_array:
                            cost_qty = cost_item.get("cost_qty", 1)
                            cost_unit_price = cost_item.get("cost_unit_price", 0)
                            cost_amount = cost_qty * cost_unit_price
                            cost_name = cost_item.get("cost_name", "Chi phí")
                            cost_unit = cost_item.get("cost_unit", "ca")
                            vendor_name = cost_item.get("vendor_name", "")

                            quotation_payload["extra_costs"].append({
                                "name": cost_name,
                                "qty": cost_qty,
                                "unit_price": cost_unit_price,
                                "unit": cost_unit,
                                "amount": cost_amount,
                                "vendor": vendor_name
                            })
                            changes.append(f"Chi phí: {cost_qty} {cost_unit} × {cost_unit_price:,.0f} = {cost_amount:,.0f} VND - {cost_name}")

                        # Process multiple revenues (for multi_cost_revenue)
                        revenues_array = entities.get("revenues", [])
                        for rev_item in revenues_array:
                            revenue_qty = rev_item.get("revenue_qty", 1)
                            revenue_unit_price = rev_item.get("revenue_unit_price", 0)
                            revenue_amount = revenue_qty * revenue_unit_price
                            revenue_name = rev_item.get("revenue_name", "Doanh thu dịch vụ")
                            revenue_unit = rev_item.get("revenue_unit", "chuyến")

                            quotation_payload["extra_revenues"].append({
                                "name": revenue_name,
                                "qty": revenue_qty,
                                "unit_price": revenue_unit_price,
                                "unit": revenue_unit,
                                "amount": revenue_amount
                            })
                            changes.append(f"Doanh thu: {revenue_qty} {revenue_unit} × {revenue_unit_price:,.0f} = {revenue_amount:,.0f} VND - {revenue_name}")

                    # Save quotation (endpoint is under /api/jobs router)
                    quote_resp = await client.put(
                        f"{API_BASE_URL}/api/jobs/services/{svc_id}/quotations",
                        json=quotation_payload,
                        timeout=30.0
                    )
                    if quote_resp.status_code == 200:
                        result = quote_resp.json()
                        if not result.get("success"):
                            return {"success": False, "message": result.get("message", "Save quotation failed")}
                    else:
                        return {"success": False, "message": f"API error: {quote_resp.status_code}"}

                if not changes:
                    return {"success": False, "message": "Không có thay đổi nào được yêu cầu."}

                return {
                    "success": True,
                    "job_number": job_number,
                    "changes": changes
                }

        except Exception as e:
            import logging
            logging.error(f"Update job error: {e}")
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

        # Delivery company (important for avoiding confusion)
        if entities.get("delivery_company"):
            lines.append(f"🏭 Công ty nhận: {entities['delivery_company']}")

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
        """Generate vehicle assignment confirmation message for customer (no bold markers)"""
        job_details = job_details or {}
        lines = []
        lines.append(f"🚚 XÁC NHẬN GÁN XE")
        lines.append(f"Job: {job_number}")
        lines.append("")

        # Job info (from job_details)
        if job_details.get("scheduled_date") or job_details.get("pickup_date"):
            date = job_details.get("scheduled_date") or job_details.get("pickup_date")
            lines.append(f"📅 Ngày: {date}")

        if job_details.get("scheduled_time") or job_details.get("pickup_time"):
            time = job_details.get("scheduled_time") or job_details.get("pickup_time")
            lines.append(f"⏰ Giờ: {time}")

        # Invoices
        if job_details.get("invoice_numbers") or job_details.get("invoices"):
            inv = job_details.get("invoice_numbers") or job_details.get("invoices")
            if isinstance(inv, list):
                inv = ', '.join(str(i) for i in inv)
            lines.append(f"📄 Invoice: {inv}")

        # Quantity/Package info - now below invoice
        pkg_qty = job_details.get("package_quantity") or job_details.get("package_display")
        pkg_unit = job_details.get("package_unit") or ""
        if pkg_qty:
            qty_str = f"{pkg_qty}"
            if pkg_unit:
                qty_str = f"{pkg_qty} {pkg_unit}"
            lines.append(f"📦 Số lượng: {qty_str}")

        lines.append("")

        # Vehicle info with tonnage
        if entities.get("license_plate"):
            plate_str = entities['license_plate']
            # Add vehicle tonnage if available
            if entities.get("vehicle_type"):
                plate_str = f"{plate_str} - {entities['vehicle_type']}"
            lines.append(f"🚗 Biển số: {plate_str}")

        if entities.get("driver_name"):
            lines.append(f"👤 Tài xế: {entities['driver_name']}")

        if entities.get("driver_phone"):
            lines.append(f"📞 SĐT: {entities['driver_phone']}")

        if entities.get("driver_cccd") or entities.get("driver_id_card"):
            cccd = entities.get("driver_cccd") or entities.get("driver_id_card")
            lines.append(f"🆔 CCCD: {cccd}")

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
        import logging
        logger = logging.getLogger(__name__)

        # Reset any previous task
        state.reset_task()

        # Classify intent if not detected
        if not detected_intent:
            intent_result = await self.intent_classifier.classify(message)
            detected_intent = intent_result["intent"]

        logger.info(f"[NEW_TASK] detected_intent={detected_intent}")

        # Load database context for entity extraction (customers, routes, vehicle_types)
        db_context = {}
        if self.context_loader:
            try:
                db_context = await self.context_loader.load(detected_intent)
                logger.info(f"[NEW_TASK] Loaded db context keys={list(db_context.keys())}")
                logger.info(f"[NEW_TASK] customers count={len(db_context.get('customers', []))}")
            except Exception as e:
                logger.error(f"[NEW_TASK] Failed to load context: {e}")

        # Merge frontend context with database context
        merged_context = {**db_context, **(context or {})}

        # Extract entities with full context
        extracted = await self.entity_extractor.extract(
            text=message,
            intent=detected_intent,
            context=merged_context
        )

        logger.info(f"[NEW_TASK] extracted entities={list(extracted.get('entities', {}).keys())}")

        entities = extracted.get("entities", {})

        # Check for low-confidence customer match - ask for confirmation
        if entities.get("customer_needs_confirmation") and entities.get("customer_candidates"):
            candidates = entities.get("customer_candidates", [])
            raw_input = entities.get("customer_raw_input", "")
            confidence = entities.get("customer_confidence", 0)

            logger.info(f"[NEW_TASK] Customer needs confirmation: '{raw_input}' -> {candidates}")

            # Build confirmation message
            response = f"⚠️ Không chắc chắn về khách hàng '{raw_input}'.\n\n"
            response += "Có phải bạn muốn chọn:\n"
            for i, c in enumerate(candidates, 1):
                score_pct = int(c['score'] * 100)
                response += f"  {i}. **{c['code']}** - {c['name']} ({score_pct}%)\n"
            response += "\nVui lòng trả lời số (1-3) hoặc nhập mã KH chính xác."

            # Start task but mark as awaiting customer selection
            state.task.start_task(detected_intent, entities)
            state.task.state = TaskState.COLLECTING
            state.task.awaiting_field = "customer_code"
            state.task.confirmation_data = {"customer_candidates": candidates}

            return ProcessResult(
                response=response,
                state=state,
                needs_confirmation=False
            )

        # Start new task
        state.task.start_task(detected_intent, entities)

        # Accumulate and check completeness
        result = self.accumulator.accumulate(state.task, {})  # Already have entities
        state.task.missing_fields = result.missing_fields

        logger.info(f"[NEW_TASK] is_complete={result.is_complete}, missing={result.missing_fields}")

        # Generate response
        if result.is_complete:
            state.task.state = TaskState.CONFIRMING
            state.task.confirmation_data = state.task.entities
            logger.info(f"[NEW_TASK] Set state to CONFIRMING, session_id={state.session_id}")
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
        import logging
        logger = logging.getLogger(__name__)

        if not state.task.is_active():
            # No active task, treat as new
            return await self._handle_new_task(state, message, None, context)

        # Check if awaiting customer selection
        if state.task.awaiting_field == "customer_code":
            return await self._handle_customer_selection(state, message, context)

        # Load database context for entity extraction
        db_context = {}
        if self.context_loader:
            try:
                db_context = await self.context_loader.load(state.task.intent)
                logger.info(f"[CONTINUATION] Loaded db context, customers={len(db_context.get('customers', []))}")
            except Exception as e:
                logger.error(f"[CONTINUATION] Failed to load context: {e}")

        # Merge frontend context with database context
        merged_context = {**db_context, **(context or {})}

        # Extract new entities with full context
        extracted = await self.entity_extractor.extract(
            text=message,
            intent=state.task.intent,
            context=merged_context
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

    async def _handle_customer_selection(
        self,
        state: ConversationState,
        message: str,
        context: Optional[Dict]
    ) -> ProcessResult:
        """Handle customer selection when awaiting confirmation"""
        import logging
        logger = logging.getLogger(__name__)

        candidates = state.task.confirmation_data.get("customer_candidates", [])
        message_stripped = message.strip()

        logger.info(f"[CUSTOMER_SELECTION] message='{message_stripped}', candidates={len(candidates)}")

        # Confirmation keywords that mean "select option 1" (the top suggestion)
        confirm_as_select_1 = [
            "ok", "được", "đồng ý", "yes", "ừ", "uh", "đúng", "đúng rồi",
            "chính xác", "phải", "oke", "okie", "vâng", "dạ"
        ]
        msg_lower = message_stripped.lower()

        # If user confirms with "OK" etc, treat as selecting option 1
        if msg_lower in confirm_as_select_1 and candidates:
            selected = candidates[0]
            logger.info(f"[CUSTOMER_SELECTION] User confirmed with '{msg_lower}', auto-selecting: {selected['code']}")

            # Update entities with confirmed customer
            state.task.entities["customer_code"] = selected["code"]
            state.task.entities["customer_confidence"] = 1.0  # User confirmed
            state.task.entities["customer_needs_confirmation"] = False
            state.task.entities.pop("customer_candidates", None)
            state.task.awaiting_field = None
            state.task.confirmation_data = {}

            # Continue with normal accumulation to check completeness
            result = self.accumulator.accumulate(state.task, {})
            state.task.missing_fields = result.missing_fields

            if result.is_complete:
                state.task.state = TaskState.CONFIRMING
                state.task.confirmation_data = state.task.entities
                response = f"✅ Đã chọn khách hàng: **{selected['code']}** - {selected['name']}\n\n"
                response += self._generate_confirmation_request(state.task)
                return ProcessResult(
                    response=response,
                    state=state,
                    needs_confirmation=True,
                    confirmation_data=state.task.entities
                )
            else:
                response = f"✅ Đã chọn khách hàng: **{selected['code']}** - {selected['name']}\n\n"
                response += self.accumulator.get_summary(state.task)
                if result.missing_fields:
                    response += f"\n\n{self.accumulator.get_missing_fields_message(state.task.intent, result.missing_fields)}"
                return ProcessResult(response=response, state=state)

        # Check if user entered a number (1-3) to select candidate
        if message_stripped.isdigit():
            idx = int(message_stripped) - 1
            if 0 <= idx < len(candidates):
                selected = candidates[idx]
                logger.info(f"[CUSTOMER_SELECTION] User selected: {selected['code']}")

                # Update entities with confirmed customer
                state.task.entities["customer_code"] = selected["code"]
                state.task.entities["customer_confidence"] = 1.0  # User confirmed
                state.task.entities["customer_needs_confirmation"] = False
                state.task.entities.pop("customer_candidates", None)
                state.task.awaiting_field = None
                state.task.confirmation_data = {}

                # Continue with normal accumulation to check completeness
                result = self.accumulator.accumulate(state.task, {})
                state.task.missing_fields = result.missing_fields

                if result.is_complete:
                    state.task.state = TaskState.CONFIRMING
                    state.task.confirmation_data = state.task.entities
                    response = f"✅ Đã chọn khách hàng: **{selected['code']}** - {selected['name']}\n\n"
                    response += self._generate_confirmation_request(state.task)
                    return ProcessResult(
                        response=response,
                        state=state,
                        needs_confirmation=True,
                        confirmation_data=state.task.entities
                    )
                else:
                    response = f"✅ Đã chọn khách hàng: **{selected['code']}** - {selected['name']}\n\n"
                    response += self.accumulator.get_summary(state.task)
                    if result.missing_fields:
                        response += f"\n\n{self.accumulator.get_missing_fields_message(state.task.intent, result.missing_fields)}"
                    return ProcessResult(response=response, state=state)
            else:
                # Invalid number
                return ProcessResult(
                    response=f"⚠️ Số không hợp lệ. Vui lòng chọn từ 1 đến {len(candidates)}.",
                    state=state
                )

        # Otherwise treat as new customer code input - re-validate
        logger.info(f"[CUSTOMER_SELECTION] Treating as new customer input: '{message_stripped}'")

        # Load customer context
        db_context = {}
        if self.context_loader:
            try:
                db_context = await self.context_loader.load(state.task.intent)
            except Exception as e:
                logger.error(f"[CUSTOMER_SELECTION] Failed to load context: {e}")

        # Re-extract with the new customer input
        from app.ai.entity_extractor import EntityExtractor
        extracted = await self.entity_extractor.extract(
            text=message_stripped,
            intent=state.task.intent,
            context={**db_context, **(context or {})}
        )

        new_entities = extracted.get("entities", {})

        # Check if new input still needs confirmation
        if new_entities.get("customer_needs_confirmation") and new_entities.get("customer_candidates"):
            candidates = new_entities.get("customer_candidates", [])
            raw_input = new_entities.get("customer_raw_input", message_stripped)

            response = f"⚠️ Không chắc chắn về khách hàng '{raw_input}'.\n\n"
            response += "Có phải bạn muốn chọn:\n"
            for i, c in enumerate(candidates, 1):
                score_pct = int(c['score'] * 100)
                response += f"  {i}. **{c['code']}** - {c['name']} ({score_pct}%)\n"
            response += "\nVui lòng trả lời số (1-3) hoặc nhập mã KH chính xác."

            state.task.confirmation_data = {"customer_candidates": candidates}
            return ProcessResult(response=response, state=state)

        # Customer is now confirmed
        if new_entities.get("customer_code"):
            state.task.entities["customer_code"] = new_entities["customer_code"]
            state.task.entities["customer_confidence"] = new_entities.get("customer_confidence", 1.0)
            state.task.entities["customer_needs_confirmation"] = False
            state.task.entities.pop("customer_candidates", None)
        state.task.awaiting_field = None
        state.task.confirmation_data = {}

        # Continue with accumulation
        result = self.accumulator.accumulate(state.task, {})
        state.task.missing_fields = result.missing_fields

        if result.is_complete:
            state.task.state = TaskState.CONFIRMING
            state.task.confirmation_data = state.task.entities
            response = self._generate_confirmation_request(state.task)
            return ProcessResult(
                response=response,
                state=state,
                needs_confirmation=True,
                confirmation_data=state.task.entities
            )
        else:
            response = self.accumulator.get_summary(state.task)
            if result.missing_fields:
                response += f"\n\n{self.accumulator.get_missing_fields_message(state.task.intent, result.missing_fields)}"
            return ProcessResult(response=response, state=state)

    def _generate_confirmation_request(self, task: Any) -> str:
        """Generate confirmation request message"""
        summary = self.accumulator.get_summary(task)

        intent_names = {
            "create_booking": "tạo booking",
            "update_job": "cập nhật job",
            "assign_vehicle": "gán xe",
            "cancel_job": "hủy job",
            "create_customer": "tạo khách hàng",
            "create_vendor": "tạo nhà cung cấp",
            "create_quotation": "tạo báo giá",
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
