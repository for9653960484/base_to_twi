@echo off
title Recover PostgreSQL and enable pgvector

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator rights...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0..\.."
echo.
echo === One-step setup: postgres password + pgvector ===
echo.

set /p PGPASS=Enter NEW postgres password (letters and digits only): 
set /p PGPASS2=Confirm password: 

echo %PGPASS%| findstr /r "[^a-zA-Z0-9]" >nul
if %errorlevel% equ 0 (
    echo Use only letters and digits in password to avoid CMD quoting issues.
    pause
    exit /b 1
)

if not "%PGPASS%"=="%PGPASS2%" (
    echo Passwords do not match.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\recover_and_enable_pgvector.ps1" -PostgresPassword "%PGPASS%"

echo.
if %errorlevel% equ 0 (
    echo Success.
) else (
    echo Failed. Exit code: %errorlevel%
)
pause
