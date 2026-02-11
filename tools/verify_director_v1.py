import requests
import json
import time

RUNTIME_BASE = "http://127.0.0.1:7010"

def test_director_api():
    print("--- Testing Director API ---")
    
    # 1. Check status
    try:
        r = requests.get(f"{RUNTIME_BASE}/api/director/status")
        r.raise_for_status()
        status = r.json()
        print(f"PASS: Director Status -> {status}")
    except Exception as e:
        print(f"FAIL: Director Status -> {e}")
        return

    # 2. Start session
    try:
        r = requests.post(f"{RUNTIME_BASE}/api/director/session/start?persona_id=persona.home@0.1")
        r.raise_for_status()
        session = r.json()
        session_id = session['id']
        print(f"PASS: Started Session -> {session_id}")
    except Exception as e:
        print(f"FAIL: Start Session -> {e}")
        return

    # 3. List sessions
    try:
        r = requests.get(f"{RUNTIME_BASE}/api/director/sessions")
        r.raise_for_status()
        sessions = r.json()
        found = any(s['id'] == session_id for s in sessions)
        if found:
            print(f"PASS: Session {session_id} found in list. Total: {len(sessions)}")
        else:
            print(f"FAIL: Session {session_id} not found in list.")
    except Exception as e:
        print(f"FAIL: List Sessions -> {e}")

    # 4. Stop session
    try:
        r = requests.post(f"{RUNTIME_BASE}/api/director/session/stop?session_id={session_id}")
        r.raise_for_status()
        stopped = r.json()
        if stopped['status'] == 'completed':
            print(f"PASS: Stopped Session {session_id}")
        else:
            print(f"FAIL: Stop Session status -> {stopped['status']}")
    except Exception as e:
        print(f"FAIL: Stop Session -> {e}")

if __name__ == "__main__":
    test_director_api()
