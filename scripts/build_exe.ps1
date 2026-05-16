$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

python -m pip install -e ".[dev]"

$PreviousPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = Join-Path $ProjectRoot "src"
    python -m PyInstaller salbotics-filecompressor.spec --noconfirm --clean
    python -m PyInstaller salbotics-filecompressor-cli.spec --noconfirm --clean
    .\scripts\package_release.ps1
}
finally {
    $env:PYTHONPATH = $PreviousPythonPath
}

Write-Host "Built dist\salbotics-filecompressor.exe"
Write-Host "Built dist\salbotics-filecompressor-cli.exe"
Write-Host "Built release\salbotics-filecompressor-windows.zip"
