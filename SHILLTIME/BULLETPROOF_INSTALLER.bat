@echo off
setlocal enabledelayedexpansion
title ProxyAssessmentTool Professional Installer
color 0A

:: Set variables
set "INSTALL_DIR=%LOCALAPPDATA%\ProxyAssessmentTool"
set "TEMP_DIR=%TEMP%\ProxyAssessmentTool_%RANDOM%"
set "GITHUB_URL=https://github.com/oranolio956/flipperflipperzero-ESP-chiptune/archive/refs/heads/proxy-assessment-tool-clean.zip"
set "ZIP_FILE=%TEMP_DIR%\download.zip"

:: Header
cls
echo.
echo ==============================================================================
echo                      ProxyAssessmentTool Professional Installer
echo                                    Version 4.0
echo ==============================================================================
echo.

:: Create directories first
echo [1/7] Creating directories...
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%" 2>nul
    if !errorlevel! neq 0 (
        echo [ERROR] Cannot create installation directory!
        echo        Path: %INSTALL_DIR%
        pause
        exit /b 1
    )
)
echo       [OK] Installation directory ready

if not exist "%TEMP_DIR%" (
    mkdir "%TEMP_DIR%" 2>nul
    if !errorlevel! neq 0 (
        echo [ERROR] Cannot create temporary directory!
        pause
        exit /b 1
    )
)
echo       [OK] Temporary directory ready
echo.

:: Download with better error handling
echo [2/7] Downloading from GitHub...
echo       This may take a few minutes depending on your connection...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$ProgressPreference = 'SilentlyContinue'; ^
try { ^
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
    $url = '%GITHUB_URL%'; ^
    $output = '%ZIP_FILE%'; ^
    Write-Host '       Connecting to GitHub...' -ForegroundColor Yellow; ^
    $response = Invoke-WebRequest -Uri $url -Method Head -UseBasicParsing; ^
    $size = [math]::Round($response.Headers['Content-Length'] / 1MB, 2); ^
    Write-Host \"       Download size: $size MB\" -ForegroundColor Cyan; ^
    Write-Host '       Downloading...' -ForegroundColor Yellow; ^
    Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing; ^
    if (Test-Path $output) { ^
        $downloadedSize = [math]::Round((Get-Item $output).Length / 1MB, 2); ^
        Write-Host \"       Downloaded: $downloadedSize MB\" -ForegroundColor Green; ^
        Write-Host '       [OK] Download complete!' -ForegroundColor Green; ^
        exit 0; ^
    } else { ^
        Write-Host '       [ERROR] Download failed - file not created' -ForegroundColor Red; ^
        exit 1; ^
    } ^
} catch { ^
    Write-Host '       [ERROR] Download failed:' -ForegroundColor Red; ^
    Write-Host \"       $_\" -ForegroundColor Red; ^
    exit 1; ^
}"

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Failed to download from GitHub.
    echo.
    echo Possible causes:
    echo - No internet connection
    echo - GitHub is blocked by firewall
    echo - Repository URL has changed
    echo.
    echo Manual download URL:
    echo %GITHUB_URL%
    echo.
    pause
    goto :CLEANUP
)

:: Verify download
echo.
echo [3/7] Verifying download...
if not exist "%ZIP_FILE%" (
    echo       [ERROR] Downloaded file not found!
    pause
    goto :CLEANUP
)

:: Get file size
for %%A in ("%ZIP_FILE%") do set SIZE=%%~zA
if %SIZE% lss 1000 (
    echo       [ERROR] Downloaded file is too small (corrupted)!
    echo       Size: %SIZE% bytes
    pause
    goto :CLEANUP
)
echo       [OK] File verified (%SIZE% bytes)
echo.

