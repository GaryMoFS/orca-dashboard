import os
import json
import shutil
import sys
from datetime import datetime

# Add root to sys.path
sys.path.append(os.getcwd())

from orca.capabilities.txt_to_ifc import txt_to_ifc

RUNTIME_BASE = "http://127.0.0.1:7010"

def verify_m14():
    print("--- Verifying M14: cap.txt_to_ifc v0 ---")
    
    # 1. Setup
    work_dir = "temp_m14_verify"
    if os.path.exists(work_dir): shutil.rmtree(work_dir)
    os.makedirs(work_dir)
    
    input_txt = os.path.join(work_dir, "input.txt")
    with open(input_txt, "w") as f:
        f.write("ROOM name=M14Room width=4500 depth=3500 height=2600")
        
    # 2. Run Pipeline
    print("Running pipeline...")
    try:
        results = txt_to_ifc.run(input_txt, work_dir)
        print(f"PASS: Pipeline finished. Receipt: {os.path.basename(results['receipt_path'])}")
    except Exception as e:
        print(f"FAIL: Pipeline failed: {e}")
        return

    # 3. Validate Artifacts
    if os.path.exists(results['ifc_path']):
        print(f"PASS: IFC file exists: {results['ifc_path']}")
    else:
        print("FAIL: IFC file missing.")
        
    if os.path.exists(results['manifest_path']):
        print("PASS: Manifest exists.")
    else:
        print("FAIL: Manifest missing.")

    # 4. Validate Receipt against Schema (manual check of key fields)
    receipt = results['receipt']
    if receipt['capability_id'] == "cap.txt_to_ifc" and receipt['status'] == "success":
        print("PASS: Receipt data valid.")
    else:
        print(f"FAIL: Invalid receipt data: {receipt}")

    # 5. Connect to Director (if running)
    print("Attempting to record receipt in Director...")
    try:
        import requests
        # We use the existing record_run_receipt endpoint or manual write
        # For M14, we'll just check if we can hit the API
        r = requests.get(f"{os.environ.get('RUNTIME_BASE', 'http://127.0.0.1:7010')}/api/director/state")
        if r.status_code == 200:
            print("PASS: Director API reachable.")
            # Record the run
            payload = {
                "run_id": receipt["receipt_id"],
                "capability_id": receipt["capability_id"],
                "status": receipt["status"],
                "timestamp": receipt["ts"]
            }
            # Note: The run_receipt schema in director might differ slightly, but we'll try the record endpoint
            # Actually, Director already has record_run_receipt(receipt: Dict)
            r2 = requests.post(f"{os.environ.get('RUNTIME_BASE', 'http://127.0.0.1:7010')}/api/director/runs/record", json=receipt)
            # (Assuming an endpoint exists or we add it)
            print(f"Director record attempt: {r2.status_code}")
    except:
        print("INFO: Director not reachable (skipping live API check).")

    print("--- M14 VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    verify_m14()
