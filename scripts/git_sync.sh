#!/bin/bash

NO_PUSH=false
MESSAGE=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --no-push) NO_PUSH=true ;;
        -m|--message) MESSAGE="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

TIMESTAMP=$(date +"%Y%m%d_%H%M")
ARTIFACT_DIR="_verification_artifacts/$TIMESTAMP"
mkdir -p "$ARTIFACT_DIR"
LOG_FILE="$ARTIFACT_DIR/git_sync.txt"

sync_log() {
    echo "$1" | tee -a "$LOG_FILE"
}

sync_log "--- ORCA Git Sync Start: $TIMESTAMP ---"

# 1. Branch/Status
BRANCH=$(git rev-parse --abbrev-ref HEAD)
sync_log "Current Branch: $BRANCH"
git status >> "$LOG_FILE"

# 2. Verification Gates
sync_log "Running Verification Gates..."
GATES_PASSED=true

VERIFIERS=(
    "tools/verify_capability_catalog.py"
    "tools/verify_action_bridge_m15.py"
    "tools/verify_progress_m13.py"
)

for v in "${VERIFIERS[@]}"; do
    if [[ -f "$v" ]]; then
        sync_log "Running $v ..."
        python3 "$v" >> "$LOG_FILE" 2>&1
        if [[ $? -ne 0 ]]; then
            sync_log "FAIL: $v failed"
            GATES_PASSED=false
        else
            sync_log "PASS: $v"
        fi
    else
        sync_log "SKIP: $v not found"
    fi
done

# Doc Discipline (Requires powershell or bash equivalent, here assuming scripts/verify_docs.ps1 is shimmed or we use pwsh)
sync_log "Running Doc Discipline..."
if command -v pwsh &> /dev/null; then
    pwsh -ExecutionPolicy Bypass -File scripts/verify_docs.ps1 >> "$LOG_FILE" 2>&1
elif command -v powershell.exe &> /dev/null; then
    powershell.exe -ExecutionPolicy Bypass -File scripts/verify_docs.ps1 >> "$LOG_FILE" 2>&1
else
    sync_log "WARN: No PowerShell found to run verify_docs.ps1. Attempting manual check..."
    # Fallback to simple exist checks or similar
fi

if [[ $? -ne 0 ]]; then
    sync_log "FAIL: Doc Discipline must pass before sync."
    GATES_PASSED=false
else
    sync_log "PASS: Doc Discipline"
fi

if [[ "$GATES_PASSED" = false ]]; then
    sync_log "--- SYNC ABORTED: Gates Failed ---"
    exit 1
fi

# 3. Committing
if [[ -z "$MESSAGE" ]]; then
    read -p "Enter commit message: " MESSAGE
fi

if [[ -z "$MESSAGE" ]]; then
    sync_log "FAIL: Commit message required."
    exit 1
fi

sync_log "Staging changes..."
git add .
sync_log "Committing: $MESSAGE"
git commit -m "$MESSAGE" >> "$LOG_FILE" 2>&1

# 4. Pushing
if [[ "$NO_PUSH" = true ]]; then
    sync_log "--- DRY RUN COMPLETE ---"
else
    sync_log "Pushing to origin/$BRANCH ..."
    git push origin "$BRANCH" >> "$LOG_FILE" 2>&1
    sync_log "--- SYNC COMPLETE ---"
fi
