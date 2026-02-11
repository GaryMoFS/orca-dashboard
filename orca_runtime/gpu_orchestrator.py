
import logging
import asyncio
import httpx
import time
from enum import Enum
from typing import Dict, Any, Optional, List

# Try to import pynvml for real telemetry
try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Constants for defaults
OLLAMA_BASE_URL = "http://127.0.0.1:11434"
ORPHEUS_BASE_URL = "http://127.0.0.1:5005"

class GPUTier(str, Enum):
    LOW = "LOW"     # <= 8GB (Strict management)
    MID = "MID"     # <= 16GB (One persist allowed)
    HIGH = "HIGH"   # > 16GB (Freewheeling)

class ModelType(str, Enum):
    LLM = "LLM"
    TTS = "TTS"
    FSPU = "FSPU"

class GPUOrchestrator:
    def __init__(self, ollama_url: str = OLLAMA_BASE_URL, orpheus_url: str = ORPHEUS_BASE_URL):
        self.logger = logging.getLogger("GPUOrchestrator")
        # Setup logging if not configured
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO)
            
        self.ollama_url = ollama_url
        self.orpheus_url = orpheus_url
        
        self.models_active: Dict[str, Any] = {}
        self.device_index = 0
        self.tier = GPUTier.LOW
        self.total_memory_mb = 0
        
        # Telemetry State
        self.last_update = 0
        self.cached_status = {}

        self._init_gpu()

    def _init_gpu(self):
        if PYNVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_index)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                self.total_memory_mb = int(mem_info.total / 1024**2)
                self.logger.info(f"NVML Initialized. Total VRAM: {self.total_memory_mb} MB")
            except Exception as e:
                self.logger.error(f"NVML Init Failed: {e}")
                self.total_memory_mb = 8192 # Fallback
        else:
            self.logger.warning("pynvml not found. Assumed 8GB VRAM (LOW tier).")
            self.total_memory_mb = 8192 # Fallback default

        self._determine_tier()

    def _determine_tier(self):
        # 12GB is a common boundary. 3060 (12GB), 4070 (12GB). 
        # 16GB often 4080 (16GB) or 4060Ti (16GB).
        # ORCA definitions: 
        # LOW (8GB), MID (16GB), HIGH (24-32GB)
        
        if self.total_memory_mb <= 12500: # Covers 8GB, 10GB, 11GB, 12GB cards under "LOW/Entry" logic roughly
            self.tier = GPUTier.LOW
        elif self.total_memory_mb <= 20000: # Covers 16GB cards
            self.tier = GPUTier.MID
        else:
            self.tier = GPUTier.HIGH
        
        self.logger.info(f"GPU Tier set to: {self.tier.value} based on {self.total_memory_mb} MB")

    def get_status(self) -> Dict[str, Any]:
        """
        Returns real-time telemetry of VRAM and orchestrated state.
        """
        now = time.time()
        # Rate limit hardware polling to 1s
        if now - self.last_update < 1.0 and self.cached_status:
           return self.cached_status

        usage = {"used": 0, "free": 0, "percent": 0.0}
        gpu_name = "Unknown"
        if PYNVML_AVAILABLE:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_index)
                gpu_name = pynvml.nvmlDeviceGetName(handle)
                # Decode bytes if needed (some pynvml versions return bytes)
                if isinstance(gpu_name, bytes): gpu_name = gpu_name.decode("utf-8")
                
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                usage["used"] = int(info.used / 1024**2)
                usage["free"] = int(info.free / 1024**2)
                if self.total_memory_mb > 0:
                    usage["percent"] = round((usage["used"] / self.total_memory_mb) * 100, 1)
            except: pass
        
        ram = {"total": 0, "available": 0, "percent": 0.0}
        if PSUTIL_AVAILABLE:
            mem = psutil.virtual_memory()
            ram["total"] = int(mem.total / 1024**2)
            ram["available"] = int(mem.available / 1024**2)
            ram["percent"] = mem.percent

        status = {
            "tier": self.tier.value,
            "device_name": gpu_name,
            "total_vram_mb": self.total_memory_mb,
            "usage": usage,
            "ram": ram,
            "active_models": self.models_active,
            "timestamp": now
        }
        self.cached_status = status
        self.last_update = now
        return status

    def advise_device(self, model: str, provider: str) -> Dict[str, Any]:
        """
        Returns a recommendation for the requested model/provider context.
        """
        status = self.get_status() # Refresh
        
        # Simple heuristics
        est_vram = 0
        if "70b" in model.lower(): est_vram = 48000
        elif "8b" in model.lower(): est_vram = 6000
        elif "7b" in model.lower(): est_vram = 5500
        elif "1b" in model.lower(): est_vram = 2000
        
        free_vram = status["usage"]["free"]
        
        # Logic
        can_fit = free_vram > (est_vram * 1.2) # 20% headroom
        
        reason = f"Free VRAM: {free_vram}MB vs Est: {est_vram}MB"
        
        if can_fit and provider != "offline":
            return {"device": "gpu", "reason": f"Fits comfortably. {reason}", "safe": True}
        
        if est_vram == 0:
             return {"device": "auto", "reason": "Unknown model size, use Auto", "safe": True}

        return {"device": "cpu", "reason": f"Insufficient VRAM. {reason}", "safe": True}

    async def prepare_for_model(self, model_type: ModelType, model_name: str) -> Dict[str, Any]:
        """
        Called BEFORE finding/loading a model. 
        Returns directives (e.g. keep_alive) for the runtime to use.
        May trigger unloading of other models.
        """
        self.logger.info(f"Preparing for model: {model_name} ({model_type})")
        
        directives = {
            "keep_alive": "5m", 
            "blocked": False
        }

        # --- LOW TIER STRATEGY ---
        if self.tier == GPUTier.LOW:
            # Single model focus.
            # If requesting LLM, unload TTS (if possible) and other LLMs.
            # If requesting TTS, unload LLM.
            
            if model_type == ModelType.LLM:
                # Unload everything else
                await self._unload_ollama_except(model_name)
                # Keep alive: On-demand only (0 or short). user said "on-demand loading only"
                directives["keep_alive"] = 0 # Immediate unload after response
                
            elif model_type == ModelType.TTS:
                # Unload LLMs to free space
                await self._unload_ollama_all()
                directives["keep_alive"] = 0 

        # --- MID TIER STRATEGY ---
        elif self.tier == GPUTier.MID:
            # Persistent LLM allowed. Transient TTS.
            if model_type == ModelType.LLM:
                directives["keep_alive"] = -1 # Keep loaded indefinitely
            elif model_type == ModelType.TTS:
                # Ensure we have space if LLM is huge? 
                # For now, just mark TTS as transient.
                directives["keep_alive"] = 0 # Transient

        # --- HIGH TIER STRATEGY ---
        elif self.tier == GPUTier.HIGH:
            # Load everything, keep everything.
            directives["keep_alive"] = -1

        # Track usage
        self.models_active[model_name] = {
            "type": model_type.value,
            "last_active": time.time()
        }
        
        return directives

    async def _unload_ollama_all(self):
        """Unload all Ollama models."""
        # Simple hack: load a non-existent model or send keep_alive=0 to running ones?
        # Better: Since we don't track exact running models in Ollama, we try to clear via generating a dummy request 
        # with keep_alive=0, or just trust the next load with keep_alive=0 handles it.
        # However, to explicitly clear VRAM:
        # We can't easily "unload all". We rely on the `prepare_for_model` returning keep_alive=0 for the NEW model.
        # But if we need to clear space *before* loading:
        pass 

    async def _unload_ollama_except(self, model_name: str):
        # Implementation depends on Ollama state features. 
        pass

    def recommend_models(self) -> Dict[str, str]:
        """Return recommended models based on Tier"""
        if self.tier == GPUTier.LOW:
            return {"llm": "llama3:8b-quant", "tts": "fast_speech_nano"}
        elif self.tier == GPUTier.MID:
            return {"llm": "llama3:8b-fp16", "tts": "orpheus_standard"}
        else:
            return {"llm": "llama3:70b", "tts": "orpheus_high_fidelity"}

