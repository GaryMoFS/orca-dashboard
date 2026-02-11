import requests
import json
import os
import time

RUNTIME_BASE = "http://127.0.0.1:7010"

def verify_m15():
    print("--- Verifying M15 Action Bridge ---")
    
    # 1. Check Actions List
    print("Fetching capability actions...")
    try:
        r = requests.get(f"{RUNTIME_BASE}/api/director/capabilities/actions")
        r.raise_for_status()
        actions = r.json()
        demo_cap = next((c for c in actions if c["id"] == "cap.txt_to_ifc"), None)
        if demo_cap and any(a["id"] == "run_demo" for a in demo_cap["actions"]):
            print("PASS: cap.txt_to_ifc has run_demo action.")
        else:
            print(f"FAIL: Action not found in: {actions}")
            return
    except Exception as e:
        print(f"FAIL: Actions fetch failed: {e}")
        return

    # 2. Execute Action
    print("Executing cap.txt_to_ifc:run_demo via Director...")
    try:
        payload = {
            "capability_id": "cap.txt_to_ifc",
            "action_id": "run_demo",
            "params": {
                "name": "M15_Action_Room",
                "width_mm": 6000,
                "depth_mm": 5000,
                "height_mm": 2800
            }
        }
        r = requests.post(f"{RUNTIME_BASE}/api/director/capabilities/run", json=payload)
        r.raise_for_status()
        data = r.json()
        run_id = data["run_id"]
        print(f"PASS: Run started: {run_id}")
        
        # 3. Verify Artifacts
        artifact_dir = data["artifact_dir"]
        if os.path.exists(artifact_dir):
            ifc_name = "M15_Action_Room.ifc"
            if os.path.exists(os.path.join(artifact_dir, ifc_name)):
                print(f"PASS: IFC generated at {artifact_dir}")
            else:
                print(f"FAIL: IFC missing in {artifact_dir}")
        else:
            print(f"FAIL: Artifact dir {artifact_dir} missing.")

        # 4. Verify Flight Recorder Events
        print("Checking flight recorder for orchestration events...")
        # Give it a moment to append
        time.sleep(1)
        r = requests.get(f"{RUNTIME_BASE}/api/director/events?limit=10")
        events = r.json()
        types = [e["type"] for e in events if e.get("payload", {}).get("run_id") == run_id]
        
        expected = ["capability.run_requested", "capability.run_started", "capability.run_completed"]
        missing = [t for t in expected if t not in types]
        
        if not missing:
            print("PASS: All flight recorder events found for this run.")
        else:
            print(f"FAIL: Missing events: {missing}. Found types for run: {types}")

    except Exception as e:
        print(f"FAIL: Action execution failed: {e}")

if __name__ == "__main__":
    verify_m15()
