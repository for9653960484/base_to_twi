#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Install pgvector for PostgreSQL 16 on Windows (prebuilt binary).

.PARAMETER PgRoot
  PostgreSQL 16 install path. Default: C:\Program Files\PostgreSQL\16

.PARAMETER PostgresPassword
  postgres superuser password (for CREATE EXTENSION).

.PARAMETER SkipFiles
  Skip DLL download/copy; only run enable_pgvector.py (DB extension + migration).
#>
param(
    [string]$PgRoot = "C:\Program Files\PostgreSQL\16",
    [string]$PostgresPassword = "",
    [switch]$SkipFiles
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ServiceName = "postgresql-x64-16"
$ZipUrl = "https://github.com/andreiramani/pgvector_pgsql_windows/releases/download/0.8.3_16.14/vector.v0.8.3-pg16.zip"
# ASCII path only (short paths like 1F43~1 break Remove-Item on some systems)
$TempDir = "C:\Windows\Temp\pgvector-pg16-install"
$VectorDll = Join-Path $PgRoot "lib\vector.dll"

Write-Host "=== Installing pgvector for PostgreSQL 16 ===" -ForegroundColor Cyan

if (-not (Test-Path $PgRoot)) {
    throw "PostgreSQL not found: $PgRoot"
}

$filesAlreadyInstalled = (Test-Path -LiteralPath $VectorDll)

if ($SkipFiles -or $filesAlreadyInstalled) {
    if ($filesAlreadyInstalled) {
        Write-Host "vector.dll already present - skipping file install."
    } else {
        Write-Host "SkipFiles: skipping file install."
    }
} else {
    Write-Host "Downloading $ZipUrl ..."
    if (Test-Path -LiteralPath $TempDir) {
        Remove-Item -LiteralPath $TempDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
    $zipPath = Join-Path $TempDir "vector.zip"
    Invoke-WebRequest -Uri $ZipUrl -OutFile $zipPath -UseBasicParsing
    Expand-Archive -Path $zipPath -DestinationPath $TempDir -Force

    Write-Host "Stopping service $ServiceName ..."
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2

    Write-Host "Copying files to $PgRoot ..."
    Copy-Item (Join-Path $TempDir "lib\vector.dll") (Join-Path $PgRoot "lib\") -Force
    Copy-Item (Join-Path $TempDir "share\extension\*") (Join-Path $PgRoot "share\extension\") -Force
    $includeDest = Join-Path $PgRoot "include\server\extension\vector"
    New-Item -ItemType Directory -Path $includeDest -Force | Out-Null
    Copy-Item (Join-Path $TempDir "include\server\extension\vector\*") $includeDest -Force

    Write-Host "Starting service $ServiceName ..."
    Start-Service -Name $ServiceName
    Start-Sleep -Seconds 3
}

$python = Join-Path $Root ".venv\Scripts\python.exe"
$enableScript = Join-Path $PSScriptRoot "enable_pgvector.py"
if (-not (Test-Path $python)) {
    Write-Host "venv not found. Run manually:" -ForegroundColor Yellow
    Write-Host "  python scripts\enable_pgvector.py"
    exit 0
}

$env:POSTGRES_SUPERUSER_PASSWORD = $PostgresPassword
& $python $enableScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "enable_pgvector.py failed." -ForegroundColor Yellow
    Write-Host "Run manually: .\.venv\Scripts\python.exe scripts\enable_pgvector.py"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Done. pgvector is enabled in database base_to." -ForegroundColor Green
Write-Host "Restart Celery worker (dev-all.ps1 window) to use vector mode."
