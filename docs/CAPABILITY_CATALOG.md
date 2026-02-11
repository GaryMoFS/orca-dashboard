# ORCA Capability Catalog (M12)

This is the canonical list of functional capabilities within the ORCA platform. This document serves as the human-readable mirror of `orca/capabilities/catalog.json`.

## Capabilities List

### cap.txt_to_ifc
- **Purpose**: Convert natural language building descriptions to Industry Foundation Classes (IFC) models.
- **Inputs**: Text
- **Outputs**: IFC
- **Status**: idea
- **Gate**: Pro
- **Verification**: `echo stub: cap.txt_to_ifc`

### cap.pdf_to_manifest
- **Purpose**: Extract structured procurement data and bill of quantities from PDF sets.
- **Inputs**: PDF
- **Outputs**: JSON, CSV
- **Status**: idea
- **Gate**: Retail, Pro
- **Verification**: `echo stub: cap.pdf_to_manifest`

### cap.txt_to_step
- **Purpose**: Convert textual mechanical descriptions to STEP (ISO 10303) CAD formats.
- **Inputs**: Text
- **Outputs**: STEP
- **Status**: idea
- **Gate**: Pro
- **Verification**: `echo stub: cap.txt_to_step`

### cap.ifc_to_glb
- **Purpose**: Optimized conversion of BIM/IFC data to web-ready GLB/gLTF assets.
- **Inputs**: IFC
- **Outputs**: GLB
- **Status**: demo
- **Gate**: Home, Work, Retail, Pro
- **Verification**: `echo stub: cap.ifc_to_glb`

### cap.sketch_to_render
- **Purpose**: Generate high-fidelity architectural visualizations from hand-drawn sketches.
- **Inputs**: Image
- **Outputs**: Image
- **Status**: demo
- **Gate**: Pro
- **Verification**: `echo stub: cap.sketch_to_render`

### cap.sketch_to_ifc
- **Purpose**: Heuristic extraction of spatial volumes and wall layouts from orthographic sketches to IFC.
- **Inputs**: Image
- **Outputs**: IFC
- **Status**: idea
- **Gate**: Pro
- **Verification**: `echo stub: cap.sketch_to_ifc`

### cap.opencnc
- **Purpose**: Standardized generation of CNC toolpaths (G-Code) for distributed fabrication.
- **Inputs**: STEP, IFC
- **Outputs**: G-Code
- **Status**: idea
- **Gate**: Pro
- **Verification**: `echo stub: cap.opencnc`

### cap.proposal_generation
- **Purpose**: Automated assembly of design proposals, including cost estimates and technical advisory.
- **Inputs**: Manifest, Render
- **Outputs**: PDF
- **Status**: demo
- **Gate**: Retail, Pro
- **Verification**: `echo stub: cap.proposal_generation`

### cap.codes_and_standards_compliance
- **Purpose**: Automated audit of designs against AS 3600, AS 4100, and NCC/BCA requirements.
- **Inputs**: IFC, Text
- **Outputs**: Report
- **Status**: demo
- **Gate**: Pro
- **Verification**: `echo stub: cap.codes_and_standards`

### cap.cost_management
- **Purpose**: Dynamic tracking of material costs and assembly labor against project budget.
- **Inputs**: Manifest
- **Outputs**: JSON
- **Status**: idea
- **Gate**: Retail, Pro
- **Verification**: `echo stub: cap.cost_management`

### cap.tendering
- **Purpose**: Bridge between project specifications and fabricator bid management.
- **Inputs**: Manifest
- **Outputs**: Bids
- **Status**: idea
- **Gate**: Pro
- **Verification**: `echo stub: cap.tendering`

### cap.logistics
- **Purpose**: Just-in-time delivery orchestration for prefab assemblies from node to site.
- **Inputs**: Manifest
- **Outputs**: Schedule
- **Status**: idea
- **Gate**: Pro
- **Verification**: `echo stub: cap.logistics`

### cap.health_defense_government_templates
- **Purpose**: Specialized design schema enforcement for highly regulated government facilities.
- **Inputs**: Schema
- **Outputs**: IFC
- **Status**: idea
- **Gate**: Pro
- **Verification**: `echo stub: cap.health_defense`

### cap.persona_workflows
- **Purpose**: Context-aware UI/Capability gating based on the active persona profile.
- **Inputs**: Persona ID
- **Outputs**: Capabilities List
- **Status**: prod
- **Gate**: Home, Work, Retail, Pro
- **Verification**: `python tools/verify_m8_personas.py`
