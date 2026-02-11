import os
import json
from typing import List, Dict, Any, Optional
import datetime
from orca_runtime.persona_installer import PersonaInstaller

class PersonaRuntime:
    def __init__(self, workspace_root: str):
        self.root = workspace_root
        self.personas_dir = os.path.join(workspace_root, "orca", "personas", "installed")
        self.registry_path = os.path.join(workspace_root, "orca", "ui", "module_registry.json")
        self.grants_path = os.path.join(workspace_root, "orca", "licenses", "grants.json")
        self.installer = PersonaInstaller(workspace_root)

    def list_installed_personas(self) -> List[str]:
        index = self.installer.load_index()
        # Return the directories (id@version) for all active personas
        active_dirs = []
        for pid, meta in index.items():
            active_dirs.append(f"{pid}@{meta['active_version']}")
        
        # Fallback for un-indexed directories to maintain M8 compatibility
        if not active_dirs and os.path.exists(self.personas_dir):
            for d in os.listdir(self.personas_dir):
                if os.path.isdir(os.path.join(self.personas_dir, d)) and "@" in d:
                    if d != "index.json": # Safety
                        active_dirs.append(d)
        
        return active_dirs

    def load_persona(self, persona_id: str) -> Optional[Dict[str, Any]]:
        # Handle persona_id being either directory name (id@version) or base_id
        actual_dir = persona_id
        if "@" not in persona_id:
            index = self.installer.load_index()
            if persona_id in index:
                actual_dir = f"{persona_id}@{index[persona_id]['active_version']}"
            else:
                return None

        pack_path = os.path.join(self.personas_dir, actual_dir, "persona.pack.json")
        if not os.path.exists(pack_path):
            return None
        
        with open(pack_path, "r") as f:
            pack = json.load(f)
        
        # Load sub-components
        base_dir = os.path.join(self.personas_dir, actual_dir)
        for key, filename in pack.get("components", {}).items():
            comp_path = os.path.join(base_dir, filename)
            if os.path.exists(comp_path):
                with open(comp_path, "r") as f:
                    pack[key] = json.load(f)
        
        return pack

    def get_user_grants(self) -> List[str]:
        if not os.path.exists(self.grants_path):
            return []
        try:
            with open(self.grants_path, "r") as f:
                data = json.load(f)
                raw_grants = data.get("grants", [])
                # Return normalized list of SKUs for checking permissions
                skus = []
                for g in raw_grants:
                    if isinstance(g, str):
                        skus.append(g)
                    elif isinstance(g, dict):
                        skus.append(g.get("sku"))
                return [s for s in skus if s]
        except:
            return []

    def get_full_grants(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.grants_path):
            return []
        try:
            with open(self.grants_path, "r") as f:
                data = json.load(f)
                return data.get("grants", [])
        except:
            return []

    def get_module_registry(self) -> Dict[str, Any]:
        if not os.path.exists(self.registry_path):
            return {}
        with open(self.registry_path, "r") as f:
            return json.load(f)

    def can_load_persona(self, pack: Dict[str, Any], user_capabilities: List[str]) -> Dict[str, Any]:
        entitlement = pack.get("entitlement", {})
        mode = entitlement.get("mode", "free")
        sku = entitlement.get("sku")
        
        if mode == "free":
            return {"allowed": True, "locked_reason": None}
        
        grants = self.get_user_grants()
        if sku in grants:
            return {"allowed": True, "locked_reason": None}
        
        return {"allowed": False, "locked_reason": "LICENSE_REQUIRED", "sku": sku}

    def filter_layout_by_registry(self, layout: Dict[str, Any], user_capabilities: List[str]) -> Dict[str, Any]:
        registry = self.get_module_registry()
        user_caps_set = set(user_capabilities)
        
        filtered_modules = []
        for module in layout.get("modules", []):
            module_id = module.get("id")
            reg_entry = registry.get(module_id)
            
            if not reg_entry:
                continue # Disallow if not in registry
            
            req_caps = reg_entry.get("capabilities", [])
            if all(cap in user_caps_set for cap in req_caps):
                filtered_modules.append(module)
        
        new_layout = layout.copy()
        new_layout["modules"] = filtered_modules
        return new_layout

    def switch_persona(self, persona_id: str, user_capabilities: List[str]) -> Dict[str, Any]:
        pack = self.load_persona(persona_id)
        if not pack:
            return {"status": "error", "message": "Persona not found"}
        
        check = self.can_load_persona(pack, user_capabilities)
        
        # If locked, we still return the structure but mark as PREVIEW
        # and we filter the layout based on capabilities only.
        
        raw_layout = pack.get("layout", {"modules": []})
        filtered_layout = self.filter_layout_by_registry(raw_layout, user_capabilities)
        
        result = {
            "id": pack["id"],
            "name": pack["name"],
            "status": "UNLOCKED" if check["allowed"] else "LOCKED_PREVIEW",
            "layout": filtered_layout,
            "theme": pack.get("theme"),
            "quests": pack.get("quests")
        }
        
        if not check["allowed"]:
            result["locked_reason"] = check["locked_reason"]
            result["sku"] = check["sku"]
            
        return result

    def get_catalog(self) -> List[Dict[str, Any]]:
        catalog_path = os.path.join(self.root, "orca", "marketplace", "catalog.json")
        if not os.path.exists(catalog_path):
            return []
        
        with open(catalog_path, "r") as f:
            data = json.load(f)
            skus = data.get("catalog", [])
        
        grants = self.get_user_grants()
        installed_personas = self.list_installed_personas()
        
        results = []
        for item in skus:
            sku_id = item.get("sku")
            # Find matching installed persona for this SKU if any
            target_persona = None
            for pid in installed_personas:
                pack = self.load_persona(pid)
                if pack and pack.get("entitlement", {}).get("sku") == sku_id:
                    target_persona = pid
                    break
            
            is_unlocked = sku_id in grants or item.get("mode") == "free"
            
            results.append({
                "sku": sku_id,
                "name": item.get("name"),
                "description": item.get("description"),
                "price": item.get("price"),
                "installed": target_persona is not None,
                "persona_id": target_persona,
                "unlocked": is_unlocked,
                "locked": not is_unlocked
            })
        return results

    def add_grant(self, sku: str) -> bool:
        full_grants = self.get_full_grants()
        
        # Idempotency check
        for g in full_grants:
            if isinstance(g, str) and g == sku:
                return True
            if isinstance(g, dict) and g.get("sku") == sku:
                return True
        
        new_entry = {
            "sku": sku,
            "granted_at": datetime.datetime.now().isoformat(),
            "granted_by": "user:local",
            "activation_source": "marketplace-ui"
        }
        
        full_grants.append(new_entry)
        os.makedirs(os.path.dirname(self.grants_path), exist_ok=True)
        with open(self.grants_path, "w") as f:
            json.dump({"grants": full_grants}, f, indent=2)
        return True
