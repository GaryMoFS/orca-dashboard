import requests
import json

RUNTIME_BASE = "http://127.0.0.1:7010"

def verify_m12_api():
    print("--- Verifying M12 Director Capability API ---")
    
    # 1. GET /api/director/capabilities
    print("Fetching capabilities list...")
    try:
        r = requests.get(f"{RUNTIME_BASE}/api/director/capabilities")
        r.raise_for_status()
        data = r.json()
        print(f"PASS: Fetched {len(data['catalog'])} capabilities.")
        # print(json.dumps(data["counts"], indent=2))
    except Exception as e:
        print(f"FAIL: Fetch failed: {e}")
        return

    # 2. POST /api/director/capabilities/emit_test_receipt
    print("Emitting test receipt...")
    try:
        payload = {"capability_id": "cap.txt_to_ifc"}
        r = requests.post(f"{RUNTIME_BASE}/api/director/capabilities/emit_test_receipt", json=payload)
        r.raise_for_status()
        receipt = r.json()
        receipt_id = receipt["receipt_id"]
        print(f"PASS: Emitted test receipt: {receipt_id}")
    except Exception as e:
        print(f"FAIL: Emit failed: {e}")
        return

    # 3. Verify event and file
    print("Checking events...")
    try:
        r = requests.get(f"{RUNTIME_BASE}/api/director/events?limit=5")
        r.raise_for_status()
        events = r.json()
        types = [e["type"] for e in events]
        if "capability.receipt_written" in types:
            print("PASS: Event found in flight recorder.")
        else:
            print(f"FAIL: Event not found. Found: {types}")
    except Exception as e:
        print(f"FAIL: Event check failed: {e}")

if __name__ == "__main__":
    verify_m12_api()
