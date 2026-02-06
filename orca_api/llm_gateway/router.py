from fastapi import APIRouter
from typing import List, Dict
import random
import aiohttp
import asyncio

router = APIRouter()

# Provider Base Logic (stubbed)
class ProviderBase:
    def __init__(self, name: str, capability: str):
        self.name = name
        self.capability = capability

    def probe(self) -> float:
        # Simulate latency in ms
        return random.uniform(10, 200)

async def check_ollama(timeout=2.0) -> dict:
    url = "http://localhost:11434/api/tags"
    try:
        async with aiohttp.ClientSession() as session:
            start = asyncio.get_event_loop().time()
            async with session.get(url, timeout=timeout) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    latency = (asyncio.get_event_loop().time() - start) * 1000
                    models = [m['name'] for m in data.get('models', [])]
                    return {
                        "active": True,
                        "latency_ms": latency,
                        "models": models
                    }
    except Exception:
        pass
    return {"active": False, "latency_ms": 0, "models": []}

# Stubs
local_stub = ProviderBase("local-stub", "chat")
lan_stub = ProviderBase("lan-stub", "embedding")

@router.get("/providers/probe")
async def probe_providers():
    ollama_status = await check_ollama()
    
    results = [
        {"name": local_stub.name, "latency_ms": local_stub.probe(), "status": "active"},
        {"name": lan_stub.name, "latency_ms": lan_stub.probe(), "status": "active"},
    ]
    
    if ollama_status["active"]:
        results.insert(0, {
            "name": "ollama_local", 
            "latency_ms": ollama_status["latency_ms"], 
            "status": "active",
            "models": ollama_status["models"]
        })
        
    
@router.post("/providers/ollama/pull_default")
async def pull_default_model():
    """Triggers 'ollama pull llama3' in background"""
    import subprocess
    try:
        # Non-blocking start (fire and forget for this MVP)
        subprocess.Popen(["ollama", "pull", "llama3"])
        return {"status": "pulling", "model": "llama3"}
    except FileNotFoundError:
        return {"error": "ollama binary not found"}
