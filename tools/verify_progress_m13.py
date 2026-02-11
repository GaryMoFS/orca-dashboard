import requests
import json
import os

RUNTIME_BASE = "http://127.0.0.1:7010"

def verify_m13():
    print("--- Verifying M13 Progress Dashboard ---")
    
    # 1. Check schemas
    schema_dir = "orca/engine/schemas"
    milestone_schema = os.path.join(schema_dir, "orca.director.milestones@0.1.schema.json")
    issue_schema = os.path.join(schema_dir, "orca.director.issues@0.1.schema.json")
    
    if os.path.exists(milestone_schema) and os.path.exists(issue_schema):
        print("PASS: Progress schemas exist.")
    else:
        print("FAIL: Missing progress schemas.")

    # 2. GET /api/director/progress
    print("Fetching progress snapshot...")
    try:
        r = requests.get(f"{RUNTIME_BASE}/api/director/progress")
        r.raise_for_status()
        data = r.json()
        if "milestones" in data and "issues" in data and "quests_summary" in data:
            print("PASS: Combined progress snapshot valid.")
        else:
            print(f"FAIL: Snapshot missing keys. Found: {data.keys()}")
    except Exception as e:
        print(f"FAIL: Snapshot fetch failed: {e}")
        return

    # 3. Create Issue
    print("Creating test issue...")
    try:
        payload = {
            "title": "M13 Verification Edge Case",
            "severity": "high",
            "area": "Director"
        }
        r = requests.post(f"{RUNTIME_BASE}/api/director/issues/create", json=payload)
        r.raise_for_status()
        issue = r.json()
        issue_id = issue["id"]
        print(f"PASS: Created issue: {issue_id}")
        
        # 4. Set status
        print("Updating issue status...")
        r = requests.post(f"{RUNTIME_BASE}/api/director/issues/set_status", json={"id": issue_id, "status": "in_progress"})
        r.raise_for_status()
        print("PASS: Set issue status to in_progress")
        
        # 5. Confirm event
        print("Checking flight recorder for events...")
        r = requests.get(f"{RUNTIME_BASE}/api/director/events?limit=5")
        r.raise_for_status()
        events = r.json()
        types = [e["type"] for e in events]
        if "issue.created" in types and "issue.status_changed" in types:
            print("PASS: Progress events logged.")
        else:
            print(f"FAIL: Missing events. Found: {types}")
            
    except Exception as e:
        print(f"FAIL: Issue lifecycle test failed: {e}")

if __name__ == "__main__":
    verify_m13()
