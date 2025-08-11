# ProxyAssessmentTool Build and Package Script
# This script builds the complete application and creates an installer

param(
    [string]$OutputPath = "$PSScriptRoot\Release"
)

Write-Host "`n=== ProxyAssessmentTool Build Script ===" -ForegroundColor Cyan
Write-Host "Building the complete application...`n" -ForegroundColor Yellow

# Check for .NET SDK
Write-Host "Checking .NET SDK..." -ForegroundColor Yellow
try {
    $dotnetVersion = dotnet --version
    Write-Host "[OK] .NET SDK found: $dotnetVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] .NET SDK not found! Please install from: https://dotnet.microsoft.com/download" -ForegroundColor Red
    exit 1
}

# Set paths
$sourceDir = "$PSScriptRoot\SHILLTIME"
$buildDir = "$PSScriptRoot\build"
$outputDir = $OutputPath
$installerDir = "$PSScriptRoot\Installer"

# Clean previous builds
Write-Host "`nCleaning previous builds..." -ForegroundColor Yellow
if (Test-Path $buildDir) { Remove-Item -Path $buildDir -Recurse -Force }
if (Test-Path $outputDir) { Remove-Item -Path $outputDir -Recurse -Force }
New-Item -ItemType Directory -Path $buildDir -Force | Out-Null
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
New-Item -ItemType Directory -Path $installerDir -Force | Out-Null

# Build the main application
Write-Host "`nBuilding ProxyAssessmentTool..." -ForegroundColor Yellow
Set-Location $sourceDir

# Restore packages
Write-Host "Restoring NuGet packages..." -ForegroundColor Gray
dotnet restore ProxyAssessmentTool.sln

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Package restore failed!" -ForegroundColor Red
    exit 1
}

# Build in Release mode
Write-Host "Building application..." -ForegroundColor Gray
dotnet build ProxyAssessmentTool.sln --configuration Release --no-restore

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Build failed!" -ForegroundColor Red
    exit 1
}

# Publish as single file
Write-Host "`nPublishing as single file executable..." -ForegroundColor Yellow
dotnet publish src\ProxyAssessmentTool\ProxyAssessmentTool.csproj `
    --configuration Release `
    --runtime win-x64 `
    --self-contained true `
    --output $buildDir `
    -p:PublishSingleFile=true `
    -p:PublishReadyToRun=true `
    -p:IncludeNativeLibrariesForSelfExtract=true `
    -p:EnableCompressionInSingleFile=true

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Publish failed!" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Application built successfully!" -ForegroundColor Green

# Copy additional files
Write-Host "`nCopying additional files..." -ForegroundColor Yellow
Copy-Item "$buildDir\ProxyAssessmentTool.exe" "$outputDir\" -Force
Copy-Item "$buildDir\appsettings.json" "$outputDir\" -Force -ErrorAction SilentlyContinue

# Check file size
$exeInfo = Get-Item "$outputDir\ProxyAssessmentTool.exe"
$sizeMB = [math]::Round($exeInfo.Length / 1MB, 2)
Write-Host "[OK] Executable size: $sizeMB MB" -ForegroundColor Green

# Create installer script
Write-Host "`nCreating installer..." -ForegroundColor Yellow

$installerContent = @'
@echo off
title ProxyAssessmentTool Installer
color 0A

echo.
echo ========================================
echo    ProxyAssessmentTool Installer
echo ========================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\ProxyAssessmentTool"

echo Creating installation directory...
mkdir "%INSTALL_DIR%" 2>nul

echo Installing application...
copy /Y "ProxyAssessmentTool.exe" "%INSTALL_DIR%\" >nul
copy /Y "appsettings.json" "%INSTALL_DIR%\" >nul 2>nul

echo Creating desktop shortcut...
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\ProxyAssessmentTool.lnk'); $s.TargetPath='%INSTALL_DIR%\ProxyAssessmentTool.exe'; $s.WorkingDirectory='%INSTALL_DIR%'; $s.Save()"

