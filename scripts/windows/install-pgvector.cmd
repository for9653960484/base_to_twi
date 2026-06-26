@echo off
title Install pgvector for dream_to

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator rights...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0..\.."
echo.
echo === Install pgvector ===
echo Project folder: %cd%
echo.

set /p PGPASS=Enter postgres password: 

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\install_pgvector_windows.ps1" -PostgresPassword "%PGPASS%"

echo.
if %errorlevel% equ 0 (
    echo Success.
) else (
    echo Failed. Exit code: %errorlevel%
)
pause
