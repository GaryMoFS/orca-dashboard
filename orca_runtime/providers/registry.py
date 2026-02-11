from .base import Provider
from .impl import Ollama, LMStudio, Orpheus
from typing import List, Dict, Any

class ProviderRegistry:
    def __init__(self):
        self.providers: Dict[str, Provider] = {}
        # Auto-register defaults
        self.register(Ollama())
        self.register(LMStudio())
        self.register(Orpheus())

    def register(self, p: Provider):
        self.providers[p.id] = p

    def list_all(self):
        return [p.to_dict() for p in self.providers.values()]

    def list_by_capability(self, cap: str):
        return [p for p in self.providers.values() if cap in p.capabilities]

    def get(self, provider_id: str) -> Provider:
        return self.providers.get(provider_id)
