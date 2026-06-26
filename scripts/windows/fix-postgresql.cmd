@echo off
title Fix PostgreSQL pg_hba.conf and start service

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator rights...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo.
echo === Restore pg_hba.conf and start PostgreSQL 16 ===
echo.

set HBA=C:\Program Files\PostgreSQL\16\data\pg_hba.conf
set BACKUP=C:\Program Files\PostgreSQL\16\data\pg_hba.conf.backup-reset

if exist "%BACKUP%" (
    copy /Y "%BACKUP%" "%HBA%" >nul
    echo Restored pg_hba.conf from backup.
) else (
    echo Backup not found - skipping restore.
)

net stop postgresql-x64-16 2>nul
timeout /t 2 /nobreak >nul
net start postgresql-x64-16

if %errorlevel% equ 0 (
    echo PostgreSQL is running on port 5433.
) else (
    echo Failed to start service. Check log in:
    echo C:\Program Files\PostgreSQL\16\data\log\
)

pause
