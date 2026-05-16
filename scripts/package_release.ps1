$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$ReleaseRoot = Join-Path $ProjectRoot "release"
$PackageDir = Join-Path $ReleaseRoot "salbotics-filecompressor"
$ZipPath = Join-Path $ReleaseRoot "salbotics-filecompressor-windows.zip"

if (Test-Path $PackageDir) {
    Remove-Item -LiteralPath $PackageDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $PackageDir | Out-Null

Copy-Item -LiteralPath "dist\salbotics-filecompressor.exe" -Destination $PackageDir
Copy-Item -LiteralPath "dist\salbotics-filecompressor-cli.exe" -Destination $PackageDir
Copy-Item -LiteralPath "README.md" -Destination $PackageDir
Copy-Item -LiteralPath "CREDITS.md" -Destination $PackageDir
Copy-Item -LiteralPath "assets\salbotics-filecompressor.ico" -Destination $PackageDir

if (Test-Path $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}
Compress-Archive -Path (Join-Path $PackageDir "*") -DestinationPath $ZipPath

Write-Host "Packaged $ZipPath"
