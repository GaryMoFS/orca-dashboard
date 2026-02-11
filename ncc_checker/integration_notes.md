# NCC/BCA Integration Notes

## Purpose
The `ncc_checker` module provides automated compliance checking against the National Construction Code (NCC) and Building Code of Australia (BCA).
This is a *demonstrator* capability and does not constitute legal advice.

## Module Structure
- `checker.py`: Main entry point.
- `rules.py`: Defines compliance rules (Setbacks, Fire, Access, Structure).
- `extractors.py`: Handles input parsing (Text, Sketch JSON, IFC).
- `reporter.py`: Generates reports.

## Inputs
1. **IFC Models**: Currently mocked. Future integration should use `IfcOpenShell` or similar to parse actual `.ifc` files.
2. **Text Descriptions**: Uses simple keyword matching. Can be enhanced with LLM-based extraction (e.g., extracting "900mm setback" from natural language).
3. **Sketch Geometry**: Expects a JSON structure representing sketch elements. This should be aligned with the output of the `sketch_ifc` module in the future.

## Integration Plan

### Phase 1: Standalone Demo (Current)
- The module runs independently via `demo.py`.
- Mocked inputs simulate the data flow.

### Phase 2: Sketch Integration
- Update `extractors.SketchGeometryExtractor` to parsing the actual JSON export format from the Sketch pipeline.
- Trigger compliance checks automatically when a sketch is "committed" or saved.

### Phase 3: IFC Pipeline Integration
- Integrate `IfcOpenShell` into `extractors.IfcExtractor`.
- Add a new API endpoint in `orca_api` to accept an IFC file upload, run `NccChecker`, and return the JSON report.

### Phase 4: Dashboard Visualization
- Update the Orca Dashboard to render the compliance report.
- Visualize "Fail" conditions directly on the 3D model (e.g., highlighting a wall that is too close to the boundary).

## Future Capabilities
- **LLM-Enhanced Rules**: Use an LLM to interpret complex clauses and apply them to the extracted data.
- **Rule Engine**: Move rules to a database or external configuration file for easier updates.
- **Detailed Reporting**: Generate PDF reports with diagrams.
