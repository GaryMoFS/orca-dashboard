# ORCA Release Checklist

Before marking a milestone as `PASS` and syncing to GitHub:

- [ ] **Functional PASS**: Run the milestone-specific verifier (e.g. `python tools/verify_action_bridge_m15.py`).
- [ ] **Regression PASS**: Run legacy Q1-Q4 verifiers.
- [ ] **Schema Check**: Any new JSON state must have a schema in `orca/engine/schemas/`.
- [ ] **Ledger Update**: Append the new run to `Antigrav Change Ledger.md` with artifact paths.
- [ ] **Story Sync**: Update `investor_demo_story.md` if the demo narrative has changed.
- [ ] **Roadmap Sync**: Update `ROADMAP.md` status.
- [ ] **Doc Discipline**: Run `.\scripts\verify_docs.ps1` and ensure it returns `PASS`.
- [ ] **Sync**: Run `.\scripts\git_sync.ps1` to stage, commit, and push.
- [ ] **GitHub PR**: Open a PR into `main` and link the verification artifacts.
