import requests
import json
import os
import shutil

RUNTIME_BASE = "http://127.0.0.1:7010"

def verify_m9_step2():
    print("--- M9 Step 2: Management & Rollback Verification ---")
    
    # 0. Boot check
    try:
        requests.get(f"{RUNTIME_BASE}/runtime/persona/catalog")
    except:
        print("FAILED: Runtime not responding at 7010")
        return False

    # 1. Install persona version 0.1.0
    print("Installing persona.test v0.1.0...")
    source = os.path.join(os.getcwd(), "orca", "personas", "samples", "test_pack")
    
    # Ensure source starts at 0.1.0
    p_path = os.path.join(source, "persona.pack.json")
    with open(p_path, "r") as f:
        p_data = json.load(f)
    p_data["version"] = "0.1.0"
    with open(p_path, "w") as f:
        json.dump(p_data, f, indent=2)

    # Cleanup any existing installed test persona to allow clean run
    test_inst = os.path.join(os.getcwd(), "orca", "personas", "installed", "persona.test@0.1.0")
    if os.path.exists(test_inst): shutil.rmtree(test_inst)
    test_inst_1 = os.path.join(os.getcwd(), "orca", "personas", "installed", "persona.test@0.1.1")
    if os.path.exists(test_inst_1): shutil.rmtree(test_inst_1)

    res = requests.post(f"{RUNTIME_BASE}/runtime/persona/install", json={"source_path": source})
    if res.status_code != 200 or not res.json().get("success"):
        print(f"FAILED: Install 0.1.0: {res.text}")
        return False
    
    # 2. Check installed status
    res = requests.get(f"{RUNTIME_BASE}/runtime/persona/installed")
    installed = res.json()
    if "persona.test" not in installed or installed["persona.test"]["active_version"] != "0.1.0":
        print(f"FAILED: Index check 0.1.0: {installed}")
        return False
    print("  PASS: v0.1.0 installed and active.")

    # 3. Create and install version 0.1.1 (duplicate with version change)
    print("Installing persona.test v0.1.1...")
    # Modify local sample for second version
    pack_path = os.path.join(source, "persona.pack.json")
    with open(pack_path, "r") as f:
        pack = json.load(f)
    pack["version"] = "0.1.1"
    with open(pack_path, "w") as f:
        json.dump(pack, f, indent=2)
    
    res = requests.post(f"{RUNTIME_BASE}/runtime/persona/install", json={"source_path": source})
    if res.status_code != 200 or not res.json().get("success"):
        print(f"FAILED: Install 0.1.1: {res.text}")
        return False
    
    # Check updated active version
    res = requests.get(f"{RUNTIME_BASE}/runtime/persona/installed")
    installed = res.json()
    if installed["persona.test"]["active_version"] != "0.1.1" or "0.1.0" not in installed["persona.test"]["versions"]:
        print(f"FAILED: Index check 0.1.1: {installed}")
        return False
    print("  PASS: v0.1.1 installed and active. v0.1.0 preserved.")

    # 4. Rollback to 0.1.0
    print("Rolling back persona.test to v0.1.0...")
    res = requests.post(f"{RUNTIME_BASE}/runtime/persona/rollback", json={"persona_id": "persona.test", "version": "0.1.0"})
    if res.status_code != 200 or not res.json().get("success"):
        print(f"FAILED: Rollback: {res.text}")
        return False
    
    res = requests.get(f"{RUNTIME_BASE}/runtime/persona/installed")
    if res.json()["persona.test"]["active_version"] != "0.1.0":
        print(f"FAILED: Active version after rollback: {res.json()}")
        return False
    print("  PASS: Rollback successful.")

    # 5. Idempotency Check (Activation)
    print("Checking activation idempotency...")
    sku = "sku.orca.pro.01"
    # First activation
    requests.post(f"{RUNTIME_BASE}/runtime/persona/activate", json={"sku": sku})
    res_a = requests.get(f"{RUNTIME_BASE}/runtime/persona/catalog")
    
    # Second activation (same)
    requests.post(f"{RUNTIME_BASE}/runtime/persona/activate", json={"sku": sku})
    
    # Count grants
    with open("orca/licenses/grants.json", "r") as f:
        grants = json.load(f)["grants"]
        count = sum(1 for g in grants if (isinstance(g, dict) and g.get("sku") == sku) or g == sku)
    
    if count != 1:
        print(f"FAILED: Idempotency failed. Grant count for {sku}: {count}")
        return False
    print("  PASS: Activation is idempotent.")

    print("\nALL M9 STEP 2 TESTS PASSED.")
    return True

if __name__ == "__main__":
    if verify_m9_step2():
        exit(0)
    else:
        exit(1)
