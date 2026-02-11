from typing import Dict, Any, List, Optional
from .as3600 import AS3600
from .as4100 import AS4100
from .as1684 import AS1684
from .accessibility import AccessibilityStandards
from .utils import extract_constraints_from_text

class StandardsAdapter:
    """
    Main integration point for Australian Standards compliance checking.
    """

    def __init__(self):
        self.as3600 = AS3600()
        self.as4100 = AS4100()
        self.as1684 = AS1684()
        self.accessibility = AccessibilityStandards
        self.custom_checks = {}

    def register_custom_check(self, name: str, check_func: callable):
        """
        Register a custom compliance check function.
        check_func should accept the extracted constraints dict and return a note string or None.
        """
        self.custom_checks[name] = check_func

    def process_query(self, query_text: str) -> Dict[str, Any]:
        """
        Takes a natural language query/description, extracts constraints,
        checks against relevant standards, and returns structured advisory notes.
        """
        extracted = extract_constraints_from_text(query_text)
        report = {
            "query": query_text,
            "extracted_constraints": extracted,
            "advisory_notes": []
        }

        # Dispatch based on extracted constraints
        if 'concrete_grade' in extracted:
            grade = extracted['concrete_grade']
            exposure = extracted.get('exposure_class', 'A1') # Default to A1
            note = self.as3600.generate_note(grade, exposure)
            report['advisory_notes'].append({"standard": "AS 3600", "content": note})

        if 'steel_grade' in extracted:
            grade = extracted['steel_grade']
            note = self.as4100.generate_note(grade)
            report['advisory_notes'].append({"standard": "AS 4100", "content": note})

        if 'timber_grade' in extracted:
            t_grade = extracted['timber_grade']
            w_class = extracted.get('wind_class', 'N1') # Default
            note = self.as1684.generate_note(w_class, t_grade)
            report['advisory_notes'].append({"standard": "AS 1684", "content": note})

        if 'ramp_rise' in extracted and 'ramp_length' in extracted:
            rise = extracted['ramp_rise']
            length = extracted['ramp_length']
            # Assume 850mm door width if not specified, just for report completeness relative to query
            door_w = extracted.get('door_width', 850) 
            note = self.accessibility.generate_note(rise, length, door_w)
            report['advisory_notes'].append({"standard": "AS 1428", "content": note})

        elif 'door_width' in extracted: # Check door independently if ramp not present
            door_w = extracted['door_width']
            status = self.accessibility.check_door(door_w)
            note = f"Standard Reference: {self.accessibility.REFERENCE_DOC}\n- Door Assessment: {status}"
            report['advisory_notes'].append({"standard": "AS 1428", "content": note})
        
        # Execute custom checks
        for name, func in self.custom_checks.items():
            try:
                custom_note = func(extracted)
                if custom_note:
                    report['advisory_notes'].append({"standard": f"Custom ({name})", "content": custom_note})
            except Exception as e:
                report['advisory_notes'].append({"standard": f"Custom ({name})", "content": f"Error: {str(e)}"})

        return report

# Integration Hook (Example)
def check_compliance(text_input: str) -> Dict[str, Any]:
    adapter = StandardsAdapter()
    return adapter.process_query(text_input)
