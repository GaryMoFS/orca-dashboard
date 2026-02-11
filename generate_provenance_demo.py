import sys
import os
import json

# Ensure we can import modules
sys.path.append(os.getcwd())

from sketch_ifc.builder import IFCBuilder
from orca_api.fstack.manifest_bridge import ManifestBuilder

def generate_signed_ifc():
    """
    Demonstrates generating an IFC file and wrapping it in a signed manifest.
    """
    print("Step 1: Generating IFC file...")
    
    # Define a simple room
    schema = {
        "walls": [
            {"start": (0.0, 0.0), "end": (5.0, 0.0), "thickness": 0.2, "height": 3.0},
            {"start": (5.0, 0.0), "end": (5.0, 5.0), "thickness": 0.2, "height": 3.0},
            {"start": (5.0, 5.0), "end": (0.0, 5.0), "thickness": 0.2, "height": 3.0},
            {"start": (0.0, 5.0), "end": (0.0, 0.0), "thickness": 0.2, "height": 3.0}
        ],
        "project_name": "Signed Demo Project"
    }
    
    output_dir = "signed_output"
    os.makedirs(output_dir, exist_ok=True)
    
    ifc_filename = "signed_demo.ifc"
    ifc_path = os.path.join(output_dir, ifc_filename)
    
    # Build IFC
    builder = IFCBuilder(filename=ifc_path)
    builder.build_from_schema(schema)
    builder.save()
    
    print(f"IFC generated at: {ifc_path}")
    
    # Read the file content for hashing
    with open(ifc_path, "rb") as f:
        content = f.read()
        
    print("Step 2: Creating Manifest...")
    
    # Create Manifest
    mb = ManifestBuilder(actor_id="fspu-ifc-gen-v1")
    
    # Artifact 1: The IFC File
    file_hash = mb.add_artifact(name=ifc_filename, content=content, mime_type="application/x-step")
    print(f"Artifact 1 (IFC) hash: {file_hash}")
    
    # Artifact 2: Geometry Descriptors / Metrics (Simulated extraction)
    # in a real scenario, we'd parse the IFC to get exact volumes
    metrics = {
        "wall_count": len(schema["walls"]),
        "total_height": schema["walls"][0]["height"],
        "estimated_volume": sum([w.get("thickness", 0.2) * 5.0 * w.get("height", 3.0) for w in schema["walls"]]), # rough calc
        "complexity_score": 0.4
    }
    metrics_json = json.dumps(metrics, indent=2).encode("utf-8")
    metrics_hash = mb.add_artifact(name="geometry_metrics.json", content=metrics_json, mime_type="application/json")
    print(f"Artifact 2 (Metrics) hash: {metrics_hash}")
    
    # Set provenance (symbolic ownership)
    mb.set_provenance(
        source_task_id="task-demo-123", 
        methodology="parametric-generation-v2", 
        params={"schema_checksum": "stub", "version": "1.0"}
    )
    
    # Export signed manifest
    manifest = mb.export()
    
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Manifest saved to: {manifest_path}")
    
    print("\nStep 3: Logging to F-Stack Audit Trail...")
    from orca_api.fstack.audit import AuditLogger, export_audit_bundle
    
    audit = AuditLogger()
    entry_id = audit.log_event("manifest_created", manifest, actor="fspu-worker")
    print(f"Logged event ID: {entry_id}")
    
    # Export audit bundle
    bundle_path = os.path.join(output_dir, "audit_bundle.json")
    export_audit_bundle(bundle_path)
    print(f"Audit Bundle exported to: {bundle_path}")

    print("\n--- Verification Check ---")
    if manifest["artifacts"][0]["hash"] == file_hash:
        print("Hash matches manifest record.")
    if manifest["signature"]["algo"] == "fstack-sim-v1":
        print("Signature type valid.")

if __name__ == "__main__":
    generate_signed_ifc()