:: Extract with better error handling
echo [4/7] Extracting files...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"try { ^
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop; ^
    $zip = '%ZIP_FILE%'; ^
    $dest = '%TEMP_DIR%'; ^
    Write-Host '       Opening archive...' -ForegroundColor Yellow; ^
    $archive = [System.IO.Compression.ZipFile]::OpenRead($zip); ^
    Write-Host \"       Found $($archive.Entries.Count) files in archive\" -ForegroundColor Cyan; ^
    $archive.Dispose(); ^
    Write-Host '       Extracting...' -ForegroundColor Yellow; ^
    [System.IO.Compression.ZipFile]::ExtractToDirectory($zip, $dest); ^
    Write-Host '       [OK] Extraction complete!' -ForegroundColor Green; ^
    exit 0; ^
} catch { ^
    Write-Host '       [ERROR] Extraction failed:' -ForegroundColor Red; ^
    Write-Host \"       $_\" -ForegroundColor Red; ^
    Write-Host '       Trying alternative method...' -ForegroundColor Yellow; ^
    try { ^
        Expand-Archive -Path $zip -DestinationPath $dest -Force; ^
        Write-Host '       [OK] Alternative extraction succeeded!' -ForegroundColor Green; ^
        exit 0; ^
    } catch { ^
        Write-Host '       [ERROR] Alternative extraction also failed!' -ForegroundColor Red; ^
        exit 1; ^
    } ^
}"

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Failed to extract files!
    echo        The ZIP file may be corrupted.
    pause
    goto :CLEANUP
)

echo.
echo [5/7] Locating installation files...

:: Find the extracted folder
set "EXTRACTED_DIR="
for /f "delims=" %%i in ('dir /ad /b "%TEMP_DIR%\*" 2^>nul') do (
    set "EXTRACTED_DIR=%TEMP_DIR%\%%i"
    echo       [OK] Found extracted directory: %%i
)

if not defined EXTRACTED_DIR (
    echo       [ERROR] No extracted directory found!
    pause
    goto :CLEANUP
)

:: Look for installer or published files
set "INSTALL_METHOD=0"

:: Method 1: Original installer
for /f "delims=" %%i in ('dir /s /b "%EXTRACTED_DIR%\*INSTALL_ProxyAssessmentTool.bat" 2^>nul') do (
    echo       [OK] Found original installer
    set "INSTALL_METHOD=1"
    set "INSTALLER_PATH=%%i"
)

:: Method 2: Published files
if %INSTALL_METHOD%==0 (
    for /f "delims=" %%i in ('dir /s /b "%EXTRACTED_DIR%\*publish" 2^>nul') do (
        echo       [OK] Found published files
        set "INSTALL_METHOD=2"
        set "PUBLISH_DIR=%%i"
    )
)

:: Method 3: Direct EXE parts
if %INSTALL_METHOD%==0 (
    for /f "delims=" %%i in ('dir /s /b "%EXTRACTED_DIR%\*ProxyAssessmentTool.exe.part1" 2^>nul') do (
        echo       [OK] Found split executable
        set "INSTALL_METHOD=3"
        set "PARTS_DIR=%%~dpi"
    )
)

if %INSTALL_METHOD%==0 (
    echo       [ERROR] No installation files found!
    echo.
    echo       Directory contents:
    dir /s "%EXTRACTED_DIR%" 2>nul | findstr /i "\.exe \.bat \.dll"
    pause
    goto :CLEANUP
)

echo.
echo [6/7] Installing application...

if %INSTALL_METHOD%==1 (
    echo       Running original installer...
    call "%INSTALLER_PATH%"
    goto :CREATE_SHORTCUT
)

if %INSTALL_METHOD%==2 (
    echo       Copying files from publish directory...
    xcopy /E /Y /I "%PUBLISH_DIR%\*.*" "%INSTALL_DIR%\" >nul 2>&1
    
    :: Check for split files
    if exist "%PUBLISH_DIR%\ProxyAssessmentTool.exe.part1" (
        echo       Assembling split executable...
        copy /b "%PUBLISH_DIR%\ProxyAssessmentTool.exe.part*" "%INSTALL_DIR%\ProxyAssessmentTool.exe" >nul 2>&1
    )
    goto :CREATE_SHORTCUT
)

