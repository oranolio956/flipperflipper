@echo off
setlocal enabledelayedexpansion

:: ProxyAssessmentTool Installer with Update Support
:: This script downloads and installs the latest version from GitHub

echo.
echo ============================================
echo ProxyAssessmentTool Installer v2.0
echo ============================================
echo.

:: Check for admin rights (optional but recommended)
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Not running as administrator.
    echo Some features may require admin privileges.
    echo.
)

:: Set installation directory
set "INSTALL_DIR=%ProgramFiles%\ProxyAssessmentTool"
if not exist "%ProgramFiles%" (
    set "INSTALL_DIR=%LOCALAPPDATA%\ProxyAssessmentTool"
)

echo Installation directory: %INSTALL_DIR%
echo.

:: Check if already installed
if exist "%INSTALL_DIR%\ProxyAssessmentTool.exe" (
    echo ProxyAssessmentTool is already installed.
    echo.
    choice /C YN /M "Do you want to reinstall/update"
    if !errorlevel! neq 1 goto :END
    echo.
)

:: Create temp directory
set "TEMP_DIR=%TEMP%\ProxyAssessmentTool_Install_%RANDOM%"
mkdir "%TEMP_DIR%" 2>nul

echo Downloading latest release from GitHub...
echo.

:: Download using PowerShell with better error handling
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"try { ^
    $ProgressPreference = 'SilentlyContinue'; ^
    $url = 'https://github.com/oranolio956/flipperflipperzero-ESP-chiptune/archive/refs/heads/proxy-assessment-tool-clean.zip'; ^
    $output = '%TEMP_DIR%\ProxyAssessmentTool.zip'; ^
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
    Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing; ^
    if (Test-Path $output) { ^
        Write-Host 'Download completed successfully.' -ForegroundColor Green; ^
        exit 0; ^
    } else { ^
        Write-Host 'Download failed - file not found.' -ForegroundColor Red; ^
        exit 1; ^
    } ^
} catch { ^
    Write-Host ('Download error: ' + $_.Exception.Message) -ForegroundColor Red; ^
    exit 1; ^
}"

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to download from GitHub.
    echo Please check your internet connection and try again.
    echo.
    echo You can also download manually from:
    echo https://github.com/oranolio956/flipperflipperzero-ESP-chiptune
    echo.
    pause
    goto :CLEANUP
)

echo.
echo Extracting files...

:: Extract ZIP file
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"try { ^
    Add-Type -AssemblyName System.IO.Compression.FileSystem; ^
    [System.IO.Compression.ZipFile]::ExtractToDirectory('%TEMP_DIR%\ProxyAssessmentTool.zip', '%TEMP_DIR%'); ^
    Write-Host 'Extraction completed.' -ForegroundColor Green; ^
    exit 0; ^
} catch { ^
    Write-Host ('Extraction error: ' + $_.Exception.Message) -ForegroundColor Red; ^
    exit 1; ^
}"

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to extract files.
    pause
    goto :CLEANUP
)

:: Find the installer
echo.
echo Locating installer files...

set "INSTALLER_FOUND=0"
for /f "delims=" %%i in ('dir /s /b "%TEMP_DIR%\*INSTALL_ProxyAssessmentTool.bat" 2^>nul') do (
    set "INSTALLER_PATH=%%i"
    set "INSTALLER_FOUND=1"
)

if %INSTALLER_FOUND% equ 0 (
    echo.
    echo WARNING: Original installer not found.
    echo Attempting direct installation...
    echo.
    
    :: Look for the published executable parts
    for /f "delims=" %%i in ('dir /s /b "%TEMP_DIR%\*ProxyAssessmentTool.exe.part1" 2^>nul') do (
        set "PARTS_DIR=%%~dpi"
        set "INSTALLER_FOUND=2"
    )
)

if %INSTALLER_FOUND% equ 0 (
    echo ERROR: No installation files found.
    echo.
    echo Please ensure the repository contains the installer.
    pause
    goto :CLEANUP
)

:: Run the appropriate installer
if %INSTALLER_FOUND% equ 1 (
    echo Found installer at: %INSTALLER_PATH%
    echo.
    echo Launching installer...
    call "%INSTALLER_PATH%"
) else (
    :: Direct installation from parts
    echo Installing directly...
    echo.
    
    :: Create installation directory
    if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
    
    :: Copy and assemble parts
    echo Assembling application files...
    copy /b "%PARTS_DIR%ProxyAssessmentTool.exe.part*" "%INSTALL_DIR%\ProxyAssessmentTool.exe" >nul 2>&1
    
    if exist "%PARTS_DIR%ProxyAssessmentTool.Updater.exe" (
        copy "%PARTS_DIR%ProxyAssessmentTool.Updater.exe" "%INSTALL_DIR%\" >nul 2>&1
    )
    
    :: Copy configuration
    if exist "%PARTS_DIR%appsettings.json" (
        copy "%PARTS_DIR%appsettings.json" "%INSTALL_DIR%\" >nul 2>&1
    )
    
    :: Create desktop shortcut
    echo Creating desktop shortcut...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$WshShell = New-Object -comObject WScript.Shell; ^
     $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\ProxyAssessmentTool.lnk'); ^
     $Shortcut.TargetPath = '%INSTALL_DIR%\ProxyAssessmentTool.exe'; ^
     $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; ^
     $Shortcut.IconLocation = '%INSTALL_DIR%\ProxyAssessmentTool.exe'; ^
     $Shortcut.Description = 'ProxyAssessmentTool - Security Assessment Platform'; ^
     $Shortcut.Save()"
    
    echo.
    echo Installation completed!
    echo.
    echo ProxyAssessmentTool has been installed to:
    echo %INSTALL_DIR%
    echo.
    echo A shortcut has been created on your desktop.
)

:: Check if we should launch the app
echo.
choice /C YN /M "Would you like to launch ProxyAssessmentTool now"
if %errorlevel% equ 1 (
    if exist "%INSTALL_DIR%\ProxyAssessmentTool.exe" (
        start "" "%INSTALL_DIR%\ProxyAssessmentTool.exe"
    ) else if exist "%USERPROFILE%\Desktop\ProxyAssessmentTool.lnk" (
        start "" "%USERPROFILE%\Desktop\ProxyAssessmentTool.lnk"
    )
)

:CLEANUP
:: Clean up temp files
echo.
echo Cleaning up temporary files...
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%" 2>nul

:END
echo.
echo Press any key to exit...
pause >nul
exit /b