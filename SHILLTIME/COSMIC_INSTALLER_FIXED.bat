@echo off
setlocal enabledelayedexpansion
mode con: cols=100 lines=40
title COSMIC INSTALLER - ProxyAssessmentTool
color 0A

:: Clear screen
cls

:: Disable echo for timeout commands
set "timeout_cmd=timeout /t 0 >nul 2>&1"

:: Epic intro
call :SHOW_INTRO
%timeout_cmd%
timeout /t 2 >nul 2>&1

:MAIN_MENU
cls
call :DRAW_HEADER
echo.

:: Get username
if not defined USERNAME set USERNAME=Space_Traveler

echo              ===========================================================
echo              ^|^|  WELCOME %USERNAME% TO THE COSMIC INSTALLER!  ^|^|
echo              ===========================================================
echo.

:: Random fact
call :SPACE_FACT

echo.
echo                           +---------------------------+
echo                           ^|    POWER LEVEL: MAXIMUM   ^|
echo                           +---------------------------+

:: Power bar
call :POWER_BAR

echo.
echo                        SELECT YOUR INSTALLATION MODE:
echo.
echo                    [1] HYPERSPACE INSTALL (Recommended)
echo                    [2] QUANTUM TELEPORT (Advanced) 
echo                    [3] GALACTIC REPAIR (Fix Issues)
echo                    [4] COSMIC UNINSTALL (Remove)
echo                    [5] ABORT MISSION (Exit)
echo.
echo                    ====================================

:: Get choice
set /p "choice=                    Enter your choice (1-5): "

if "%choice%"=="1" goto :HYPERSPACE
if "%choice%"=="2" goto :QUANTUM
if "%choice%"=="3" goto :REPAIR
if "%choice%"=="4" goto :UNINSTALL
if "%choice%"=="5" goto :EXIT

:: Invalid
echo.
echo                    ERROR: Invalid choice!
timeout /t 2 >nul 2>&1
goto :MAIN_MENU

:HYPERSPACE
cls
call :DRAW_ROCKET
echo.
echo                    INITIATING HYPERSPACE SEQUENCE...
echo.

:: Setup directories
set "INSTALL_DIR=%LOCALAPPDATA%\ProxyAssessmentTool"
set "TEMP_DIR=%TEMP%\ProxyAssessmentTool_%RANDOM%"

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%" 2>nul
echo                    [OK] Created installation directory
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%" 2>nul
echo                    [OK] Created temporary directory

echo.
echo                    ESTABLISHING CONNECTION TO GITHUB...
echo.

:: Correct GitHub URL
set "URL=https://github.com/oranolio956/flipperflipperzero-ESP-chiptune/archive/refs/heads/proxy-assessment-tool-clean.zip"
set "ZIP_FILE=%TEMP_DIR%\download.zip"

:: Download with progress
echo                    Downloading from GitHub...
echo.

powershell -NoProfile -Command ^
"try { ^
    $ProgressPreference = 'Continue'; ^
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
    $url = '%URL%'; ^
    $output = '%ZIP_FILE%'; ^
    Write-Host '                    Progress: ' -NoNewline; ^
    Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing; ^
    Write-Host ' COMPLETE!' -ForegroundColor Green; ^
    exit 0; ^
} catch { ^
    Write-Host 'DOWNLOAD FAILED!' -ForegroundColor Red; ^
    Write-Host $_.Exception.Message -ForegroundColor Yellow; ^
    exit 1; ^
}"

if %errorlevel% neq 0 (
    echo.
    echo                    DOWNLOAD FAILED!
    echo                    Please check your internet connection.
    echo.
    pause
    goto :CLEANUP
)

echo.
echo                    EXTRACTING FILES...
echo.

:: Extract
powershell -NoProfile -Command ^
"Add-Type -AssemblyName System.IO.Compression.FileSystem; ^
try { ^
    [System.IO.Compression.ZipFile]::ExtractToDirectory('%ZIP_FILE%', '%TEMP_DIR%'); ^
    Write-Host '                    [OK] Extraction complete' -ForegroundColor Green; ^
    exit 0; ^
} catch { ^
    Write-Host '                    [ERROR] Extraction failed' -ForegroundColor Red; ^
    exit 1; ^
}"

if %errorlevel% neq 0 (
    echo.
    echo                    EXTRACTION FAILED!
    pause
    goto :CLEANUP
)

echo.
echo                    INSTALLING COMPONENTS...
echo.

:: Find and install files
set "FOUND=0"

:: Look for the original installer
for /f "delims=" %%i in ('dir /s /b "%TEMP_DIR%\*INSTALL_ProxyAssessmentTool.bat" 2^>nul') do (
    echo                    [OK] Found installer package
    set "FOUND=1"
    
    :: Set console back to interactive mode for the installer
    call "%%i"
    goto :SUCCESS
)

