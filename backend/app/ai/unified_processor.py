# -*- coding: utf-8 -*-
"""
SLMS AI - Unified Conversation Processor
========================================

A simpler, AI-driven conversation processor that replaces:
- Rule-based intent detection
- Multiple separate prompts
- Rigid entity extraction

Instead, uses a single unified prompt and lets AI handle everything naturally.
"""

import logging
import json
import re
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from app.db.supabase_client import get_supabase

logger = logging.getLogger(__name__)


@dataclass
class UnifiedState:
    """Simple state for unified conversation"""
    session_id: str
    intent: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    history: list = field(default_factory=list)
    ready_to_execute: bool = False
    needs_confirmation: bool = False


@dataclass
class UnifiedResult:
    """Result from unified processor"""
    response: str
    state: UnifiedState
    action: Optional[Dict[str, Any]] = None
    ready_to_execute: bool = False


class UnifiedProcessor:
    """
    AI-driven conversation processor using unified prompt.

    Key differences from classic approach:
    - No hardcoded keywords for intent detection
    - Single prompt handles all cases
    - AI decides what's missing and asks naturally
    - More flexible with input formats
    """

    def __init__(self, ai_client, db_session=None):
        self.ai = ai_client
        self.db = db_session
        self.states: Dict[str, UnifiedState] = {}

        # Lazy import context loader
        from app.ai.context_loader import ContextLoader
        self.context_loader = ContextLoader(db_session) if db_session else None

    def _get_state(self, session_id: str) -> UnifiedState:
        """Get or create session state"""
        if session_id not in self.states:
            logger.info(f"[UNIFIED] NEW session {session_id[:8]}... (total_sessions={len(self.states)}, pid={__import__('os').getpid()})")
            self.states[session_id] = UnifiedState(session_id=session_id)
        else:
            s = self.states[session_id]
            logger.info(f"[UNIFIED] EXISTING session {session_id[:8]}... intent={s.intent}, entities={len(s.entities)}, history={len(s.history)}")
        return self.states[session_id]

    async def process(
        self,
        session_id: str,
        message: str,
        context: Optional[Dict] = None
    ) -> UnifiedResult:
        """
        Process user message with unified AI approach.

        Args:
            session_id: Session identifier
            message: User message
            context: Additional context from frontend

        Returns:
            UnifiedResult with response and state
        """
        state = self._get_state(session_id)

        logger.info(f"[UNIFIED] session={session_id[:8]}, message={message[:50]}...")
        logger.info(f"[UNIFIED] current_intent={state.intent}, entities={len(state.entities)}")

        # Check for confirmation without context (session expired/lost)
        confirmation_words = ['ok', 'có', 'được', 'đồng ý', 'xác nhận', 'tạo đi', 'làm đi', 'yes', 'confirm']
        msg_lower = message.strip().lower()
        is_confirmation = any(msg_lower == word or msg_lower.startswith(word + ' ') for word in confirmation_words)

        if is_confirmation and not state.intent and len(state.history) <= 1:
            logger.warning(f"[UNIFIED] Confirmation received but no active task - session may have expired")
            return UnifiedResult(
                response="Phiên làm việc đã hết hạn hoặc chưa có tác vụ nào được bắt đầu.\n\n"
                        "Vui lòng nhập lại yêu cầu của bạn (ví dụ: tạo job, gán xe, cập nhật trạng thái...).",
                state=state
            )

        # Add user message to history
        state.history.append({"role": "user", "content": message})

        # Load database context
        db_context = await self._load_context(state.intent)

        # Build unified prompt
        from app.ai.prompts.unified_logistics_prompt import build_unified_prompt

        prompt = build_unified_prompt(
            user_message=message,
            conversation_history=state.history,
            accumulated_entities=state.entities,
            db_context=db_context,
            current_task={"intent": state.intent} if state.intent else None
        )

        # Call AI
        try:
            ai_response = await self.ai.generate(
                prompt=prompt,
                response_format="json",
                temperature=0.3
            )

            logger.info(f"[UNIFIED] AI response type: {type(ai_response)}")

            # Parse AI response
            result = self._parse_response(ai_response)

            logger.info(f"[UNIFIED] parsed intent={result.get('intent')}, ready={result.get('ready_to_execute')}")
            logger.info(f"[UNIFIED] entities keys={list(result.get('entities', {}).keys())}")
            logger.info(f"[UNIFIED] response preview={result.get('response', '')[:100]}...")

        except Exception as e:
            logger.error(f"[UNIFIED] AI call failed: {e}")
            return UnifiedResult(
                response=f"Xin lỗi, có lỗi xảy ra. Vui lòng thử lại.",
                state=state
            )

        # Update state with extracted entities
        new_entities = result.get("entities", {})
        if new_entities:
            state.entities.update(new_entities)

        # Update intent if detected
        if result.get("intent") and result["intent"] != "clarification_needed":
            state.intent = result["intent"]

        # Check if ready to execute
        ready_to_execute = result.get("ready_to_execute", False)
        needs_confirmation = result.get("needs_confirmation", False)

        # SAFETY NET: If user confirmed and we have active intent+entities,
        # force execution even if AI didn't set ready_to_execute
        if is_confirmation and state.intent and state.entities and not ready_to_execute:
            logger.info(f"[UNIFIED] Forcing execution: user confirmed with active intent={state.intent}")
            ready_to_execute = True

        # Track confirmation state for next turn
        if needs_confirmation:
            state.needs_confirmation = True

        # Get response text
        response_text = result.get("response", "")
        if not response_text:
            response_text = self._generate_response(state, result)

        # Add assistant response to history
        state.history.append({"role": "assistant", "content": response_text})

        # If ready to execute, prepare action
        action = None
        if ready_to_execute and state.intent:
            action = await self._prepare_action(state)
            if action:
                # Always show action response (success or error)
                response_text = action.get("response", response_text)
                if action.get("success"):
                    # Reset state after successful execution
                    self._reset_state(state)

        return UnifiedResult(
            response=response_text,
            state=state,
            action=action,
            ready_to_execute=ready_to_execute
        )

    def _parse_response(self, response: Any) -> Dict:
        """Parse AI response to dict"""
        if isinstance(response, dict):
            return response

        if isinstance(response, str):
            try:
                # Try direct parse
                return json.loads(response)
            except json.JSONDecodeError:
                pass

            # Try extracting JSON from markdown
            match = re.search(r"```json\s*([\s\S]*?)\s*```", response)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass

            # Try finding JSON object
            match = re.search(r"\{[\s\S]*\}", response)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass

        logger.warning(f"[UNIFIED] Could not parse response: {str(response)[:200]}")
        return {"response": str(response), "intent": "general_query"}

    async def _load_context(self, intent: Optional[str]) -> Dict:
        """Load database context"""
        if not self.context_loader:
            return {}

        try:
            return await self.context_loader.load(intent or "create_booking")
        except Exception as e:
            logger.error(f"[UNIFIED] Failed to load context: {e}")
            return {}

    def _generate_response(self, state: UnifiedState, result: Dict) -> str:
        """Generate response if AI didn't provide one"""
        missing = result.get("missing_fields", [])

        if missing:
            fields_vi = {
                "customer_code": "mã khách hàng",
                "booking_date": "ngày booking",
                "job_number": "mã job",
                "license_plate": "biển số xe",
                "driver_name": "tên tài xế",
                "cost_unit_price": "số tiền chi phí",
                "revenue_unit_price": "số tiền doanh thu",
            }
            missing_vi = [fields_vi.get(f, f) for f in missing]
            return f"Vui lòng cho biết thêm: {', '.join(missing_vi)}"

        if state.intent and state.entities:
            return self._generate_confirmation(state)

        return "Tôi có thể giúp gì cho bạn?"

    def _generate_confirmation(self, state: UnifiedState) -> str:
        """Generate confirmation message with Vietnamese labels"""
        intent_names = {
            "create_booking": "tạo booking",
            "assign_vehicle": "gán xe",
            "update_status": "cập nhật trạng thái",
            "add_cost": "thêm chi phí",
            "add_revenue": "thêm doanh thu",
            "add_note": "thêm ghi chú",
        }

        # Vietnamese labels for important fields
        field_labels = {
            "customer_code": "Khách hàng",
            "customer_name": "Tên KH",
            "booking_date": "Ngày",
            "pickup_time": "Giờ",
            "pickup_address": "Điểm lấy",
            "origin_address": "Điểm lấy",
            "delivery_address": "Điểm giao",
            "dest_address": "Điểm giao",
            "cargo_type": "Loại hàng",
            "package_quantity": "Số lượng",
            "package_unit": "Đơn vị",
            "invoice_numbers": "📋 Số INV/CD",
            "vehicle_type": "Loại xe",
            "license_plate": "Biển số xe",
            "driver_name": "Tài xế",
            "driver_phone": "SĐT tài xế",
            "vendor_code": "Vendor",
            "job_number": "Job",
            "new_status": "Trạng thái mới",
            "notes": "Ghi chú",
        }

        action = intent_names.get(state.intent, state.intent)
        lines = [f"✅ Xác nhận {action}:"]

        skip_keys = {"vehicles", "rates", "bookings"}
        for key, value in state.entities.items():
            if value and not key.startswith("_") and key not in skip_keys:
                label = field_labels.get(key, key)
                lines.append(f"• {label}: {value}")

        # Handle multiple vehicles
        vehicles = state.entities.get("vehicles", [])
        if vehicles and len(vehicles) > 0:
            lines.append(f"• 🚚 Xe ({len(vehicles)}):")
            for i, v in enumerate(vehicles, 1):
                v_info = f"  {i}. {v.get('license_plate', 'N/A')}"
                if v.get('driver_name'):
                    v_info += f" - {v.get('driver_name')}"
                lines.append(v_info)

        # Handle multiple rates (quotation)
        rates = state.entities.get("rates", [])
        if rates and len(rates) > 0:
            lines.append(f"• 💰 Báo giá ({len(rates)} loại xe):")
            for r in rates:
                vt = r.get("vehicle_type", "?")
                p = r.get("price", 0)
                try:
                    if isinstance(p, (int, float)):
                        p = float(p)
                    else:
                        p = float(str(p).replace(",", "").strip())
                    lines.append(f"  - {vt}: {p:,.0f} VND")
                except (ValueError, TypeError):
                    lines.append(f"  - {vt}: {p}")

        lines.append("\nGõ 'ok' để xác nhận hoặc sửa thông tin.")
        return "\n".join(lines)

    async def _prepare_action(self, state: UnifiedState) -> Optional[Dict]:
        """Prepare and execute action"""
        import httpx
        from os import getenv

        API_BASE_URL = getenv("SLMS_API_URL", "http://localhost:8000")

        try:
            async with httpx.AsyncClient() as client:
                if state.intent == "create_booking":
                    # Check if there are multiple bookings
                    bookings = state.entities.get("bookings", [])
                    if not bookings:
                        # Single booking - use entities directly
                        bookings = [state.entities]

                    created_jobs = []  # List of (job_no, booking_data) tuples
                    all_assigned_vehicles = []
                    # Capture the first validator rejection so we can show the
                    # user a specific Vietnamese message instead of a generic error.
                    first_rejection: Optional[Dict] = None

                    for booking in bookings:
                        # Merge with base entities for common fields
                        merged_entities = {**state.entities, **booking}
                        # Remove bookings array to avoid recursion
                        merged_entities.pop("bookings", None)

                        response = await client.post(
                            f"{API_BASE_URL}/api/jobs/create",
                            json={
                                "session_id": state.session_id,
                                "entities": merged_entities,
                                "enriched_data": merged_entities
                            },
                            timeout=30.0
                        )
                        if response.status_code == 200:
                            result = response.json()
                            if result.get("success"):
                                job_no = result.get("job_number", "N/A")
                                job_id = result.get("job_id")
                                # Store job with booking details for vendor message
                                created_jobs.append((job_no, merged_entities))

                                # If vehicles present in this booking, assign them
                                vehicles = merged_entities.get("vehicles", [])
                                if not vehicles and merged_entities.get("license_plate"):
                                    vehicles = [{
                                        "license_plate": merged_entities.get("license_plate"),
                                        "vehicle_type": merged_entities.get("vehicle_type"),
                                        "driver_name": merged_entities.get("driver_name"),
                                        "driver_phone": merged_entities.get("driver_phone"),
                                        "driver_cccd": merged_entities.get("driver_cccd")
                                    }]

                                if vehicles and job_id:
                                    vendor_code = merged_entities.get("vendor_code") or merged_entities.get("vendor_name")
                                    for v in vehicles:
                                        if not v.get("license_plate"):
                                            continue
                                        assign = await client.post(
                                            f"{API_BASE_URL}/api/jobs/{job_id}/assign-vehicle",
                                            json={
                                                "license_plate": v.get("license_plate"),
                                                "vehicle_type": v.get("vehicle_type"),
                                                "driver_name": v.get("driver_name"),
                                                "driver_phone": v.get("driver_phone"),
                                                "driver_id_card": v.get("driver_cccd"),
                                                "vendor_code": vendor_code
                                            },
                                            timeout=30.0
                                        )
                                        if assign.status_code == 200:
                                            all_assigned_vehicles.append(v.get("license_plate"))
                                        else:
                                            logger.warning(f"[UNIFIED] Failed to assign {v.get('license_plate')}: {assign.text}")
                            else:
                                logger.warning(f"[UNIFIED] Failed to create job: {result.get('message')}")
                                if first_rejection is None:
                                    first_rejection = result
                        else:
                            logger.warning(f"[UNIFIED] API error creating job: {response.text}")
                            if first_rejection is None:
                                try:
                                    first_rejection = response.json()
                                except Exception:
                                    first_rejection = {"message": response.text}

                    # Build vendor-ready response for all created jobs
                    if created_jobs:
                        resp_text = f"✅ Đã tạo {len(created_jobs)} Job thành công!\n\n"
                        resp_text += "📋 **THÔNG TIN GỬI VENDOR** (bấm Copy để sao chép):\n\n"

                        for job_no, data in created_jobs:
                            # Build copyable message for this job
                            vendor_msg = self._build_vendor_message(job_no, data)
                            # Wrap in code block for copy button
                            resp_text += f"```\n{vendor_msg}```\n\n"

                        if all_assigned_vehicles:
                            resp_text += f"🚛 Đã gán xe: {', '.join(all_assigned_vehicles)}"

                        return {"success": True, "response": resp_text}

                    # No job created — surface the specific rejection to the user.
                    # For missing_loai_hinh / invalid_loai_hinh we include the
                    # code list so user can pick one directly in the reply.
                    if first_rejection:
                        msg = first_rejection.get("message") or "Không tạo được job."
                        suggestions = first_rejection.get("suggestions") or []
                        if suggestions and first_rejection.get("error") in (
                            "missing_loai_hinh", "invalid_loai_hinh"
                        ):
                            msg += "\n\n**Các mã loại hình hải quan thường dùng:**"
                            for s in suggestions:
                                msg += f"\n- `{s['code']}` — {s['label']}"
                        return {"success": False, "response": msg}
                    return {"success": False, "response": "Lỗi tạo job"}

                elif state.intent == "assign_vehicle":
                    # Get job_id from job_number
                    job_number = state.entities.get("job_number")
                    if not job_number:
                        return {"success": False, "response": "Thiếu mã job"}

                    # Try exact match first
                    lookup = await client.get(
                        f"{API_BASE_URL}/api/jobs/by-number/{job_number}",
                        timeout=10.0
                    )

                    # If not found and job_number is short (3-4 digits), search recent jobs
                    if lookup.status_code == 200:
                        job_data = lookup.json()
                        if not job_data.get("success") and len(job_number) <= 4 and job_number.isdigit():
                            # Search recent jobs ending with this number
                            recent = await client.get(
                                f"{API_BASE_URL}/api/jobs/recent?limit=50",
                                timeout=10.0
                            )
                            if recent.status_code == 200:
                                jobs = recent.json().get("jobs", [])
                                for j in jobs:
                                    if j.get("job_no", "").endswith(job_number):
                                        job_number = j.get("job_no")
                                        # Re-fetch with full job number
                                        lookup = await client.get(
                                            f"{API_BASE_URL}/api/jobs/by-number/{job_number}",
                                            timeout=10.0
                                        )
                                        break

                    if lookup.status_code != 200:
                        return {"success": False, "response": f"Không tìm thấy job {job_number}"}

                    job_data = lookup.json()
                    if not job_data.get("success"):
                        return {"success": False, "response": f"Không tìm thấy job {job_number}"}

                    job_id = job_data.get("job_id")
                    vendor_code = state.entities.get("vendor_code") or state.entities.get("vendor_name")

                    # Support multiple vehicles
                    vehicles = state.entities.get("vehicles", [])
                    if not vehicles:
                        # Fallback to single vehicle
                        vehicles = [{
                            "license_plate": state.entities.get("license_plate"),
                            "vehicle_type": state.entities.get("vehicle_type"),
                            "driver_name": state.entities.get("driver_name"),
                            "driver_phone": state.entities.get("driver_phone"),
                            "driver_cccd": state.entities.get("driver_cccd")
                        }]

                    assigned = []
                    for v in vehicles:
                        if not v.get("license_plate"):
                            continue
                        assign = await client.post(
                            f"{API_BASE_URL}/api/jobs/{job_id}/assign-vehicle",
                            json={
                                "license_plate": v.get("license_plate"),
                                "vehicle_type": v.get("vehicle_type"),
                                "driver_name": v.get("driver_name"),
                                "driver_phone": v.get("driver_phone"),
                                "driver_id_card": v.get("driver_cccd"),
                                "vendor_code": vendor_code
                            },
                            timeout=30.0
                        )
                        if assign.status_code == 200:
                            assigned.append(v.get("license_plate"))
                        else:
                            logger.warning(f"[UNIFIED] Failed to assign {v.get('license_plate')}: {assign.text}")

                    if assigned:
                        # Fetch job details to build vendor message
                        details_resp = await client.get(
                            f"{API_BASE_URL}/api/jobs/{job_id}/details",
                            timeout=10.0
                        )

                        resp_text = f"✅ Đã gán {len(assigned)} xe cho Job {job_number}!\n\n"
                        resp_text += "📋 **THÔNG TIN GỬI VENDOR** (bấm Copy để sao chép):\n\n"

                        # Build job data from details or entities
                        job_details = {}
                        if details_resp.status_code == 200:
                            detail_data = details_resp.json()
                            job_info = detail_data.get("job", {})
                            services = detail_data.get("services", [])
                            svc = services[0] if services else {}

                            job_details = {
                                "invoice_numbers": svc.get("invoice_numbers") or (svc.get("service_details") or {}).get("invoice_numbers"),
                                "cargo_type": svc.get("cargo_type"),
                                "package_quantity": svc.get("package_quantity"),
                                "package_unit": svc.get("package_unit"),
                                "booking_date": svc.get("scheduled_date"),
                                "pickup_time": svc.get("scheduled_time"),
                                "pickup_address": svc.get("origin_address"),
                                "delivery_address": svc.get("dest_address"),
                                "receiver_contact": state.entities.get("receiver_contact"),
                                "vehicle_type": state.entities.get("vehicle_type") or vehicles[0].get("vehicle_type") if vehicles else None
                            }

                        # Build vendor message with vehicle info
                        for v in vehicles:
                            if v.get("license_plate") in assigned:
                                vendor_msg = self._build_vendor_message(job_number, job_details, vehicle_info=v)
                                resp_text += f"```\n{vendor_msg}```\n\n"

                        return {"success": True, "response": resp_text}
                    return {"success": False, "response": "Không gán được xe nào"}

                elif state.intent == "update_status":
                    # If entities also contain cost/revenue, redirect to update_job handler
                    has_cost = state.entities.get("cost_unit_price") or state.entities.get("costs")
                    has_revenue = state.entities.get("revenue_unit_price") or state.entities.get("revenues")
                    if has_cost or has_revenue:
                        state.intent = "update_job"
                        return await self._prepare_action(state)

                    response = await client.post(
                        f"{API_BASE_URL}/api/jobs/update",
                        json={"entities": state.entities},
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            return {
                                "success": True,
                                "response": f"✅ Đã cập nhật trạng thái thành công!"
                            }
                    return {"success": False, "response": "Lỗi cập nhật trạng thái"}

                elif state.intent == "update_job":
                    # Combined update: status + cost + revenue for same job
                    job_number = state.entities.get("job_number")
                    if not job_number:
                        return {"success": False, "response": "Vui lòng cho biết mã job."}

                    lookup = await client.get(
                        f"{API_BASE_URL}/api/jobs/by-number/{job_number}",
                        timeout=10.0
                    )
                    if lookup.status_code != 200:
                        return {"success": False, "response": f"Không tìm thấy job {job_number}"}

                    job_data = lookup.json()
                    if not job_data.get("success"):
                        return {"success": False, "response": f"Không tìm thấy job {job_number}"}

                    job_id = job_data.get("job_id")
                    changes = []

                    # 1. Update status if present
                    new_status = state.entities.get("new_status")
                    if new_status:
                        status_resp = await client.post(
                            f"{API_BASE_URL}/api/jobs/update",
                            json={"entities": {
                                "job_number": job_number,
                                "new_status": new_status
                            }},
                            timeout=30.0
                        )
                        if status_resp.status_code == 200 and status_resp.json().get("success"):
                            changes.append(f"Trạng thái → {new_status}")
                        else:
                            logger.warning(f"[UNIFIED] Status update failed: {status_resp.text}")

                    # 2. Add cost/revenue if present
                    has_cost = state.entities.get("cost_unit_price") or state.entities.get("costs")
                    has_revenue = state.entities.get("revenue_unit_price") or state.entities.get("revenues")
                    if has_cost or has_revenue:
                        details = await client.get(
                            f"{API_BASE_URL}/api/jobs/{job_id}/details",
                            timeout=10.0
                        )
                        if details.status_code == 200:
                            job_details = details.json()
                            services = job_details.get("services", [])
                            if services:
                                svc_id = services[0].get("svc_id")
                                existing = services[0].get("service_details") or {}

                                payload = {
                                    "extra_costs": existing.get("extra_costs") or [],
                                    "extra_revenues": existing.get("extra_revenues") or []
                                }

                                # Add costs (single or multiple)
                                costs_array = state.entities.get("costs", [])
                                if not costs_array and state.entities.get("cost_unit_price"):
                                    costs_array = [state.entities]
                                for c in costs_array:
                                    qty = c.get("cost_qty", 1)
                                    unit_price = c.get("cost_unit_price", 0)
                                    payload["extra_costs"].append({
                                        "name": c.get("cost_name", "Chi phí"),
                                        "qty": qty,
                                        "unit_price": unit_price,
                                        "unit": c.get("cost_unit", "chuyến"),
                                        "amount": qty * unit_price,
                                        "vendor": c.get("vendor_name", state.entities.get("vendor_name", ""))
                                    })
                                    changes.append(f"Chi phí: {qty} × {unit_price:,.0f}")

                                # Add revenues (single or multiple)
                                revenues_array = state.entities.get("revenues", [])
                                if not revenues_array and state.entities.get("revenue_unit_price"):
                                    revenues_array = [state.entities]
                                for r in revenues_array:
                                    qty = r.get("revenue_qty", 1)
                                    unit_price = r.get("revenue_unit_price", 0)
                                    payload["extra_revenues"].append({
                                        "name": r.get("revenue_name", "Doanh thu"),
                                        "qty": qty,
                                        "unit_price": unit_price,
                                        "unit": r.get("revenue_unit", "chuyến"),
                                        "amount": qty * unit_price
                                    })
                                    changes.append(f"Doanh thu: {qty} × {unit_price:,.0f}")

                                save = await client.put(
                                    f"{API_BASE_URL}/api/jobs/services/{svc_id}/quotations",
                                    json=payload,
                                    timeout=30.0
                                )
                                if save.status_code != 200 or not save.json().get("success"):
                                    logger.warning(f"[UNIFIED] Save quotation failed: {save.text}")

                    if changes:
                        resp = f"✅ Đã cập nhật Job {job_number}:\n"
                        for ch in changes:
                            resp += f"• {ch}\n"
                        return {"success": True, "response": resp}
                    return {"success": False, "response": f"Không có thay đổi nào được thực hiện cho job {job_number}"}

                elif state.intent in ["add_cost", "add_revenue"]:
                    # Get job details first
                    job_number = state.entities.get("job_number")
                    if not job_number:
                        return {
                            "success": False,
                            "response": "Vui lòng cho biết mã job (ví dụ: TRK-0702-0001) để thêm chi phí/doanh thu."
                        }
                    if job_number:
                        lookup = await client.get(
                            f"{API_BASE_URL}/api/jobs/by-number/{job_number}",
                            timeout=10.0
                        )
                        if lookup.status_code == 200:
                            job_data = lookup.json()
                            if job_data.get("success"):
                                job_id = job_data.get("job_id")
                                # Get service details
                                details = await client.get(
                                    f"{API_BASE_URL}/api/jobs/{job_id}/details",
                                    timeout=10.0
                                )
                                if details.status_code == 200:
                                    job_details = details.json()
                                    services = job_details.get("services", [])
                                    if services:
                                        svc_id = services[0].get("svc_id")
                                        existing = services[0].get("service_details") or {}

                                        payload = {
                                            "extra_costs": existing.get("extra_costs") or [],
                                            "extra_revenues": existing.get("extra_revenues") or []
                                        }

                                        if state.intent == "add_cost":
                                            payload["extra_costs"].append({
                                                "name": state.entities.get("cost_name", "Chi phí"),
                                                "qty": state.entities.get("cost_qty", 1),
                                                "unit_price": state.entities.get("cost_unit_price", 0),
                                                "unit": state.entities.get("cost_unit", "chuyến"),
                                                "amount": state.entities.get("cost_qty", 1) * state.entities.get("cost_unit_price", 0),
                                                "vendor": state.entities.get("vendor_name", "")
                                            })
                                        else:
                                            payload["extra_revenues"].append({
                                                "name": state.entities.get("revenue_name", "Doanh thu"),
                                                "qty": state.entities.get("revenue_qty", 1),
                                                "unit_price": state.entities.get("revenue_unit_price", 0),
                                                "unit": state.entities.get("revenue_unit", "chuyến"),
                                                "amount": state.entities.get("revenue_qty", 1) * state.entities.get("revenue_unit_price", 0)
                                            })

                                        save = await client.put(
                                            f"{API_BASE_URL}/api/jobs/services/{svc_id}/quotations",
                                            json=payload,
                                            timeout=30.0
                                        )
                                        if save.status_code == 200:
                                            return {
                                                "success": True,
                                                "response": f"✅ Đã thêm {'chi phí' if state.intent == 'add_cost' else 'doanh thu'} thành công!"
                                            }
                    return {"success": False, "response": "Lỗi thêm chi phí/doanh thu"}

                elif state.intent == "create_quotation":
                    return await self._execute_create_quotation(state, client, API_BASE_URL)

                elif state.intent in ("create_customer", "create_vendor"):
                    return await self._execute_create_entity(state, client, API_BASE_URL)

        except Exception as e:
            logger.error(f"[UNIFIED] Action execution failed: {e}")
            return {"success": False, "response": f"Lỗi: {str(e)}"}

        return None

    def _build_vendor_message(self, job_no: str, data: dict, vehicle_info: dict = None) -> str:
        """Build copy-friendly vendor message for a job"""
        lines = []

        # Line 1: Job + Invoice
        inv = data.get("invoice_numbers") or ""
        lines.append(f"{job_no} | INV: {inv}")

        # Line 2: Packages + cargo + vehicle
        pkg_qty = data.get("package_quantity") or ""
        pkg_unit = data.get("package_unit") or "kiện"
        cargo = data.get("cargo_type") or ""
        vehicle = data.get("vehicle_type") or ""
        if pkg_qty:
            pkg_line = f"📦 {pkg_qty} {pkg_unit}"
            if cargo:
                pkg_line += f" ({cargo})"
            if vehicle:
                pkg_line += f" - Xe {vehicle}"
            lines.append(pkg_line)

        # Line 3: Date/Time
        booking_date = data.get("booking_date") or data.get("pickup_date") or ""
        pickup_time = data.get("pickup_time") or ""
        if booking_date or pickup_time:
            date_line = f"📅 {booking_date}"
            if pickup_time:
                date_line += f" - {pickup_time}"
            lines.append(date_line)

        # Line 4-5: Addresses
        pickup = data.get("pickup_address") or ""
        delivery = data.get("delivery_address") or ""
        if pickup:
            lines.append(f"🔵 Lấy: {pickup}")
        if delivery:
            lines.append(f"🔴 Giao: {delivery}")

        # Line 6: Notes/Receiver
        receiver = data.get("receiver_contact") or data.get("receiver_company") or ""
        notes = data.get("special_requirements") or data.get("notes") or ""
        if receiver:
            lines.append(f"📞 LH: {receiver}")
        if notes:
            lines.append(f"📝 {notes}")

        # Vehicle info at the end (for assign_vehicle)
        if vehicle_info:
            plate = vehicle_info.get("license_plate") or ""
            driver = vehicle_info.get("driver_name") or ""
            phone = vehicle_info.get("driver_phone") or ""
            cccd = vehicle_info.get("driver_cccd") or vehicle_info.get("driver_id_card") or ""
            v_type = vehicle_info.get("vehicle_type") or vehicle or ""

            lines.append(f"🚛 Xe: {plate} ({v_type})")
            if driver:
                driver_line = f"👤 Tài xế: {driver}"
                if phone:
                    driver_line += f" - {phone}"
                if cccd:
                    driver_line += f" - CCCD: {cccd}"
                lines.append(driver_line)

        return "\n".join(lines)

    async def _execute_create_quotation(self, state, client, api_base):
        """Create quotation(s) (buying or selling rate) via direct DB insert.
        Supports multiple rates when AI returns 'rates' array."""
        from datetime import date as date_type
        entities = state.entities
        quote_type = entities.get("quote_type", "buying").lower()
        db = get_supabase()

        # Lookup vendor/customer
        vendor_id = None
        customer_id = None

        if quote_type == "buying" and entities.get("vendor_name"):
            result = db.table('vendors').select('vendor_id, short_name, company_name').eq('is_active', True).execute()
            name_lower = entities["vendor_name"].lower()
            for v in result.data or []:
                if name_lower in (v.get("short_name") or "").lower() or \
                   name_lower in (v.get("company_name") or "").lower():
                    vendor_id = v.get("vendor_id")
                    break
        elif quote_type == "selling" and entities.get("customer_name"):
            result = db.table('customers').select('customer_id, short_name, company_name, customer_code').eq('is_active', True).execute()
            name_lower = entities["customer_name"].lower()
            for c in result.data or []:
                if name_lower in (c.get("short_name") or "").lower() or \
                   name_lower in (c.get("company_name") or "").lower() or \
                   name_lower in (c.get("customer_code") or "").lower():
                    customer_id = c.get("customer_id")
                    break

        # Determine table and owner
        if quote_type == "buying":
            if not vendor_id:
                return {"success": False, "response": f"Không tìm thấy NCC '{entities.get('vendor_name')}'. Vui lòng tạo NCC trước."}
            table = 'vendor_rates'
            owner_field, owner_id = 'vendor_id', vendor_id
        else:
            if not customer_id:
                return {"success": False, "response": f"Không tìm thấy KH '{entities.get('customer_name')}'. Vui lòng tạo KH trước."}
            table = 'customer_rates'
            owner_field, owner_id = 'customer_id', customer_id

        # Build rate items: support multiple rates or single rate
        rates_list = entities.get("rates", [])
        if not rates_list:
            # Single rate mode - build from flat entities
            price = entities.get("price")
            if not price:
                return {"success": False, "response": "Thiếu giá (price). Vui lòng cung cấp giá báo giá."}
            rates_list = [{"vehicle_type": entities.get("vehicle_type"), "price": price}]

        # Validate all rates have price
        for r in rates_list:
            if not r.get("price"):
                return {"success": False, "response": f"Thiếu giá cho loại xe {r.get('vehicle_type', '?')}. Vui lòng cung cấp đầy đủ giá."}
            # Parse price: handle int, float, or string like "450,000"
            try:
                p = r["price"]
                if isinstance(p, (int, float)):
                    r["price"] = float(p)
                else:
                    # String: remove comma separators, keep as number
                    r["price"] = float(str(p).replace(",", "").strip())
            except (ValueError, TypeError):
                return {"success": False, "response": f"Giá không hợp lệ: {r.get('price')}"}

        # Common fields for all rates
        base_data = {
            'currency': entities.get("currency", "VND"),
            'unit': entities.get("unit", "TRIP"),
            'origin_province': entities.get("origin_province"),
            'destination_province': entities.get("destination_province"),
            'notes': entities.get("sub_route") or entities.get("notes"),
            'rate_type': entities.get("rate_type", "STANDARD"),
            'is_active': True,
            'effective_date': date_type.today().isoformat(),
            'service_type_code': entities.get("service_type_code"),
            owner_field: owner_id,
        }
        # Remove None values from base
        base_data = {k: v for k, v in base_data.items() if v is not None}

        # Insert all rates
        created = 0
        errors = []
        for rate_item in rates_list:
            insert_data = {**base_data, 'price': rate_item["price"]}
            if rate_item.get("vehicle_type"):
                insert_data["vehicle_type"] = rate_item["vehicle_type"]
            try:
                result = db.table(table).insert(insert_data).execute()
                if result.data:
                    created += 1
            except Exception as e:
                logger.error(f"[UNIFIED] Rate insert failed: {e}")
                errors.append(f"{rate_item.get('vehicle_type', '?')}: {e}")

        if created == 0:
            return {"success": False, "response": f"Lỗi tạo báo giá: {'; '.join(errors)}"}

        label = "mua" if quote_type == "buying" else "bán"
        route = ""
        if entities.get("origin_province") and entities.get("destination_province"):
            route = f" {entities['origin_province']}→{entities['destination_province']}"

        if len(rates_list) == 1:
            p = rates_list[0]["price"]
            return {"success": True, "response": f"✅ Đã tạo báo giá {label}{route} | {p:,.0f} VND thành công!"}

        details = ", ".join(f"{r.get('vehicle_type', '?')}: {r['price']:,.0f}" for r in rates_list[:created])
        msg = f"✅ Đã tạo {created}/{len(rates_list)} báo giá {label}{route}\n{details}"
        if errors:
            msg += f"\n⚠️ Lỗi: {'; '.join(errors)}"
        return {"success": True, "response": msg}

    async def _execute_create_entity(self, state, client, api_base):
        """Create customer or vendor via admin API."""
        entities = state.entities
        if state.intent == "create_customer":
            payload = {
                "customer_code": entities.get("customer_code"),
                "company_name": entities.get("company_name"),
                "short_name": entities.get("short_name"),
                "address": entities.get("address"),
                "tax_code": entities.get("tax_code"),
                "contact_phone": entities.get("contact_phone"),
                "contact_email": entities.get("contact_email"),
                "contact_person": entities.get("contact_person"),
            }
            resp = await client.post(f"{api_base}/api/admin/customers", json=payload, timeout=30.0)
            if resp.status_code == 200 and resp.json().get("data"):
                return {"success": True, "response": f"✅ Đã tạo khách hàng {entities.get('company_name')} thành công!"}
            return {"success": False, "response": f"Lỗi tạo KH: {resp.text[:200]}"}
        else:
            payload = {
                "vendor_code": entities.get("vendor_code"),
                "vendor_name": entities.get("vendor_name"),
                "short_name": entities.get("short_name"),
                "phone": entities.get("phone"),
                "email": entities.get("email"),
                "address": entities.get("address"),
                "tax_code": entities.get("tax_code"),
            }
            resp = await client.post(f"{api_base}/api/admin/vendors", json=payload, timeout=30.0)
            if resp.status_code == 200 and resp.json().get("data"):
                return {"success": True, "response": f"✅ Đã tạo NCC {entities.get('vendor_name')} thành công!"}
            return {"success": False, "response": f"Lỗi tạo NCC: {resp.text[:200]}"}

    def _reset_state(self, state: UnifiedState):
        """Reset state after successful execution"""
        state.intent = None
        state.entities = {}
        state.ready_to_execute = False
        state.needs_confirmation = False
        # Keep history for context
