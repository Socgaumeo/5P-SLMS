# Service Type Determination System - Backend Exploration Report

**Date:** 2026-01-25  
**Scope:** How service types (trucking, trucking_short, packing, warehouse) are determined across the backend codebase

---

## 1. SERVICE TYPE OVERVIEW

The system recognizes 4 main service type categories with specific codes:

### Service Type Categories
- **Trucking**: `TRUCKING_SHORT`, `TRUCKING_LONG`
- **Warehouse**: `WHS_STORAGE`, `WHS_HANDLE`
- **Customs**: (Custom codes)
- **Packing**: `PACKING` (default for quotation files)

**Default Service Type:** `TRUCKING_SHORT` (set in job creation)  
**Default for Quotation Files:** `PACKING`

---

## 2. SERVICE TYPE DETERMINATION FLOW

### 2.1 File Upload Flow (chat.py)

**Location:** `/backend/app/api/chat.py:405-419`

When a user uploads an Excel file, the system:

1. **Detects file type using detection functions:**
   - `is_quotation_file()` → Uses QuotationParser (sets service_type = 'PACKING')
   - `is_booking_form()` → Uses BookingFormParser (trucking related)
   - Fallback → Tries BookingFormParser

2. **Detection Logic:**
   ```
   if is_quotation_file(tmp_path):
       parser = QuotationParser(tmp_path)
       result['service_type'] = 'PACKING'
   elif is_booking_form(tmp_path):
       parser = BookingFormParser(tmp_path)
       # Service type determined later during job creation
   ```

### 2.2 Quotation File Detection

**Location:** `/backend/app/ai/excel/quotation_parser.py:362-385`

```python
def is_quotation_file(file_path: str) -> bool:
    # Filename check - keywords: 'quotation', 'debit', 'estimate', 'packing'
    if any(kw in filename for kw in ['quotation', 'debit', 'estimate', 'packing']):
        return True
    
    # Sheet name check - looks for 'debit' or 'estimate' sheets
    if 'debit' in sheet_names or 'estimate' in sheet_names:
        return True
```

**Service Type Set:** Line 50 - `'service_type': 'PACKING'` (hardcoded default)

### 2.3 Booking Form Detection

**Location:** `/backend/app/ai/excel/booking_form_parser.py:492-518`

```python
def is_booking_form(file_path: str) -> bool:
    # Filename patterns checked:
    # - 'book xe', 'booking', 'phiếu book', 'phieu book'
    
    # Cell indicators (needs 2+ matches):
    # - A6 contains 'BOOKING'
    # - A7 contains 'book xe'
    # - B13 contains 'ngày'
```

**No service_type set here** - Determined during job creation.

---

## 3. JOB CREATION AND SERVICE TYPE ASSIGNMENT

**Location:** `/backend/app/api/jobs.py:156-158`

### Priority Order (Fallback Chain):
```python
'service_type_code': (
    entities.get('services') or [None]
)[0] or 
entities.get('service_type') or 
enriched.get('service_type') or 
'TRUCKING_SHORT'  # DEFAULT
```

**Priority Chain:**
1. **AI-extracted services array** (first element) - from entity_extractor.py
2. **service_type field** - from entity extraction
3. **enriched data service_type** - from data enrichment
4. **Default: 'TRUCKING_SHORT'** - Applied if nothing above found

### Where Service Type Comes From:

#### Source 1: QuotationParser (File Type Detection)
- **File:** `/backend/app/ai/excel/quotation_parser.py:50`
- Sets: `'service_type': 'PACKING'` when quotation file detected
- Passed through: `_format_quotation_result()` → Chat message → Entity extraction

#### Source 2: BookingFormParser (File Type Detection)
- **File:** `/backend/app/ai/excel/booking_form_parser.py`
- Does NOT set service_type
- Passed through: `_format_booking_result()` → Chat message → Job creation
- Falls back to `TRUCKING_SHORT` by default

