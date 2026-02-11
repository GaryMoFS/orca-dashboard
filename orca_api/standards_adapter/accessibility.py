from typing import Dict, List, Optional

class AccessibilityStandards:
    """
    Structured summary and reference logic for Accessibility Standards (AS 1428).
    """

    REFERENCE_DOC = "AS 1428.1-2009 Design for Access and Mobility"

    RAMP_GRADIENT_MAX = {
        "1:14": "Standard ramp max gradient (preferred 1:20)",
        "1:10": "Step ramp max gradient (max rise 190mm)",
        "1:8": "Kerb ramp max gradient (max rise 152mm)",
        "1:33": "Walkway gradient limit",
        "1:40": "Minimum gradient for drainage"
    }

    # Simplified clear width requirements
    DOOR_WIDTH_MIN = {
        "Continuous accessible": 850,
        "Passage": 1000,
        "Toilet door": 850,
        "Circulation space": 1200
    }

    @staticmethod
    def check_ramp(rise: float, length: float) -> str:
        """
        Calculates gradient and checks against AS 1428 limits.
        WARNING: Simplified check.
        """
        gradient = rise / length
        if gradient > 1/14:
            return f"Non-Compliant: Gradient {gradient:.2f} (Max 1:14)"
        elif gradient > 1/20:
             return f"Acceptable: Gradient {gradient:.2f} (Standard Ramp)"
        else:
             return f"Compliant: Gradient {gradient:.2f} (Walkway)"

    @staticmethod
    def check_door(width: float) -> str:
        """Checks door width against minimum requirements."""
        if width < 850:
            return f"Non-Compliant: Width {width}mm (Min 850mm)"
        else:
            return f"Compliant: Width {width}mm"
    
    @staticmethod
    def generate_note(rise: float, length: float, door_width: float) -> str:
        """Generates a standard advisory note."""
        ramp_status = AccessibilityStandards.check_ramp(rise, length)
        door_status = AccessibilityStandards.check_door(door_width)
        
        note = f"Standard Reference: {AccessibilityStandards.REFERENCE_DOC}\n"
        note += f"- Ramp Assessment: {ramp_status}\n"
        note += f"- Door Assessment: {door_status}\n"
        return note
