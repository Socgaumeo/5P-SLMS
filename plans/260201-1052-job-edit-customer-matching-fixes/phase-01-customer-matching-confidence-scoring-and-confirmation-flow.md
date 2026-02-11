# Phase 1: Customer Matching Confidence Scoring and Confirmation Flow

## Context Links

- [Entity Extractor](/Users/bear1108/Documents/GitHub/5P-SLMS/backend/app/ai/entity_extractor.py) - `_match_customer` method at line 886-913
- [Data Service](/Users/bear1108/Documents/GitHub/5P-SLMS/backend/app/services/data_service.py) - `_enrich_create_job` method
- [Conversation Manager](/Users/bear1108/Documents/GitHub/5P-SLMS/backend/app/ai/memory/conversation_manager.py)

## Overview

**Priority:** P1 - Critical Bug Fix
**Status:** pending
**Effort:** 3h

**Problem:** User sent "LKV Mien Bac" but bot matched to "LKVMN" (Loc khi viet Mien Nam) - completely wrong customer. Current matching uses simple substring matching without confidence scoring.

## Key Insights

- Current `_match_customer` method (lines 886-913) uses basic substring matching
- No confidence score returned - always assumes correct match
- No confirmation flow when match is uncertain
- Data enrichment in `data_service.py` has similar fuzzy matching issue

## Requirements

### Functional
1. Calculate match confidence score (0.0-1.0) for customer matching
2. When confidence <0.85, ask user to confirm/select correct customer
3. Support multiple match candidates with scores
4. Handle "Mien Bac" vs "Mien Nam" disambiguation

### Non-Functional
1. Maintain backward compatibility - high confidence matches work as before
2. Keep response time under 500ms
3. Support Vietnamese accent-insensitive matching

## Architecture

```
User Input: "LKV Mien Bac"
       │
       ▼
┌─────────────────────────┐
│  _match_customer_v2()   │
│  - Exact match: 1.0     │
│  - Prefix match: 0.9    │
│  - Contains: 0.7        │
│  - Fuzzy: 0.3-0.6       │
└─────────────────────────┘
       │
       ▼
┌─────────────────────────┐
│ confidence >= 0.85?     │
│  YES → Use match        │
│  NO  → Return candidates│
└─────────────────────────┘
       │ (low confidence)
       ▼
┌─────────────────────────┐
│ Conversation Manager    │
│ - Set needs_confirmation│
│ - Ask user to select    │
└─────────────────────────┘
```

## Related Code Files

### Files to Modify
- `backend/app/ai/entity_extractor.py`
  - Refactor `_match_customer` to `_match_customer_with_confidence`
  - Return dict with `code`, `confidence`, `candidates`
- `backend/app/ai/memory/conversation_manager.py`
  - Handle low-confidence customer match in `_handle_new_task`
  - Add confirmation state for customer selection
- `backend/app/ai/memory/entity_accumulator.py`
  - Add customer_confirmed field tracking

### Files to Create
- None (modifying existing files)

## Implementation Steps

### Step 1: Enhance Customer Matching in EntityExtractor

```python
# In entity_extractor.py, replace _match_customer with:

def _match_customer_with_confidence(
    self,
    input_customer: str,
    customers: List[Dict]
) -> Dict[str, Any]:
    """
    Match input customer to customer list with confidence scoring

    Returns:
        Dict with:
        - code: matched customer_code or None
        - confidence: 0.0-1.0
        - candidates: list of top 3 matches with scores
        - needs_confirmation: bool
    """
    if not input_customer:
        return {"code": None, "confidence": 0.0, "candidates": [], "needs_confirmation": False}

    input_lower = self._normalize_vietnamese(str(input_customer).lower().strip())
    candidates = []

    for c in customers:
        code = (c.get("customer_code") or "").lower()
        short_name = (c.get("short_name") or "").lower()
        company_name = (c.get("company_name") or "").lower()

        # Normalize Vietnamese
        code_norm = self._normalize_vietnamese(code)
        short_norm = self._normalize_vietnamese(short_name)
        company_norm = self._normalize_vietnamese(company_name)

        # Calculate scores for different match types
        score = 0.0
        match_type = "none"

        # Exact match - highest confidence
        if input_lower == code_norm or input_lower == short_norm:
            score = 1.0
            match_type = "exact"
        # Prefix match - high confidence
        elif code_norm.startswith(input_lower) or short_norm.startswith(input_lower):
            score = 0.9
            match_type = "prefix"
        # Reverse prefix (input starts with customer code)
        elif input_lower.startswith(code_norm) or input_lower.startswith(short_norm):
            score = 0.85
            match_type = "reverse_prefix"
        # Contains match - medium confidence
        elif input_lower in short_norm or input_lower in company_norm:
            score = 0.7
            match_type = "contains"
        elif short_norm in input_lower or code_norm in input_lower:
            score = 0.65
            match_type = "reverse_contains"
        # Fuzzy match - low confidence (Levenshtein-like)
        else:
            score = self._fuzzy_score(input_lower, short_norm)
            if score > 0.3:
                match_type = "fuzzy"

        if score > 0.3:
            candidates.append({
                "code": c.get("customer_code"),
                "name": c.get("short_name") or c.get("company_name"),
                "score": score,
                "match_type": match_type
            })

    # Sort by score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)
    top_candidates = candidates[:3]

    if not candidates:
        return {
            "code": input_customer.upper(),
            "confidence": 0.0,
            "candidates": [],
            "needs_confirmation": True
        }

    best = candidates[0]

    # High confidence threshold
    HIGH_CONFIDENCE = 0.85

    # Check for ambiguity - if top 2 are too close
    is_ambiguous = (
        len(candidates) >= 2 and
        candidates[0]["score"] - candidates[1]["score"] < 0.1
    )

    return {
        "code": best["code"],
        "confidence": best["score"],
        "candidates": top_candidates,
        "needs_confirmation": best["score"] < HIGH_CONFIDENCE or is_ambiguous
    }

def _normalize_vietnamese(self, text: str) -> str:
    """Remove Vietnamese accents for matching"""
    import unicodedata
    # NFD normalization separates base chars from accents
    text = unicodedata.normalize('NFD', text)
    # Remove combining diacritical marks
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower().strip()

def _fuzzy_score(self, input_str: str, target: str) -> float:
    """Simple fuzzy matching score"""
    if not input_str or not target:
        return 0.0

    # Count matching characters in order
    matches = 0
    target_idx = 0
    for char in input_str:
        while target_idx < len(target):
            if target[target_idx] == char:
                matches += 1
                target_idx += 1
                break
            target_idx += 1

    return matches / max(len(input_str), len(target))
```

