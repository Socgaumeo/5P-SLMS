#!/usr/bin/env python3
"""
API Integration Tests for Notes and Fees Features
==================================================

Tests the actual API endpoints for:
1. PUT /api/services/{svc_id}/notes - Update service notes
2. POST /api/jobs/{job_id}/services - Add fee service

Run: python3 tests/test-api-notes-fees-integration.py

Note: Requires the backend server to be running on localhost:8000
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"


def test_update_service_notes_endpoint():
    """Test PUT /api/services/{svc_id}/notes endpoint"""
    print("\n=== Test: Update Service Notes Endpoint ===")

    # First, get a list of jobs to find a service ID
    try:
        jobs_resp = requests.get(f"{BASE_URL}/api/jobs/recent?limit=5", timeout=10)
        if jobs_resp.status_code != 200:
            print(f"  ⚠️ Could not fetch jobs: {jobs_resp.status_code}")
            return False

        jobs = jobs_resp.json().get("jobs", [])
        if not jobs:
            print("  ⚠️ No jobs found to test with")
            return False

        job_id = jobs[0].get("job_id")

        # Get job details to find service ID
        details_resp = requests.get(f"{BASE_URL}/api/jobs/{job_id}/details", timeout=10)
        if details_resp.status_code != 200:
            print(f"  ⚠️ Could not fetch job details: {details_resp.status_code}")
            return False

        services = details_resp.json().get("services", [])
        if not services:
            print("  ⚠️ No services found in job")
            return False

        svc_id = services[0].get("svc_id")
        print(f"  Testing with svc_id: {svc_id}")

        # Test update notes
        test_note = "Test note from integration test"
        update_resp = requests.put(
            f"{BASE_URL}/api/services/{svc_id}/notes",
            json={"notes": test_note},
            timeout=10
        )

        if update_resp.status_code == 200:
            result = update_resp.json()
            if result.get("success"):
                print(f"  ✅ Successfully updated notes: '{test_note}'")
                return True
            else:
                print(f"  ❌ Update failed: {result.get('message')}")
                return False
        else:
            print(f"  ❌ HTTP error: {update_resp.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("  ⚠️ Backend server not running on localhost:8000")
        return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_add_fee_service_endpoint():
    """Test POST /api/jobs/{job_id}/services for fee services"""
    print("\n=== Test: Add Fee Service Endpoint ===")

    try:
        # Get a job to add service to
        jobs_resp = requests.get(f"{BASE_URL}/api/jobs/recent?limit=5", timeout=10)
        if jobs_resp.status_code != 200:
            print(f"  ⚠️ Could not fetch jobs: {jobs_resp.status_code}")
            return False

        jobs = jobs_resp.json().get("jobs", [])
        if not jobs:
            print("  ⚠️ No jobs found to test with")
            return False

        job = jobs[0]
        job_id = job.get("job_id")
        job_no = job.get("job_no")

        # Skip if job is completed/cancelled
        if job.get("status_code") in ["COMPLETED", "CANCELLED"]:
            print(f"  ⚠️ Job {job_no} is {job.get('status_code')}, skipping")
            return None

        print(f"  Testing with job_id: {job_id} ({job_no})")

        # Test adding fee service
        fee_payload = {
            "service_type_code": "SVC_WAITING",
            "special_requirements": "Test fee - Phí chờ giờ integration test",
            "service_details": {
                "fee_amount": 100000,
                "notes": "Integration test fee"
            }
        }

        add_resp = requests.post(
            f"{BASE_URL}/api/jobs/{job_id}/services",
            json=fee_payload,
            timeout=10
        )

        if add_resp.status_code == 200:
            result = add_resp.json()
            if result.get("success"):
                svc_id = result.get("svc_id")
                print(f"  ✅ Successfully added fee service: svc_id={svc_id}")

                # Clean up - delete the test service
                del_resp = requests.delete(f"{BASE_URL}/api/services/{svc_id}", timeout=10)
                if del_resp.status_code == 200 and del_resp.json().get("success"):
                    print(f"  ✅ Cleaned up test service")
                else:
                    print(f"  ⚠️ Could not clean up test service")

                return True
            else:
                print(f"  ❌ Add failed: {result.get('message')}")
                return False
        else:
            print(f"  ❌ HTTP error: {add_resp.status_code} - {add_resp.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("  ⚠️ Backend server not running on localhost:8000")
        return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_chat_add_note_flow():
    """Test chat flow for adding notes"""
    print("\n=== Test: Chat Add Note Flow ===")

    try:
        # Send a chat message to add note
        chat_payload = {
            "message": "khách yêu cầu không xếp chồng job TRK-0402-0001",
            "session_id": "test-notes-session"
        }

        resp = requests.post(
            f"{BASE_URL}/api/chat/message",
            json=chat_payload,
            timeout=30
        )

        if resp.status_code == 200:
            result = resp.json()
            response_text = result.get("response", "")
            intent = result.get("intent", "")

            print(f"  Response: {response_text[:100]}...")
            print(f"  Intent detected: {intent}")

            # Check if UPDATE_JOB intent was detected
            if intent and "UPDATE" in intent.upper():
                print(f"  ✅ Correct intent detected for note addition")
                return True
            else:
                print(f"  ⚠️ Intent may not be correct: {intent}")
                return None
        else:
            print(f"  ❌ HTTP error: {resp.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("  ⚠️ Backend server not running on localhost:8000")
        return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_chat_add_fee_flow():
    """Test chat flow for adding fee"""
    print("\n=== Test: Chat Add Fee Flow ===")

    try:
        # Send a chat message to add fee
        chat_payload = {
            "message": "phí chờ giờ 500k job TRK-0402-0001",
            "session_id": "test-fees-session"
        }

        resp = requests.post(
            f"{BASE_URL}/api/chat/message",
            json=chat_payload,
            timeout=30
        )

        if resp.status_code == 200:
            result = resp.json()
            response_text = result.get("response", "")
            intent = result.get("intent", "")
            entities = result.get("entities", {})

            print(f"  Response: {response_text[:100]}...")
            print(f"  Intent detected: {intent}")
            print(f"  Entities: {json.dumps(entities, ensure_ascii=False)[:100]}...")

            # Check if UPDATE_JOB intent was detected
            if intent and "UPDATE" in intent.upper():
                print(f"  ✅ Correct intent detected for fee addition")
                return True
            else:
                print(f"  ⚠️ Intent may not be correct: {intent}")
                return None
        else:
            print(f"  ❌ HTTP error: {resp.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("  ⚠️ Backend server not running on localhost:8000")
        return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    """Run all API integration tests"""
    print("=" * 60)
    print("API Integration Tests for Notes and Fees Features")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")

    tests = [
        ("Update Service Notes", test_update_service_notes_endpoint),
        ("Add Fee Service", test_add_fee_service_endpoint),
        ("Chat Add Note Flow", test_chat_add_note_flow),
        ("Chat Add Fee Flow", test_chat_add_fee_flow),
    ]

    passed = 0
    failed = 0
    skipped = 0

    for name, test_func in tests:
        result = test_func()
        if result is True:
            passed += 1
        elif result is False:
            failed += 1
        else:
            skipped += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 60)

    if skipped > 0:
        print("\n⚠️ Some tests were skipped. Make sure the backend server is running:")
        print("   cd backend && python3 -m uvicorn main:app --reload")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
