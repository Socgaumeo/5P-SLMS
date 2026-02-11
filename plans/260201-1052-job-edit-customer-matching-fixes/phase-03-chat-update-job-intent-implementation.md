# Phase 3: Chat Update Job Intent Implementation

## Context Links

- [Intent Classifier](/Users/bear1108/Documents/GitHub/5P-SLMS/backend/app/ai/intent_classifier.py)
- [Conversation Manager](/Users/bear1108/Documents/GitHub/5P-SLMS/backend/app/ai/memory/conversation_manager.py)
- [Entity Accumulator](/Users/bear1108/Documents/GitHub/5P-SLMS/backend/app/ai/memory/entity_accumulator.py)
- [Jobs API - /update endpoint](/Users/bear1108/Documents/GitHub/5P-SLMS/backend/app/api/jobs.py) - Line 708-827

## Overview

**Priority:** P1
**Status:** pending
**Effort:** 3h

**Problem:** When user requests job edit via chat (e.g., "sua thong tin khach hang cua Job TRK-0102-0004"), system should:
1. Recognize `update_job` intent
2. Extract job number and what to update
3. Perform the update via API
4. Confirm success to user

Currently `update_job` is not in VALID_INTENTS list and has no handler.

## Key Insights

- IntentClassifier has `update_status` but not `update_job`
- EntityAccumulator has `update_job` in REQUIRED_FIELDS (line 28)
- ConversationManager handles `update_status` but not `update_job`
- Jobs API has `/update` endpoint but only handles status, pickup_time, delivery_address, notes
- Need to differentiate: update_status (change job status) vs update_job (change job info)

## Requirements

### Functional
1. Add `update_job` to valid intents
2. Extract: job_number, update_field (customer, address, time, notes), new_value
3. Support commands like:
   - "sua thong tin khach hang cua Job TRK-0102-0004 thanh LKVMB"
   - "doi dia chi giao cua job 0004 thanh KCN Quang Minh"
   - "them ghi chu cho job TRK-0102-0004: can co nguoi boc xep"
   - "them dich vu dong goi cho job 0004"

### Non-Functional
1. Clear disambiguation between update_status and update_job
2. Confirmation before destructive updates
3. Support partial job numbers (e.g., "0004")

## Architecture

```
User: "sua khach hang cua job 0004 thanh LKVMN"
                │
                ▼
┌─────────────────────────┐
│   IntentClassifier      │
│   → update_job          │
└─────────────────────────┘
                │
                ▼
┌─────────────────────────┐
│   EntityExtractor       │
│   - job_number: 0004    │
│   - update_field: customer │
│   - new_value: LKVMN    │
└─────────────────────────┘
                │
                ▼
┌─────────────────────────┐
│  ConversationManager    │
│  - Lookup job           │
│  - Confirm change       │
│  - Execute update       │
└─────────────────────────┘
```

## Related Code Files

### Files to Modify
- `backend/app/ai/intent_classifier.py`
  - Add `update_job` to VALID_INTENTS
  - Add mapping for update_job keywords
  - Add QuickClassifier keywords

- `backend/app/ai/prompts/intent_prompts.py`
  - Add update_job examples to prompt

- `backend/app/ai/entity_extractor.py`
  - Add `_extract_update_job` method

- `backend/app/ai/memory/conversation_manager.py`
  - Add `_execute_update_job` method
  - Handle update_job in confirmation flow

- `backend/app/api/jobs.py`
  - Extend `/update` endpoint for customer/service changes

### Files to Create
- `backend/app/ai/prompts/update-job-extraction-prompts.py`

## Implementation Steps

### Step 1: Add update_job to Intent Classifier

```python
# In intent_classifier.py, update VALID_INTENTS (line 30):

VALID_INTENTS = [
    "create_booking",
    "assign_vehicle",
    "update_status",
    "update_job",      # NEW: Edit job info (customer, address, etc.)
    "query_info",
    "create_customer",
    "create_vendor",
    "create_quotation",
    "general_chat",
    "unknown"
]

# In _map_intent method (around line 158), add mappings:
"update_job": "update_job",
"edit_job": "update_job",
"sua_job": "update_job",
"chinh_sua": "update_job",
"thay_doi": "update_job",
"doi_khach_hang": "update_job",
"doi_dia_chi": "update_job",
"them_dich_vu": "update_job",
```

### Step 2: Add QuickClassifier Keywords

```python
# In intent_classifier.py, QuickClassifier class:

UPDATE_JOB_KEYWORDS = [
    "sua", "chinh sua", "thay doi", "doi",
    "cap nhat thong tin", "sua thong tin",
    "doi khach hang", "doi kh", "sua kh",
    "doi dia chi", "sua dia chi",
    "them dich vu", "them service",
    "them ghi chu", "sua ghi chu",
]

# In classify method, add:
update_job_score = sum(1 for k in cls.UPDATE_JOB_KEYWORDS if k in text_lower)
scores["update_job"] = update_job_score
```

### Step 3: Create Update Job Extraction Prompt

