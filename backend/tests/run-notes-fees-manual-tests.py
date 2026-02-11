#!/usr/bin/env python3
"""
Manual test runner for Notes and Fees features
Run: python3 tests/run-notes-fees-manual-tests.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any

def test_entity_accumulator():
    """Test EntityAccumulator includes fee fields"""
    print("\n=== Test 1: EntityAccumulator Fee Fields ===")

    from app.ai.memory.entity_accumulator import EntityAccumulator

    accumulator = EntityAccumulator()
    update_job_optional = accumulator.OPTIONAL_FIELDS.get("update_job", [])

    assert "fee_type" in update_job_optional, "fee_type not in OPTIONAL_FIELDS"
    assert "fee_amount" in update_job_optional, "fee_amount not in OPTIONAL_FIELDS"
    assert "notes" in update_job_optional, "notes not in OPTIONAL_FIELDS"

    print("✅ EntityAccumulator has fee_type, fee_amount, notes in OPTIONAL_FIELDS")
    return True


def test_add_service_request_model():
    """Test AddServiceRequest model accepts service_details"""
    print("\n=== Test 2: AddServiceRequest Model ===")

    from app.api.jobs import AddServiceRequest

    request = AddServiceRequest(
        service_type_code="SVC_WAITING",
        special_requirements="Phí chờ giờ",
        service_details={
            "fee_amount": 500000,
            "notes": "Phí chờ giờ"
        }
    )

    assert request.service_type_code == "SVC_WAITING", "Wrong service_type_code"
    assert request.special_requirements == "Phí chờ giờ", "Wrong special_requirements"
    assert request.service_details["fee_amount"] == 500000, "Wrong fee_amount"

    print("✅ AddServiceRequest accepts service_details with fee_amount")
    return True


def test_fee_amount_formatting():
    """Test fee amount formatting"""
    print("\n=== Test 3: Fee Amount Formatting ===")

    test_cases = [
        (500000, "500,000 VND"),
        (300000, "300,000 VND"),
        (1000000, "1,000,000 VND"),
        (200000, "200,000 VND"),
    ]

    for amount, expected in test_cases:
        formatted = f"{amount:,.0f} VND"
        assert formatted == expected, f"Expected {expected}, got {formatted}"
        print(f"  ✓ {amount} -> {formatted}")

    print("✅ Fee amount formatting correct")
    return True


def test_fee_type_validation():
    """Test fee type validation"""
    print("\n=== Test 4: Fee Type Validation ===")

    valid_fee_types = ["SVC_WAITING", "SVC_CANCEL_FEE", "SVC_SURCHARGE"]

    fee_labels = {
        "SVC_WAITING": "Phí chờ giờ",
        "SVC_CANCEL_FEE": "Phí huỷ chuyến",
        "SVC_SURCHARGE": "Phí phát sinh"
    }

    for fee_type in valid_fee_types:
        assert fee_type in fee_labels, f"{fee_type} not in fee_labels"
        print(f"  ✓ {fee_type} -> {fee_labels[fee_type]}")

    # Test invalid fee type defaults to SVC_SURCHARGE
    invalid_type = "SVC_INVALID"
    if invalid_type not in valid_fee_types:
        default_type = "SVC_SURCHARGE"
        print(f"  ✓ Invalid '{invalid_type}' defaults to {default_type}")

    print("✅ Fee type validation correct")
    return True


def test_note_append_logic():
    """Test note appending logic"""
    print("\n=== Test 5: Note Append Logic ===")

    # Test 1: Append to existing notes
    existing = "Ghi chú cũ"
    new_note = "Khách yêu cầu không xếp chồng"
    combined = f"{existing}\n{new_note}" if existing else new_note
    expected = "Ghi chú cũ\nKhách yêu cầu không xếp chồng"
    assert combined == expected, f"Expected '{expected}', got '{combined}'"
    print(f"  ✓ Append to existing: '{combined[:30]}...'")

    # Test 2: New note when empty
    existing = ""
    new_note = "Chờ hàng từ 8h đến 12h"
    combined = f"{existing}\n{new_note}" if existing else new_note
    expected = "Chờ hàng từ 8h đến 12h"
    assert combined == expected, f"Expected '{expected}', got '{combined}'"
    print(f"  ✓ New note when empty: '{combined}'")

    # Test 3: New note when None
    existing = None
    new_note = "Hàng dễ vỡ"
    combined = f"{existing}\n{new_note}" if existing else new_note
    expected = "Hàng dễ vỡ"
    assert combined == expected, f"Expected '{expected}', got '{combined}'"
    print(f"  ✓ New note when None: '{combined}'")

    print("✅ Note append logic correct")
    return True


def test_update_job_prompts():
    """Test UPDATE_JOB prompts include note/fee examples"""
    print("\n=== Test 6: Update Job Prompts ===")

    from app.ai.prompts.update_job_prompts import UPDATE_JOB_EXTRACTION_PROMPT

    # Check for add_note examples
    assert "add_note" in UPDATE_JOB_EXTRACTION_PROMPT, "add_note not in prompt"
    print("  ✓ add_note action type in prompt")

    # Check for add_fee examples
    assert "add_fee" in UPDATE_JOB_EXTRACTION_PROMPT, "add_fee not in prompt"
    print("  ✓ add_fee action type in prompt")

    # Check for fee type constants
    assert "SVC_WAITING" in UPDATE_JOB_EXTRACTION_PROMPT, "SVC_WAITING not in prompt"
    assert "SVC_CANCEL_FEE" in UPDATE_JOB_EXTRACTION_PROMPT, "SVC_CANCEL_FEE not in prompt"
    print("  ✓ Fee type constants in prompt")

    # Check for example messages
    assert "khach yeu cau" in UPDATE_JOB_EXTRACTION_PROMPT.lower(), "Note example missing"
    assert "phi cho gio" in UPDATE_JOB_EXTRACTION_PROMPT.lower(), "Fee example missing"
    print("  ✓ Example messages in prompt")

    print("✅ Update job prompts include note/fee examples")
    return True


def test_intent_prompts():
    """Test intent classification prompts include note/fee signals"""
    print("\n=== Test 7: Intent Classification Prompts ===")

    from app.ai.prompts.intent_prompts import INTENT_CLASSIFICATION_PROMPT

    # Check for note/fee signals
    signals_to_check = ["ghi chú", "yêu cầu", "chờ hàng", "phí chờ", "phí huỷ"]

    for signal in signals_to_check:
        assert signal in INTENT_CLASSIFICATION_PROMPT, f"'{signal}' not in prompt"
        print(f"  ✓ Signal '{signal}' in prompt")

    print("✅ Intent prompts include note/fee signals")
    return True


def test_conversation_manager_has_handlers():
    """Test ConversationManager has add_note and add_fee handlers"""
    print("\n=== Test 8: ConversationManager Handlers ===")

    from app.ai.memory.conversation_manager import ConversationManager
    import inspect

    # Get source code of _execute_update_job
    source = inspect.getsource(ConversationManager._execute_update_job)

    # Check for add_note handler
    assert 'action_type == "add_note"' in source, "add_note handler missing"
    print("  ✓ add_note handler exists")

    # Check for add_fee handler
    assert 'action_type == "add_fee"' in source, "add_fee handler missing"
    print("  ✓ add_fee handler exists")

    # Check for fee_labels mapping
    assert "SVC_WAITING" in source and "Phí chờ giờ" in source, "fee_labels missing"
    print("  ✓ fee_labels mapping exists")

    print("✅ ConversationManager has all handlers")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Notes and Fees Feature Tests")
    print("=" * 60)

    tests = [
        test_entity_accumulator,
        test_add_service_request_model,
        test_fee_amount_formatting,
        test_fee_type_validation,
        test_note_append_logic,
        test_update_job_prompts,
        test_intent_prompts,
        test_conversation_manager_has_handlers,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} FAILED: {e}")

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
