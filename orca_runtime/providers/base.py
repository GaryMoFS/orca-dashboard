from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class Provider(ABC):
    def __init__(self, id: str, label: str, capabilities: List[str]):
        self.id = id
        self.label = label
        self.capabilities = capabilities

    @abstractmethod
    async def list_models(self) -> List[str]:
        pass

    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        """Returns { "ok": bool, "detail": str, "latency_ms": float }"""
        pass

    def recommend_device(self, model: str) -> Dict[str, Any]:
        """Returns { "device": "cpu"|"gpu", "reason": str, "est_vram": int }"""
        return {"device": "auto", "reason": "No recommendation", "est_vram": 0}

    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "capabilities": self.capabilities
        }
