from fastapi import APIRouter
from typing import List, Dict
import random

router = APIRouter()

# Provider Base Logic (stubbed)
class ProviderBase:
    def __init__(self, name: str, capability: str):
        self.name = name
        self.capability = capability

    def probe(self) -> float:
        # Simulate latency in ms
        return random.uniform(10, 200)

# Stubs
local_stub = ProviderBase("local-stub", "chat")
lan_stub = ProviderBase("lan-stub", "embedding")

@router.get("/providers/probe")
async def probe_providers():
    results = [
        {"name": local_stub.name, "latency_ms": local_stub.probe(), "status": "active"},
        {"name": lan_stub.name, "latency_ms": lan_stub.probe(), "status": "active"},
    ]
    return {"probes": results}