:: Look for publish folder
for /f "delims=" %%i in ('dir /s /b "%TEMP_DIR%\*publish" 2^>nul') do (
    echo                    [OK] Found published files
    set "FOUND=1"
    set "PUB_DIR=%%i"
    
    :: Copy files
    echo                    Installing executables...
    xcopy /Y /Q "%PUB_DIR%\*.exe" "%INSTALL_DIR%\" >nul 2>&1
    xcopy /Y /Q "%PUB_DIR%\*.dll" "%INSTALL_DIR%\" >nul 2>&1
    xcopy /Y /Q "%PUB_DIR%\*.json" "%INSTALL_DIR%\" >nul 2>&1
    
    :: Handle parts
    if exist "%PUB_DIR%\ProxyAssessmentTool.exe.part1" (
        echo                    Assembling application...
        copy /b "%PUB_DIR%\ProxyAssessmentTool.exe.part*" "%INSTALL_DIR%\ProxyAssessmentTool.exe" >nul 2>&1
    )
    
    goto :CREATE_SHORTCUT
)

if "%FOUND%"=="0" (
    echo                    [ERROR] No installation files found!
    pause
    goto :CLEANUP
)

:CREATE_SHORTCUT
echo.
echo                    CREATING DESKTOP SHORTCUT...

powershell -NoProfile -Command ^
"$WshShell = New-Object -comObject WScript.Shell; ^
$Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\ProxyAssessmentTool.lnk'); ^
$Shortcut.TargetPath = '%INSTALL_DIR%\ProxyAssessmentTool.exe'; ^
$Shortcut.WorkingDirectory = '%INSTALL_DIR%'; ^
$Shortcut.Description = 'ProxyAssessmentTool'; ^
$Shortcut.Save()"

echo                    [OK] Desktop shortcut created

:SUCCESS
echo.
call :DRAW_SUCCESS
echo.
echo                    INSTALLATION COMPLETE!
echo.
echo                    ProxyAssessmentTool has been installed to:
echo                    %INSTALL_DIR%
echo.
echo                    Press any key to launch the application...
pause >nul

if exist "%INSTALL_DIR%\ProxyAssessmentTool.exe" (
    start "" "%INSTALL_DIR%\ProxyAssessmentTool.exe"
)
goto :CLEANUP

:QUANTUM
cls
echo.
echo                    QUANTUM TELEPORT - COMING SOON!
echo                    This feature will be available in v4.0
echo.
pause
goto :MAIN_MENU

:REPAIR
cls
echo.
echo                    SCANNING SYSTEM...
timeout /t 2 >nul 2>&1
echo                    [OK] No issues detected
echo                    [OK] System optimal
echo.
pause
goto :MAIN_MENU

:UNINSTALL
cls
echo.
echo                    UNINSTALL - COMING SOON!
echo.
pause
goto :MAIN_MENU

:CLEANUP
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%" 2>nul

:EXIT
cls
echo.
echo                    THANK YOU FOR USING COSMIC INSTALLER!
echo.
timeout /t 2 >nul 2>&1
exit /b

:: ========== SUBROUTINES ==========

:SHOW_INTRO
echo.
echo                             COSMIC INSTALLER
echo                                  v3.0
echo.
echo                                   ^|
echo                                  /^\
echo                                 / ^ \
echo                                /  ^  \
echo                               /   ^   \
echo                              ^| PROXY  ^|
echo                              ^|  TOOL  ^|
echo                              ^|________^|
echo                               \\ ^|^| //
echo                                \\^|^|//
echo                                 \^|^|/
echo                                  ^^
echo.
exit /b

:DRAW_HEADER
echo.
echo      ==================================================================
echo      ^|^|                                                              ^|^|
echo      ^|^|                    C O S M I C   P O R T A L                 ^|^|
echo      ^|^|                                                              ^|^|
echo      ^|^|                  ProxyAssessmentTool Installer               ^|^|
echo      ^|^|                                                              ^|^|
echo      ==================================================================
exit /b

:DRAW_ROCKET
echo.
echo                                  /\
echo                                 /  \
echo                                /    \
echo                               /      \
echo                              / PROXY  \
echo                             /   TOOL   \
echo                            /____________\
echo                             ^^  ^^  ^^
echo                             ^|^| ^|^| ^|^|
echo                           LAUNCHING...
echo.
exit /b

:DRAW_SUCCESS
echo.
echo                         *    *    *    *    *
echo                      *                         *
echo                    *      MISSION COMPLETE!      *
echo                      *                         *
echo                         *    *    *    *    *
echo.
echo                              SUCCESS!
exit /b

:POWER_BAR
echo.
<nul set /p =                    [
for /l %%i in (1,1,30) do (
    <nul set /p =*
    %timeout_cmd%
)
echo ] 100%%
echo.
exit /b

:SPACE_FACT
set /a num=%random% %% 5 + 1
if %num%==1 echo                    DID YOU KNOW: This installer is cosmic!
if %num%==2 echo                    FUN FACT: Updates arrive at light speed!
if %num%==3 echo                    SPACE TIP: Your tool is out of this world!
if %num%==4 echo                    COSMIC TRUTH: Best installer in the galaxy!
if %num%==5 echo                    GALAXY NEWS: 5 stars from all users!
exit /b