#### Source 3: Intent Classifier
- **File:** `/backend/app/ai/intent_classifier.py`
- Classifies intent (create_booking, assign_vehicle, etc.)
- Does NOT extract service_type directly

#### Source 4: Entity Extractor (AI-based)
- **File:** `/backend/app/ai/entity_extractor.py`
- Extracts entities based on intent
- Could return 'service_type' or 'services' array
- Booking extraction prompt does NOT explicitly ask for service_type

---

## 4. BOOKING EXTRACTION PROMPT ANALYSIS

**Location:** `/backend/app/ai/prompts/booking_prompts.py`

The booking extraction prompt includes example fields but does NOT mention service_type:
- customer_code
- date, time
- vehicle_type
- cargo
- quantity, unit
- weight_kg
- invoices
- origin, destination
- urgent
- notes
- confidence

**No service_type field** in the prompt template.

---

## 5. DATA ENRICHMENT SERVICE

**Location:** `/backend/app/services/data_service.py:53-100`

The `_enrich_create_job()` method:
- Looks up customer matching
- Enriches customer_id, customer_code
- Does NOT determine service_type

**No service_type enrichment** happening at database lookup stage.

---

## 6. INTENT CLASSIFICATION (Does Not Determine Service Type)

**Location:** `/backend/app/ai/intent_classifier.py:24-37`

Valid intents:
- create_booking
- assign_vehicle
- update_status
- query_info
- general_chat
- unknown

**Note:** Intent and service type are independent concepts. Intent is WHAT the user wants to do (book, update, query). Service type is WHICH logistics service (trucking, warehouse, packing).

---

## 7. CONVERSATION MANAGER FLOW

**Location:** `/backend/app/ai/memory/conversation_manager.py`

The conversation manager:
1. Detects continuation type (NEW_TASK, CONTINUATION, CORRECTION, etc.)
2. Classifies intent using IntentClassifier
3. Extracts entities using EntityExtractor
4. Accumulates entities across messages
5. Passes to job creation (which applies service_type fallback)

**Service type NOT tracked** in ConversationState or TaskState.

---

## 8. SERVICE TYPE MAPPING IN ENDPOINTS

**Location:** `/backend/app/api/jobs.py:889-915`

Service type codes are mapped for querying:
```python
service_type_codes = {
    "trucking": ['TRUCKING_SHORT', 'TRUCKING_LONG'],
    "warehouse": ['WHS_STORAGE', 'WHS_HANDLE'],
    "customs": ['CUSTOMS_...'],
    "packing": ['PACKING']
}
```

Used in `get_service_data()` and export endpoints to filter jobs by service type.

---

## 9. DEFAULT SERVICE TYPE FALLBACK LOCATIONS

### Primary Fallback: Job Creation
- **File:** `/backend/app/api/jobs.py:158`
- **Default:** `'TRUCKING_SHORT'`
- **When Applied:** When entities/enriched data have no service_type

### Secondary Fallback: Quotation Parser
- **File:** `/backend/app/ai/excel/quotation_parser.py:50`
- **Default:** `'PACKING'`
- **When Applied:** When quotation file detected

### Data Service Fallback
- **File:** `/backend/app/services/data_service.py:317`
- **Default:** `'TRUCKING_SHORT'`
- **When Applied:** When creating job from data service

---

## 10. HOW SERVICE TYPES FLOW THROUGH THE SYSTEM

### Scenario 1: User Uploads Quotation File
```
1. File uploaded (Excel with "quotation" in filename or "debit" sheet)
2. is_quotation_file() returns True
3. QuotationParser used → sets service_type = 'PACKING'
4. _format_quotation_result() includes in message
5. Entity extraction (no explicit service_type field in prompt)
6. Job creation receives service_type from... (unclear - may lose it)
7. Fallback to TRUCKING_SHORT if not preserved
```

**ISSUE:** Service type set by parser may not propagate through entity extraction.

