from typing import Dict, List, Optional

class AS3600:
    """
    Structured summary and reference logic for AS 3600 Concrete Structures.
    """

    CONCRETE_CHARACTERISTIC_STRENGTHS = {
        "N20": 20, "N25": 25, "N32": 32, "N40": 40, "N50": 50,
        "S65": 65, "S80": 80, "S100": 100
    }

    # Simplified exposure classifications based on AS 3600 Table 4.3
    EXPOSURE_CLASSIFICATIONS = {
        "A1": "Inland, non-industrial",
        "A2": "Inland, industrial or <50km from coast",
        "B1": "Coastal, 1km-50km from coast",
        "B2": "Coastal, <1km from coast",
        "C1": "Splash zone or tidal",
        "C2": "Aggressive soil/groundwater",
        "U": "Undefined/To be specified"
    }

    # Simplified cover requirements (mm) for standard formwork, ignoring specialized cases
    # (Exposure Class -> Minimum Cover) - indicative only
    MINIMUM_COVER_INTENT = {
        "A1": 20,
        "A2": 25,
        "B1": 30,
        "B2": 45,
        "C1": 50,
        "C2": 50
    }
    
    REFERENCE_DOC = "AS 3600:2018 Concrete Structures"

    @staticmethod
    def validate_strength(grade: str) -> bool:
        """Checks if a concrete grade is a standard AS 3600 grade."""
        return grade in AS3600.CONCRETE_CHARACTERISTIC_STRENGTHS

    @staticmethod
    def get_exposure_description(classification: str) -> str:
        """Returns description for a given exposure classification."""
        return AS3600.EXPOSURE_CLASSIFICATIONS.get(classification, "Unknown Classification")

    @staticmethod
    def get_advisory_cover(classification: str) -> str:
        """
        Returns advisory minimum cover string based on simplified logic.
        WARNING: This is not certification. Consult Engineer.
        """
        cover = AS3600.MINIMUM_COVER_INTENT.get(classification)
        if cover:
            return f"Advisory: {cover}mm minimum cover for {classification} (Ref: {AS3600.REFERENCE_DOC})"
        return f"Advisory: Consult engineer for {classification} cover requirements."

    @staticmethod
    def generate_note(grade: str, exposure: str) -> str:
        """Generates a standard advisory note."""
        strength_valid = AS3600.validate_strength(grade)
        exposure_desc = AS3600.get_exposure_description(exposure)
        
        note = f"Standard Reference: {AS3600.REFERENCE_DOC}\n"
        note += f"- Concrete Grade: {grade} ({'Standard' if strength_valid else 'Non-Standard/Check'})\n"
        note += f"- Exposure Environment: {exposure} ({exposure_desc})\n"
        return note
