Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "[1/3] Creating virtual environment (.venv)..." -ForegroundColor Cyan
py -m venv .venv

Write-Host "[2/3] Activating virtual environment..." -ForegroundColor Cyan
.\.venv\Scripts\Activate.ps1

Write-Host "[3/3] Installing project + dev dependencies..." -ForegroundColor Cyan
py -m pip install --upgrade pip
py -m pip install -e ".[dev]"

Write-Host "Local bootstrap completed." -ForegroundColor Green
