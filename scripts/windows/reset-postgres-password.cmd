@echo off
title Reset postgres password (PG16 port 5433)

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator rights...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0..\.."
echo.
echo === Reset postgres password ===
echo This sets a NEW password for user postgres on port 5433.
echo.

set /p NEWPASS=Enter NEW postgres password: 
set /p NEWPASS2=Confirm password: 

if not "%NEWPASS%"=="%NEWPASS2%" (
    echo Passwords do not match.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\reset_postgres_password.ps1" -NewPassword "%NEWPASS%"

echo.
pause
