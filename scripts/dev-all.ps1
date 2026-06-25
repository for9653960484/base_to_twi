# Открыть все сервисы в отдельных окнах PowerShell
$Root = Split-Path -Parent $PSScriptRoot

$scripts = @(
    "dev-backend.ps1",
    "dev-ai.ps1",
    "dev-worker.ps1",
    "dev-frontend.ps1"
)

foreach ($s in $scripts) {
    $path = Join-Path $PSScriptRoot $s
    Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", $path
    Start-Sleep -Milliseconds 500
}

Write-Host "Started 4 windows: backend :8000, ai :8001, celery worker, frontend :5173"
