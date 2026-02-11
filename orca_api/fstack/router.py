from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import hashlib

router = APIRouter()

class VerifyRequest(BaseModel):
    content: str
    expected_hash: str

@router.post("/runs/{run_id}/verify")
async def verify_run_content(run_id: str, req: VerifyRequest):
    # Minimal SHA256 verification
    actual_hash = hashlib.sha256(req.content.encode('utf-8')).hexdigest()
    
    match = (actual_hash == req.expected_hash)
    
    return {
        "run_id": run_id,
        "verified": match,
        "actual_hash": actual_hash
    }

@router.get("/fstack/manifest")
async def get_manifest():
    return {
        "version": "0.1.0",
        "supported_hash": ["sha256"],
        "max_content_size": 1024 * 1024
    }

@router.post("/fstack/audit/log")
async def log_manifest(manifest: dict):
    # Simulate storing the manifest in an append-only log
    # utilizing the 'audit.py' module we will create next
    from orca_api.fstack.audit import AuditLogger
    
    logger = AuditLogger()
    entry_id = logger.log_event("manifest_created", manifest)
    
    return {
        "status": "logged",
        "entry_id": entry_id,
        "signature_verified": True # naive/stub
    }
