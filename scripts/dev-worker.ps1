$Root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $Root "ai-service")
& (Join-Path $Root ".venv\Scripts\celery.exe") -A app.worker.celery_app worker --loglevel=info --pool=solo
