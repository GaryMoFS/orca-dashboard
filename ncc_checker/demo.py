from ncc_checker.checker import NccChecker
from ncc_checker.reporter import Reporter
from ncc_checker.rules import ComplianceResult, NccClause

def demo_text():
    print("\n--- TEXT INPUT DEMO ---")
    text_input = """
    Proposed dwelling at 123 Fake St.
    Setback from boundary is 1200mm.
    Uses FRL 60/60/60 for side walls.
    Access via stairs only.
    Use: Habitable dwelling.
    """
    
    checker = NccChecker()
    results = checker.check_text(text_input)
    
    reporter = Reporter()
    print(reporter.generate_text_report(results))

def demo_sketch():
    print("\n--- SKETCH JSON DEMO ---")
    sketch_json = {
        "building_type": "garage",
        "boundary_ref": {
            "distance_mm": 500
        },
        "features": ["roller_door"], # No ramp
        "wall_frl": "None"
    }

    checker = NccChecker()
    results = checker.check_sketch(sketch_json)
    
    reporter = Reporter()
    print(reporter.generate_text_report(results))

def demo_ifc():
    print("\n--- IFC FILE DEMO (Mocked) ---")
    ifc_path = "c:\\temp\\project_alpha.ifc"
    
    checker = NccChecker()
    results = checker.check_ifc(ifc_path)
    
    reporter = Reporter()
    print(reporter.generate_text_report(results))

if __name__ == "__main__":
    demo_text()
    demo_sketch()
    demo_ifc()
