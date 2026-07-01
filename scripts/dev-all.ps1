# Открыть все сервисы в отдельных окнах PowerShell
$Root = Split-Path -Parent $PSScriptRoot

function Test-RedisPort {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $connect = $tcp.BeginConnect("127.0.0.1", 6379, $null, $null)
        $ok = $connect.AsyncWaitHandle.WaitOne(1000, $false)
        if ($ok -and $tcp.Connected) {
            $tcp.Close()
            return $true
        }
        return $false
    } catch {
        return $false
    }
}

function Start-RedisDocker {
    $composeFile = Join-Path $Root "docker-compose.yml"
    if (-not (Test-Path $composeFile)) {
        return $false
    }
    $null = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        return $false
    }
    Write-Host "Starting Redis via Docker..." -ForegroundColor Cyan
    Push-Location $Root
    try {
        docker compose up -d redis 2>&1 | Out-Null
    } finally {
        Pop-Location
    }
    if ($LASTEXITCODE -ne 0) {
        return $false
    }
    foreach ($i in 1..15) {
        Start-Sleep -Seconds 1
        if (Test-RedisPort) {
            Write-Host "Redis is ready on localhost:6379" -ForegroundColor Green
            return $true
        }
    }
    return $false
}

if (-not (Test-RedisPort)) {
    if (-not (Start-RedisDocker)) {
        Write-Host ""
        Write-Host "WARNING: Redis is not running on localhost:6379." -ForegroundColor Yellow
        Write-Host "AI processing requires Redis + Celery worker." -ForegroundColor Yellow
        Write-Host "1) Start Docker Desktop, then: docker compose up -d redis" -ForegroundColor Yellow
        Write-Host "2) Or install Memurai (Redis for Windows)" -ForegroundColor Yellow
        Write-Host "See docs\local-development.md" -ForegroundColor Yellow
        Write-Host ""
    }
}

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
