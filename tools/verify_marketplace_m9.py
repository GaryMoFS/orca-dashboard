import requests
import json
import time

RUNTIME_BASE = "http://127.0.0.1:7010"

def verify_m9():
    print("--- M9 Marketplace Verification ---")
    
    # 1. Check Initial Catalog
    try:
        res = requests.get(f"{RUNTIME_BASE}/runtime/persona/catalog")
        catalog = res.json()
        print(f"Catalog loaded: {len(catalog)} items.")
        
        work_sku = "sku.orca.pro.01"
        work_item = next((item for item in catalog if item["sku"] == work_sku), None)
        
        if not work_item:
            print("FAILED: Work persona SKU not found in catalog.")
            return False
        
        # We don't assume it's locked, but we want to test activation
        print(f"Work Persona Status: {'Unlocked' if work_item['unlocked'] else 'Locked'}")
    except Exception as e:
        print(f"FAILED: Could not fetch catalog: {e}")
        return False

    # 2. Activate Work Persona
    print(f"Activating SKU: {work_sku}...")
    try:
        res = requests.post(f"{RUNTIME_BASE}/runtime/persona/activate", json={"sku": work_sku})
        data = res.json()
        if not data.get("success"):
            print(f"FAILED: Activation returned failure: {data}")
            return False
        print("Activation successful via API.")
    except Exception as e:
        print(f"FAILED: Activation request failed: {e}")
        return False

    # 3. Verify Catalog Update
    try:
        res = requests.get(f"{RUNTIME_BASE}/runtime/persona/catalog")
        catalog = res.json()
        work_item = next((item for item in catalog if item["sku"] == work_sku), None)
        if not work_item or not work_item["unlocked"]:
            print("FAILED: Catalog still shows Work persona as locked after activation.")
            return False
        print("Catalog verified: Work persona is now Unlocked.")
    except Exception as e:
        print(f"FAILED: Catalog verification failed: {e}")
        return False

    # 4. Verify Persona List Update
    try:
        res = requests.get(f"{RUNTIME_BASE}/runtime/persona/list?cap_profile=enterprise")
        personas = res.json()
        work_persona = next((p for p in personas if p["id"] == "persona.work@0.1"), None)
        if not work_persona or work_persona["status"] != "UNLOCKED":
            print(f"FAILED: Persona list status for Work: {work_persona['status'] if work_persona else 'Not Found'}")
            return False
        print("Persona List verified: Work persona is UNLOCKED.")
    except Exception as e:
        print(f"FAILED: Persona list verification failed: {e}")
        return False

    print("\nPASS: Marketplace M9 functionality verified.")
    return True

if __name__ == "__main__":
    if verify_m9():
        exit(0)
    else:
        exit(1)
