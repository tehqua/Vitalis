import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_health():
    print("1. Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Health: {response.json()}")
    print()

def test_login():
    print("2. Testing login...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"patient_id": "Adam631_Cronin387_aff8f143-2375-416f-901d-b0e4c73e3e58"}
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Session: {data['session_id']}")
    print(f"   Token: {data['access_token'][:50]}...")
    print()
    return data["access_token"]

def test_chat(token):
    print("3. Testing chat...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/chat/message",
        headers=headers,
        json={"message": "I have a headache for 2 days"}
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data['response'][:100]}...")
    print(f"   Emergency: {data['metadata'].get('emergency_detected')}")
    print()

def test_history(token):
    print("4. Testing conversation history...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/chat/history", headers=headers)
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Total messages: {data['total_messages']}")
    print()

def test_upload_limits():
    print("5. Testing upload limits...")
    response = requests.get(f"{BASE_URL}/upload/limits")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Image max: {data['image']['max_size_mb']}MB")
    print(f"   Audio max: {data['audio']['max_size_mb']}MB")
    print()


def test_delete_session_history(token):
    print("6. Testing delete session history...")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get current sessions list
    r = requests.get(f"{BASE_URL}/chat/sessions", headers=headers)
    assert r.status_code == 200, f"sessions list failed: {r.status_code}"
    sessions = r.json().get("sessions", [])
    if not sessions:
        print("   SKIP: no sessions exist yet (send a message first)")
        return

    session_id = sessions[0]["session_id"]
    print(f"   Deleting session: {session_id[:24]}...")

    # 2. Delete the session
    r = requests.delete(f"{BASE_URL}/chat/history/{session_id}", headers=headers)
    print(f"   Status: {r.status_code}")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    print(f"   Deleted count: {data.get('deleted_count')}")
    assert data.get("deleted_count", 0) > 0, "deleted_count should be > 0"

    # 3. Confirm session no longer in list
    r2 = requests.get(f"{BASE_URL}/chat/sessions", headers=headers)
    remaining_ids = [s["session_id"] for s in r2.json().get("sessions", [])]
    assert session_id not in remaining_ids, "Session still present after deletion!"
    print("   Session deleted successfully.\n")


def test_delete_nonexistent_session(token):
    print("7. Testing delete non-existent session (expect 404)...")
    headers = {"Authorization": f"Bearer {token}"}
    fake_id = "00000000-0000-0000-0000-000000000000"
    r = requests.delete(f"{BASE_URL}/chat/history/{fake_id}", headers=headers)
    print(f"   Status: {r.status_code}")
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"
    print("   Correctly returned 404.\n")

if __name__ == "__main__":
    print("Starting Backend Tests...\n")
    print("=" * 60)
    
    try:
        test_health()
        token = test_login()
        test_chat(token)
        test_history(token)
        test_upload_limits()
        test_delete_session_history(token)
        test_delete_nonexistent_session(token)
        
        print("=" * 60)
        print("\nAll tests PASSED!")
        
    except requests.exceptions.ConnectionError:
        print("\nERROR: Cannot connect to backend!")
        print("Make sure server is running: python main.py")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()