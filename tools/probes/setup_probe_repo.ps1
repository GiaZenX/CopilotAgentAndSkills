# Creates the S2b/S3 probe scratch repo (phase0-disposition.md par. 5).
# Usage:  powershell -NoProfile -ExecutionPolicy Bypass -File setup_probe_repo.ps1 [-Target <dir>]
param(
    [string]$Target = (Join-Path $env:TEMP "v2-probe")
)

$ErrorActionPreference = "Stop"
$here = $PSScriptRoot

New-Item -ItemType Directory -Force (Join-Path $Target ".claude\hooks") | Out-Null
Copy-Item (Join-Path $here "probe_hook.py") (Join-Path $Target ".claude\hooks\probe_hook.py") -Force
Copy-Item (Join-Path $here "probe_settings.json") (Join-Path $Target ".claude\settings.json") -Force
Copy-Item (Join-Path $here "evaluate_probe.py") (Join-Path $Target "evaluate_probe.py") -Force

Write-Host ""
Write-Host "Probe-Repo bereit: $Target"
Write-Host "Naechste Schritte (Anleitung: tools/probes/README.md):"
Write-Host "  1. cd `"$Target`"  und dort eine NEUE Claude-Code-Session starten"
Write-Host "  2. Beim Start die Hooks vertrauen (/hooks bestaetigen)"
Write-Host "  3. Die zwei 2-Minuten-Probeschritte aus dem README ausfuehren"
Write-Host "  4. python evaluate_probe.py   (im Probe-Repo) fuer das Verdikt"
