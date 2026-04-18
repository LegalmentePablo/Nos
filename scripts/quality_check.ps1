Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Run-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Command
    )

    Write-Host "`n==> $Name" -ForegroundColor Cyan
    Invoke-Expression $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Name (exit code $LASTEXITCODE)"
    }
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Virtual environment not found. Run scripts/bootstrap_local.ps1 first."
}

Run-Step -Name "Ruff lint" -Command ".\.venv\Scripts\python.exe -m ruff check ."
Run-Step -Name "Mypy type-check" -Command ".\.venv\Scripts\python.exe -m mypy src"
Run-Step -Name "Pytest" -Command ".\.venv\Scripts\python.exe -m pytest -q"

Write-Host "`nAll local quality checks passed." -ForegroundColor Green
