import asyncio
import os
import uvicorn
import httpx
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="ORCA Runtime", version="M1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import orca_runtime.ifc_gen as ifc_gen
import json
from orca_runtime.gpu_orchestrator import GPUOrchestrator, ModelType
from orca_runtime.providers import ProviderRegistry
from fastapi import WebSocket, WebSocketDisconnect

registry = ProviderRegistry()

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
            try:
                await connection.send_text(message)
            except: pass

manager = ConnectionManager()

# --- Configuration ---
# --- Configuration Persistence ---
CONFIG_FILE = "orca_config.json"

class Config(BaseModel):
    chat_mode: str = "offline"   # offline, cloud, hybrid
    tts_mode: str = "offline"    # offline, cloud, hybrid
    voice_local: str = "tara"
    voice_cloud: str = "placeholder"
    llm_provider: str = "ollama" # DEFAULT for CHAT
    llm_model: str = "llama3:latest" # Added for sticky settings
    tts_provider: str = "lm_studio"   # Ecosystem provider host for TTS model selection
    tts_model: str = "default" # Model for TTS (if applicable)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                # Backward compatibility: older builds stored "orpheus" as TTS provider.
                if data.get("tts_provider") == "orpheus":
                    fallback = data.get("llm_provider", "lm_studio")
                    data["tts_provider"] = fallback if fallback in {"ollama", "lm_studio"} else "lm_studio"
                return Config(**data)
        except: pass
    return Config()

def save_config(cfg: Config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg.dict(), f, indent=2)

runtime_config = load_config()
gpu_mgr = GPUOrchestrator()

# --- Adapters ---

# Local Chat Adapters
OLLAMA_BASE_URL = "http://127.0.0.1:11434/api"
LM_STUDIO_BASE_URL = "http://127.0.0.1:1234/v1"

# Local TTS Adapter (Orpheus)
ORPHEUS_URL = "http://127.0.0.1:5005/v1/audio/speech"
ORPHEUS_VOICES_URL = "http://127.0.0.1:5005/voices"
ORPHEUS_HEALTH_URL = "http://127.0.0.1:5005/health"

async def call_llm_json(text: str):
    provider = runtime_config.llm_provider
    
    # CASE A: OLLAMA (Native JSON mode)
    if provider == "ollama":
        schema = """
        {
          "project_name": "string",
          "levels": [ { "name": "string", "elevation": float } ]
        }
        """
        messages = [
            {"role": "system", "content": f"Extract building info into JSON. Schema: {schema}"},
            {"role": "user", "content": text}
        ]
        payload = {
            "model": "llama3:latest", # Default for Ollama
            "messages": messages, 
            "stream": False,
            "format": "json"
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                r = await client.post(f"{OLLAMA_BASE_URL}/chat", json=payload)
                r.raise_for_status()
                content = r.json().get("message", {}).get("content", "{}")
                return json.loads(content)
            except Exception as e:
                print(f"Ollama JSON fail: {e}")
                
    # CASE B: LM STUDIO (OpenAI Mode)
    else:
        messages = [
            {"role": "system", "content": "Extract building info into JSON with keys: project_name, levels(name, elevation). Output JSON only."},
            {"role": "user", "content": text}
        ]
        payload = {
            "model": "local-model", 
            "messages": messages, 
            "temperature": 0.2
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                r = await client.post(f"{LM_STUDIO_BASE_URL}/chat/completions", json=payload)
                r.raise_for_status()
                content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "{}")
                if "```json" in content: content = content.split("```json")[1].split("```")[0]
                return json.loads(content)
            except Exception as e:
                print(f"LM Studio JSON fail: {e}")

    return {"project_name": "Fallback Project", "levels": [{"name": "Ground", "elevation": 0.0}]}

async def call_llm(messages: List[Dict], model: Optional[str] = None):
    provider = runtime_config.llm_provider
    model_name = model or "local-model"
    
    # CASE A: OLLAMA
    if provider == "ollama":
         # Fallback for model name if "local-model" generic string was passed
         if model_name == "local-model": model_name = "llama3:latest"
         
         payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "keep_alive": "5m"
         }
         async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                r = await client.post(f"{OLLAMA_BASE_URL}/chat", json=payload)
                r.raise_for_status()
                return {"role": "assistant", "content": r.json().get("message", {}).get("content", "")}
            except httpx.HTTPError as e:
                raise HTTPException(status_code=503, detail=f"Ollama Unavailable: {e}")

    # CASE B: LM STUDIO
    else:
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                r = await client.post(f"{LM_STUDIO_BASE_URL}/chat/completions", json=payload)
                r.raise_for_status()
                return {"role": "assistant", "content": r.json().get("choices", [{}])[0].get("message", {}).get("content", "")}
            except httpx.HTTPError as e:
                raise HTTPException(status_code=503, detail=f"LM Studio Unavailable: {e}")

