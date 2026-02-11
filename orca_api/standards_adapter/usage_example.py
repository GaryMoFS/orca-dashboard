from orca_api.standards_adapter.core import StandardsAdapter, check_compliance


def my_site_specific_check(constraints):
    # Example custom check: if "heritage" is mentioned, add a note
    # (Note: 'heritage' isn't currently extracted, let's use something we do extract)
    # Let's say we have a site rule: No timber in Wind Class C4
    if constraints.get('wind_class') == 'C4' and 'timber_grade' in constraints:
        return "SITE RULE: Timber construction prohibited in Cyclonic C4 zones."
    return None

def run_examples():
    adapter = StandardsAdapter()
    adapter.register_custom_check("Site Specific Rules", my_site_specific_check)


    with open("standards_report.txt", "w") as f:
        # Example 1: Concrete
        f.write("-" * 30 + "\n")
        f.write("Example 1: Concrete N32 in B1 environment\n")
        result1 = adapter.process_query("I need to use N32 concrete for a B1 exposure classification.")
        f.write(f"Constraints: {result1['extracted_constraints']}\n")
        for note in result1['advisory_notes']:
            f.write(f"Note:\n{note['content']}\n")

        # Example 2: Steel
        f.write("\n" + "-" * 30 + "\n")
        f.write("Example 2: Steel structure with grade 350\n")
        result2 = check_compliance("Check compliance for a 350 grade steel beam.")
        f.write(f"Constraints: {result2['extracted_constraints']}\n")
        for note in result2['advisory_notes']:
            f.write(f"Note:\n{note['content']}\n")

        # Example 3: Accessibility Ramp
        f.write("\n" + "-" * 30 + "\n")
        f.write("Example 3: Access ramp 1:12 check\n")
        # "ramp 150x1800" -> rise=150, length=1800 -> 1:12
        result3 = check_compliance("Design includes a ramp 150x1800 mm.")
        f.write(f"Constraints: {result3['extracted_constraints']}\n")
        for note in result3['advisory_notes']:
            f.write(f"Note:\n{note['content']}\n")
    
        # Example 4: Custom Site Rule Check
        f.write("\n" + "-" * 30 + "\n")
        f.write("Example 4: C4 wind zone with timber (should trigger custom rule)\n")
        result4 = adapter.process_query("Plan uses F17 timber in C4 wind zone.")
        f.write(f"Constraints: {result4['extracted_constraints']}\n")
        for note in result4['advisory_notes']:
            f.write(f"Note:\n{note['content']}\n")
    
    print("Report written to standards_report.txt")

if __name__ == "__main__":
    run_examples()
