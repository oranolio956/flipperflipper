# ProxyAssessmentTool Installer Creator
# This script creates a self-extracting installer

Write-Host "Creating ProxyAssessmentTool Installer..." -ForegroundColor Green

# Create temp directory for installer files
$tempDir = "installer_temp"
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Copy necessary files
Write-Host "Copying files..."
Copy-Item "publish\*" -Destination $tempDir -Recurse
Copy-Item "LICENSE.txt" -Destination $tempDir
Copy-Item "README.md" -Destination $tempDir

# Create install script
$installScript = @'
@echo off
title ProxyAssessmentTool Installer
echo.
echo ====================================
echo  ProxyAssessmentTool v1.1.0 Setup
echo ====================================
echo.
echo This will install ProxyAssessmentTool on your system.
echo.
echo IMPORTANT: This tool is for authorized security assessments only.
echo By continuing, you agree to use it only on systems you own or
echo have explicit written permission to assess.
echo.
pause

echo.
echo Assembling application files...
cd /d "%~dp0"
copy /b ProxyAssessmentTool.exe.part* ProxyAssessmentTool.exe > nul
if errorlevel 1 goto error

echo Installing to %ProgramFiles%\ProxyAssessmentTool...
if not exist "%ProgramFiles%\ProxyAssessmentTool" mkdir "%ProgramFiles%\ProxyAssessmentTool"
xcopy /y /e * "%ProgramFiles%\ProxyAssessmentTool\" > nul
if errorlevel 1 goto error

echo Creating shortcuts...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\ProxyAssessmentTool.lnk'); $Shortcut.TargetPath = '%ProgramFiles%\ProxyAssessmentTool\ProxyAssessmentTool.exe'; $Shortcut.Save()"

echo.
echo Installation complete!
echo.
echo ProxyAssessmentTool has been installed to:
echo %ProgramFiles%\ProxyAssessmentTool
echo.
echo A desktop shortcut has been created.
echo.
pause
exit /b 0

:error
echo.
echo ERROR: Installation failed!
echo Please run this installer as Administrator.
echo.
pause
exit /b 1
'@

$installScript | Out-File -FilePath "$tempDir\install.bat" -Encoding ASCII

# Create uninstall script
$uninstallScript = @'
@echo off
title ProxyAssessmentTool Uninstaller
echo.
echo This will uninstall ProxyAssessmentTool from your system.
echo.
pause

echo Removing installation...
rmdir /s /q "%ProgramFiles%\ProxyAssessmentTool"
del "%USERPROFILE%\Desktop\ProxyAssessmentTool.lnk" 2>nul

echo.
echo Uninstallation complete.
echo.
pause
'@

$uninstallScript | Out-File -FilePath "$tempDir\uninstall.bat" -Encoding ASCII

# Create self-extracting archive using built-in Windows tools
Write-Host "Creating self-extracting installer..."

# Create a simple self-extracting batch file
$sfxHeader = @'
@echo off
setlocal enabledelayedexpansion

:: Self-extracting installer for ProxyAssessmentTool
:: This file contains the application and installer

echo Extracting ProxyAssessmentTool installer...
set "TEMP_DIR=%TEMP%\ProxyAssessmentTool_Setup"
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"

:: Extract embedded files (marker: ___ARCHIVE_START___)
findstr /v /c:"___ARCHIVE_START___" "%~f0" > "%TEMP_DIR%\archive.tmp"
certutil -decode "%TEMP_DIR%\archive.tmp" "%TEMP_DIR%\files.zip" >nul 2>&1
del "%TEMP_DIR%\archive.tmp"

:: Extract files
cd /d "%TEMP_DIR%"
powershell -Command "Expand-Archive -Path 'files.zip' -DestinationPath '.' -Force"
del files.zip

:: Run installer
call install.bat

:: Cleanup
cd /d "%TEMP%"
rmdir /s /q "%TEMP_DIR%"
exit /b

___ARCHIVE_START___
'@

# Create the installer
$installerPath = "ProxyAssessmentTool_Setup.exe"
$sfxHeader | Out-File -FilePath $installerPath -Encoding ASCII -NoNewline

# Create a zip of the temp directory
Write-Host "Compressing files..."
Compress-Archive -Path "$tempDir\*" -DestinationPath "$tempDir\files.zip" -CompressionLevel Optimal

# Encode the zip file and append to installer
$zipContent = [System.Convert]::ToBase64String([System.IO.File]::ReadAllBytes("$tempDir\files.zip"))
$zipContent | Out-File -FilePath $installerPath -Encoding ASCII -Append

# Cleanup
Remove-Item $tempDir -Recurse -Force

Write-Host "Installer created successfully: $installerPath" -ForegroundColor Green
Write-Host "File size: $([math]::Round((Get-Item $installerPath).Length / 1MB, 2)) MB" -ForegroundColor Cyan