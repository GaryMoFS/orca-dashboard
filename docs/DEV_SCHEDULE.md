# ORCA Development Schedule

This is a living document for tracking actionable, testable tasks. All entries must follow the $DoD + Verification$ contract.

## NOW (Next 1–3 Sessions)

### A) M9 Marketplace UI: Catalog Browser
- **Owner**: Antigravity / Gary
- **Definition of Done (DoD)**: Marketplace side-panel or modal loads contents of `GET /runtime/persona/list` and `catalog.json`, rendering persona cards with status (Free/Paid/Locked).
- **Verification**: 
  - `python -m orca_runtime.main`
  - Open Dashboard -> Click "Store" -> Confirm cards match `orca/marketplace/catalog.json`.
- **Docs**: `Antigrav Change Ledger.md`

### B) M9 Marketplace UI: Preview Flow
- **Owner**: Antigravity
- **Definition of Done (DoD)**: Clicking a locked persona in the Marketplace triggers a `LOCKED_PREVIEW` layout via the `/runtime/persona/preview` endpoint, rendering the "Locked Mode" banner in the UI.
- **Verification**: 
  - `python tools/verify_persona_api.py` (ensure preview endpoint returns correct modules).
  - Manual check: Click "Professional" in Store -> Dashboard layout updates to Pro view with Red Banner.
- **Docs**: `Antigrav Change Ledger.md`

### C) M9 Marketplace UI: Activation (MVP)
- **Owner**: Antigravity
- **Definition of Done (DoD)**: "Activate" button writes the persona SKU to `orca/licenses/grants.json` and triggers a layout refresh. Persona status must move from `LOCKED_PREVIEW` to `UNLOCKED`.
- **Verification**: 
  - `type orca\licenses\grants.json` (Verify SKU presence after click).
  - `python tools/validate_persona_schemas.py` (Verify grants still match schema).
- **Docs**: `Antigrav Change Ledger.md`, `investor_demo_story.md` (Update M9 to PASS).

---

## NEXT

### D) Marketplace: Creator Pack Workflow
- **Owner**: Gary / Antigravity
- **Definition of Done (DoD)**: Documentation and simple script/installer for packaging new personas (manifest + theme + layout) into the `installed/` directory.
- **Verification**: `python tools/install_persona.py sample_persona_pack.zip`
- **Docs**: `Antigrav Change Ledger.md`

### E) Security Hardening: Locked Mode Enforcement
- **Owner**: Antigravity
- **Definition of Done (DoD)**: Ensure all mutation buttons and protected API calls (bundle generation, audit access) are consistently blocked at the runtime level when in `LOCKED_PREVIEW` status, not just hidden in UI.
- **Verification**: `curl -X POST http://127.0.0.1:7010/runtime/audit/protected_call` (Should return 403 when locked).
- **Docs**: `Antigrav Change Ledger.md`

---

## LATER

### F) Real Entitlements / Payment Integration
- **Owner**: Gary
- **Definition of Done (DoD)**: Replace local `grants.json` stub with an external auth/entitlement check or mock payment bridge.
- **Verification**: TBD

### G) Enterprise Policy Overlays
- **Owner**: Gary / Antigravity
- **Definition of Done (DoD)**: Support for organization-wide "Policy" overrides that can force-disable specific persona modules regardless of user grants.
- **Verification**: TBD
