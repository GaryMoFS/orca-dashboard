import json
import os
import sys
import argparse
from datetime import datetime

CATALOG_PATH = "orca/capabilities/catalog.json"
DOCS_DIR = "docs/capabilities"

def create_new_capability(cid, title, description):
    if not cid.startswith("cap."):
        cid = "cap." + cid
        
    print(f"Creating new capability: {cid}")
    
    # 1. Update catalog.json
    with open(CATALOG_PATH, "r") as f:
        catalog = json.load(f)
        
    if any(e["id"] == cid for e in catalog):
        print(f"ERROR: Capability {cid} already exists.")
        return
        
    entry = {
        "id": cid,
        "title": title,
        "description": description,
        "status": "idea",
        "inputs": [],
        "outputs": [],
        "tags": [],
        "persona_gates": ["pro"],
        "scripts": { "verify": [f"echo stub: {cid}"] },
        "docs": [f"docs/capabilities/{cid}.md"]
    }
    
    catalog.append(entry)
    
    with open(CATALOG_PATH, "w") as f:
        json.dump(catalog, f, indent=2)
        
    # 2. Create stub doc
    os.makedirs(DOCS_DIR, exist_ok=True)
    doc_path = os.path.join(DOCS_DIR, f"{cid}.md")
    with open(doc_path, "w") as f:
        f.write(f"# Capability: {title}\n\nID: {cid}\n\n## Purpose\n{description}\n\n## Spec\n- **Inputs**: \n- **Outputs**: \n\n## Verification\n- Run: `python tools/verify_capability_catalog.py` (checks catalog entry)\n")
        
    print(f"SUCCESS: Created capability {cid} and doc {doc_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a new ORCA capability skeleton.")
    parser.add_argument("id", help="Capability ID (e.g., txt_to_ifc)")
    parser.add_argument("--title", help="Human-readable title", default="New Capability")
    parser.add_argument("--desc", help="Short description", default="Description pending.")
    
    args = parser.parse_args()
    create_new_capability(args.id, args.title, args.desc)
