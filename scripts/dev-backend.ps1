$Root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $Root "backend")

$port = "8000"
$envFile = Join-Path $Root ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*API_PORT\s*=\s*(.+)\s*$') {
            $port = $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
}

Write-Host "Backend API: http://127.0.0.1:$port (docs: /docs)" -ForegroundColor Cyan
& (Join-Path $Root ".venv\Scripts\python.exe") -m uvicorn app.main:app --reload --host 0.0.0.0 --port $port
