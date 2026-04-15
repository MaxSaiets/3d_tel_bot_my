param(
    [string]$VenvDir = ".venv-bot",
    [string]$PythonExe = "py -3.11"
)

$ErrorActionPreference = "Stop"

$pythonCmd = "$PythonExe -m venv $VenvDir"
Invoke-Expression $pythonCmd

$activatePath = Join-Path $VenvDir "Scripts\Activate.ps1"
. $activatePath

python -m pip install --upgrade pip
pip install -e .[dev]

Write-Host "Venv ready: $VenvDir"
