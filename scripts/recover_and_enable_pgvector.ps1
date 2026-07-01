#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Recover PostgreSQL service state, set postgres password, enable pgvector.
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$PostgresPassword
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$PgRoot = "C:\Program Files\PostgreSQL\16"
$DataDir = Join-Path $PgRoot "data"
$HbaFile = Join-Path $DataDir "pg_hba.conf"
$HbaBackup = "$HbaFile.backup-reset"
$ServiceName = "postgresql-x64-16"
$PgCtl = Join-Path $PgRoot "bin\pg_ctl.exe"
$Psql = Join-Path $PgRoot "bin\psql.exe"
$Port = 5433
$TempDir = "C:\Windows\Temp"

function Remove-TempFile {
    param([string]$Path)
    try {
        if ([System.IO.File]::Exists($Path)) {
            [System.IO.File]::Delete($Path)
        }
    } catch {
        # ignore cleanup errors
    }
}

function Write-TextFileNoBom {
    param([string]$Path, [string[]]$Lines)
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllLines($Path, $Lines, $utf8NoBom)
}

function Test-PortListening {
    param([int]$PortNum)
    return (Test-NetConnection -ComputerName 127.0.0.1 -Port $PortNum -WarningAction SilentlyContinue).TcpTestSucceeded
}

function Stop-PostgresFully {
    Write-Host "Stopping PostgreSQL ..."
    & $PgCtl -D $DataDir -m fast stop 2>$null | Out-Null
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
}

function Start-PostgresFully {
    Write-Host "Starting PostgreSQL ..."
    Start-Service -Name $ServiceName -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 4
    if (-not (Test-PortListening $Port)) {
        & $PgCtl -D $DataDir -l (Join-Path $DataDir "log\pg_ctl-recover.log") start -w 2>$null | Out-Null
        Start-Sleep -Seconds 3
    }
    if (-not (Test-PortListening $Port)) {
        throw "PostgreSQL is not listening on port $Port. Check $DataDir\log\"
    }
}

function Set-HbaTrust {
    Write-Host "Enabling temporary trust auth in pg_hba.conf ..."
    if (-not (Test-Path -LiteralPath $HbaBackup)) {
        Copy-Item -LiteralPath $HbaFile -Destination $HbaBackup -Force
    }
    $hba = Get-Content -LiteralPath $HbaFile -Encoding UTF8
    $trustHba = $hba | ForEach-Object {
        if ($_ -match '^\s*(local|host)\s+' -and $_ -notmatch '^\s*#') {
            $_ -replace 'scram-sha-256', 'trust' -replace '\smd5\s', ' trust '
        } else {
            $_
        }
    }
    Write-TextFileNoBom -Path $HbaFile -Lines $trustHba
}

function Restore-HbaSecure {
    if (-not (Test-Path -LiteralPath $HbaBackup)) {
        Write-Host "Warning: backup pg_hba.conf not found."
        return
    }
    Write-Host "Restoring pg_hba.conf (scram-sha-256) ..."
    $original = Get-Content -LiteralPath $HbaBackup -Encoding UTF8
    Write-TextFileNoBom -Path $HbaFile -Lines $original
}

function New-AlterUserSql {
    param([string]$Password)
    $escaped = $Password -replace "'", "''"
    return "ALTER USER postgres WITH PASSWORD '$escaped';"
}

function Write-SqlFile {
    param([string]$Path, [string]$Sql)
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $Sql, $utf8NoBom)
}

function Invoke-PsqlFile {
    param(
        [string]$SqlFile,
        [string]$Password = "",
        [string]$Database = "postgres"
    )
    $env:PGCLIENTENCODING = "UTF8"
    if ($Password) {
        $env:PGPASSWORD = $Password
    } else {
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    }
    $out = & $Psql -h 127.0.0.1 -p $Port -U postgres -d $Database -v ON_ERROR_STOP=1 -f $SqlFile 2>&1
    $code = $LASTEXITCODE
    return @{ ExitCode = $code; Output = ($out | Out-String) }
}

Write-Host "=== Recover PostgreSQL + enable pgvector ===" -ForegroundColor Cyan

# 1) trust auth + clean restart (do not rely on current hba state)
Set-HbaTrust
Stop-PostgresFully
Start-PostgresFully

# 2) set postgres password via SQL file (safe for special characters)
Write-Host "Setting postgres password ..."
$sqlFile = Join-Path $TempDir "base_to_alter_postgres.sql"
Write-SqlFile -Path $sqlFile -Sql (New-AlterUserSql -Password $PostgresPassword)
$result = Invoke-PsqlFile -SqlFile $sqlFile
Remove-TempFile $sqlFile
if ($result.ExitCode -ne 0) {
    Write-Host $result.Output
    throw "ALTER USER postgres failed. See message above."
}

# 3) enable pgvector
$python = Join-Path $Root ".venv\Scripts\python.exe"
$enableScript = Join-Path $PSScriptRoot "enable_pgvector.py"
if (-not (Test-Path $python)) {
    throw "venv not found: $python"
}
$env:POSTGRES_SUPERUSER_PASSWORD = $PostgresPassword
& $python $enableScript
if ($LASTEXITCODE -ne 0) {
    throw "enable_pgvector.py failed."
}

# 4) restore secure hba and reload
Restore-HbaSecure
$reloadFile = Join-Path $TempDir "base_to_reload.sql"
Write-SqlFile -Path $reloadFile -Sql "SELECT pg_reload_conf();"
Invoke-PsqlFile -SqlFile $reloadFile -Password $PostgresPassword | Out-Null
Remove-TempFile $reloadFile

# 5) normalize service
Stop-PostgresFully
Start-PostgresFully

$verifyFile = Join-Path $TempDir "base_to_verify.sql"
Write-SqlFile -Path $verifyFile -Sql "SELECT extversion FROM pg_extension WHERE extname='vector';"
$verify = Invoke-PsqlFile -SqlFile $verifyFile -Password $PostgresPassword -Database "base_to"
Remove-TempFile $verifyFile
if ($verify.ExitCode -ne 0) {
    Write-Host $verify.Output
    throw "Verification failed after restart."
}

Write-Host "pgvector version: $($verify.Output.Trim())"
Write-Host ""
Write-Host "Done. pgvector enabled, postgres password set, service running." -ForegroundColor Green
Write-Host "Restart Celery worker (dev-all.ps1)."
