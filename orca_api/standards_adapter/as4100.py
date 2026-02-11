from typing import Dict, List, Optional

class AS4100:
    """
    Structured summary and reference logic for AS 4100 Steel Structures.
    """

    STEEL_GRADES = {
        "250": 250, "300": 300, "350": 350, "400": 400, "450": 450,
        "L0": 250, "L15": 300, "L25": 350, "L35": 400, "L50": 450
    }

    BOLT_GRADES = {
        "PC 4.6": 400,
        "PC 8.8": 800,
        "PC 10.9": 1000
    }

    # Reference data for standard sections and material properties
    SLENDERNESS_LIMITS_COMPRESSION = {
        "Class 1": 15,
        "Class 2": 20,
        "Class 3": 25,
        "Class 4": 30
    }
    
    REFERENCE_DOC = "AS 4100:1998 Steel Structures"

    @staticmethod
    def validate_grade(grade: str) -> bool:
        """Checks if a steel grade is a standard AS 4100 grade."""
        return grade in AS4100.STEEL_GRADES

    @staticmethod
    def get_bolt_info(grade: str) -> Optional[int]:
        """Provides tensile strength for standard bolt grades."""
        return AS4100.BOLT_GRADES.get(grade)

    @staticmethod
    def generate_note(grade: str) -> str:
        """Generates a standard advisory note."""
        strength = AS4100.STEEL_GRADES.get(grade)
        
        note = f"Standard Reference: {AS4100.REFERENCE_DOC}\n"
        if strength:
            note += f"- Steel Grade: {grade} (Yield Strength: {strength} MPa)\n"
        else:
            note += f"- Steel Grade: {grade} (Non-Standard/Check)\n"
        return note
