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
