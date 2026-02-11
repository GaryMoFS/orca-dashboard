import requests
import time

RUNTIME_BASE = "http://127.0.0.1:7010"

def verify_q1():
    print("--- Verifying Q1 Director Flight Recorder ---")
    
    # 1. State check
    try:
        r = requests.get(f"{RUNTIME_BASE}/api/director/state")
        r.raise_for_status()
        state = r.json()
        print(f"PASS: State -> {state}")
    except Exception as e:
        print(f"FAIL: State -> {e}")

    # 2. Trigger test event
    try:
        r = requests.post(f"{RUNTIME_BASE}/api/director/events/test")
        r.raise_for_status()
        ev = r.json()
        print(f"PASS: Test Event Triggered -> {ev['id']}")
    except Exception as e:
        print(f"FAIL: Test Event -> {e}")

    # 3. Check events list
    try:
        r = requests.get(f"{RUNTIME_BASE}/api/director/events?limit=5")
        r.raise_for_status()
        events = r.json()
        found = any(e['type'] == 'test.manual' for e in events)
        if found:
            print(f"PASS: Event found in log. Count: {len(events)}")
        else:
            print(f"FAIL: Event not found in log.")
    except Exception as e:
        print(f"FAIL: Events List -> {e}")

if __name__ == "__main__":
    verify_q1()
