import os
import json
import uuid
import hashlib
import shutil
from datetime import datetime
from typing import List, Dict, Optional
from PIL import Image
import pytesseract

class Director:
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.state_root = os.path.join(workspace_root, "runtime", "director_state")
        self.events_file = os.path.join(self.state_root, "events.jsonl")
        self.quests_file = os.path.join(self.state_root, "quests.json")
        self.milestones_file = os.path.join(self.state_root, "milestones.json")
        self.issues_file = os.path.join(self.state_root, "issues.json")
        self.runs_dir = os.path.join(self.state_root, "runs")
        self.inbox_dir = os.path.join(self.state_root, "inbox")
        self.artifacts_dir = os.path.join(self.state_root, "artifacts")
        self.capabilities_path = os.path.join(workspace_root, "orca", "capabilities", "catalog.json")
        
        os.makedirs(self.runs_dir, exist_ok=True)
        os.makedirs(self.inbox_dir, exist_ok=True)
        os.makedirs(self.artifacts_dir, exist_ok=True)
        
        self._ensure_files()
        self.on_event_callback = None

    def _ensure_files(self):
        if not os.path.exists(self.events_file):
            with open(self.events_file, "w") as f:
                pass
        if not os.path.exists(self.quests_file):
            with open(self.quests_file, "w") as f:
                json.dump({"quests": [], "active": [], "next": [], "later": []}, f)
        
        if not os.path.exists(self.milestones_file):
            initial_milestones = {
                "milestones": [
                    {"id": "q1", "title": "Q1: Director Foundation", "status": "done", "order": 1, "updated_ts": datetime.now().isoformat()},
                    {"id": "q2", "title": "Q2: Director Inbox", "status": "done", "order": 2, "updated_ts": datetime.now().isoformat()},
                    {"id": "q3", "title": "Q3: Quest Engine", "status": "done", "order": 3, "updated_ts": datetime.now().isoformat()},
                    {"id": "q4", "title": "Q4: Doc Discipline", "status": "done", "order": 4, "updated_ts": datetime.now().isoformat()},
                    {"id": "m11", "title": "M11: Director Flight Recorder", "status": "done", "order": 5, "updated_ts": datetime.now().isoformat()},
                    {"id": "m12", "title": "M12: Capability Trails", "status": "done", "order": 6, "updated_ts": datetime.now().isoformat()},
                    {"id": "m13", "title": "M13: Progress Dashboard", "status": "in_progress", "order": 7, "updated_ts": datetime.now().isoformat()}
                ]
            }
            with open(self.milestones_file, "w") as f:
                json.dump(initial_milestones, f, indent=2)
                
        if not os.path.exists(self.issues_file):
            with open(self.issues_file, "w") as f:
                json.dump({"issues": []}, f, indent=2)

    def set_on_event(self, callback):
        self.on_event_callback = callback

    def append_event(self, type: str, source: str, payload: Dict = None, severity: str = "info") -> Dict:
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "type": type,
            "source": source,
            "payload": payload or {},
            "severity": severity
        }
        with open(self.events_file, "a") as f:
            f.write(json.dumps(event) + "\n")
        
        if self.on_event_callback:
            try:
                self.on_event_callback(event)
            except: pass
        return event

    def get_state(self) -> Dict:
        # Calculate counts
        inbox_count = len([n for n in os.listdir(self.inbox_dir) if os.path.isdir(os.path.join(self.inbox_dir, n))])
        runs_count = len([n for n in os.listdir(self.runs_dir) if os.path.isfile(os.path.join(self.runs_dir, n))])
        
        try:
            with open(self.quests_file, "r") as f:
                quests_data = json.load(f)
                quests_count = len(quests_data.get("quests", []))
        except:
            quests_count = 0
        
        # Get last event ts
        last_ts = None
        try:
            with open(self.events_file, "rb") as f:
                f.seek(0, os.SEEK_END)
                if f.tell() > 0:
                    f.seek(-2, os.SEEK_END) # skip last newline
                    while f.read(1) != b'\n':
                        if f.tell() == 1:
                            f.seek(0)
                            break
                        f.seek(-2, os.SEEK_CUR)
                    last_line = f.readline().decode()
                    last_ts = json.loads(last_line).get("timestamp")
        except: pass

        return {
            "status": "ready",
            "active_quest_id": None,
            "counts": {
                "inbox": inbox_count,
                "quests": quests_count,
                "runs": runs_count
            },
            "last_event_ts": last_ts
        }

    def list_events(self, limit: int = 50) -> List[Dict]:
        events = []
        try:
            with open(self.events_file, "r") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    events.append(json.loads(line))
        except: pass
        return events

    # --- Progress Dashboard (M13) ---

    def get_progress_snapshot(self) -> Dict:
        with open(self.milestones_file, "r") as f:
            milestones = json.load(f)
        with open(self.issues_file, "r") as f:
            issues = json.load(f)
        
        quests = self.get_quests()
        capabilities = self.get_capability_catalog()
        
        return {
            "director_state": self.get_state(),
            "milestones": milestones["milestones"],
            "issues": issues["issues"],
            "quests_summary": {
                "active": len(quests["active"]),
                "next": len(quests["next"]),
                "later": len(quests["later"]),
                "total": len(quests["quests"])
            },
            "capabilities_summary": capabilities["counts"]
        }

    def create_issue(self, title: str, severity: str, area: str = None, links: Dict = None) -> Dict:
        issue_id = f"issue_{str(uuid.uuid4())[:8]}"
        issue = {
            "id": issue_id,
            "title": title,
            "status": "open",
            "severity": severity,
            "area": area,
            "links": links or {},
            "created_ts": datetime.now().isoformat(),
            "updated_ts": datetime.now().isoformat()
        }
        
        with open(self.issues_file, "r") as f:
            data = json.load(f)
        data["issues"].append(issue)
        with open(self.issues_file, "w") as f:
            json.dump(data, f, indent=2)
            
        self.append_event("issue.created", "director", {"issue_id": issue_id, "severity": severity})
        return issue

    def set_issue_status(self, issue_id: str, status: str) -> Dict:
        with open(self.issues_file, "r") as f:
            data = json.load(f)
        
        found = False
        for issue in data["issues"]:
            if issue["id"] == issue_id:
                issue["status"] = status
                issue["updated_ts"] = datetime.now().isoformat()
                found = True
                break
        
        if not found:
            raise ValueError(f"Issue {issue_id} not found")
            
        with open(self.issues_file, "w") as f:
            json.dump(data, f, indent=2)
            
        self.append_event("issue.status_changed", "director", {"issue_id": issue_id, "status": status})
        return {"success": True, "issue_id": issue_id, "status": status}

    def set_milestone_status(self, milestone_id: str, status: str) -> Dict:
        with open(self.milestones_file, "r") as f:
            data = json.load(f)
        
        found = False
        for m in data["milestones"]:
            if m["id"] == milestone_id:
                m["status"] = status
                m["updated_ts"] = datetime.now().isoformat()
                found = True
                break
        
        if not found:
            raise ValueError(f"Milestone {milestone_id} not found")
            
        with open(self.milestones_file, "w") as f:
            json.dump(data, f, indent=2)
            
        self.append_event("milestone.status_changed", "director", {"milestone_id": milestone_id, "status": status})
        return {"success": True, "milestone_id": milestone_id, "status": status}

    # --- Inbox Operations ---

    def ingest_to_inbox(self, filename: str, content: bytes) -> Dict:
        inbox_id = str(uuid.uuid4())
        bundle_path = os.path.join(self.inbox_dir, inbox_id)
        original_path = os.path.join(bundle_path, "original")
        derived_path = os.path.join(bundle_path, "derived")
        
        os.makedirs(original_path, exist_ok=True)
        os.makedirs(derived_path, exist_ok=True)
        
        dest_file = os.path.join(original_path, filename)
        with open(dest_file, "wb") as f:
            f.write(content)
            
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Manifest
        manifest = {
            "inbox_id": inbox_id,
            "files": [{
                "name": filename,
                "hash_sha256": file_hash,
                "size_bytes": len(content)
            }]
        }
        with open(os.path.join(bundle_path, "manifest.json"), "w") as f:
            json.dump(manifest, f, indent=2)
            
        # Meta
        ext = os.path.splitext(filename)[1].lower()
        item_type = "image" if ext in ['.jpg', '.jpeg', '.png', '.bmp'] else "unknown"
        
        meta = {
            "id": inbox_id,
            "type": item_type,
            "created_ts": datetime.now().isoformat(),
            "filenames": [filename],
            "artifacts": {}
        }
        
        self.append_event("inbox.created", "director", {"inbox_id": inbox_id, "type": item_type})
        
        # OCR / Derived
        if item_type == "image":
            # Preview
            try:
                with Image.open(dest_file) as img:
                    img.thumbnail((800, 800))
                    img.save(os.path.join(derived_path, "preview.jpg"), "JPEG")
                    meta["artifacts"]["preview"] = "derived/preview.jpg"
            except Exception as e:
                print(f"Preview gen failed: {e}")
                
            # OCR
            ocr_text = "(ocr unavailable)"
            try:
                ocr_text = pytesseract.image_to_string(Image.open(dest_file))
            except Exception as e:
                print(f"OCR failed: {e}")
                
            with open(os.path.join(derived_path, "ocr.txt"), "w", encoding="utf-8") as f:
                f.write(ocr_text)
            meta["artifacts"]["ocr"] = "derived/ocr.txt"
            
            self.append_event("inbox.derived_written", "director", {"inbox_id": inbox_id, "artifacts": list(meta["artifacts"].keys())})
            
        with open(os.path.join(bundle_path, "meta.json"), "w") as f:
            json.dump(meta, f, indent=2)
            
        return meta

    def list_inbox(self) -> List[Dict]:
        items = []
        if not os.path.exists(self.inbox_dir): return []
        for entry in os.listdir(self.inbox_dir):
            meta_path = os.path.join(self.inbox_dir, entry, "meta.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r") as f:
                        items.append(json.load(f))
                except: pass
        return sorted(items, key=lambda x: x.get("created_ts", ""), reverse=True)

    def get_inbox_artifact(self, inbox_id: str, artifact_path: str) -> Optional[bytes]:
        # Safety check for path traversal
        if ".." in artifact_path or artifact_path.startswith("/") or artifact_path.startswith("\\"):
            return None
        full_path = os.path.join(self.inbox_dir, inbox_id, artifact_path)
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                return f.read()
        return None

    def get_inbox_original(self, inbox_id: str, filename: str) -> Optional[bytes]:
        full_path = os.path.join(self.inbox_dir, inbox_id, "original", filename)
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                return f.read()
        return None

    # --- Quest Engine ---

    def create_quest_from_inbox(self, inbox_id: str, title: str = None, acceptance: str = None) -> Dict:
        with open(self.quests_file, "r") as f:
            quests_data = json.load(f)
            
        quest_id = str(uuid.uuid4())
        quest = {
            "id": quest_id,
            "title": title or f"Quest from {inbox_id[:8]}",
            "status": "later",
            "created_ts": datetime.now().isoformat(),
            "source_inbox_id": inbox_id,
            "acceptance": acceptance or "(No acceptance criteria specified)",
            "links": {"ledger": None, "story": None},
            "runs": []
        }
        
        quests_data["quests"].append(quest)
        quests_data["later"].append(quest_id)
        
        with open(self.quests_file, "w") as f:
            json.dump(quests_data, f, indent=2)
            
        self.append_event("quest.created", "director", {"quest_id": quest_id, "source_inbox_id": inbox_id})
        return quest

    def set_quest_status(self, quest_id: str, status: str) -> Dict:
        if status not in ["active", "next", "later"]:
            raise ValueError("Invalid quest status")
            
        with open(self.quests_file, "r") as f:
            quests_data = json.load(f)
            
        # Remove from old status lists
        for s in ["active", "next", "later"]:
            if quest_id in quests_data[s]:
                quests_data[s].remove(quest_id)
        
        # Add to new status list
        quests_data[status].append(quest_id)
        
        # Update quest object
        for q in quests_data["quests"]:
            if q["id"] == quest_id:
                q["status"] = status
                break
                
        with open(self.quests_file, "w") as f:
            json.dump(quests_data, f, indent=2)
            
        self.append_event("quest.status_changed", "director", {"quest_id": quest_id, "status": status})
        return {"success": True, "quest_id": quest_id, "status": status}

    def get_quests(self) -> Dict:
        if not os.path.exists(self.quests_file):
            return {"quests": [], "active": [], "next": [], "later": []}
        with open(self.quests_file, "r") as f:
            return json.load(f)

    # --- Capability Trails ---

    def get_capability_catalog(self) -> Dict:
        if not os.path.exists(self.capabilities_path):
            return {"catalog": [], "counts": {}}
            
        with open(self.capabilities_path, "r") as f:
            catalog = json.load(f)
            
        counts = {}
        for entry in catalog:
            s = entry.get("status", "unknown")
            counts[s] = counts.get(s, 0) + 1
            
        return {"catalog": catalog, "counts": counts}

    def get_capability_actions(self) -> List[Dict]:
        catalog_data = self.get_capability_catalog()
        caps = []
        for cap in catalog_data["catalog"]:
            if "actions" in cap:
                caps.append({
                    "id": cap["id"],
                    "title": cap["title"],
                    "actions": cap["actions"]
                })
        return caps

    def run_capability(self, capability_id: str, action_id: str, params: Dict) -> Dict:
        # 1. Start Logging
        run_id = f"run_{str(uuid.uuid4())[:8]}"
        self.append_event("capability.run_requested", "director", {"run_id": run_id, "capability_id": capability_id, "action_id": action_id})
        
        # 2. Find Action
        catalog_data = self.get_capability_catalog()
        target_cap = next((c for c in catalog_data["catalog"] if c["id"] == capability_id), None)
        if not target_cap:
            raise ValueError(f"Capability {capability_id} not found")
            
        action = next((a for a in target_cap.get("actions", []) if a["id"] == action_id), None)
        if not action:
            raise ValueError(f"Action {action_id} not found for {capability_id}")
            
        # 3. Validate Entrypoint
        entrypoint = action["entrypoint"]
        if not entrypoint.startswith("python:"):
            raise ValueError(f"Unsupported entrypoint: {entrypoint}")
            
        # 4. Execute (In-Process for Demo)
        try:
            self.append_event("capability.run_started", "director", {"run_id": run_id})
            
            # Format: python:module.path:function_name
            _, mod_path, func_name = entrypoint.split(":")
            
            import importlib
            module = importlib.import_module(mod_path)
            func = getattr(module, func_name)
            
            # Create artifact dir
            out_dir = os.path.join(self.artifacts_dir, capability_id, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{run_id}")
            os.makedirs(out_dir, exist_ok=True)
            
            # Run it
            result = func(out_dir=out_dir, **params)
            
            # Record receipt
            receipt = result["receipt"]
            receipt["run_id"] = run_id # Override with director's run_id
            receipt_path = self.record_run_receipt(receipt)
            
            self.append_event("capability.run_completed", "director", {
                "run_id": run_id, 
                "status": "success",
                "artifact_dir": out_dir
            })
            
            return {
                "run_id": run_id,
                "status": "success",
                "receipt_id": receipt["receipt_id"],
                "artifact_dir": out_dir
            }
            
        except Exception as e:
            self.append_event("capability.run_failed", "director", {"run_id": run_id, "error": str(e)}, severity="error")
            return {"run_id": run_id, "status": "failed", "error": str(e)}

    def emit_capability_test_receipt(self, capability_id: str) -> Dict:
        receipt_id = f"test_{str(uuid.uuid4())[:8]}"
        receipt = {
            "receipt_id": receipt_id,
            "ts": datetime.now().isoformat(),
            "capability_id": capability_id,
            "status": "success",
            "inputs": ["test_input"],
            "outputs": ["test_output"],
            "command": "verify --test",
            "exit_code": 0,
            "artifacts": [f"test_artifact_{receipt_id}.txt"],
            "hashes": {"test_artifact": "sha256_placeholder"},
            "notes": "Automated test receipt for M12 validation."
        }
        
        receipt_path = os.path.join(self.artifacts_dir, f"receipt_{receipt_id}.json")
        with open(receipt_path, "w") as f:
            json.dump(receipt, f, indent=2)
            
        self.append_event("capability.receipt_written", "director", {"receipt_id": receipt_id, "capability_id": capability_id})
        return receipt

    # --- Run Receipts ---

    def record_run_receipt(self, receipt: Dict) -> str:
        run_id = receipt.get("run_id", str(uuid.uuid4()))
        receipt["run_id"] = run_id
        receipt["timestamp"] = receipt.get("timestamp", datetime.now().isoformat())
        
        file_path = os.path.join(self.runs_dir, f"{run_id}.json")
        with open(file_path, "w") as f:
            json.dump(receipt, f, indent=2)
            
        self.append_event("run.complete", "director", {"run_id": run_id, "status": receipt.get("status")})
        return run_id

    def list_runs(self) -> List[Dict]:
        runs = []
        for filename in os.listdir(self.runs_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.runs_dir, filename), "r") as f:
                        runs.append(json.load(f))
                except: pass
        return sorted(runs, key=lambda x: x.get("timestamp", ""), reverse=True)
