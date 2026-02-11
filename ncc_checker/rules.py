from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class NccClause:
    id: str
    title: str
    description: str
    reference_url: str = ""

@dataclass
class ComplianceResult:
    clause_id: str
    status: str  # PASS, FAIL, CAUTION, NOT_CHECKED
    message: str
    confidence: float  # 0.0 to 1.0

class ComplianceRule:
    def __init__(self, clause: NccClause):
        self.clause = clause

    def check(self, data: Dict[str, Any]) -> ComplianceResult:
        raise NotImplementedError

# --- Specific Rules ---

class SetbackRule(ComplianceRule):
    def __init__(self):
        super().__init__(NccClause(
            id="3.7.1",
            title="Fire Separation - Setbacks",
            description="External walls must be at least 900mm from the boundary or have FRL 60/60/60."
        ))

    def check(self, data: Dict[str, Any]) -> ComplianceResult:
        # Expects: {'boundary_distance_mm': float, 'wall_frl': str}
        # Simplified Logic
        dist = data.get('boundary_distance_mm')
        if dist is None:
            return ComplianceResult(self.clause.id, "NOT_CHECKED", "Missing boundary distance data", 0.0)
        
        if dist >= 900:
            return ComplianceResult(self.clause.id, "PASS", f"Boundary distance {dist}mm >= 900mm", 0.9)
        else:
            frl = data.get('wall_frl', 'None')
            if frl == "60/60/60":
                return ComplianceResult(self.clause.id, "PASS", f"Boundary distance < 900mm but FRL is {frl}", 0.8)
            return ComplianceResult(self.clause.id, "FAIL", f"Boundary distance {dist}mm < 900mm and FRL insufficient ({frl})", 0.95)

class AccessibilityRule(ComplianceRule):
    def __init__(self):
        super().__init__(NccClause(
            id="D3.2",
            title="Access to Buildings",
            description="Accessway required from pedestrian entry to principal entrance."
        ))

    def check(self, data: Dict[str, Any]) -> ComplianceResult:
        # Expects: {'has_step_free_access': bool, 'ramp_gradient': float}
        has_access = data.get('has_step_free_access')
        if has_access is None:
             return ComplianceResult(self.clause.id, "NOT_CHECKED", "Missing accessibility data", 0.0)

        if has_access:
             return ComplianceResult(self.clause.id, "PASS", "Step-free access provided", 0.85)
        return ComplianceResult(self.clause.id, "FAIL", "No step-free access detected", 0.9)

class StructuralClassRule(ComplianceRule):
    def __init__(self):
        super().__init__(NccClause(
            id="A6.1",
            title="Class 1 Buildings",
            description="Classification of buildings and structures."
        ))

    def check(self, data: Dict[str, Any]) -> ComplianceResult:
         # Expects: {'proposed_use': str, 'is_habitable': bool}
         use = data.get('proposed_use', '').lower()
         is_habitable = data.get('is_habitable', False)
         
         if 'dwelling' in use or 'house' in use:
             return ComplianceResult(self.clause.id, "PASS", "Consistent with Class 1a definition", 0.9)
         elif 'garage' in use or 'shed' in use:
             return ComplianceResult(self.clause.id, "PASS", "Consistent with Class 10a definition", 0.9)
         
         return ComplianceResult(self.clause.id, "CAUTION", f"Proposed use '{use}' requires manual verification for classification", 0.5)

# Registry
RULES_REGISTRY = [
    SetbackRule(),
    AccessibilityRule(),
    StructuralClassRule()
]