```python
# Create new file: backend/app/ai/prompts/update_job_prompts.py

UPDATE_JOB_EXTRACTION_PROMPT = """
Ban la tro ly logistics. Phan tich yeu cau cap nhat job va trich xuat:

1. job_number: Ma job can cap nhat (VD: TRK-0102-0004, hoac so ngan 0004)
2. update_type: Loai cap nhat
   - "customer": Doi khach hang
   - "origin_address": Doi dia chi lay hang
   - "dest_address": Doi dia chi giao
   - "pickup_time": Doi gio lay hang
   - "notes": Them/sua ghi chu
   - "add_service": Them dich vu moi
3. new_value: Gia tri moi
4. new_customer_code: Ma KH moi (neu update_type = customer)
5. new_service_type: Loai dich vu them (neu update_type = add_service)

Vi du:
- "sua khach hang cua job 0004 thanh LKVMN"
  -> job_number: "0004", update_type: "customer", new_customer_code: "LKVMN"

- "doi dia chi giao cua TRK-0102-0004 thanh KCN Quang Minh"
  -> job_number: "TRK-0102-0004", update_type: "dest_address", new_value: "KCN Quang Minh"

- "them dich vu dong goi cho job 0004"
  -> job_number: "0004", update_type: "add_service", new_service_type: "SVC_PACK"

INPUT: {input}

Tra ve JSON:
{{
  "job_number": "...",
  "update_type": "customer|origin_address|dest_address|pickup_time|notes|add_service",
  "new_value": "...",
  "new_customer_code": "...",
  "new_service_type": "...",
  "confidence": 0.0-1.0
}}
"""
```

### Step 4: Add Entity Extraction for update_job

```python
# In entity_extractor.py, add method:

async def _extract_update_job(self, text: str, context: Dict) -> Dict[str, Any]:
    """Extract update job entities"""
    from .prompts.update_job_prompts import UPDATE_JOB_EXTRACTION_PROMPT

    prompt = UPDATE_JOB_EXTRACTION_PROMPT.format(input=text)

    logger.info("[EntityExtractor] Calling AI for update_job extraction...")
    response = await self.ai.generate(
        prompt=prompt,
        response_format="json",
        temperature=0.2
    )

    parsed_response = self._ensure_dict(response)
    if not parsed_response:
        return {"entities": {}, "confidence": 0.3}

    entities = {}

    # Job number - normalize
    job_num = parsed_response.get("job_number")
    if job_num:
        entities["job_number"] = self._normalize_job_number(
            str(job_num),
            context.get("active_jobs", [])
        )

    # Update type
    update_type = parsed_response.get("update_type")
    if update_type:
        entities["update_type"] = update_type

    # New value
    new_value = parsed_response.get("new_value")
    if new_value:
        entities["new_value"] = str(new_value)

    # Customer code (if changing customer)
    if update_type == "customer":
        new_customer = parsed_response.get("new_customer_code")
        if new_customer:
            # Use confidence-based matching
            match = self._match_customer_with_confidence(
                str(new_customer),
                context.get("customers", [])
            )
            entities["new_customer_code"] = match["code"]
            entities["customer_confidence"] = match["confidence"]
            entities["customer_candidates"] = match["candidates"]
            entities["customer_needs_confirmation"] = match["needs_confirmation"]

    # Service type (if adding service)
    if update_type == "add_service":
        new_svc = parsed_response.get("new_service_type")
        if new_svc:
            entities["new_service_type"] = normalize_service_code(new_svc)

    confidence = self._extract_confidence(parsed_response)

    logger.info(f"[EntityExtractor] Update job extracted: {list(entities.keys())}")
    return {"entities": entities, "confidence": confidence}


# Update extract() method to handle update_job:
elif intent == "update_job":
    return await self._extract_update_job(text, context)
```

### Step 5: Add Execution Handler in ConversationManager

```python
# In conversation_manager.py, add to _handle_confirmation:

elif state.task.intent == "update_job":
    execution_result = await self._execute_update_job(state.task.entities)
    if execution_result.get("success"):
        entities = state.task.entities
        job_number = execution_result.get("job_number") or entities.get("job_number")
        update_type = entities.get("update_type", "")

        update_labels = {
            "customer": "khach hang",
            "origin_address": "dia chi lay hang",
            "dest_address": "dia chi giao",
            "pickup_time": "gio lay hang",
            "notes": "ghi chu",
            "add_service": "dich vu"
        }
        label = update_labels.get(update_type, update_type)

        response = f"Da cap nhat {label} cho Job {job_number} thanh cong!"

        if update_type == "customer":
            response += f"\n• Khach hang moi: {entities.get('new_customer_code')}"
        elif update_type == "add_service":
            response += f"\n• Dich vu moi: {entities.get('new_service_type')}"
        elif entities.get("new_value"):
            response += f"\n• Gia tri moi: {entities['new_value']}"
    else:
        response = f"Loi cap nhat job: {execution_result.get('message', 'Unknown error')}"
```

