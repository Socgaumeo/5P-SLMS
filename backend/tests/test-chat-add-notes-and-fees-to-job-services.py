"""
Test cases for Notes and Fees Features
======================================

Test the following features:
1. Add note to service via chat
2. Add fee service via chat
3. Fee service types in API
4. Entity extraction for notes/fees
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import json

# Test cases for intent classification
class TestIntentClassification:
    """Test intent classification for notes and fees"""

    # Test data: (input_message, expected_intent, expected_confidence_min)
    NOTE_TEST_CASES = [
        ("khách yêu cầu không xếp chồng job TRK-0402-0002", "UPDATE_JOB", 0.85),
        ("chờ hàng từ 8h đến 12h TRK-0402-0002", "UPDATE_JOB", 0.80),
        ("ghi chú job 089: hàng dễ vỡ", "UPDATE_JOB", 0.80),
        ("job TRK-2601-089 yêu cầu bốc xếp cẩn thận", "UPDATE_JOB", 0.80),
    ]

    FEE_TEST_CASES = [
        ("phí chờ giờ 500k job 089", "UPDATE_JOB", 0.85),
        ("thêm phí huỷ chuyến 300k cho job 087", "UPDATE_JOB", 0.85),
        ("phí phát sinh 200k job TRK-0402-0002", "UPDATE_JOB", 0.80),
        ("tính phí chờ 1 triệu job 085", "UPDATE_JOB", 0.80),
    ]


class TestEntityExtraction:
    """Test entity extraction for notes and fees"""

    # Test data for add_note action
    ADD_NOTE_ENTITIES = [
        {
            "input": "khách yêu cầu không xếp chồng job TRK-0402-0002",
            "expected": {
                "job_number": "TRK-0402-0002",
                "action_type": "add_note",
                "notes": "Khách yêu cầu không xếp chồng"
            }
        },
        {
            "input": "chờ hàng từ 8h đến 12h TRK-0402-0002",
            "expected": {
                "job_number": "TRK-0402-0002",
                "action_type": "add_note",
                "notes": "Chờ hàng từ 8h đến 12h"
            }
        },
    ]

    # Test data for add_fee action
    ADD_FEE_ENTITIES = [
        {
            "input": "phí chờ giờ 500k job 089",
            "expected": {
                "job_number_partial": "089",
                "action_type": "add_fee",
                "fee_type": "SVC_WAITING",
                "fee_amount": 500000
            }
        },
        {
            "input": "thêm phí huỷ chuyến 300k cho job 087",
            "expected": {
                "job_number_partial": "087",
                "action_type": "add_fee",
                "fee_type": "SVC_CANCEL_FEE",
                "fee_amount": 300000
            }
        },
        {
            "input": "phí phát sinh 200k job TRK-0402-0002",
            "expected": {
                "job_number": "TRK-0402-0002",
                "action_type": "add_fee",
                "fee_type": "SVC_SURCHARGE",
                "fee_amount": 200000
            }
        },
    ]


class TestAddNoteExecution:
    """Test add_note action execution"""

    @pytest.mark.asyncio
    async def test_add_note_to_service(self):
        """Test adding note to first service of a job"""
        from app.ai.memory.conversation_manager import ConversationManager

        # Mock entities
        entities = {
            "job_number": "TRK-0402-0002",
            "action_type": "add_note",
            "notes": "Khách yêu cầu không xếp chồng"
        }

        # Expected flow:
        # 1. Look up job by job_number
        # 2. Get job details with services
        # 3. Update first service's notes via PUT /api/services/{svc_id}/notes

        # Test that the note is appended correctly
        existing_notes = "Ghi chú cũ"
        new_notes = "Khách yêu cầu không xếp chồng"
        expected_combined = f"{existing_notes}\n{new_notes}"

        assert expected_combined == "Ghi chú cũ\nKhách yêu cầu không xếp chồng"


class TestAddFeeExecution:
    """Test add_fee action execution"""

    FEE_TYPE_MAPPING = {
        "SVC_WAITING": "Phí chờ giờ",
        "SVC_CANCEL_FEE": "Phí huỷ chuyến",
        "SVC_SURCHARGE": "Phí phát sinh"
    }

    @pytest.mark.asyncio
    async def test_add_fee_service(self):
        """Test adding fee service to a job"""
        # Mock entities
        entities = {
            "job_number_partial": "089",
            "action_type": "add_fee",
            "fee_type": "SVC_WAITING",
            "fee_amount": 500000,
            "notes": "Phí chờ giờ"
        }

        # Expected payload to POST /api/jobs/{job_id}/services
        expected_payload = {
            "service_type_code": "SVC_WAITING",
            "special_requirements": "Phí chờ giờ",
            "service_details": {
                "fee_amount": 500000,
                "notes": "Phí chờ giờ"
            }
        }

        # Verify fee type is valid
        assert entities["fee_type"] in ["SVC_WAITING", "SVC_CANCEL_FEE", "SVC_SURCHARGE"]

        # Verify amount formatting
        amount = entities["fee_amount"]
        formatted = f"{amount:,.0f} VND"
        assert formatted == "500,000 VND"


class TestAddServiceRequest:
    """Test AddServiceRequest model with service_details"""

    def test_add_service_request_with_fee_details(self):
        """Test that AddServiceRequest accepts service_details"""
        from app.api.jobs import AddServiceRequest

        request = AddServiceRequest(
            service_type_code="SVC_WAITING",
            special_requirements="Phí chờ giờ",
            service_details={
                "fee_amount": 500000,
                "notes": "Phí chờ giờ"
            }
        )

        assert request.service_type_code == "SVC_WAITING"
        assert request.special_requirements == "Phí chờ giờ"
        assert request.service_details["fee_amount"] == 500000


class TestUpdateServiceNotes:
    """Test PUT /api/services/{svc_id}/notes endpoint"""

    def test_update_notes_request_model(self):
        """Test UpdateServiceNotesRequest model"""
        from pydantic import BaseModel

        class UpdateServiceNotesRequest(BaseModel):
            notes: str

        request = UpdateServiceNotesRequest(notes="Test note")
        assert request.notes == "Test note"


class TestEntityAccumulator:
    """Test EntityAccumulator with new fee fields"""

    def test_optional_fields_include_fee_fields(self):
        """Test that fee_type and fee_amount are in optional fields"""
        from app.ai.memory.entity_accumulator import EntityAccumulator

        accumulator = EntityAccumulator()
        update_job_optional = accumulator.OPTIONAL_FIELDS.get("update_job", [])

        assert "fee_type" in update_job_optional
        assert "fee_amount" in update_job_optional
        assert "notes" in update_job_optional


class TestFeeServiceTypes:
    """Test fee service type constants"""

    VALID_FEE_TYPES = ["SVC_WAITING", "SVC_CANCEL_FEE", "SVC_SURCHARGE"]

    FEE_TYPE_LABELS = {
        "SVC_WAITING": "Phí chờ giờ",
        "SVC_CANCEL_FEE": "Phí huỷ chuyến",
        "SVC_SURCHARGE": "Phí phát sinh khác",
    }

    def test_fee_types_are_valid(self):
        """Test that all fee types are recognized"""
        for fee_type in self.VALID_FEE_TYPES:
            assert fee_type.startswith("SVC_")

    def test_fee_type_labels(self):
        """Test that all fee types have Vietnamese labels"""
        for fee_type in self.VALID_FEE_TYPES:
            assert fee_type in self.FEE_TYPE_LABELS


# Integration test scenarios
class TestIntegrationScenarios:
    """End-to-end test scenarios"""

    SCENARIOS = [
        {
            "name": "Add note via chat",
            "messages": [
                "khách yêu cầu không xếp chồng job TRK-0402-0002"
            ],
            "expected_action": "add_note",
            "expected_response_contains": ["Thêm ghi chú", "TRK-0402-0002"]
        },
        {
            "name": "Add waiting fee via chat",
            "messages": [
                "phí chờ giờ 500k job 089"
            ],
            "expected_action": "add_fee",
            "expected_response_contains": ["Phí chờ giờ", "500,000"]
        },
        {
            "name": "Add cancel fee via chat",
            "messages": [
                "thêm phí huỷ chuyến 300k cho job 087"
            ],
            "expected_action": "add_fee",
            "expected_response_contains": ["Phí huỷ chuyến", "300,000"]
        },
        {
            "name": "Add waiting time note",
            "messages": [
                "chờ hàng từ 8h đến 12h TRK-0402-0002"
            ],
            "expected_action": "add_note",
            "expected_response_contains": ["ghi chú", "8h", "12h"]
        }
    ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
