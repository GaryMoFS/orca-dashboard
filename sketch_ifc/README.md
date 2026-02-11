# ORCA Sketch-to-IFC Pipeline

This module provides a lightweight pipeline to convert sketch images into IFC building models, with a web-based VR preview.

## Components

1.  **Stage 1: Sketch Interpretation (`processor.py`)**
    - Uses OpenCV to detect walls from sketch images (currently black lines on white background).
    - Outputs a JSON schema defining walls and basic geometry.

2.  **Stage 2 & 3: Geometry Construction & IFC Export (`builder.py`)**
    - Uses `IfcOpenShell` to generate a standard IFC4 file.
    - Creates `IfcWall` entities with proper placement.
    - Autogenerates an `IfcSlab` (Floor) based on wall footprint.
    - Outputs `.ifc` files compatible with Revit, ArchiCAD, BlenderBIM.

3.  **Stage 4: VR Preview (`app.py` + `templates/`)**
    - Flask web server.
    - Converts IFC geometry to GLB (using `trimesh`).
    - Embeds a `<model-viewer>` for WebXR/AR viewing on mobile or desktop.

## Installation

Ensure you have the required Python packages:

```bash
pip install ifcopenshell trimesh opencv-python-headless numpy flask
```

## Running the Demo

1.  **Start the Web Interface:**
    ```bash
    cd sketch_ifc
    python app.py
    ```
    Open `http://127.0.0.1:5001` in your browser.

2.  **Generate a Sample Manually:**
    ```bash
    python generate_example.py
    ```
    This creates `example_output/sample.ifc` and `example_output/sample.glb`.

## Integration Notes

-   **Headless Operation:** The pipeline supports headless operation (no GPU required for IFC generation). GLB export uses software rendering logic via `trimesh` + `ifcopenshell`.
-   **Extensibility:** Modify `processor.py` to connect to ORCA's LLM vision services for better semantic labeling of rooms/openings.
-   **Performance:** Processing is local and CPU-based. Complex sketches take < 2 seconds.

## Constraints & Limitations

-   Current wall detection assumes clear, high-contrast, closed-loop sketches.
-   Roof generation is not yet implemented (Floor slab is included).
-   Scale is estimated based on image width assumption (10m).