### Scenario 2: User Uploads Booking Form
```
1. File uploaded (Excel with "book xe" in filename)
2. is_booking_form() returns True
3. BookingFormParser used → NO service_type set
4. _format_booking_result() formats as "Phiếu book xe"
5. Entity extraction runs (no service_type in prompt)
6. Job creation applies default: TRUCKING_SHORT
7. Service type = TRUCKING_SHORT (correct by accident)
```

**CORRECT RESULT:** But only because TRUCKING_SHORT is default.

### Scenario 3: User Types Text Message
```
1. Message processed through conversation manager
2. Intent classified (e.g., create_booking)
3. Entity extraction runs (no service_type field)
4. Job created with default: TRUCKING_SHORT
5. Service type = TRUCKING_SHORT (assumed correct)
```

**PROBLEM:** No way to specify service type in text message.

---

## 11. KEY FINDINGS & ISSUES

### Current State
✓ Service type defaults are applied (TRUCKING_SHORT for jobs, PACKING for quotations)  
✓ File detection correctly identifies quotation vs booking forms  
✓ Database schema supports service type codes  

### Problems/Gaps
✗ **No explicit service_type extraction in entity extraction prompt**
  - Booking prompt doesn't ask for service_type
  - Extracted service_type from quotation file may be lost
  
✗ **No service type field in conversation state**
  - Can't track service type across multi-turn conversation
  - Can't accumulate service type like other entities
  
✗ **Parser service_type not propagated to job creation**
  - QuotationParser sets service_type = 'PACKING'
  - But no guarantee it reaches job creation
  - May be overridden by default TRUCKING_SHORT
  
✗ **No way to specify service type in text messages**
  - User can't say "I need packing service"
  - System would create TRUCKING_SHORT by default

---

## 12. FILE LOCATIONS SUMMARY

### Core Files
- `/backend/app/api/chat.py:405-419` - File type detection & parser selection
- `/backend/app/api/jobs.py:156-158` - Service type fallback chain in job creation
- `/backend/app/ai/excel/quotation_parser.py:50, 362-385` - Quotation detection & PACKING default
- `/backend/app/ai/excel/booking_form_parser.py:492-518` - Booking form detection
- `/backend/app/ai/prompts/booking_prompts.py` - Entity extraction prompt (missing service_type)
- `/backend/app/ai/entity_extractor.py:96-150` - Entity extraction logic
- `/backend/app/services/data_service.py:53-100` - Data enrichment (no service_type)
- `/backend/app/ai/memory/conversation_manager.py` - Conversation handling (no service_type tracking)
- `/backend/app/api/jobs.py:889-915` - Service type mapping for querying

---

## 13. SERVICE TYPE DETERMINATION SUMMARY TABLE

| Source | File | Field | Value |
|--------|------|-------|-------|
| Quotation Parser | quotation_parser.py:50 | service_type | PACKING |
| Job Creation Default | jobs.py:158 | service_type_code | TRUCKING_SHORT |
| Data Service Default | data_service.py:317 | service_type | TRUCKING_SHORT |
| Booking Form | booking_form_parser.py | (none) | (not set) |
| Entity Extraction | entity_extractor.py | (none) | (not in prompt) |
| Conversation Manager | conversation_manager.py | (none) | (not tracked) |

---

## 14. RECOMMENDATIONS FOR IMPROVEMENT

1. **Add service_type field to entity extraction prompts**
   - Include in booking_prompts.py with examples
   - Include in other extraction prompts

2. **Track service_type in conversation state**
   - Add to TaskState or entities accumulation
   - Allow multi-turn service type refinement

3. **Propagate parser service_type to entity extraction**
   - Ensure quotation file's PACKING service_type reaches job creation
   - Pass file type info through the pipeline

4. **Create service type detection in intent/context**
   - Add keywords mapping for service types in continuation_detector.py
   - Load service type context in context_loader.py

5. **Add fallback mechanism to preserve parser service_type**
   - Don't override parser's PACKING with default TRUCKING_SHORT
   - Check entities['service_type'] before applying default