echo.
echo ========================================
echo    Installation Complete!
echo ========================================
echo.
echo ProxyAssessmentTool has been installed to:
echo %INSTALL_DIR%
echo.
echo A shortcut has been created on your desktop.
echo.

choice /C YN /M "Launch ProxyAssessmentTool now"
if errorlevel 2 goto END
if errorlevel 1 start "" "%INSTALL_DIR%\ProxyAssessmentTool.exe"

:END
pause
'@

$installerContent | Out-File -FilePath "$outputDir\INSTALL.bat" -Encoding ASCII

# Create a self-extracting archive (if 7-Zip is available)
$7zipPath = "C:\Program Files\7-Zip\7z.exe"
if (Test-Path $7zipPath) {
    Write-Host "Creating self-extracting archive..." -ForegroundColor Yellow
    
    & $7zipPath a -sfx "$installerDir\ProxyAssessmentTool_Installer.exe" "$outputDir\*" | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Self-extracting installer created!" -ForegroundColor Green
    }
} else {
    # Create a ZIP file instead
    Write-Host "Creating ZIP package..." -ForegroundColor Yellow
    Compress-Archive -Path "$outputDir\*" -DestinationPath "$installerDir\ProxyAssessmentTool.zip" -Force
    Write-Host "[OK] ZIP package created!" -ForegroundColor Green
}

# Create PowerShell installer
$psInstallerContent = @'
# ProxyAssessmentTool Quick Installer
Write-Host "`nInstalling ProxyAssessmentTool..." -ForegroundColor Green

$installDir = "$env:LOCALAPPDATA\ProxyAssessmentTool"
$currentDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Create directory
New-Item -ItemType Directory -Path $installDir -Force | Out-Null

# Copy files
Copy-Item "$currentDir\ProxyAssessmentTool.exe" $installDir -Force
Copy-Item "$currentDir\appsettings.json" $installDir -Force -ErrorAction SilentlyContinue

# Create shortcut
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\ProxyAssessmentTool.lnk")
$Shortcut.TargetPath = "$installDir\ProxyAssessmentTool.exe"
$Shortcut.WorkingDirectory = $installDir
$Shortcut.Save()

Write-Host "`nInstallation complete!" -ForegroundColor Green
Write-Host "ProxyAssessmentTool has been installed to: $installDir" -ForegroundColor Cyan
Write-Host "A shortcut has been created on your desktop." -ForegroundColor Yellow

$response = Read-Host "`nLaunch ProxyAssessmentTool now? (Y/N)"
if ($response -eq 'Y') {
    Start-Process "$installDir\ProxyAssessmentTool.exe"
}
'@

$psInstallerContent | Out-File -FilePath "$outputDir\INSTALL.ps1" -Encoding UTF8

# Summary
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "         BUILD COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nOutput location: $outputDir" -ForegroundColor Cyan
Write-Host "`nFiles created:" -ForegroundColor Yellow
Get-ChildItem $outputDir | ForEach-Object {
    Write-Host "  - $($_.Name) ($([math]::Round($_.Length / 1KB, 2)) KB)" -ForegroundColor Gray
}

if (Test-Path "$installerDir\ProxyAssessmentTool_Installer.exe") {
    Write-Host "`nSelf-extracting installer:" -ForegroundColor Yellow
    Write-Host "  - $installerDir\ProxyAssessmentTool_Installer.exe" -ForegroundColor Cyan
} elseif (Test-Path "$installerDir\ProxyAssessmentTool.zip") {
    Write-Host "`nZIP package:" -ForegroundColor Yellow
    Write-Host "  - $installerDir\ProxyAssessmentTool.zip" -ForegroundColor Cyan
}

Write-Host "`nTo install:" -ForegroundColor Yellow
Write-Host "  1. Run INSTALL.bat (double-click)" -ForegroundColor Gray
Write-Host "  2. Or run INSTALL.ps1 in PowerShell" -ForegroundColor Gray
Write-Host "  3. Or manually copy ProxyAssessmentTool.exe to desired location" -ForegroundColor Gray

Set-Location $PSScriptRoot