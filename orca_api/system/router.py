from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
from pydantic import BaseModel, Field
import datetime
import time
import os
import json
import asyncio
from orca_api.events.router import manager

router = APIRouter()

SYSTEM_RUNS_DIR = "runs/_system"
LOCATION_FILE = f"{SYSTEM_RUNS_DIR}/location.json"

class LocationUpdate(BaseModel):
    lat: float = Field(..., description="Latitude rounded to 2 decimals")
    lon: float = Field(..., description="Longitude rounded to 2 decimals")
    accuracy_m: float
    source: str
    run_id: Optional[str] = None

@router.post("/location")
async def update_location(loc: LocationUpdate):
    # Enforce Coarse Precision (Server-side safety)
    lat_safe = round(loc.lat, 2)
    lon_safe = round(loc.lon, 2)
    
    # Save to disk
    os.makedirs(SYSTEM_RUNS_DIR, exist_ok=True)
    
    start_ts = datetime.datetime.utcnow().isoformat() + "Z"
    
    data = {
        "lat": lat_safe,
        "lon": lon_safe,
        "accuracy_m": loc.accuracy_m,
        "source": loc.source,
        "updated_ts": start_ts
    }
    
    # Global save
    with open(LOCATION_FILE, "w") as f:
        json.dump(data, f)
        
    # Also save to run if provided
    if loc.run_id:
        run_dir = f"runs/{loc.run_id}/artifacts"
        os.makedirs(run_dir, exist_ok=True)
        with open(f"{run_dir}/location.json", "w") as f:
            json.dump(data, f)
            
        # Emit artifact event
        await manager.broadcast(json.dumps({
            "type": "artifact.written",
            "run_id": loc.run_id,
            "kind": "location",
            "path": f"{run_dir}/location.json"
        }))

    # Emit system event
    await manager.broadcast(json.dumps({
        "type": "system.location_updated",
        "data": data
    }))
    
    return {"status": "updated", "location": data}

@router.get("/location")
async def get_location():
    if os.path.exists(LOCATION_FILE):
        try:
            with open(LOCATION_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"enabled": False}

@router.get("/now")
async def get_system_time(run_id: Optional[str] = Query(None)):
    now = datetime.datetime.now().astimezone()
    iso = now.isoformat()
    return {
        "iso": iso,
        "timestamp": now.timestamp(),
        "human": now.strftime("%Y-%m-%d %H:%M:%S")
    }
