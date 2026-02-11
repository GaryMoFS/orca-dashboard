# Walkthrough: M15 Action Bridge

## Overview
Milestone M15 transforms the Director Console from a passive observer into an active orchestrator. Users can now trigger complex capabilities (like TXT→IFC generation) directly from the dashboard, supplying real parameters that drive the underlying AI and geometry pipelines.

## Key Components

### 1. The Action Registry
Capabilities in `catalog.json` now declare their interactive "Actions".
- **Action ID**: `run_demo`
- **Entrypoint**: `python:orca.capabilities.txt_to_ifc.txt_to_ifc:run`
- **Parameter Schema**: Defines `name`, `width_mm`, `depth_mm`, and `height_mm`.

### 2. The Parameter Modal (Dynamic UI)
When the user clicks **RUN** on a capability in the Progress Dashboard:
- The UI fetches action metadata via `/api/director/capabilities/actions`.
- A modal form is dynamically generated based on the `param_schema`.
- Real-time validation (integer types, min/max bounds) is handled by the browser inputs.

### 3. Safe Execution Bridge
- The Director resolves the Python entrypoint string into a callable function.
- It executes the function in-process (or isolated via sub-process in later versions).
- It generates a unique `run_id` and artifact directory.
- It emits lifecycle events to the Flight Recorder.

### 4. Close-Loop Governance
Every execution automatically:
- Writes a **Run Receipt** to `runtime/director_state/runs/`.
- Updates the **Event Stream** in the Flight Recorder.
- Creates artifacts with a **Cryptographic Manifest**.

## User Value
This milestone enables "Single Click Design-to-BIM", where an operator can observe a field request, click Run, parameterize the design, and instantly produce an auditable IFC asset without ever leaving the Director Console.
