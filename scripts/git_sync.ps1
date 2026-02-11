param (
    [switch]$NoPush,
    [string]$Message
)

$timestamp = Get-Date -Format "yyyyMMdd_HHmm"
$artifact_dir = "_verification_artifacts\$timestamp"
New-Item -ItemType Directory -Force -Path $artifact_dir | Out-Null
$log_file = "$artifact_dir\git_sync.txt"

function Write-SyncLog($msg) {
    Write-Host $msg
    $msg | Out-File -Append -FilePath $log_file
}

Write-SyncLog "--- ORCA Git Sync Start: $timestamp ---"

# 1. Branch/Status
$branch = git rev-parse --abbrev-ref HEAD
Write-SyncLog "Current Branch: $branch"
git status | Out-File -Append -FilePath $log_file

# 2. Verification Gates
Write-SyncLog "`nRunning Verification Gates..."
$gates_passed = $true

$verifiers = @(
    "tools/verify_capability_catalog.py",
    "tools/verify_action_bridge_m15.py",
    "tools/verify_progress_m13.py"
)

foreach ($v in $verifiers) {
    if (Test-Path $v) {
        Write-SyncLog "Running $v ..."
        python $v 2>&1 | Tee-Object -FilePath $log_file -Append
        if ($LASTEXITCODE -ne 0) {
            Write-SyncLog "FAIL: $v returned exit code $LASTEXITCODE"
            $gates_passed = $false
        }
        else {
            Write-SyncLog "PASS: $v"
        }
    }
    else {
        Write-SyncLog "SKIP: $v not found"
    }
}

# Doc Discipline is mandatory
Write-SyncLog "`nRunning Doc Discipline..."
powershell -ExecutionPolicy Bypass -File scripts/verify_docs.ps1 2>&1 | Tee-Object -FilePath $log_file -Append
if ($LASTEXITCODE -ne 0) {
    Write-SyncLog "FAIL: Doc Discipline must pass before sync."
    $gates_passed = $false
}
else {
    Write-SyncLog "PASS: Doc Discipline"
}

if (-not $gates_passed) {
    Write-SyncLog "`n--- SYNC ABORTED: Gates Failed ---"
    exit 1
}

# 3. Committing
if ([string]::IsNullOrWhiteSpace($Message)) {
    $Message = Read-Host "Enter commit message (e.g. M15: short summary)"
}

if ([string]::IsNullOrWhiteSpace($Message)) {
    Write-SyncLog "FAIL: Commit message required."
    exit 1
}

Write-SyncLog "`nStaging changes..."
git add .
git status | Tee-Object -FilePath $log_file -Append

Write-SyncLog "`nCommitting: $Message"
git commit -m $Message | Tee-Object -FilePath $log_file -Append

# 4. Pushing
if ($NoPush) {
    Write-SyncLog "`n--- DRY RUN COMPLETE: Changes committed but NOT pushed ---"
}
else {
    Write-SyncLog "`nPushing to origin/$branch ..."
    git push origin $branch | Tee-Object -FilePath $log_file -Append
    Write-SyncLog "`n--- SYNC COMPLETE ---"
}
