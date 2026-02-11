from fastapi import APIRouter
from typing import List, Dict
import random
# import aiohttp 
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

import subprocess
import shutil
import json

import requests
import json
import asyncio

def check_ollama_sync(timeout=2.0) -> dict:
    models = []
    active = False
    provider = "none"

    models_ollama = []
    models_lm_studio = []

    # 1. Check Ollama (11434)
    try:
        url = "http://localhost:11434/api/tags"
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            m_list = [m['name'] for m in data.get('models', [])]
            models.extend(m_list)
            models_ollama.extend(m_list)
            active = True
            provider = "ollama"
    except: pass

    # 2. Check LM Studio (1234)
    try:
        url = "http://localhost:1234/v1/models"
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            lm_list = [m['id'] for m in data.get('data', [])]
            models.extend(lm_list)
            models_lm_studio.extend(lm_list)
            
            if not active: 
                active = True
                provider = "lm_studio"
    except: pass

    return {
        "active": active,
        "latency_ms": 10 if active else 0,
        "models": models,
        "models_ollama": models_ollama,
        "models_lm_studio": models_lm_studio,
        "provider": provider
    }

async def check_ollama(timeout=2.0) -> dict:
    """Check Ollama via requests in a thread to be robust"""
    return await asyncio.to_thread(check_ollama_sync, timeout)

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
        
    return results
        
    
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