async def call_orpheus_tts(text: str, voice: str, model: Optional[str] = None, response_format: str = "wav", speed: Optional[float] = None):
    payload = {
        "input": text,
        "voice": voice,
        "response_format": response_format
    }
    # Validation Logic
    BAD_MODEL_SENTINELS = {"loading...", "loading", "default", "none", "null", ""}
    m = (model or "").strip()
    if m.lower() not in BAD_MODEL_SENTINELS:
        payload["model"] = m

    if speed is not None:
        payload["speed"] = speed
        
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            r = await client.post(ORPHEUS_URL, json=payload)
            r.raise_for_status()
            content = r.content # WAV bytes
            
            # Guard: 44-byte check
            if len(content) <= 44:
                print(f"Orpheus returned empty audio ({len(content)} bytes). Model might be invalid: {model}")
                raise HTTPException(status_code=502, detail="TTS Engine returned empty audio (invalid model?)")
            
            return content
        except httpx.HTTPStatusError as e:
            # Server responded with error
            raise HTTPException(status_code=503, detail=f"Orpheus TTS Error: {e.response.status_code} {e.response.text}")
        except httpx.HTTPError as e:
            # Connection/Timeout error
            raise HTTPException(status_code=503, detail=f"Orpheus TTS Unavailable: {repr(e)}")

async def get_orpheus_voices():
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.get(ORPHEUS_VOICES_URL)
            if r.status_code == 200:
                data = r.json()
                return data.get("voices", [])
        except: pass
    return ["tara"] # Fallback

# --- Endpoints ---

@app.get("/runtime/status")
async def get_status():
    # 1. Chat Provider Status
    chat_prov = registry.get(runtime_config.llm_provider)
    chat_status = {"ok": False, "detail": "unknown", "latency_ms": 0}
    if chat_prov:
        chat_status = await chat_prov.health()
    
    # 2. TTS Host Provider Status (ecosystem model host)
    tts_host_prov = registry.get(runtime_config.tts_provider)
    tts_host_status = {"ok": False, "detail": "unknown", "latency_ms": 0}
    if tts_host_prov:
        tts_host_status = await tts_host_prov.health()

    # 3. TTS Engine Status (Orpheus service)
    tts_engine_prov = registry.get("orpheus")
    tts_engine_status = {"ok": False, "detail": "unknown", "latency_ms": 0}
    if tts_engine_prov:
        tts_engine_status = await tts_engine_prov.health()

    tts_ready = tts_host_status["ok"] and tts_engine_status["ok"]
    tts_detail = f"host={tts_host_status['detail']}, engine={tts_engine_status['detail']}"

    return {
        "ok": True,
        "providers": {
            "chat": { 
                "id": runtime_config.llm_provider,
                "mode": runtime_config.chat_mode, 
                "ready": chat_status["ok"], 
                "detail": chat_status["detail"],
                "latency_ms": chat_status["latency_ms"]
            },
            "tts":  { 
                "id": runtime_config.tts_provider,
                "mode": runtime_config.tts_mode, 
                "ready": tts_ready, 
                "detail": tts_detail,
                "latency_ms": max(tts_host_status["latency_ms"], tts_engine_status["latency_ms"])
            }
        },
        "gpu": gpu_mgr.get_status()
    }

@app.get("/runtime/providers")
async def list_providers():
    return registry.list_all()

@app.get("/runtime/providers/{pid}/models")
async def list_provider_models(pid: str):
    prov = registry.get(pid)
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found")
    models = await prov.list_models()
    return {"models": models}

@app.get("/runtime/providers/{pid}/health")
async def check_provider_health(pid: str):
    prov = registry.get(pid)
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found")
    return await prov.health()

@app.get("/runtime/gpu/status")
async def get_gpu_status():
    return gpu_mgr.get_status()

@app.get("/runtime/device/advise")
async def advise_device(model: str, provider: str):
    return gpu_mgr.advise_device(model, provider)

@app.get("/runtime/settings")
async def get_settings():
    return runtime_config

