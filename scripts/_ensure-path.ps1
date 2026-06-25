# Добавить Node.js в PATH (новые окна PowerShell не наследуют ручной $env:Path)
$NodeDir = Join-Path ${env:ProgramFiles} "nodejs"
if ((Test-Path $NodeDir) -and ($env:Path -notlike "*$NodeDir*")) {
    $env:Path = "$NodeDir;$env:Path"
}
