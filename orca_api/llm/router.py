from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import aiohttp
import asyncio
import requests
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
    temperature: Optional[float] = 0.7

@router.get("/llm/models")
async def list_models():
    status = await check_ollama()
    return {
        "models": status.get("models", []),
        "ollama": status.get("models_ollama", []),
        "lm_studio": status.get("models_lm_studio", [])
    }

# Non-streaming sync generator (Unified)
def generate_ollama_sync(model: str, prompt: str, temperature: float = 0.7):
    # Try LM Studio (1234)
    try:
        url = "http://localhost:1234/v1/chat/completions"
        payload = {
            "model": model or "local-model",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "stream": False
        }
        resp = requests.post(url, json=payload, timeout=120)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
    except: pass

    # Try Ollama (11434)
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model or "llama3",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature}
    }
    try:
        resp = requests.post(url, json=payload, timeout=120) 
        if resp.status_code == 200:
             return resp.json().get("response", "")
        else:
             return f"LLM Error: {resp.status_code} - {resp.text}"
    except Exception as e:
        return f"Connection Error: {e}"

@router.post("/llm/generate")
async def generate_text(req: GenerateRequest):
    # 1. Validate Run
    if req.run_id not in active_runs:
         # Auto-create run if needed for robustness
         active_runs[req.run_id] = {"events": [], "created": time.time(), "id": req.run_id}
    
    run_events = active_runs[req.run_id]["events"]

    # 2. Determine Provider/Model
    provider_id = "ollama_local"
    model = req.model
    if not model:
        status = await check_ollama()
        if status["active"] and status["models"]:
            model = status["models"][0]
        else:
            provider_id = "stub"
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
    
    async def emit_delta(delta_text: str):
        evt = {"type": "llm.delta", "provider_id": provider_id, "model": model, "delta": delta_text, "delta_chars": len(delta_text), "run_id": req.run_id}
        await manager.broadcast(json.dumps(evt))

    # 4. Execute Generation via Requests (Threaded)
    try:
        if provider_id == "ollama_local":
            # Run sync request in thread
            # Handle empty prompt
            p_text = req.prompt or ""
            full_text = await asyncio.to_thread(generate_ollama_sync, model, p_text, 0.7)
            
            if full_text.startswith("Ollama Error") or full_text.startswith("Connection Error"):
                 error_msg = full_text
            else:
                 # Emit as one big delta since we disabled streaming
                 await emit_delta(full_text)
        else:
            # Stub Behavior
            full_text = f"STUB RESPONSE: {req.prompt[:20]}..."
            await emit_delta(full_text)

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

    # 7. Write Artifacts
    artifact_dir = f"runs/{req.run_id}/artifacts"
    os.makedirs(artifact_dir, exist_ok=True)
    
    # 7a. Text
    txt_path = f"{artifact_dir}/llm_output.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    # 7b. Meta JSON
    prompt_hash = hashlib.sha256(req.prompt.encode()).hexdigest()
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

class ChatRequest(BaseModel):
    run_id: str
    message: Optional[str] = None
    model: Optional[str] = None
    reset: bool = False

@router.post("/llm/chat")
async def chat_endpoint(req: ChatRequest):
    # 1. Validate Run
    if req.run_id not in active_runs:
        raise HTTPException(status_code=404, detail="Run not found")
        
    artifact_dir = f"runs/{req.run_id}/artifacts"
    os.makedirs(artifact_dir, exist_ok=True)
    conv_path = f"{artifact_dir}/conversation.json"
    
    # 2. Handle Reset
    if req.reset:
        with open(conv_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        await manager.broadcast(json.dumps({"type": "chat.reset", "run_id": req.run_id}))
        return {"status": "reset", "conversation_path": conv_path}

    if not req.message:
         raise HTTPException(status_code=400, detail="Message required unless reset=True")

    # 3. Load Conversation
    history = []
    if os.path.exists(conv_path):
        try:
            with open(conv_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = []
            
    # 4. Append User Message
    user_msg = {
        "role": "user", 
        "content": req.message, 
        "ts": datetime.datetime.utcnow().isoformat() + "Z"
    }
    history.append(user_msg)
    
    # Emit user event
    await manager.broadcast(json.dumps({
        "type": "chat.user_message",
        "chars": len(req.message),
        "prompt_sha256": hashlib.sha256(req.message.encode()).hexdigest()
    }))

    # 5. Build Transcript
    now = datetime.datetime.now().astimezone()
    time_str = f"{now.isoformat()} ({now.strftime('%A')}, {now.tzname() or 'UTC'})"
    
    prompt_text = f"SYSTEM: Current local time is {time_str}. You are ORCA Control. Helpful and accurate interaction.\n\n"
    
    # Optional Location Injection
    if os.environ.get("ORCA_ALLOW_LOCATION_IN_PROMPT") == "1":
        # Check for system location
        loc_file = "runs/_system/location.json"
        if os.path.exists(loc_file):
            try:
                with open(loc_file, "r") as f:
                    loc_data = json.load(f)
                    if "lat" in loc_data:
                        prompt_text += f"SYSTEM: Approximate user location (coarse) lat={loc_data['lat']}, lon={loc_data['lon']}.\n"
            except:
                pass

    for msg in history[-10:]: # Context window heuristic
        role = "USER" if msg["role"] == "user" else "ASSISTANT"
        prompt_text += f"{role}: {msg['content']}\n"
    prompt_text += "ASSISTANT:"

    # 6. Delegate to Generate Logic (Reuse by internal call)
    gen_req = GenerateRequest(
        run_id=req.run_id,
        prompt=prompt_text,
        model=req.model,
        stream=True
    )
    
    # We await the generation. The generate_text function emits llm.delta/llm.completed.
    # The UI will see these and update the "current assistant bubble".
    result = await generate_text(gen_req)
    
    if "error" in result:
        return result
        
    assistant_text = ""
    
    # Read back the generated text
    with open(f"{artifact_dir}/llm_output.txt", "r", encoding="utf-8") as f:
        assistant_text = f.read()

    # 7. Append Assistant Message
    asst_msg = {
        "role": "assistant",
        "content": assistant_text,
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
        "provider_id": result["provider"],
        "model": result["model"]
    }
    history.append(asst_msg)
    
    # 8. Save Conversation
    with open(conv_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
        
    # 9. Emit Chat Specific Events
    await manager.broadcast(json.dumps({
        "type": "chat.assistant_message",
        "chars": len(assistant_text),
        "output_sha256": result["output_sha256"]
    }))
    
    # Emit artifact event for conversation
    await manager.broadcast(json.dumps({
        "type": "artifact.written",
        "kind": "conversation",
        "path": conv_path.replace("\\", "/"),
        "sha256": hashlib.sha256(json.dumps(history).encode()).hexdigest(),
        "bytes": len(json.dumps(history))
    }))
    
    return {
        "run_id": req.run_id,
        "provider_id": result["provider"],
        "model": result["model"],
        "assistant_text": assistant_text,
        "conversation_path": conv_path.replace("\\", "/")
    }