@app.post("/runtime/settings")
async def update_settings(cfg: Config):
    global runtime_config
    runtime_config = cfg
    save_config(runtime_config)
    return runtime_config

class ChatInput(BaseModel):
    messages: List[Dict]
    model: Optional[str] = None

@app.post("/runtime/chat")
async def chat(
    req: ChatInput
):
    messages = req.messages
    model = req.model
    mode = runtime_config.chat_mode
    if mode == "offline" or mode == "hybrid":
        # Try local first
        try:
            return await call_llm(messages, model)
        except HTTPException as e:
            if mode == "hybrid":
                # Fallback to cloud
                return {"role": "assistant", "content": "[Cloud Fallback: Not Configured]"}
            raise e
    
    if mode == "cloud":
        return {"role": "assistant", "content": "[Cloud Chat: Not Configured]"}
        
    raise HTTPException(status_code=400, detail="Invalid Chat Mode")


class TTSInput(BaseModel):
    text: str
    voice: Optional[str] = None
    model: Optional[str] = None
    speed: Optional[float] = None

@app.post("/runtime/tts_json")
async def tts_json(req: TTSInput):
    # Wrapper to reuse logic
    return await process_tts(req.text, req.voice, req.model, req.speed)

async def process_tts(text: str, voice: Optional[str], model: Optional[str], speed: Optional[float]):
    mode = runtime_config.tts_mode
    target_voice = voice or runtime_config.voice_local
    target_model = model or runtime_config.tts_model
    
    # Notify orchestrator (TTS usually persistent or handled by external service loop, but we track request)
    await gpu_mgr.prepare_for_model(ModelType.TTS, target_voice)
    
    if mode == "offline" or mode == "hybrid":
        try:
            wav_bytes = await call_orpheus_tts(text, target_voice, model=target_model, speed=speed)
            if not wav_bytes or not isinstance(wav_bytes, bytes):
                raise HTTPException(status_code=500, detail="TTS produced no audio")
            return Response(content=wav_bytes, media_type="audio/wav")
        except HTTPException as e:
             if mode == "hybrid":
                # Fallback cloud?
                raise HTTPException(status_code=501, detail="Cloud TTS Fallback Not Implemented")
             raise e

    if mode == "cloud":
        raise HTTPException(status_code=501, detail="Cloud TTS Not Configured")
        
    raise HTTPException(status_code=400, detail="Invalid TTS Mode")

# Redefine /runtime/tts to use Pydantic model
@app.post("/runtime/tts")
async def tts_endpoint_main(req: TTSInput):
    return await process_tts(req.text, req.voice, req.model, req.speed)


@app.post("/runtime/generate/ifc")
async def generate_ifc_endpoint(req: dict = Body(...)):
    text = req.get("text", "")
    
    # 1. LLM Parse
    spec = await call_llm_json(text)
    
    # 2. Generate IFC
    import asyncio
    loop = asyncio.get_running_loop()
    ifc_str = await loop.run_in_executor(None, ifc_gen.generate_ifc_content, text, spec)
    
    # 3. Return File
    return Response(content=ifc_str, media_type="application/x-step", headers={"Content-Disposition": "attachment; filename=model.ifc"})

def should_use_orpheus_voices(provider: Optional[str], model: Optional[str]) -> bool:
    # Voice inventory always comes from Orpheus runtime for local/hybrid TTS.
    return True

@app.get("/runtime/voices")
async def list_voices(provider: Optional[str] = None, model: Optional[str] = None):
    # Helper for UI (best-effort)
    mode = runtime_config.tts_mode
    local: List[str] = []
    if mode in ["offine", "hybrid", "offline"]:
        if should_use_orpheus_voices(provider, model):
            local = await get_orpheus_voices()
    return {"local": local, "cloud": []}

# --- Persona API (M8) ---
from orca_runtime.persona_runtime import PersonaRuntime

WORKSPACE_ROOT = os.getcwd() # Assumes we run from the project root
persona_runtime = PersonaRuntime(WORKSPACE_ROOT)
STATE_FILE = os.path.join(WORKSPACE_ROOT, "orca_runtime", "state", "active_persona.json")

def get_active_persona_id() -> str:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f).get("active_persona_id", "persona.home@0.1")
        except: pass
    return "persona.home@0.1"

def set_active_persona_id(persona_id: str):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"active_persona_id": persona_id}, f)

