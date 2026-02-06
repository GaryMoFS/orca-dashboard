from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import aiohttp
import asyncio
import json
import os
import hashlib
import time

# Import shared resources (dirty import but fits "minimal edit" constraint)
from orca_api.events.router import manager, active_runs
from orca_api.llm_gateway.router import check_ollama

router = APIRouter()

class GenerateRequest(BaseModel):
    run_id: str
    prompt: str
    model: Optional[str] = None
    stream: bool = True

@router.post("/llm/generate")
async def generate_text(req: GenerateRequest):
    # 1. Validate Run
    if req.run_id not in active_runs:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run_events = active_runs[req.run_id]["events"]

    # 2. Determine Provider/Model
    provider_id = "stub"
    model = req.model
    
    ollama_status = await check_ollama(timeout=0.5)
    
    if ollama_status["active"] and ollama_status["models"]:
        provider_id = "ollama_local"
        if not model:
            model = ollama_status["models"][0] # Default to first
    else:
        # Fallback Stub
        model = "stub-v1"

    # 3. Log Request Event
    req_event = {
        "type": "llm.requested",
        "timestamp": time.time(),
        "provider_id": provider_id,
        "model": model,
        "prompt_sha256": hashlib.sha256(req.prompt.encode()).hexdigest(),
        "stream": req.stream
    }
    run_events.append(req_event)
    await manager.broadcast(json.dumps(req_event))

    full_text = ""
    error_msg = None

    # 4. Execute Generation
    try:
        if provider_id == "ollama_local":
            url = "http://localhost:11434/api/generate"
            payload = {"model": model, "prompt": req.prompt, "stream": req.stream}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        error_msg = f"Ollama Error: {resp.status}"
                    else:
                        if req.stream:
                            async for line in resp.content:
                                if line:
                                    try:
                                        chunk = json.loads(line)
                                        if "response" in chunk:
                                            text_chunk = chunk["response"]
                                            full_text += text_chunk
                                            # Optional: emit delta (can be noisy)
                                            # await manager.broadcast(json.dumps({"type": "llm.delta", "delta": text_chunk}))
                                    except:
                                        pass
                        else:
                            data = await resp.json()
                            full_text = data.get("response", "")
        else:
            # Stub Behavior
            full_text = f"STUB RESPONSE: {req.prompt[:20]}..."
            await asyncio.sleep(0.5) # Simulate work

    except Exception as e:
        error_msg = str(e)

    # 5. Handle Result
    if error_msg:
        err_event = {"type": "llm.error", "timestamp": time.time(), "message": error_msg}
        run_events.append(err_event)
        await manager.broadcast(json.dumps(err_event))
        return {"error": error_msg}

    # 6. Log Completion Event
    comp_event = {
        "type": "llm.completed", 
        "timestamp": time.time(),
        "provider_id": provider_id,
        "model": model,
        "output_sha256": hashlib.sha256(full_text.encode()).hexdigest(),
        "output_chars": len(full_text)
    }
    run_events.append(comp_event)
    await manager.broadcast(json.dumps(comp_event))

    # 7. Write Artifact
    artifact_dir = f"runs/{req.run_id}/artifacts"
    os.makedirs(artifact_dir, exist_ok=True)
    with open(f"{artifact_dir}/llm_output.txt", "w", encoding="utf-8") as f:
        f.write(full_text)

    return {
        "status": "completed",
        "provider": provider_id,
        "model": model,
        "output_preview": full_text[:50]
    }
