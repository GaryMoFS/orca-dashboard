# ORCA Standards Adapter

This module provides a structured way for the ORCA design workflow to reference Australian Standards (AS) and generate advisory notes. It is not a certification tool but serves as a "compliance co-pilot" to flag potential issues or suggest standard specifications.

## Supported Standards

1.  **AS 3600 (Concrete Structures)**
    - Checks concrete strength grades (N20, N32, etc.)
    - Suggests exposure classification descriptions (A1, B1, C2, etc.)
    - Provides advisory minimum cover notes.

2.  **AS 4100 (Steel Structures)**
    - Verifies standard steel grades (250, 300, 350, etc.)
    - Lists yield strengths.

3.  **AS 1684 (Residential Timber-Framed Construction)**
    - Validates wind classifications (N1-N6, C1-C4).
    - Checks standard timber stress grades (F5, F17, MGP10, etc.).

4.  **AS 1428.1 (Design for Access and Mobility)**
    - Checks ramp gradients (Max 1:14).
    - Checks minimum door widths.

## Integration

### Basic Usage

You can use the high-level `check_compliance` function or the `StandardsAdapter` class directly.

```python
from orca_api.standards_adapter import check_compliance

# Text-based query processing
result = check_compliance("I need a ramp with 150mm rise and 1800mm run.")

# Access advisory notes
for note in result['advisory_notes']:
    print(note['content'])
```

### Custom Checks (Hooks)

The system allows registering custom, project-specific rules that run alongside standard checks.

```python
from orca_api.standards_adapter import StandardsAdapter

def strict_fire_check(constraints):
    if constraints.get('timber_grade') and constraints.get('bushfire_zone') == 'BAL-FZ':
        return "CRITICAL: Timber may not be suitable for BAL-FZ. Check AS 3959."

adapter = StandardsAdapter()
adapter.register_custom_check("Bushfire Overlay", strict_fire_check)

result = adapter.process_query("Frame using F17 timber in BAL-FZ area.")
```

## Module Structure

- `core.py`: Main `StandardsAdapter` logic and orchestration.
- `utils.py`: Regex extraction tools for parsing natural language or simple text constraints.
- `as3600.py`, `as4100.py`, `as1684.py`, `accessibility.py`: Individual standard logic modules.
- `usage_example.py`: Demonstration script.

## Disclaimer

**Verify all outputs.** This software provides advisory information only and does not replace professional engineering certification or review against the full, current Australian Standards.
