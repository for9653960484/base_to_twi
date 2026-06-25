# Первичная настройка локальной разработки (Windows PowerShell)
# Запуск: .\scripts\setup.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== Dream To: настройка локальной разработки ===" -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Создан .env из .env.example" -ForegroundColor Yellow
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Host "Создание .venv (Python 3.12) ..."
    py -3.12 -m venv .venv
    if (-not (Test-Path $Python)) {
        Write-Host "Не найден py -3.12. Установите Python 3.12 с python.org" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Установка Python-зависимостей ..."
& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt

New-Item -ItemType Directory -Force -Path storage | Out-Null

Write-Host "Установка frontend (npm) ..."
. (Join-Path $PSScriptRoot "_ensure-path.ps1")
Push-Location frontend
if (-not (Test-Path "node_modules")) { npm install }
Pop-Location

Write-Host ""
Write-Host "=== Готово ===" -ForegroundColor Green
Write-Host "1. PostgreSQL 16 + pgvector и Redis — см. docs\local-development.md"
Write-Host "2. БД:  .\.venv\Scripts\python.exe scripts\init_database.py"
Write-Host "3. Запуск:  .\scripts\dev-all.ps1"
