from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import aiohttp
import asyncio
import json
import os
import hashlib
import time
import datetime

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
    
    # 3b. Define Helper for Delta Emission
    async def emit_delta(delta_text: str):
        evt = {"type": "llm.delta", "provider_id": provider_id, "model": model, "delta": delta_text, "delta_chars": len(delta_text)}
        await manager.broadcast(json.dumps(evt))

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
                            buffer = ""
                            last_emit = time.time()
                            
                            async for line in resp.content:
                                if line:
                                    try:
                                        chunk = json.loads(line)
                                        if "response" in chunk:
                                            text_chunk = chunk["response"]
                                            full_text += text_chunk
                                            buffer += text_chunk
                                            
                                            # Emit if buffer large enough or time elapsed
                                            if len(buffer) > 20 or (time.time() - last_emit) > 0.1:
                                                await emit_delta(buffer)
                                                buffer = ""
                                                last_emit = time.time()
                                    except:
                                        pass
                            # Flush remaining buffer
                            if buffer:
                                await emit_delta(buffer)
                        else:
                            data = await resp.json()
                            full_text = data.get("response", "")
                            # For non-streaming, just emit one big delta so UI updates
                            await emit_delta(full_text)
        else:
            # Stub Behavior
            full_text = f"STUB RESPONSE: {req.prompt[:20]}..."
            # Simulate streaming
            chunk_size = 5
            for i in range(0, len(full_text), chunk_size):
                chunk = full_text[i:i+chunk_size]
                await emit_delta(chunk)
                await asyncio.sleep(0.05)

    except Exception as e:
        error_msg = str(e)

    # 5. Handle Result
    if error_msg:
        err_event = {"type": "llm.error", "timestamp": time.time(), "message": error_msg}
        run_events.append(err_event)
        await manager.broadcast(json.dumps(err_event))
        return {"error": error_msg}

    # 6. Log Completion Event
    output_hash = hashlib.sha256(full_text.encode()).hexdigest()
    prompt_hash = hashlib.sha256(req.prompt.encode()).hexdigest()
    
    comp_event = {
        "type": "llm.completed", 
        "timestamp": time.time(),
        "provider_id": provider_id,
        "model": model,
        "output_sha256": output_hash,
        "output_chars": len(full_text)
    }
    run_events.append(comp_event)
    await manager.broadcast(json.dumps(comp_event))

    # 7. Write Artifacts (Text + Meta)
    artifact_dir = f"runs/{req.run_id}/artifacts"
    os.makedirs(artifact_dir, exist_ok=True)
    
    # 7a. Text
    txt_path = f"{artifact_dir}/llm_output.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)
    
    # 7b. Meta JSON
    meta_json = {
        "run_id": req.run_id,
        "provider_id": provider_id,
        "model": model,
        "prompt_sha256": prompt_hash,
        "output_sha256": output_hash,
        "output_chars": len(full_text),
        "created_ts": datetime.datetime.utcnow().isoformat() + "Z"
    }
    with open(f"{artifact_dir}/llm_output.meta.json", "w", encoding="utf-8") as f:
        json.dump(meta_json, f, indent=2)

    # 8. Emit Artifact Written Event
    art_event = {
        "type": "artifact.written",
        "kind": "llm_output",
        "path": txt_path.replace("\\", "/"),
        "sha256": output_hash,
        "bytes": len(full_text.encode("utf-8"))
    }
    await manager.broadcast(json.dumps(art_event))

    return {
        "status": "completed",
        "provider": provider_id,
        "model": model,
        "output_path": txt_path.replace("\\", "/"),
        "output_sha256": output_hash,
        "output_chars": len(full_text)
    }
