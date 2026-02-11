# ORCA Git Workflow

This document outlines the "Local-first -> GitHub sync" workflow for developing the ORCA AI dashboard.

## 1. Branching Strategy
We use **Feature Branches** for every milestone or quest. Direct commits to `main` are prohibited.

- **main**: Protected. Contains production-ready demo code.
- **feature/M##-<short-name>**: Where development happens (e.g., `feature/M16-pdf-parsing`).

### Creating a new branch:
```bash
git checkout -b feature/M16-pdf-parsing
```

## 2. Commit Message Convention
Commits should be atomic and descriptive, prefixed by the Milestone ID.

**Format**: `M##: <summary of changes>`
**Example**: `M14: Implement room geometry generator for txt_to_ifc`

## 3. The Sync Loop
Before pushing to GitHub, you MUST run the verification gates.

1. **Develop** local code.
2. **Verify**: Run `scripts/git_sync.ps1` (Windows) or `scripts/git_sync.sh` (WSL).
3. **Ledger**: Ensure `Antigrav Change Ledger.md` is updated.
4. **Push**: Only after gates pass.

```powershell
.\scripts\git_sync.ps1 --no-push
```

## 4. Artifact Policy
- `_verification_artifacts/` is ignored by git to prevent repo bloat.
- To keep a specific run as permanent proof, move it to:
  `_verification_artifacts/.keep/<YYYYMMDD_HHMM>/`

## 5. Pull Requests
- Push your feature branch to `origin`.
- Open a PR into `main`.
- Include the `verification_log.txt` from your latest run in the PR description.