def get_caps_for_profile(profile: str) -> List[str]:
    if profile == "enterprise":
        return ["assets.ingest", "assets.verify", "audio.render", "llm.streaming", "provenance.bundle", "admin.audit"]
    return ["assets.ingest", "assets.verify", "audio.render"] # Default: retail

@app.get("/runtime/persona/list")
async def list_personas_api(cap_profile: str = "retail"):
    caps = get_caps_for_profile(cap_profile)
    persona_ids = persona_runtime.list_installed_personas()
    results = []
    
    for pid in persona_ids:
        pack = persona_runtime.load_persona(pid)
        if not pack: continue
        
        status_info = persona_runtime.switch_persona(pid, caps)
        
        # Determine available modules for this persona with these caps
        reg = persona_runtime.get_module_registry()
        layout = pack.get("layout", {"modules": []})
        filtered = persona_runtime.filter_layout_by_registry(layout, caps)
        
        results.append({
            "id": pid,
            "version": pack.get("version"),
            "label": pack.get("name"),
            "entitlement_mode": pack.get("entitlement", {}).get("mode"),
            "status": status_info["status"],
            "preview_allowed": True,
            "available_modules": [m["id"] for m in filtered["modules"]]
        })
    return results

@app.get("/runtime/persona/active")
async def get_active_persona_api(cap_profile: str = "retail"):
    active_id = get_active_persona_id()
    caps = get_caps_for_profile(cap_profile)
    return persona_runtime.switch_persona(active_id, caps)

class SwitchInput(BaseModel):
    persona_id: str

@app.post("/runtime/persona/switch")
async def switch_persona_api(req: SwitchInput, cap_profile: str = "retail"):
    # Note: We allow switching even to "locked" personas, they just render in LOCKED_PREVIEW status
    set_active_persona_id(req.persona_id)
    caps = get_caps_for_profile(cap_profile)
    return persona_runtime.switch_persona(req.persona_id, caps)

@app.get("/runtime/persona/preview")
async def preview_persona_api(persona_id: str, cap_profile: str = "retail"):
    caps = get_caps_for_profile(cap_profile)
    return persona_runtime.switch_persona(persona_id, caps)

@app.get("/runtime/persona/catalog")
async def get_catalog_api():
    return persona_runtime.get_catalog()

@app.get("/runtime/persona/installed")
async def get_installed_personas_api():
    return persona_runtime.installer.get_installed()

class InstallInput(BaseModel):
    source_path: Optional[str] = None
    zip_path: Optional[str] = None

@app.post("/runtime/persona/install")
async def install_persona_api(req: InstallInput):
    if req.source_path:
        return persona_runtime.installer.install(req.source_path)
    if req.zip_path:
        return persona_runtime.installer.import_zip(req.zip_path)
    raise HTTPException(status_code=400, detail="Source path or Zip path required.")

@app.post("/runtime/persona/import")
async def import_persona_api(req: InstallInput):
    if req.zip_path:
        return persona_runtime.installer.import_zip(req.zip_path)
    raise HTTPException(status_code=400, detail="Zip path required.")

class RollbackInput(BaseModel):
    persona_id: str
    version: str

@app.post("/runtime/persona/rollback")
async def rollback_persona_api(req: RollbackInput):
    return persona_runtime.installer.rollback(req.persona_id, req.version)

class ActivateInput(BaseModel):
    sku: Optional[str] = None
    persona_id: Optional[str] = None

@app.post("/runtime/persona/activate")
async def activate_persona_api(req: ActivateInput):
    sku = req.sku
    if not sku and req.persona_id:
        pack = persona_runtime.load_persona(req.persona_id)
        if pack:
            sku = pack.get("entitlement", {}).get("sku")
    
    if not sku:
        raise HTTPException(status_code=400, detail="Missing SKU or Persona ID")
    
    success = persona_runtime.add_grant(sku)
    return {"success": success, "sku": sku, "grants": persona_runtime.get_user_grants()}

# --- Director API (Flight Recorder) ---
from orca_runtime.director import Director

director_ctrl = Director(WORKSPACE_ROOT)

def handle_director_event(event: Dict):
    # This runs in the same process, we need to broadcast to WS clients
    # Note: Flask/FastAPI async context might be tricky, but we'll try basic broadcast
    asyncio.create_task(manager.broadcast(json.dumps(event)))

director_ctrl.set_on_event(handle_director_event)

@app.get("/api/director/state")
async def director_state():
    return director_ctrl.get_state()

@app.get("/api/director/events")
async def director_events(limit: int = 50):
    return director_ctrl.list_events(limit)

