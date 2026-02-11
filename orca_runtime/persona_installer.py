import os
import json
import shutil
import zipfile
import datetime
from typing import Dict, List, Optional, Any
from jsonschema import validate, ValidationError

class PersonaInstaller:
    def __init__(self, workspace_root: str):
        self.root = workspace_root
        self.installed_dir = os.path.join(workspace_root, "orca", "personas", "installed")
        self.schema_dir = os.path.join(workspace_root, "orca", "engine", "schemas")
        self.index_path = os.path.join(self.installed_dir, "index.json")
        self.tmp_dir = os.path.join(workspace_root, "orca_runtime", "state", "tmp_import")
        os.makedirs(self.installed_dir, exist_ok=True)
        os.makedirs(self.tmp_dir, exist_ok=True)

    def load_index(self) -> Dict[str, Any]:
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, "r") as f:
                    return json.load(f)
            except:
                pass
        
        # Seed index from filesystem if missing
        index = {}
        if os.path.exists(self.installed_dir):
            for d in os.listdir(self.installed_dir):
                if os.path.isdir(os.path.join(self.installed_dir, d)) and "@" in d:
                    base_id, version = d.split("@", 1)
                    if base_id not in index:
                        index[base_id] = {"active_version": version, "versions": []}
                    if version not in index[base_id]["versions"]:
                        index[base_id]["versions"].append(version)
        
        return index

    def save_index(self, index: Dict[str, Any]):
        with open(self.index_path, "w") as f:
            json.dump(index, f, indent=2)

    def _validate_json(self, data: Any, schema_filename: str) -> Optional[str]:
        schema_path = os.path.join(self.schema_dir, schema_filename)
        if not os.path.exists(schema_path):
            return f"Schema {schema_filename} not found."
        
        try:
            with open(schema_path, "r") as f:
                schema = json.load(f)
            validate(instance=data, schema=schema)
            return None
        except ValidationError as e:
            return f"Validation error in {schema_filename}: {e.message}"
        except Exception as e:
            return f"Error validating {schema_filename}: {str(e)}"

    def validate_pack(self, source_path: str) -> List[str]:
        errors = []
        pack_path = os.path.join(source_path, "persona.pack.json")
        if not os.path.exists(pack_path):
            return ["Missing persona.pack.json"]
        
        try:
            with open(pack_path, "r") as f:
                pack = json.load(f)
            err = self._validate_json(pack, "orca.ui.persona.pack@0.1.schema.json")
            if err: errors.append(err)
            
            comp = pack.get("components", {})
            
            # Layout
            layout_file = comp.get("layout")
            if layout_file:
                lpath = os.path.join(source_path, layout_file)
                if os.path.exists(lpath):
                    with open(lpath, "r") as f:
                        layout_data = json.load(f)
                    err = self._validate_json(layout_data, "orca.ui.layout@0.1.schema.json")
                    if err: errors.append(err)
                else:
                    errors.append(f"Layout component file {layout_file} not found.")

            # Theme
            theme_file = comp.get("theme")
            if theme_file:
                tpath = os.path.join(source_path, theme_file)
                if os.path.exists(tpath):
                    with open(tpath, "r") as f:
                        theme_data = json.load(f)
                    err = self._validate_json(theme_data, "orca.ui.theme@0.1.schema.json")
                    if err: errors.append(err)
                else:
                    errors.append(f"Theme component file {theme_file} not found.")

        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {str(e)}")
        except Exception as e:
            errors.append(f"Unexpected validation error: {str(e)}")
            
        return errors

    def install(self, source_path: str, auto_switch: bool = True) -> Dict[str, Any]:
        source_path = os.path.abspath(source_path)
        errors = self.validate_pack(source_path)
        if errors:
            return {"success": False, "errors": errors}
            
        with open(os.path.join(source_path, "persona.pack.json"), "r") as f:
            pack = json.load(f)
        
        persona_id = pack.get("id")
        version = str(pack.get("version"))
        
        # Normalized base ID
        base_id = persona_id.split("@")[0]
        
        target_dirname = f"{base_id}@{version}"
        target_path = os.path.join(self.installed_dir, target_dirname)
        
        # Safe copy: do not overwrite if exists or at least log it.
        # Requirements say "Never overwrite existing persona version directories"
        if os.path.exists(target_path):
            return {"success": False, "errors": [f"Version {version} of {base_id} already exists."]}
        
        shutil.copytree(source_path, target_path)
            
        index = self.load_index()
        if base_id not in index:
            index[base_id] = {"active_version": version, "versions": []}
        
        if version not in index[base_id]["versions"]:
            index[base_id]["versions"].append(version)
        
        if auto_switch:
            index[base_id]["active_version"] = version
        
        self.save_index(index)
        return {"success": True, "persona_id": base_id, "version": version, "active_version": index[base_id]["active_version"]}

    def import_zip(self, zip_path: str) -> Dict[str, Any]:
        if not os.path.exists(zip_path):
            return {"success": False, "errors": [f"ZIP file not found: {zip_path}"]}
        
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        extract_path = os.path.join(self.tmp_dir, ts)
        os.makedirs(extract_path, exist_ok=True)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Security check for path traversal
                for member in zip_ref.namelist():
                    filename = os.path.basename(member)
                    if not filename: continue # directory
                    
                    # Ensure no ".." or absolute paths
                    if member.startswith("/") or ".." in member:
                        return {"success": False, "errors": ["Zip member path is suspicious (traversal blocked)."]}
                
                zip_ref.extractall(extract_path)
            
            # Check if there is a root folder inside the zip
            content = os.listdir(extract_path)
            work_dir = extract_path
            if len(content) == 1 and os.path.isdir(os.path.join(extract_path, content[0])):
                work_dir = os.path.join(extract_path, content[0])
            
            # Install
            return self.install(work_dir, auto_switch=False)
            
        except zipfile.BadZipFile:
            return {"success": False, "errors": ["Invalid or corrupted ZIP file."]}
        except Exception as e:
            return {"success": False, "errors": [f"Unexpected import error: {str(e)}"]}
        finally:
            # Cleanup tmp if needed? Requirements don't specify, but good practice.
            # shutil.rmtree(extract_path, ignore_errors=True)
            pass

    def rollback(self, base_id: str, version: str) -> Dict[str, Any]:
        index = self.load_index()
        if base_id not in index:
            return {"success": False, "errors": [f"Persona {base_id} not installed"]}
        
        if version not in index[base_id]["versions"]:
            return {"success": False, "errors": [f"Version {version} not found for {base_id}"]}
        
        index[base_id]["active_version"] = version
        self.save_index(index)
        return {"success": True, "persona_id": base_id, "active_version": version}

    def get_installed(self) -> Dict[str, Any]:
        return self.load_index()