if %INSTALL_METHOD%==3 (
    echo       Copying files...
    xcopy /E /Y /I "%PARTS_DIR%*.*" "%INSTALL_DIR%\" >nul 2>&1
    
    echo       Assembling split executable...
    copy /b "%PARTS_DIR%ProxyAssessmentTool.exe.part*" "%INSTALL_DIR%\ProxyAssessmentTool.exe" >nul 2>&1
    goto :CREATE_SHORTCUT
)

:CREATE_SHORTCUT
echo.
echo [7/7] Creating shortcuts...

:: Verify exe exists
if not exist "%INSTALL_DIR%\ProxyAssessmentTool.exe" (
    echo       [WARNING] Main executable not found!
    echo       Installation may be incomplete.
) else (
    :: Create desktop shortcut
    powershell -NoProfile -Command ^
    "try { ^
        $WshShell = New-Object -comObject WScript.Shell; ^
        $desktop = [Environment]::GetFolderPath('Desktop'); ^
        $shortcut = $WshShell.CreateShortcut(\"$desktop\ProxyAssessmentTool.lnk\"); ^
        $shortcut.TargetPath = '%INSTALL_DIR%\ProxyAssessmentTool.exe'; ^
        $shortcut.WorkingDirectory = '%INSTALL_DIR%'; ^
        $shortcut.IconLocation = '%INSTALL_DIR%\ProxyAssessmentTool.exe,0'; ^
        $shortcut.Description = 'ProxyAssessmentTool - Security Assessment Platform'; ^
        $shortcut.Save(); ^
        Write-Host '       [OK] Desktop shortcut created' -ForegroundColor Green; ^
    } catch { ^
        Write-Host '       [WARNING] Could not create desktop shortcut' -ForegroundColor Yellow; ^
    }"
    
    :: Create start menu shortcut
    powershell -NoProfile -Command ^
    "try { ^
        $WshShell = New-Object -comObject WScript.Shell; ^
        $startMenu = [Environment]::GetFolderPath('StartMenu'); ^
        $folder = \"$startMenu\Programs\ProxyAssessmentTool\"; ^
        if (!(Test-Path $folder)) { New-Item -ItemType Directory -Path $folder -Force | Out-Null }; ^
        $shortcut = $WshShell.CreateShortcut(\"$folder\ProxyAssessmentTool.lnk\"); ^
        $shortcut.TargetPath = '%INSTALL_DIR%\ProxyAssessmentTool.exe'; ^
        $shortcut.WorkingDirectory = '%INSTALL_DIR%'; ^
        $shortcut.IconLocation = '%INSTALL_DIR%\ProxyAssessmentTool.exe,0'; ^
        $shortcut.Description = 'ProxyAssessmentTool - Security Assessment Platform'; ^
        $shortcut.Save(); ^
        Write-Host '       [OK] Start menu shortcut created' -ForegroundColor Green; ^
    } catch { ^
        Write-Host '       [WARNING] Could not create start menu shortcut' -ForegroundColor Yellow; ^
    }"
)

:: Success
echo.
echo ==============================================================================
echo                           INSTALLATION COMPLETE!
echo ==============================================================================
echo.
echo ProxyAssessmentTool has been installed to:
echo %INSTALL_DIR%
echo.
echo Shortcuts created:
echo - Desktop: ProxyAssessmentTool.lnk
echo - Start Menu: Programs\ProxyAssessmentTool\
echo.

:: Launch option
choice /C YN /M "Would you like to launch ProxyAssessmentTool now"
if %errorlevel%==1 (
    if exist "%INSTALL_DIR%\ProxyAssessmentTool.exe" (
        start "" "%INSTALL_DIR%\ProxyAssessmentTool.exe"
    ) else (
        echo [ERROR] Executable not found!
    )
)

:CLEANUP
echo.
echo Cleaning up temporary files...
if exist "%TEMP_DIR%" (
    rmdir /S /Q "%TEMP_DIR%" 2>nul
)
echo Done.
echo.
pause
exit /b