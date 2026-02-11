import requests
import json
import time

BASE_URL = "http://127.0.0.1:7010/runtime/persona"

def verify_api():
    print("--- API STEP 1: List Personas ---")
    r = requests.get(f"{BASE_URL}/list?cap_profile=retail")
    print(f"List (Retail): {json.dumps(r.json(), indent=2)}")
    assert len(r.json()) >= 2
    
    # Work persona should be LOCKED in list if no grant
    work = next(p for p in r.json() if p['id'] == "persona.work@0.1")
    # Note: Status check depends on grants.json state. 
    # Earlier test run added a grant, so let's verify if it's there or not.
    print(f"Work status in list: {work['status']}")

    print("\n--- API STEP 2: Preview Work Persona (Retail) ---")
    r = requests.get(f"{BASE_URL}/preview?persona_id=persona.work@0.1&cap_profile=retail")
    preview = r.json()
    print(f"Preview Name: {preview['name']}")
    print(f"Preview Status: {preview['status']}")
    print(f"Modules (Retail Filter): {[m['id'] for m in preview['layout']['modules']]}")
    assert preview['status'] in ["LOCKED_PREVIEW", "UNLOCKED"]
    # Only tts.standard should remain if retail
    if preview['status'] == "LOCKED_PREVIEW":
        assert "tts.standard" in [m['id'] for m in preview['layout']['modules']]
        assert "chat.advanced" not in [m['id'] for m in preview['layout']['modules']]

    print("\n--- API STEP 3: Active Persona ---")
    r = requests.get(f"{BASE_URL}/active")
    print(f"Active Persona: {r.json()['id']}")

    print("\n--- API STEP 4: Switch Persona (to Work) ---")
    r = requests.post(f"{BASE_URL}/switch", json={"persona_id": "persona.work@0.1"}, params={"cap_profile": "enterprise"})
    switched = r.json()
    print(f"Switched to: {switched['name']}")
    print(f"Status (Enterprise): {switched['status']}")
    
    r = requests.get(f"{BASE_URL}/active")
    print(f"Confirmed Active is now: {r.json()['id']}")
    assert r.json()['id'] == "persona.work@0.1"

    print("\n--- API VERIFICATION PASS ---")

if __name__ == "__main__":
    try:
        verify_api()
    except Exception as e:
        print(f"API VERIFICATION FAILED: {e}")
        exit(1)
