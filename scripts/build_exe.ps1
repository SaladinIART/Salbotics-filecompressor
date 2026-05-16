$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

python -m pip install -e ".[dev]"
python -m PyInstaller salbotics-filecompressor.spec --noconfirm
python -m PyInstaller salbotics-filecompressor-cli.spec --noconfirm
.\scripts\package_release.ps1

Write-Host "Built dist\salbotics-filecompressor.exe"
Write-Host "Built dist\salbotics-filecompressor-cli.exe"
Write-Host "Built release\salbotics-filecompressor-windows.zip"
