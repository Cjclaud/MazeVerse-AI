param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

if ($Clean) {
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
}

python -m PyInstaller --noconfirm "MazeverseAI.spec"

Write-Host ""
Write-Host "Build complete."
Write-Host "Executable folder: dist\\MazeverseAI"
Write-Host "Installer script: installer.iss"