@app.get("/api/director/runs")
async def director_runs():
    return director_ctrl.list_runs()

@app.post("/api/director/events/test")
async def director_test_event():
    return director_ctrl.append_event("test.manual", "director", {"msg": "Manual test event triggered"})

@app.websocket("/api/director/ws")
async def director_ws_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/api/director/session/start")
async def director_start_session(persona_id: str = "persona.home@0.1"):
    # Bridge to new run receipt logic if needed, or keep as is
    event = director_ctrl.append_event("session.start", "director", {"persona_id": persona_id})
    return event

@app.post("/api/director/session/stop")
async def director_stop_session(session_id: str):
    event = director_ctrl.append_event("session.stop", "director", {"session_id": session_id})
    return event

@app.post("/api/director/inbox/upload")
async def director_inbox_upload(file: UploadFile = File(...)):
    content = await file.read()
    item = director_ctrl.ingest_to_inbox(file.filename, content)
    return item

@app.get("/api/director/inbox/list")
async def director_inbox_list():
    return director_ctrl.list_inbox()

@app.get("/api/director/inbox/{inbox_id}/artifacts/{path:path}")
async def director_inbox_artifact(inbox_id: str, path: str):
    content = director_ctrl.get_inbox_artifact(inbox_id, path)
    if not content:
        raise HTTPException(status_code=404, detail="Artifact not found")
    media_type = "image/jpeg" if path.endswith(".jpg") else "text/plain"
    return Response(content=content, media_type=media_type)

@app.get("/api/director/inbox/{inbox_id}/original/{filename}")
async def director_inbox_original(inbox_id: str, filename: str):
    content = director_ctrl.get_inbox_original(inbox_id, filename)
    if not content:
        raise HTTPException(status_code=404, detail="Original file not found")
    return Response(content=content, media_type="application/octet-stream")

# --- Quest Engine API ---

class QuestFromInboxReq(BaseModel):
    inbox_id: str
    title: Optional[str] = None
    acceptance: Optional[str] = None

@app.post("/api/director/quests/from_inbox")
async def director_quests_from_inbox(req: QuestFromInboxReq):
    return director_ctrl.create_quest_from_inbox(req.inbox_id, req.title, req.acceptance)

class QuestStatusReq(BaseModel):
    quest_id: str
    status: str

@app.post("/api/director/quests/set_status")
async def director_quests_set_status(req: QuestStatusReq):
    try:
        return director_ctrl.set_quest_status(req.quest_id, req.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/director/quests")
async def director_get_quests():
    return director_ctrl.get_quests()

# --- Capability Trails API (M12) ---

@app.get("/api/director/capabilities")
async def director_list_capabilities():
    return director_ctrl.get_capability_catalog()

@app.get("/api/director/capabilities/actions")
async def director_list_capability_actions():
    return director_ctrl.get_capability_actions()

class RunCapabilityReq(BaseModel):
    capability_id: str
    action_id: str
    params: Dict = {}

@app.post("/api/director/capabilities/run")
async def director_run_capability(req: RunCapabilityReq):
    try:
        return director_ctrl.run_capability(req.capability_id, req.action_id, req.params)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class CapabilityReceiptReq(BaseModel):
    capability_id: str

@app.post("/api/director/capabilities/emit_test_receipt")
async def director_capability_test_receipt(req: CapabilityReceiptReq):
    return director_ctrl.emit_capability_test_receipt(req.capability_id)

@app.post("/api/director/runs/record")
async def director_record_run(receipt: Dict):
    return director_ctrl.record_run_receipt(receipt)

# --- Progress Dashboard API (M13) ---

@app.get("/api/director/progress")
async def director_get_progress():
    return director_ctrl.get_progress_snapshot()

class IssueCreateReq(BaseModel):
    title: str
    severity: str
    area: Optional[str] = None
    links: Optional[Dict] = None

@app.post("/api/director/issues/create")
async def director_create_issue(req: IssueCreateReq):
    return director_ctrl.create_issue(req.title, req.severity, req.area, req.links)

class StatusUpdateReq(BaseModel):
    id: str
    status: str

@app.post("/api/director/issues/set_status")
async def director_set_issue_status(req: StatusUpdateReq):
    return director_ctrl.set_issue_status(req.id, req.status)

@app.post("/api/director/milestones/set_status")
async def director_set_milestone_status(req: StatusUpdateReq):
    return director_ctrl.set_milestone_status(req.id, req.status)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7010)
