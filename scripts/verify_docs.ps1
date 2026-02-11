# ORCA Doc Discipline Verifier (Q4 + M12)
# Enforces sync between Code, Ledger, Investor Story, and Capability Catalog.

$CodeDirs = @("orca/", "orca_runtime/", "orca_dashboard/")
$LedgerFile = "Antigrav Change Ledger.md"
$StoryFile = "investor_demo_story.md"
$RoadmapFile = "ROADMAP.md"
$CatalogFile = "orca/capabilities/catalog.json"
$CatalogDoc = "docs/CAPABILITY_CATALOG.md"
$SchemaDir = "orca/engine/schemas"

Write-Host "--- ORCA DOC DISCIPLINE START ---"

# 1. Check Git status for changes
$StatusLines = git status --porcelain
$AllChanges = $StatusLines | ForEach-Object { 
    if ($_.Length -gt 3) { 
        $path = $_.Substring(3).Trim()
        # Remove surrounding quotes if present
        if ($path.StartsWith('"') -and $path.EndsWith('"')) {
            $path = $path.Substring(1, $path.Length - 2)
        }
        $path
    } 
}

$CodeChanged = $false
foreach ($dir in $CodeDirs) {
    if ($AllChanges | Where-Object { $_ -like "$dir*" }) {
        $CodeChanged = $true
        break
    }
}

$LedgerChanged = $AllChanges | Where-Object { $_ -eq $LedgerFile }
$StoryChanged = $AllChanges | Where-Object { $_ -eq $StoryFile }
$RoadmapChanged = $AllChanges | Where-Object { $_ -eq $RoadmapFile }
$CatalogChanged = $AllChanges | Where-Object { $_ -eq $CatalogFile }
$CatalogDocChanged = $AllChanges | Where-Object { $_ -eq $CatalogDoc -or $_ -like "docs/capabilities/*" }

$Fail = $false

# Rule 1: Code changes require Ledger entry
if ($CodeChanged -and -not $LedgerChanged) {
    Write-Host "[FAIL] Code changed in $CodeDirs but '$LedgerFile' was NOT updated." -ForegroundColor Red
    $Fail = $true
}
else {
    Write-Host "[PASS] Ledger sync check." -ForegroundColor Green
}

# Rule 2: Roadmap changes require Investor Story update
if ($RoadmapChanged -and -not $StoryChanged) {
    Write-Host "[FAIL] '$RoadmapFile' changed but '$StoryFile' was NOT updated." -ForegroundColor Red
    $Fail = $true
}
else {
    Write-Host "[PASS] Investor Story sync check." -ForegroundColor Green
}

# Rule 4 (M12): Catalog changes require doc updates
if ($CatalogChanged -and -not $CatalogDocChanged) {
    Write-Host "[FAIL] '$CatalogFile' changed but neither '$CatalogDoc' nor 'docs/capabilities/' was updated." -ForegroundColor Red
    $Fail = $true
}
else {
    Write-Host "[PASS] Capability Catalog sync check." -ForegroundColor Green
}

# Rule 3: Schema References
Write-Host "Checking Schema references..."
$DocFiles = Get-ChildItem -Recurse -Include *.md, *.json | Where-Object { 
    $_.FullName -notlike "*node_modules*" -and 
    $_.FullName -notlike "*.git*" -and 
    $_.FullName -notlike "*_verification_artifacts*" 
}

$SchemaPattern = '(orca\.[a-z0-9\.]+\@0\.1\.(schema\.)?json)'

foreach ($file in $DocFiles) {
    $content = Get-Content $file.FullName -Raw
    
    # Check for direct matches or SCHEMAS/ prefix
    $matches = [regex]::Matches($content, $SchemaPattern)
    $matches += [regex]::Matches($content, 'SCHEMAS/([a-zA-Z0-9\.\@_-]+\.json)')
    
    foreach ($match in $matches) {
        $schemaName = $match.Groups[1].Value
        $schemaPath = Join-Path $SchemaDir $schemaName
        if (-not (Test-Path $schemaPath)) {
            $relPath = $file.FullName.Replace($PWD.Path, "").TrimStart('\').TrimStart('/')
            Write-Host "[FAIL] Reference to '$schemaName' in '$relPath' not found in $SchemaDir" -ForegroundColor Red
            $Fail = $true
        }
    }
}

if (-not $Fail) {
    Write-Host "--- ALL DISCIPLINE CHECKS PASSED ---" -ForegroundColor Cyan
    exit 0
}
else {
    Write-Host "--- DISCIPLINE CHECKS FAILED ---" -ForegroundColor Red
    exit 1
}