### Step 2: Update _parse_booking_response

```python
# In entity_extractor.py, update customer extraction:

# Replace line 705:
# entities["customer_code"] = self._match_customer(str(customer), context.get("customers", []))

# With:
customer_match = self._match_customer_with_confidence(
    str(customer),
    context.get("customers", [])
)
entities["customer_code"] = customer_match["code"]
entities["customer_confidence"] = customer_match["confidence"]
entities["customer_candidates"] = customer_match["candidates"]
entities["customer_needs_confirmation"] = customer_match["needs_confirmation"]
```

### Step 3: Handle Low Confidence in ConversationManager

```python
# In conversation_manager.py, update _handle_new_task:

async def _handle_new_task(self, ...):
    # ... existing code ...

    # After entity extraction, check for customer confirmation
    entities = extracted.get("entities", {})

    if entities.get("customer_needs_confirmation"):
        candidates = entities.get("customer_candidates", [])
        confidence = entities.get("customer_confidence", 0)

        # Build confirmation message
        if candidates:
            response = f"⚠️ Tìm thấy nhiều khách hàng phù hợp với '{customer}':\n\n"
            for i, c in enumerate(candidates, 1):
                response += f"{i}. {c['code']} - {c['name']} (độ khớp: {c['score']*100:.0f}%)\n"
            response += "\nVui lòng chọn số (1-3) hoặc nhập lại mã khách hàng chính xác."
        else:
            response = f"⚠️ Không tìm thấy khách hàng '{customer}'. Vui lòng nhập mã KH chính xác."

        # Set task state to awaiting customer confirmation
        state.task.state = TaskState.AWAITING_INPUT
        state.task.awaiting_field = "customer_code"
        state.task.confirmation_data = {"candidates": candidates}

        return ProcessResult(
            response=response,
            state=state,
            needs_confirmation=False
        )

    # ... rest of existing code ...
```

### Step 4: Handle Customer Selection Response

```python
# In conversation_manager.py, add handler for customer selection:

async def _handle_continuation(self, state, message, context):
    # Check if awaiting customer selection
    if state.task.awaiting_field == "customer_code":
        candidates = state.task.confirmation_data.get("candidates", [])

        # Check if user entered a number
        if message.strip().isdigit():
            idx = int(message.strip()) - 1
            if 0 <= idx < len(candidates):
                selected = candidates[idx]
                state.task.entities["customer_code"] = selected["code"]
                state.task.entities["customer_confidence"] = 1.0  # User confirmed
                state.task.entities["customer_needs_confirmation"] = False
                state.task.awaiting_field = None

                # Continue with normal flow
                result = self.accumulator.accumulate(state.task, {})
                # ... generate response ...

        # Otherwise treat as new customer code input
        # Re-extract with new input
```

## Todo List

- [ ] Implement `_match_customer_with_confidence` in entity_extractor.py
- [ ] Add `_normalize_vietnamese` and `_fuzzy_score` helper methods
- [ ] Update `_parse_booking_response` to use new matching
- [ ] Add `awaiting_field` to TaskState in conversation_state.py
- [ ] Update `_handle_new_task` for low-confidence handling
- [ ] Update `_handle_continuation` for customer selection
- [ ] Add unit tests for customer matching with edge cases
- [ ] Test "LKV Mien Bac" vs "LKVMN" disambiguation

## Success Criteria

- [ ] "LKV Mien Bac" correctly prompts for confirmation with LKVMB and LKVMN as candidates
- [ ] Exact matches (e.g., "LKVMB") work instantly without confirmation
- [ ] User can select by number from candidate list
- [ ] Confidence scores are logged for debugging
- [ ] No regression in high-confidence customer matching

## Security Considerations

- Customer data exposure: Only show customer codes and short names in confirmation
- No PII (phone, email, tax code) exposed during matching
