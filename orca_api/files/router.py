from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import os
import shutil
import hashlib
import time
import datetime
import json
from orca_api.events.router import manager

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    run_id: Optional[str] = Form(None)
):
    # 1. Determine Run ID / Target Dir
    if run_id:
        target_dir = f"runs/{run_id}/artifacts/uploads"
    else:
        # Fallback to general uploads if no run specified
        target_dir = f"runs/_uploads/{int(time.time())}"
        
    os.makedirs(target_dir, exist_ok=True)
    
    # 2. Sanitize Filename
    filename = os.path.basename(file.filename)
    if not filename or filename.startswith("."):
        filename = f"upload_{int(time.time())}.dat"
        
    file_path = os.path.join(target_dir, filename)
    
    # 3. Save File
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
         
    # 4. Compute Hash & Size
    sha256_hash = hashlib.sha256()
    file_size = 0
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256_hash.update(chunk)
            file_size += len(chunk)
            
    hex_digest = sha256_hash.hexdigest()
    
    # 5. Emit Event
    if run_id:
        evt = {
            "type": "artifact.written",
            "run_id": run_id,
            "kind": "upload",
            "path": file_path.replace("\\", "/"),
            "sha256": hex_digest,
            "bytes": file_size,
            "timestamp": time.time()
        }
        await manager.broadcast(json.dumps(evt))
        
    return {
        "status": "uploaded",
        "path": file_path.replace("\\", "/"),
        "sha256": hex_digest,
        "bytes": file_size
    }
