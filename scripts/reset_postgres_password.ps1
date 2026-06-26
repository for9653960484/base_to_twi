#Requires -RunAsAdministrator
param(
    [Parameter(Mandatory = $true)]
    [string]$NewPassword
)

$ErrorActionPreference = "Stop"
$PgRoot = "C:\Program Files\PostgreSQL\16"
$DataDir = Join-Path $PgRoot "data"
$HbaFile = Join-Path $DataDir "pg_hba.conf"
$ServiceName = "postgresql-x64-16"
$PgCtl = Join-Path $PgRoot "bin\pg_ctl.exe"
$Psql = Join-Path $PgRoot "bin\psql.exe"
$Port = 5433

function Write-TextFileNoBom {
    param([string]$Path, [string[]]$Lines)
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllLines($Path, $Lines, $utf8NoBom)
}

function Test-PortListening {
    return (Test-NetConnection -ComputerName 127.0.0.1 -Port $Port -WarningAction SilentlyContinue).TcpTestSucceeded
}

function Stop-PostgresFully {
    & $PgCtl -D $DataDir -m fast stop 2>$null | Out-Null
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
}

function Start-PostgresFully {
    Start-Service -Name $ServiceName -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 4
    if (-not (Test-PortListening)) {
        & $PgCtl -D $DataDir start -w 2>$null | Out-Null
        Start-Sleep -Seconds 3
    }
    if (-not (Test-PortListening)) {
        throw "PostgreSQL is not listening on port $Port"
    }
}

if (-not (Test-Path $HbaFile)) {
    throw "pg_hba.conf not found: $HbaFile"
}

$backupFile = "$HbaFile.backup-reset"
Copy-Item -LiteralPath $HbaFile -Destination $backupFile -Force
Write-Host "Backup: $backupFile"

$hba = Get-Content -LiteralPath $HbaFile -Encoding UTF8
$trustHba = $hba | ForEach-Object {
    if ($_ -match '^\s*(local|host)\s+' -and $_ -notmatch '^\s*#') {
        $_ -replace 'scram-sha-256', 'trust' -replace '\smd5\s', ' trust '
    } else {
        $_
    }
}
Write-TextFileNoBom -Path $HbaFile -Lines $trustHba

Stop-PostgresFully
Start-PostgresFully

Write-Host "Setting postgres password ..."
$escaped = $NewPassword -replace "'", "''"
$sql = "ALTER USER postgres WITH PASSWORD '$escaped';"
& $Psql -h 127.0.0.1 -p $Port -U postgres -d postgres -v ON_ERROR_STOP=1 -c $sql
if ($LASTEXITCODE -ne 0) {
    $original = Get-Content -LiteralPath $backupFile -Encoding UTF8
    Write-TextFileNoBom -Path $HbaFile -Lines $original
    Stop-PostgresFully
    Start-PostgresFully
    throw "ALTER USER failed. pg_hba.conf restored."
}

Write-Host "Restoring pg_hba.conf ..."
$original = Get-Content -LiteralPath $backupFile -Encoding UTF8
Write-TextFileNoBom -Path $HbaFile -Lines $original
& $Psql -h 127.0.0.1 -p $Port -U postgres -d postgres -c "SELECT pg_reload_conf();" 2>$null | Out-Null

Stop-PostgresFully
Start-PostgresFully

Write-Host "Done. postgres password updated on port $Port."
Write-Host "Now run: scripts\windows\enable-pgvector.cmd (or enable-pgvector.cmd in repo root)"
