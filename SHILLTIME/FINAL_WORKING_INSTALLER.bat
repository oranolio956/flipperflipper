@echo off
setlocal
title ProxyAssessmentTool Installer
color 0A

echo.
echo ==============================================================================
echo                      ProxyAssessmentTool Installer
echo ==============================================================================
echo.

:: Set paths
set "INSTALL_DIR=%LOCALAPPDATA%\ProxyAssessmentTool"
set "TEMP_DIR=%TEMP%\PAT_Install"

:: Create directories
echo Creating directories...
mkdir "%INSTALL_DIR%" 2>nul
mkdir "%TEMP_DIR%" 2>nul
echo [OK] Directories created
echo.

:: Download the repository
echo Downloading from GitHub...
echo This may take a minute...
echo.

cd /d "%TEMP_DIR%"

:: Use curl (built into Windows 10+) to download
curl -L -o repo.zip "https://github.com/oranolio956/flipperflipperzero-ESP-chiptune/archive/refs/heads/proxy-assessment-tool-clean.zip"

if not exist repo.zip (
    echo [ERROR] Download failed!
    echo.
    echo Trying PowerShell method...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/oranolio956/flipperflipperzero-ESP-chiptune/archive/refs/heads/proxy-assessment-tool-clean.zip' -OutFile 'repo.zip'"
)

if not exist repo.zip (
    echo.
    echo [ERROR] Could not download files!
    echo Please download manually and extract to: %INSTALL_DIR%
    pause
    exit /b 1
)

echo [OK] Download complete
echo.

:: Extract files
echo Extracting files...
powershell -Command "Expand-Archive -Path 'repo.zip' -DestinationPath '.' -Force"
echo [OK] Files extracted
echo.

:: Find the publish folder
echo Looking for application files...
set "FOUND=0"

:: Look in the extracted folder
for /d %%i in (*) do (
    if exist "%%i\SHILLTIME\publish\ProxyAssessmentTool.exe.part1" (
        echo [OK] Found application files
        set "SOURCE_DIR=%%i\SHILLTIME\publish"
        set "FOUND=1"
    )
)

if "%FOUND%"=="0" (
    echo [ERROR] Could not find application files!
    echo.
    echo Directory contents:
    dir /s /b *.exe.part1
    pause
    exit /b 1
)

:: Copy and assemble the exe
echo.
echo Installing application...

:: Copy all files to install directory
xcopy /E /Y "%SOURCE_DIR%\*" "%INSTALL_DIR%\" >nul 2>&1

:: Assemble the exe from parts
cd /d "%INSTALL_DIR%"
if exist ProxyAssessmentTool.exe.part1 (
    echo Assembling executable...
    copy /b ProxyAssessmentTool.exe.part* ProxyAssessmentTool.exe >nul
    
    :: Delete part files after assembly
    del ProxyAssessmentTool.exe.part* >nul 2>&1
    
    echo [OK] Executable assembled
)

:: Verify exe exists
if not exist "%INSTALL_DIR%\ProxyAssessmentTool.exe" (
    echo [ERROR] Failed to create executable!
    pause
    exit /b 1
)

echo [OK] Application installed
echo.

:: Create desktop shortcut
echo Creating desktop shortcut...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\ProxyAssessmentTool.lnk'); $s.TargetPath = '%INSTALL_DIR%\ProxyAssessmentTool.exe'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Save()"
echo [OK] Shortcut created
echo.

:: Clean up
echo Cleaning up...
cd /d "%TEMP%"
rmdir /S /Q "%TEMP_DIR%" 2>nul
echo [OK] Cleanup complete
echo.

:: Success!
echo ==============================================================================
echo                         INSTALLATION COMPLETE!
echo ==============================================================================
echo.
echo ProxyAssessmentTool has been installed to:
echo %INSTALL_DIR%
echo.
echo You can launch it from:
echo - Desktop shortcut: ProxyAssessmentTool
echo - Direct path: %INSTALL_DIR%\ProxyAssessmentTool.exe
echo.

:: Ask to launch
choice /C YN /T 10 /D N /M "Launch ProxyAssessmentTool now"
if errorlevel 2 goto :END
if errorlevel 1 start "" "%INSTALL_DIR%\ProxyAssessmentTool.exe"

:END
echo.
echo Press any key to exit...
pause >nul
exit /b 0