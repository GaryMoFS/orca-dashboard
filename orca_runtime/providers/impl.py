import httpx
import time
import os
from .base import Provider
from typing import List, Dict, Any

class Ollama(Provider):
    def __init__(self, base_url: str = "http://localhost:11434/api"):
        # Ollama can host both chat and speech-capable models.
        super().__init__("ollama", "Ollama", ["chat.llm", "llm", "tts"])
        self.base_url = base_url

    async def list_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                r = await client.get(f"{self.base_url}/tags")
                if r.status_code == 200:
                    return [m['name'] for m in r.json().get('models', [])]
        except:
             pass
        return []

    async def health(self) -> Dict[str, Any]:
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                r = await client.get(f"{self.base_url}/tags")
                ok = r.status_code == 200
                latency = (time.time() - start) * 1000
                if ok: return {"ok": True, "detail": "up", "latency_ms": latency}
                return {"ok": False, "detail": f"http {r.status_code}", "latency_ms": 0}
        except Exception as e:
            return {"ok": False, "detail": str(e), "latency_ms": 0}

    def recommend_device(self, model: str) -> Dict[str, Any]:
        # Simple heuristic: 7B/8B fits in 6GB, 70B needs 48GB+
        est = 0
        reason = "Ollama Auto"
        if "70b" in model.lower():
            est = 48000
            reason = "Big model (Requires >48GB)"
        elif "8b" in model.lower() or "7b" in model.lower():
            est = 6000
            reason = "Fits mid-range GPU"
        elif "1b" in model.lower() or "3b" in model.lower():
            est = 2000
            reason = "Fits most GPUs"
            
        return {"device": "auto", "reason": reason, "est_vram": est}

class LMStudio(Provider):
    def __init__(self, base_url: str = "http://localhost:1234/v1"):
        # LM Studio can host both chat and speech-capable models.
        super().__init__("lm_studio", "LM Studio", ["chat.llm", "llm", "tts"])
        self.base_url = base_url

    async def list_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                r = await client.get(f"{self.base_url}/models")
                if r.status_code == 200:
                    data = r.json()
                    return [m['id'] for m in data.get('data', [])]
        except:
            pass
        return []

    async def health(self) -> Dict[str, Any]:
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                r = await client.get(f"{self.base_url}/models")
                ok = r.status_code == 200
                latency = (time.time() - start) * 1000
                if ok: return {"ok": True, "detail": "up", "latency_ms": latency}
                return {"ok": False, "detail": f"http error", "latency_ms": 0}
        except Exception as e:
             return {"ok": False, "detail": "connection refused", "latency_ms": 0}

class Orpheus(Provider):
    # Orpheus is a TTS provider running on port 5005
    def __init__(self, base_url: str = "http://localhost:5005", lmstudio_url: str = "http://localhost:1234/v1"):
        # Engine runtime only; not exposed as ecosystem model host in UI.
        super().__init__("orpheus", "Orpheus TTS Engine", ["tts.engine"])
        self.base_url = base_url
        self.lmstudio_url = os.environ.get("ORPHEUS_LMSTUDIO_URL", lmstudio_url)

    async def list_models(self) -> List[str]:
        # Orpheus relies on LM Studio loaded models when using the LM Studio backend.
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                r = await client.get(f"{self.lmstudio_url}/models")
                if r.status_code == 200:
                    data = r.json()
                    return [m["id"] for m in data.get("data", [])]
        except: pass
        return []

    async def health(self) -> Dict[str, Any]:
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                r = await client.get(f"{self.base_url}/health")
                ok = r.status_code == 200
                latency = (time.time() - start) * 1000
                if ok: return {"ok": True, "detail": "up", "latency_ms": latency}
                return {"ok": False, "detail": "error", "latency_ms": 0}
        except Exception as e:
             return {"ok": False, "detail": "down", "latency_ms": 0}
