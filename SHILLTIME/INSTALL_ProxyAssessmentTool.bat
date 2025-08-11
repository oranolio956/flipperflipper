@echo off
cls
color 0B
title ProxyAssessmentTool v1.1.0 - Quick Installer

echo.
echo    ____                      _                                                _   _____           _ 
echo   ^|  _ \ _ __ _____  ___   _^| ^|    ___  ___  ___  ___ ___ _ __ ___   ___ _ __ ^| ^|_^|_   _^|__   ___ ^| ^|
echo   ^| ^|_) ^| '__/ _ \ \/ / ^| ^| ^| ^|   / _ \/ __^|/ __^|/ _ \ __^| '_ ` _ \ / _ \ '_ \^| __^| ^| ^|/ _ \ / _ \^| ^|
echo   ^|  __/^| ^| ^| (_) ^>  ^<^| ^|_^| ^| ^|  ^| (_) \__ \ (__  __/__ \ ^| ^| ^| ^| ^|  __/ ^| ^| ^| ^|_  ^| ^| (_) ^| (_) ^| ^|
echo   ^|_^|   ^|_^|  \___/_/\_\\__, ^|_^|   \___/^|___/\___^|\___^|___/_^| ^|_^| ^|_^|\___^|_^| ^|_^|\__^| ^|_^|\___/ \___/^|_^|
echo                       ^|___/                                                                          
echo.
echo   Version 1.1.0 - Security Assessment Tool
echo   =====================================
echo.
echo   This installer will set up ProxyAssessmentTool on your Windows system.
echo.
echo   LEGAL NOTICE: This tool is for authorized security assessments ONLY.
echo   By proceeding, you confirm you will use it only on systems you own
echo   or have explicit written permission to assess.
echo.
echo   Press [Y] to accept and install, or [N] to cancel.

choice /c YN /n /m "   Do you accept these terms? "
if %errorlevel% neq 1 goto :cancel

:: Check if running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   [!] This installer requires Administrator privileges.
    echo   [!] Please right-click and select "Run as administrator"
    echo.
    echo   Press any key to exit...
    pause >nul
    exit /b 1
)

echo.
echo   [*] Starting installation...
echo.

:: Set paths
set "SOURCE_DIR=%~dp0"
set "INSTALL_DIR=%ProgramFiles%\ProxyAssessmentTool"

:: Create install directory
echo   [1/6] Creating installation directory...
if exist "%INSTALL_DIR%" (
    echo        - Directory exists, updating installation
) else (
    mkdir "%INSTALL_DIR%" 2>nul
    if errorlevel 1 (
        echo        [ERROR] Cannot create directory
        goto :error
    )
)

:: Assemble executable from parts
echo   [2/6] Preparing application files...
cd /d "%SOURCE_DIR%publish"
if not exist ProxyAssessmentTool.exe (
    echo        - Assembling executable from parts...
    copy /b ProxyAssessmentTool.exe.part* ProxyAssessmentTool.exe >nul 2>&1
    if errorlevel 1 (
        echo        [ERROR] Failed to assemble executable
        goto :error
    )
)

:: Copy files
echo   [3/6] Installing application files...
echo        - Main executable
xcopy /y /q "ProxyAssessmentTool.exe" "%INSTALL_DIR%\" >nul
echo        - Configuration files
xcopy /y /q "appsettings.json" "%INSTALL_DIR%\" >nul
xcopy /y /q "default.yaml" "%INSTALL_DIR%\" >nul
echo        - Documentation
xcopy /y /q "*.xml" "%INSTALL_DIR%\" >nul 2>&1
xcopy /y /q "%SOURCE_DIR%README.md" "%INSTALL_DIR%\" >nul 2>&1
xcopy /y /q "%SOURCE_DIR%LICENSE.txt" "%INSTALL_DIR%\" >nul 2>&1

:: Create required directories
echo   [4/6] Creating application directories...
mkdir "%INSTALL_DIR%\logs" 2>nul
mkdir "%INSTALL_DIR%\config" 2>nul
mkdir "%INSTALL_DIR%\data" 2>nul
mkdir "%INSTALL_DIR%\reports" 2>nul

:: Create shortcuts
echo   [5/6] Creating shortcuts...
echo        - Desktop shortcut
powershell -NoProfile -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\ProxyAssessmentTool.lnk'); $SC.TargetPath = '%INSTALL_DIR%\ProxyAssessmentTool.exe'; $SC.WorkingDirectory = '%INSTALL_DIR%'; $SC.IconLocation = '%INSTALL_DIR%\ProxyAssessmentTool.exe,0'; $SC.Description = 'ProxyAssessmentTool - Authorized Security Assessments Only'; $SC.Save()" >nul 2>&1

echo        - Start Menu shortcut
set "START_MENU=%ProgramData%\Microsoft\Windows\Start Menu\Programs\ProxyAssessmentTool"
if not exist "%START_MENU%" mkdir "%START_MENU%"
powershell -NoProfile -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%START_MENU%\ProxyAssessmentTool.lnk'); $SC.TargetPath = '%INSTALL_DIR%\ProxyAssessmentTool.exe'; $SC.WorkingDirectory = '%INSTALL_DIR%'; $SC.IconLocation = '%INSTALL_DIR%\ProxyAssessmentTool.exe,0'; $SC.Save()" >nul 2>&1

:: Create uninstaller
echo   [6/6] Creating uninstaller...
(
echo @echo off
echo cls
echo color 0C
echo title ProxyAssessmentTool - Uninstaller
echo.
echo echo.
echo echo   ProxyAssessmentTool Uninstaller
echo echo   ==============================
echo echo.
echo echo   This will remove ProxyAssessmentTool from your system.
echo echo.
echo pause
echo.
echo echo   Removing application files...
echo cd /d "%%TEMP%%"
echo rmdir /s /q "%INSTALL_DIR%" 2^>nul
echo.
echo echo   Removing shortcuts...
echo del "%%USERPROFILE%%\Desktop\ProxyAssessmentTool.lnk" 2^>nul
echo rmdir /s /q "%ProgramData%\Microsoft\Windows\Start Menu\Programs\ProxyAssessmentTool" 2^>nul
echo.
echo echo   Uninstallation complete.
echo pause
) > "%INSTALL_DIR%\Uninstall.bat"

:: Add uninstall shortcut
powershell -NoProfile -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%START_MENU%\Uninstall ProxyAssessmentTool.lnk'); $SC.TargetPath = '%INSTALL_DIR%\Uninstall.bat'; $SC.WorkingDirectory = '%INSTALL_DIR%'; $SC.IconLocation = 'shell32.dll,31'; $SC.Description = 'Uninstall ProxyAssessmentTool'; $SC.Save()" >nul 2>&1

echo.
echo   =========================================
echo   Installation completed successfully!
echo   =========================================
echo.
echo   Installed to: %INSTALL_DIR%
echo.
echo   Created shortcuts:
echo   - Desktop: ProxyAssessmentTool
echo   - Start Menu: ProxyAssessmentTool
echo.
echo   REMEMBER: Use this tool only for authorized assessments!
echo.
echo   Would you like to launch ProxyAssessmentTool now?

choice /c YN /n /m "   Launch application? [Y/N]: "
if %errorlevel%==1 (
    echo.
    echo   Starting ProxyAssessmentTool...
    start "" "%INSTALL_DIR%\ProxyAssessmentTool.exe"
)

echo.
echo   Press any key to exit the installer...
pause >nul
exit /b 0

:error
echo.
echo   [ERROR] Installation failed!
echo.
echo   Please ensure you have administrator privileges and
echo   sufficient disk space, then try again.
echo.
pause
exit /b 1

:cancel
echo.
echo   Installation cancelled.
echo.
pause
exit /b 0