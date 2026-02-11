from typing import Dict, Any, List

class Extractor:
    def extract(self, input_data: Any) -> Dict[str, Any]:
        """Extract relevant data for compliance checking."""
        raise NotImplementedError

class TextExtractor(Extractor):
    def extract(self, input_text: str) -> Dict[str, Any]:
        """Simple keyword matching for demonstration."""
        extracted = {}
        text = input_text.lower()
        
        # Setback logic
        if "setback" in text:
            import re
            match = re.search(r'setback (\d+)mm', text)
            if match:
                extracted['boundary_distance_mm'] = int(match.group(1))

        # Fire rating logic
        if "frl" in text:
             import re
             match = re.search(r'frl (\d+/\d+/\d+)', text)
             if match:
                 extracted['wall_frl'] = match.group(0)

        # Accessibility logic
        if "ramp" in text or "step-free" in text:
            extracted['has_step_free_access'] = True
        elif "stairs only" in text:
            extracted['has_step_free_access'] = False

        # Structural logic
        if "dwelling" in text or "house" in text:
            extracted['proposed_use'] = 'dwelling'
            extracted['is_habitable'] = True
        elif "garage" in text:
            extracted['proposed_use'] = 'garage'
            extracted['is_habitable'] = False

        return extracted

class SketchGeometryExtractor(Extractor):
    def extract(self, sketch_json: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from a sketch JSON representation."""
        extracted = {}
        
        # Extract boundary distance
        if 'boundary_ref' in sketch_json:
            extracted['boundary_distance_mm'] = sketch_json['boundary_ref'].get('distance_mm', 0)
        
        # Extract access features
        features = sketch_json.get('features', [])
        if 'ramp' in features:
            extracted['has_step_free_access'] = True
        else:
             extracted['has_step_free_access'] = False # Default assumption for demo

        # Extract usage
        extracted['proposed_use'] = sketch_json.get('building_type', 'unknown')
        
        return extracted

class IfcExtractor(Extractor):
    def extract(self, ifc_path: str) -> Dict[str, Any]:
        """Mock extraction from an IFC file path."""
        # In a real implementation, this would use IfcOpenShell
        print(f"DEBUG: Mocking IFC extraction from {ifc_path}")
        return {
            'building_storeys': 2,
            'boundary_distance_mm': 1200, # Mock value
            'wall_frl': 'n/a',
            'has_step_free_access': True, # Mock value
            'proposed_use': 'dwelling'
        }
