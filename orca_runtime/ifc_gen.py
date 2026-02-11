import ifcopenshell
import ifcopenshell.api
import time
import json

def generate_ifc_content(text_description: str, json_spec: dict) -> str:

    # Init blank project
    model = ifcopenshell.api.run("project.create_file", version="IFC4")
    
    # Robust Project Check
    projects = model.by_type("IfcProject")
    if not projects:
        # Fallback manual creation
        project = model.create_entity("IfcProject", GlobalId=ifcopenshell.guid.new(), Name=json_spec.get("project_name", "ORCA Project"))
    else:
        project = projects[0]
        project.Name = json_spec.get("project_name", "ORCA Project")
    
    # Units
    ifcopenshell.api.run("unit.assign_unit", model)
    
    # Context (3D)
    model3d = ifcopenshell.api.run("context.add_context", model, context_type="Model")
    body = ifcopenshell.api.run("context.add_context", model, context_type="Model", 
        context_identifier="Body", target_view="MODEL_VIEW", parent=model3d)

    # Site
    site = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSite", name="Default Site")
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=project, products=[site])
    
    # Building
    building = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuilding", name="Main Building")
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=site, products=[building])
    
    # Parse levels
    levels = json_spec.get("levels", [])
    if not levels: levels = [{"name": "Level 1", "elevation": 0.0}]
    
    for lvl in levels:
        storey = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuildingStorey", name=lvl.get("name", "Level"))
        storey.Elevation = float(lvl.get("elevation", 0.0))
        ifcopenshell.api.run("aggregate.assign_object", model, relating_object=building, products=[storey])
        
        # Add basic placeholder slab
        slab = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSlab", name="Floor Slab")
        ifcopenshell.api.run("aggregate.assign_object", model, relating_object=storey, products=[slab])
        
        # Add placeholder wall
        wall = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Sample Wall")
        ifcopenshell.api.run("aggregate.assign_object", model, relating_object=storey, products=[wall])
        
        # Manifest properties on wall too
        ifcopenshell.api.run("pset.add_pset", model, product=wall, name="Pset_WallCommon")
        
    # Provenance Manifest (Critical M2 Requirement)
    manifest = ifcopenshell.api.run("pset.add_pset", model, product=project, name="ORCA_Manifest")
    
    # Prepare manifest props
    # Truncate text to avoid 255 char limit issues in some IFC viewers if property is simple string
    safe_text = (text_description[:250] + '...') if len(text_description) > 250 else text_description
    
    props = {
        "SourceText": safe_text,
        "Generator": "ORCA M2 Runtime",
        "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "AI_Provider": "Ollama (Llama3)"
    }
    ifcopenshell.api.run("pset.edit_pset", model, pset=manifest, properties=props)

    return model.to_string()
