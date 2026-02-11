from typing import List, Dict, Any
from .rules import ComplianceResult
import json

class Reporter:
    def generate_text_report(self, results: List[ComplianceResult]) -> str:
        """Generate a simple text report."""
        report = ["# NCC Compliance Report\n"]
        report.append("## Summary")
        
        pass_count = sum(1 for r in results if r.status == "PASS")
        fail_count = sum(1 for r in results if r.status == "FAIL")
        caution_count = sum(1 for r in results if r.status == "CAUTION")
        
        report.append(f"PASSED: {pass_count}")
        report.append(f"FAILED: {fail_count}")
        report.append(f"CAUTION: {caution_count}\n")
        
        report.append("## Detailed results")
        for result in results:
            icon = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⚠️"
            report.append(f"{icon} {result.clause_id}: {result.status}")
            report.append(f"   Message: {result.message}")
            report.append(f"   Confidence: {result.confidence * 100:.1f}%")
            report.append("")
            
        return "\n".join(report)

    def generate_json_report(self, results: List[ComplianceResult]) -> str:
        """Generate a detailed JSON report."""
        data = []
        for r in results:
            data.append({
                'clause_id': r.clause_id,
                'status': r.status,
                'message': r.message,
                'confidence': r.confidence
            })
        return json.dumps(data, indent=2)
