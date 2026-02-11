import os
import json
import time
import uuid

class AuditLogger:
    def __init__(self, log_path="files/audit_log.jsonl"):
        self.log_path = log_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log_event(self, event_type: str, payload: dict, actor: str = "system"):
        """Append an event to the audit log."""
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "type": event_type,
            "actor": actor,
            "payload": payload
        }
        
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
            
        return entry["id"]

    def get_trail(self, limit: int = 50):
        """Retrieve recent audit logs."""
        trail = []
        if not os.path.exists(self.log_path):
            return trail
            
        with open(self.log_path, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        trail.append(json.loads(line))
                    except:
                        pass
        
        return trail[-limit:]

def export_audit_bundle(output_path: str):
    """Export the audit log as a verified bundle (stub)."""
    # In a real system, this would sign the entire log file chain
    logger = AuditLogger()
    trail = logger.get_trail(limit=1000)
    
    bundle = {
        "exported_at": time.time(),
        "record_count": len(trail),
        "records": trail,
        "bundle_signature": "simulated_signature_of_all_records"
    }
    
    with open(output_path, "w") as f:
        json.dump(bundle, f, indent=2)
    
    return output_path
