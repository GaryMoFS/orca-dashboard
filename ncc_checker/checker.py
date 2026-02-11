from typing import List, Dict, Any
from .rules import RULES_REGISTRY, ComplianceRule, ComplianceResult
from .extractors import TextExtractor, SketchGeometryExtractor, IfcExtractor

class NccChecker:
    def __init__(self):
        self.rules: List[ComplianceRule] = RULES_REGISTRY
        self.text_extractor = TextExtractor()
        self.sketch_extractor = SketchGeometryExtractor()
        self.ifc_extractor = IfcExtractor()

    def check_text(self, text_input: str) -> List[ComplianceResult]:
        """Run checks against text input."""
        data = self.text_extractor.extract(text_input)
        return self._run_checks(data)

    def check_sketch(self, sketch_json: Dict[str, Any]) -> List[ComplianceResult]:
        """Run checks against sketch JSON input."""
        data = self.sketch_extractor.extract(sketch_json)
        return self._run_checks(data)

    def check_ifc(self, ifc_path: str) -> List[ComplianceResult]:
        """Run checks against IFC file input."""
        data = self.ifc_extractor.extract(ifc_path)
        return self._run_checks(data)

    def _run_checks(self, data: Dict[str, Any]) -> List[ComplianceResult]:
        results = []
        for rule in self.rules:
            # Only run the rule if we have relevant data
            # For this simplified demo, we just try to run it.
            # Real implementation would check data requirements first.
            try:
                result = rule.check(data)
                results.append(result)
            except Exception as e:
                # Log error or return a "CHECK FAILED" result
                print(f"Error checking rule {rule.clause.id}: {e}")
                results.append(ComplianceResult(
                    rule.clause.id, "ERROR", f"Internal error during check: {str(e)}", 0.0
                ))
        return results
