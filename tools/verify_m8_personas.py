import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from orca_runtime.persona_runtime import PersonaRuntime

def run_test():
    workspace_root = os.getcwd()
    grants_path = os.path.join(workspace_root, "orca", "licenses", "grants.json")
    if os.path.exists(grants_path): os.remove(grants_path)
    
    runtime = PersonaRuntime(workspace_root)
    
    print("--- STEP 1: Discovery ---")
    personas = runtime.list_installed_personas()
    print(f"Discovered Personas: {personas}")
    assert "persona.home@0.1" in personas
    assert "persona.work@0.1" in personas

    print("\n--- STEP 2: Capability Simulation (Retail) ---")
    # Retail user (no pro caps)
    retail_caps = ["assets.ingest", "assets.verify", "audio.render"]
    
    home_persona = runtime.switch_persona("persona.home@0.1", retail_caps)
    print(f"Home Persona (Retail): {home_persona['name']} - Status: {home_persona['status']}")
    print(f"Home Modules: {[m['id'] for m in home_persona['layout']['modules']]}")
    
    work_persona = runtime.switch_persona("persona.work@0.1", retail_caps)
    print(f"Work Persona (Retail): {work_persona['name']} - Status: {work_persona['status']}")
    # Should be filtered: chat.advanced (missing llm.streaming), provenance.bundle (missing provenance.bundle), admin.audit (missing admin.audit)
    print(f"Work Modules (Filtered): {[m['id'] for m in work_persona['layout']['modules']]}")

    print("\n--- STEP 3: Capability Simulation (Enterprise) ---")
    ent_caps = ["assets.ingest", "assets.verify", "audio.render", "llm.streaming", "provenance.bundle", "admin.audit"]
    
    work_persona_ent = runtime.switch_persona("persona.work@0.1", ent_caps)
    print(f"Work Persona (Enterprise): {work_persona_ent['name']} - Status: {work_persona_ent['status']}")
    print(f"Work Modules (All): {[m['id'] for m in work_persona_ent['layout']['modules']]}")

    print("\n--- STEP 4: License Simulation ---")
    # Currently work is LOCKED_PREVIEW even for Enterprise because no grant exists.
    assert work_persona_ent['status'] == "LOCKED_PREVIEW"
    
    print("Adding license grant for Orca Pro...")
    grants_path = os.path.join(workspace_root, "orca", "licenses", "grants.json")
    with open(grants_path, "w") as f:
        json.dump({"grants": ["sku.orca.pro.01"]}, f)
    
    work_persona_unlocked = runtime.switch_persona("persona.work@0.1", ent_caps)
    print(f"Work Persona (Unlocked): {work_persona_unlocked['name']} - Status: {work_persona_unlocked['status']}")
    assert work_persona_unlocked['status'] == "UNLOCKED"

    print("\n--- VERIFICATION PASS ---")

if __name__ == "__main__":
    run_test()
