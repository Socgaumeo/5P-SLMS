"""
Test case for session confirmation flow.
Verifies that session state persists between requests.
"""

import asyncio
import httpx
import sys


API_URL = "http://localhost:8000"


async def test_session_confirmation_flow():
    """
    Test the complete flow:
    1. Send booking request with all required info
    2. Verify session is in CONFIRMING state
    3. Send "OK" to confirm
    4. Verify job is created (not general_chat error)
    """
    print("=" * 60)
    print("TEST: Session Confirmation Flow")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Send booking request
        print("\n[Step 1] Sending booking request...")
        booking_message = """
        Đặt xe cho VINHPHUC
        Ngày: 03/02/2026
        Giờ lấy: 08:00
        Lấy tại: Kho VINHPHUC Bình Dương
        Giao tại: Công ty ABC - KCN Tân Bình, TP.HCM
        Invoice: INV-2026-001
        Số lượng: 5 pallet
        """

        response1 = await client.post(
            f"{API_URL}/api/chat/message",
            json={
                "message": booking_message,
                "session_id": None,  # New session
            }
        )

        if response1.status_code != 200:
            print(f"❌ FAILED: Status {response1.status_code}")
            print(response1.text)
            return False

        result1 = response1.json()
        session_id = result1.get("session_id")
        task_state = result1.get("task_state")
        intent = result1.get("intent")

        print(f"   Response received:")
        print(f"   - session_id: {session_id}")
        print(f"   - task_state: {task_state}")
        print(f"   - intent: {intent}")
        print(f"   - response: {result1.get('response', '')[:100]}...")

        if not session_id:
            print("❌ FAILED: No session_id returned")
            return False

        # Step 2: Check session state via debug endpoint
        print(f"\n[Step 2] Checking session state...")
        session_response = await client.get(
            f"{API_URL}/api/chat/session/{session_id}"
        )

        if session_response.status_code == 200:
            session_data = session_response.json()
            print(f"   Session state: {session_data.get('task_state')}")
            print(f"   Intent: {session_data.get('intent')}")
            print(f"   Entities count: {len(session_data.get('entities', {}))}")

            if session_data.get("task_state") != "confirming":
                print(f"⚠️ WARNING: Expected 'confirming', got '{session_data.get('task_state')}'")
        else:
            print(f"   Could not fetch session: {session_response.status_code}")

        # Step 3: Send confirmation "OK"
        print(f"\n[Step 3] Sending confirmation 'OK'...")
        response2 = await client.post(
            f"{API_URL}/api/chat/message",
            json={
                "message": "OK",
                "session_id": session_id,  # Use same session
            }
        )

        if response2.status_code != 200:
            print(f"❌ FAILED: Status {response2.status_code}")
            print(response2.text)
            return False

        result2 = response2.json()
        task_state2 = result2.get("task_state")
        intent2 = result2.get("intent")
        response_text = result2.get("response", "")

        print(f"   Response received:")
        print(f"   - task_state: {task_state2}")
        print(f"   - intent: {intent2}")
        print(f"   - response: {response_text[:200]}...")

        # Step 4: Verify result
        print(f"\n[Step 4] Verifying result...")

        # Check for success indicators
        if "general_chat" in response_text.lower():
            print("❌ FAILED: Got 'general_chat' error - session was lost!")
            print("\n   DIAGNOSIS: Session state not persisted between requests.")
            print("   POSSIBLE CAUSES:")
            print("   1. Server running with --reload (restarts on file change)")
            print("   2. Multiple workers (each has separate memory)")
            print("   3. Session store bug")
            return False

        if "✅" in response_text and ("Đã tạo" in response_text or "Job" in response_text):
            print("✅ SUCCESS: Job created successfully!")
            return True

        if "Chưa có thông tin" in response_text:
            print("❌ FAILED: No entities found - session was reset!")
            return False

        print("⚠️ UNCLEAR: Check response manually")
        print(f"   Full response: {response_text}")
        return False


async def test_debug_sessions():
    """Check all active sessions"""
    print("\n" + "=" * 60)
    print("DEBUG: Active Sessions")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{API_URL}/api/chat/debug/sessions")

        if response.status_code == 200:
            data = response.json()
            print(f"Total sessions: {data.get('total_sessions', 0)}")
            for session in data.get("sessions", []):
                print(f"  - {session['session_id'][:8]}... state={session['task_state']} intent={session['intent']}")
        else:
            print(f"Could not fetch sessions: {response.status_code}")


async def main():
    print("\n" + "=" * 60)
    print("SLMS Session Confirmation Test")
    print("=" * 60)

    # Check if server is running
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(f"{API_URL}/")
            if response.status_code != 200:
                print(f"❌ Server not responding correctly: {response.status_code}")
                return
        except httpx.ConnectError:
            print(f"❌ Cannot connect to server at {API_URL}")
            print("   Please start the server first:")
            print("   cd backend && uvicorn main:app --host 0.0.0.0 --port 8000")
            return

    print("✅ Server is running")

    # Run tests
    success = await test_session_confirmation_flow()
    await test_debug_sessions()

    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ TESTS FAILED")
    print("=" * 60)

    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
