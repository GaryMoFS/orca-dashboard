from typing import Dict, List, Optional

class AS1684:
    """
    Structured summary and reference logic for AS 1684 Residential Timber-Framed Construction.
    """

    WIND_CLASSIFICATIONS = {
        "N1": "Protected non-cyclonic",
        "N2": "Non-cyclonic, minimal shielding",
        "N3": "Non-cyclonic, exposed",
        "N4": "Non-cyclonic, exposed (severe)",
        "N5": "Non-cyclonic, exposed (extreme)",
        "N6": "Non-cyclonic, exposed (catastrophic)",
        "C1": "Cyclonic, protected",
        "C2": "Cyclonic, exposed",
        "C3": "Cyclonic, exposed (severe)",
        "C4": "Cyclonic, exposed (extreme)"
    }

    # Reference data for timber grades (stress grades)
    STRESS_GRADES = {
        "F4": 4, "F5": 5, "F7": 8, "F8": 10, "F11": 15, "F14": 20, "F17": 25,
        "MGP10": 10, "MGP12": 15, "MGP15": 21
    }

    REFERENCE_DOC = "AS 1684.2-2010 Residential Timber-Framed Construction"

    @staticmethod
    def validate_wind_class(classification: str) -> bool:
        """Checks if a wind classification is a standard AS 1684 classification."""
        return classification in AS1684.WIND_CLASSIFICATIONS

    @staticmethod
    def validate_grade(grade: str) -> bool:
        """Checks if a timber stress grade is standard."""
        return grade in AS1684.STRESS_GRADES

    @staticmethod
    def generate_note(wind_class: str, grade: str) -> str:
        """Generates a standard advisory note."""
        wind_desc = AS1684.WIND_CLASSIFICATIONS.get(wind_class, "Unknown")
        grade_desc = AS1684.STRESS_GRADES.get(grade, "Unknown")
        
        note = f"Standard Reference: {AS1684.REFERENCE_DOC}\n"
        note += f"- Wind Classification: {wind_class} ({wind_desc})\n"
        note += f"- Timber Stress Grade: {grade} (Bending Strength: {grade_desc} MPa)\n"
        return note
