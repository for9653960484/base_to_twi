$Root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $Root "ai-service")
& (Join-Path $Root ".venv\Scripts\python.exe") -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
