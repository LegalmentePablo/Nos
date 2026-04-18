Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $projectRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Error "Virtual environment not found. Run scripts/bootstrap_local.ps1 first."
    exit 1
}

& "$projectRoot\scripts\quality_check.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Pre-commit checks failed."
    exit $LASTEXITCODE
}

Write-Host "Pre-commit checks passed." -ForegroundColor Green
