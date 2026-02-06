from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
import os
import uuid

router = APIRouter()

# Simple in-memory runs (REPLACE with DB later)
active_runs: Dict[str, dict] = {}
# Connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.post("/runs/start")
async def start_run():
    run_id = str(uuid.uuid4())
    active_runs[run_id] = {"status": "running", "events": []}
    await manager.broadcast(json.dumps({"type": "run_started", "run_id": run_id}))
    return {"run_id": run_id, "status": "started"}

@router.post("/runs/{run_id}/close")
async def close_run(run_id: str):
    if run_id in active_runs:
        active_runs[run_id]["status"] = "closed"
        # Dump to JSONL
        os.makedirs("runs", exist_ok=True)
        with open(f"runs/{run_id}_events.jsonl", "w") as f:
            for evt in active_runs[run_id]["events"]:
                f.write(json.dumps(evt) + "\n")
        
        await manager.broadcast(json.dumps({"type": "run_closed", "run_id": run_id}))
        return {"status": "closed"}
    return {"error": "Run not found"}

@router.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo or process
            await manager.broadcast(f"Server received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
