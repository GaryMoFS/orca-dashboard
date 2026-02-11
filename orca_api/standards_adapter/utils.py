import re
from typing import Dict, Any

def extract_constraints_from_text(text: str) -> Dict[str, Any]:
    """
    Extracts potential design constraints from natural language text.
    Returns a dictionary of detected parameters.
    """
    constraints = {}

    # Concrete patterns
    concrete_match = re.search(r'\b[N|S](\d{2,3})\b', text)
    if concrete_match:
        constraints['concrete_grade'] = concrete_match.group(0)

    exposure_match = re.search(r'\b[A|B|C]\d\b', text)
    if exposure_match:
        constraints['exposure_class'] = exposure_match.group(0)

    # Steel patterns
    steel_match = re.search(r'\b(250|300|350|400|450)\b', text)
    if steel_match:
        constraints['steel_grade'] = steel_match.group(0)

    # Timber patterns
    wind_match = re.search(r'\b[N|C]\d\b', text)
    if wind_match:
        constraints['wind_class'] = wind_match.group(0)

    timber_grade = re.search(r'\b(F\d+|MGP\d+)\b', text)
    if timber_grade:
        constraints['timber_grade'] = timber_grade.group(0)
    
    # Accessibility
    ramp_dims = re.search(r'ramp.*?(\d+).*?x.*?(\d+)', text, re.IGNORECASE)
    if ramp_dims:
         constraints['ramp_rise'] = float(ramp_dims.group(1))
         constraints['ramp_length'] = float(ramp_dims.group(2))
    
    door_chk = re.search(r'door.*?(\d+)', text, re.IGNORECASE)
    if door_chk:
        constraints['door_width'] = float(door_chk.group(1))

    return constraints

# Mock IFC extractor (placeholder)
def extract_constraints_from_ifc(ifc_entity: Any) -> Dict[str, Any]:
    """
    Extracts parameter data from an IFC entity (mock implementation).
    """
    # In a real implementation, this would parse IfcPropertySets
    return {}
