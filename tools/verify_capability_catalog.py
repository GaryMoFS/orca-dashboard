import json
import os
import re
import jsonschema

CATALOG_PATH = "orca/capabilities/catalog.json"
SCHEMA_PATH = "orca/engine/schemas/orca.capability.spec@0.1.schema.json"

def verify_catalog():
    print("--- Verifying Capability Catalog ---")
    
    # 1. Load Schema
    if not os.path.exists(SCHEMA_PATH):
        print(f"FAIL: Schema not found at {SCHEMA_PATH}")
        return False
    
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)
        
    # 2. Load Catalog
    if not os.path.exists(CATALOG_PATH):
        print(f"FAIL: Catalog not found at {CATALOG_PATH}")
        return False
        
    with open(CATALOG_PATH, "r") as f:
        catalog = json.load(f)
        
    # 3. Validate each entry
    seen_ids = set()
    fail = False
    
    for entry in catalog:
        cid = entry.get("id", "??")
        try:
            jsonschema.validate(instance=entry, schema=schema)
            
            # Additional checks
            if cid in seen_ids:
                print(f"FAIL: Duplicate ID: {cid}")
                fail = True
            seen_ids.add(cid)
            
            # Check script existence or stub
            scripts = entry.get("scripts", {}).get("verify", [])
            if not scripts:
                print(f"FAIL: {cid} must have at least one verify script.")
                fail = True
                
        except Exception as e:
            print(f"FAIL: {cid} validation failed: {e}")
            fail = True
            
    # 4. Cross-check with Docs (Best effort regex)
    print("Cross-checking mentions in docs...")
    doc_paths = ["Antigrav Change Ledger.md", "investor_demo_story.md"]
    for dp in doc_paths:
        if os.path.exists(dp):
            with open(dp, "r") as f:
                content = f.read()
                mentions = re.findall(r'cap\.[a-z0-9_]+', content)
                for m in mentions:
                    if m not in seen_ids:
                        print(f"WARNING: Mention of '{m}' in {dp} not found in catalog.json")

    if not fail:
        print("PASS: Capability Catalog is valid.")
        return True
    else:
        print("FAIL: Capability Catalog validation issues found.")
        return False

if __name__ == "__main__":
    if verify_catalog():
        exit(0)
    else:
        exit(1)
