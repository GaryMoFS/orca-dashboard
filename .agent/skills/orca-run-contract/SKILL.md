---
name: orca-run-contract
description: Run contract for Orca AI dashboard r1. Enforces source-of-truth doc updates, verification commands, and non-breaking changes.
---

# ORCA Run Contract (Always-On)

## Workspace root
C:\Users\Gary\Documents\Projects\Orca AI dashboard

## Source-of-truth docs (MUST update every run)
- C:\Users\Gary\Documents\Projects\Orca AI dashboard\Antigrav Change Ledger.md
- C:\Users\Gary\Documents\Projects\Orca AI dashboard\investor_demo_story.md

## Non-negotiables
1) Do not break existing working modules.
2) Prefer data-driven additions (JSON manifests) over hardcoded UI changes.
3) Every run MUST:
   - List files created/modified
   - Run verification commands (and record outputs)
   - Append a new run entry to “Antigrav Change Ledger.md”
   - Update “investor_demo_story.md” if milestone/status changed

## Required append-only ledger format (write to Antigrav Change Ledger.md)
Append ONE new section per run:

## Run - YYYYMMDD HHMM
### Executive Summary
### Detailed Changes
- Files created:
- Files modified:
### Verification
- Commands:
- Outputs:
### Status
- PASS/FAIL and why
### Next Step
- One small recommended step only

## How to use this skill
At the start of any run, explicitly state:
“Using skill: orca-run-contract”
Then follow the rules above.
