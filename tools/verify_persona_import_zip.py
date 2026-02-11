import requests
import json
import os
import zipfile
import shutil
import time

RUNTIME_BASE = "http://127.0.0.1:7010"

def create_test_zip(zip_path, version="0.1.2", broken=False):
    # Base source: home persona
    src = "orca/personas/installed/persona.home@0.1"
    tmp_src = "orca_runtime/state/tmp_test_zip"
    if os.path.exists(tmp_src): shutil.rmtree(tmp_src)
    os.makedirs(tmp_src, exist_ok=True)
    
    # Copy files
    for f in os.listdir(src):
        shutil.copy(os.path.join(src, f), os.path.join(tmp_src, f))
    
    # Modify version
    pack_path = os.path.join(tmp_src, "persona.pack.json")
    with open(pack_path, "r") as f:
        pack = json.load(f)
    
    if broken:
        os.remove(pack_path)
    else:
        pack["version"] = version
        pack["id"] = "persona.test.zip" # Distinguish from previous tests
        with open(pack_path, "w") as f:
            json.dump(pack, f, indent=2)
            
    # Zip it
    if os.path.exists(zip_path): os.remove(zip_path)
    with zipfile.ZipFile(zip_path, 'w') as z:
        for f in os.listdir(tmp_src):
            z.write(os.path.join(tmp_src, f), f)
            
    shutil.rmtree(tmp_src)

def verify_import():
    print("--- M10 Creator Workflow: ZIP Import Verification ---")
    
    zip_ok = os.path.abspath("orca_runtime/state/test_persona_v012.zip")
    zip_fail = os.path.abspath("orca_runtime/state/test_persona_broken.zip")
    os.makedirs("orca_runtime/state", exist_ok=True)

    # 1. Success Case
    print(f"Creating valid zip: {zip_ok}")
    create_test_zip(zip_ok, version="0.1.2")
    
    print("Calling /runtime/persona/import (valid zip)...")
    res = requests.post(f"{RUNTIME_BASE}/runtime/persona/import", json={"zip_path": zip_ok})
    data = res.json()
    
    if not data.get("success"):
        print(f"FAILED: Import valid zip: {data}")
        return False
    
    print(f"  PASS: Imported {data['persona_id']} v{data['version']}")
    
    # Check index
    res_idx = requests.get(f"{RUNTIME_BASE}/runtime/persona/installed")
    idx = res_idx.json()
    if "persona.test.zip" not in idx or "0.1.2" not in idx["persona.test.zip"]["versions"]:
        print(f"FAILED: Index not updated correctly: {idx}")
        return False
    print("  PASS: Index verified.")

    # 2. Failure Case (Broken ZIP)
    print(f"Creating broken zip: {zip_fail}")
    create_test_zip(zip_fail, broken=True)
    
    print("Calling /runtime/persona/import (broken zip)...")
    res = requests.post(f"{RUNTIME_BASE}/runtime/persona/import", json={"zip_path": zip_fail})
    data = res.json()
    
    if data.get("success"):
        print("FAILED: Broken zip should not have imported successfully.")
        return False
    
    print(f"  PASS: Refused broken zip. Errors: {data.get('errors')}")

    # 3. Schema Validation Fail (Invalid Layout)
    zip_schema_fail = os.path.abspath("orca_runtime/state/test_persona_schema_fail.zip")
    print(f"Creating schema-failing zip: {zip_schema_fail}")
    
    # Create valid base
    create_test_zip(zip_schema_fail, version="0.1.3")
    # Unzip, break layout, re-zip
    tmp_ext = "orca_runtime/state/tmp_schema_fail"
    os.makedirs(tmp_ext, exist_ok=True)
    with zipfile.ZipFile(zip_schema_fail, 'r') as z:
        z.extractall(tmp_ext)
    
    layout_path = os.path.join(tmp_ext, "ui.layout.json")
    with open(layout_path, "r") as f:
        layout = json.load(f)
    layout["modules"][0]["position"] = "TOP_SECRET" # Invalid enum
    with open(layout_path, "w") as f:
        json.dump(layout, f)
        
    with zipfile.ZipFile(zip_schema_fail, 'w') as z:
        for f in os.listdir(tmp_ext):
            z.write(os.path.join(tmp_ext, f), f)
    shutil.rmtree(tmp_ext)

    print("Calling /runtime/persona/import (schema fail)...")
    res = requests.post(f"{RUNTIME_BASE}/runtime/persona/import", json={"zip_path": zip_schema_fail})
    data = res.json()
    
    if data.get("success"):
        print("FAILED: Schema failure should have blocked import.")
        return False
    
    found_validation_err = any("Validation error" in e for e in data.get("errors", []))
    if not found_validation_err:
        print(f"FAILED: Expected validation error message, got: {data.get('errors')}")
        return False
    
    print(f"  PASS: Blocked invalid schema. Errors: {data.get('errors')}")

    print("\nALL M10 STEP 1 TESTS PASSED.")
    return True

if __name__ == "__main__":
    if verify_import():
        exit(0)
    else:
        exit(1)
