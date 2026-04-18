Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$gitDir = Join-Path $projectRoot ".git"

if (-not (Test-Path $gitDir)) {
    Write-Error "No .git directory found in project root. Initialize Git first: git init"
    exit 1
}

$hooksDir = Join-Path $gitDir "hooks"
if (-not (Test-Path $hooksDir)) {
    New-Item -ItemType Directory -Path $hooksDir | Out-Null
}

$hookPath = Join-Path $hooksDir "pre-commit"
$hookContent = @'
#!/usr/bin/env bash
powershell -NoProfile -ExecutionPolicy Bypass -File "./scripts/pre_commit.ps1"
status=$?
if [ $status -ne 0 ]; then
  echo "Commit aborted: local quality checks failed."
  exit $status
fi
'@

Set-Content -Path $hookPath -Value $hookContent -Encoding ascii

Write-Host "Pre-commit hook installed at $hookPath" -ForegroundColor Green
Write-Host "It will run scripts/pre_commit.ps1 before every commit." -ForegroundColor Green
