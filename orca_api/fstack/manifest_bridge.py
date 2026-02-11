import hashlib
import json
import time
import uuid
from typing import Dict, Any, Optional

class ManifestBuilder:
    def __init__(self, actor_id: str = "fspu-core-v1"):
        self.actor_id = actor_id
        self.manifest = {
            "version": "1.0.0",
            "id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "actor": actor_id,
            "artifacts": [],
            "provenance": {},
            "signature": None
        }

    def add_artifact(self, name: str, content: bytes, mime_type: str = "application/octet-stream"):
        """Add a file/artifact to the manifest with its hash."""
        sha256 = hashlib.sha256(content).hexdigest()
        self.manifest["artifacts"].append({
            "name": name,
            "hash": sha256,
            "algo": "sha256",
            "size": len(content),
            "mime_type": mime_type
        })
        return sha256

    def set_provenance(self, source_task_id: str, methodology: str, params: Dict[str, Any]):
        """Link this manifest to a specific task and methodology."""
        self.manifest["provenance"] = {
            "source_task_id": source_task_id,
            "methodology": methodology,
            "params": params
        }

    def sign(self, private_key: str = "simulated_key"):
        """
        Sign the manifest content (excluding signature field).
        For now, this is a simulation.
        """
        # Create a canonical representation of the data to sign
        data_to_sign = json.dumps({k:v for k,v in self.manifest.items() if k != "signature"}, sort_keys=True)
        
        # Simulate signing by hashing the content + key
        signature = hashlib.sha256(f"{data_to_sign}{private_key}".encode("utf-8")).hexdigest()
        
        self.manifest["signature"] = {
            "value": signature,
            "algo": "fstack-sim-v1",
            "key_id": "dev-key-001"
        }
        
    def export(self) -> Dict[str, Any]:
        """Return the final manifest dictionary."""
        if not self.manifest["signature"]:
            self.sign()
        return self.manifest