### Step 6: Implement _execute_update_job

```python
# In conversation_manager.py, add method:

async def _execute_update_job(self, entities: Dict) -> Dict:
    """Execute job update via API"""
    import httpx

    try:
        job_number = entities.get("job_number")
        update_type = entities.get("update_type")

        if not job_number:
            return {"success": False, "message": "Thieu ma job"}

        async with httpx.AsyncClient() as client:
            # First, lookup job_id from job_number
            lookup_resp = await client.get(
                f"{API_BASE_URL}/api/jobs/by-number/{job_number}",
                timeout=10.0
            )
            if lookup_resp.status_code != 200:
                return {"success": False, "message": f"Khong tim thay job {job_number}"}

            job_data = lookup_resp.json()
            job_id = job_data.get("job_id")

            # Handle different update types
            if update_type == "customer":
                # Change customer
                new_customer = entities.get("new_customer_code")
                # Lookup customer_id
                cust_resp = await client.get(
                    f"{API_BASE_URL}/api/customers",
                    timeout=10.0
                )
                customers = cust_resp.json().get("customers", [])
                cust_id = None
                for c in customers:
                    if c.get("customer_code") == new_customer:
                        cust_id = c.get("customer_id")
                        break

                if not cust_id:
                    return {"success": False, "message": f"Khong tim thay KH {new_customer}"}

                resp = await client.put(
                    f"{API_BASE_URL}/api/jobs/{job_id}/customer",
                    json={"customer_id": cust_id, "customer_code": new_customer},
                    timeout=30.0
                )

            elif update_type == "add_service":
                # Add service
                svc_type = entities.get("new_service_type", "TRUCKING_SHORT")
                resp = await client.post(
                    f"{API_BASE_URL}/api/jobs/{job_id}/services",
                    json={"service_type_code": svc_type},
                    timeout=30.0
                )

            else:
                # Other updates (address, time, notes)
                update_payload = {"entities": {
                    "job_number": job_number
                }}

                if update_type == "dest_address":
                    update_payload["entities"]["update_delivery_address"] = entities.get("new_value")
                elif update_type == "origin_address":
                    update_payload["entities"]["update_pickup_address"] = entities.get("new_value")
                elif update_type == "pickup_time":
                    update_payload["entities"]["update_pickup_time"] = entities.get("new_value")
                elif update_type == "notes":
                    update_payload["entities"]["update_notes"] = entities.get("new_value")

                resp = await client.post(
                    f"{API_BASE_URL}/api/jobs/update",
                    json=update_payload,
                    timeout=30.0
                )

            if resp.status_code == 200:
                result = resp.json()
                result["job_number"] = job_number
                return result
            else:
                return {"success": False, "message": f"API error: {resp.status_code}"}

    except Exception as e:
        logger.error(f"Update job error: {e}")
        return {"success": False, "message": str(e)}
```

### Step 7: Update Intent Prompts

```python
# In intent_prompts.py, add examples for update_job:

# Add to few-shot examples:
"""
Input: "sua thong tin khach hang cua job TRK-0102-0004 thanh LKVMB"
Output: {"intent": "update_job", "confidence": 0.95, "key_signals": ["sua", "khach hang", "job"], "reasoning": "User wants to change customer for existing job"}

Input: "them dich vu dong goi cho job 0004"
Output: {"intent": "update_job", "confidence": 0.92, "key_signals": ["them dich vu", "job"], "reasoning": "User wants to add service to existing job"}

Input: "doi dia chi giao cua job TRK-0102-0004"
Output: {"intent": "update_job", "confidence": 0.90, "key_signals": ["doi", "dia chi", "job"], "reasoning": "User wants to change delivery address"}
"""
```

## Todo List

- [ ] Add `update_job` to VALID_INTENTS in intent_classifier.py
- [ ] Add intent mappings for update_job
- [ ] Add UPDATE_JOB_KEYWORDS to QuickClassifier
- [ ] Create update_job_prompts.py
- [ ] Add `_extract_update_job` method in entity_extractor.py
- [ ] Update extract() to handle update_job intent
- [ ] Add update_job to EntityAccumulator required fields
- [ ] Add `_execute_update_job` in conversation_manager.py
- [ ] Handle update_job in _handle_confirmation
- [ ] Update intent_prompts.py with examples
- [ ] Test "sua khach hang cua job 0004 thanh LKVMN"
- [ ] Test "them dich vu dong goi cho job 0004"
- [ ] Test "doi dia chi giao cua job TRK-0102-0004"

## Success Criteria

- [ ] "sua khach hang cua job 0004 thanh LKVMN" changes customer
- [ ] "them dich vu dong goi cho job 0004" adds packing service
- [ ] "doi dia chi giao" updates delivery address
- [ ] Confirmation required before changes
- [ ] Partial job numbers (0004) resolved to full number
- [ ] Low-confidence customer matches trigger selection

## Security Considerations

- Validate job ownership before update
- Log all changes with user ID
- Prevent updates to completed/cancelled jobs
