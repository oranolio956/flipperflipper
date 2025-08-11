@echo off
title ProxyAssessmentTool Installer v1.1.0
color 0A

echo.
echo  ===============================================
echo   ProxyAssessmentTool v1.1.0 - Setup Wizard
echo  ===============================================
echo.
echo  IMPORTANT NOTICE:
echo  This tool is for authorized security assessments only.
echo  By installing, you agree to use it only on systems you
echo  own or have explicit written permission to assess.
echo.
echo  Press any key to accept and continue, or close this window to cancel.
pause > nul

:: Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo  ERROR: Administrator privileges required!
    echo  Please right-click and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo.
echo  [1/5] Preparing installation...
set "INSTALL_DIR=%ProgramFiles%\ProxyAssessmentTool"
set "CURRENT_DIR=%~dp0"

:: Create installation directory
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%" 2>nul
    if errorlevel 1 (
        echo  ERROR: Cannot create installation directory
        pause
        exit /b 1
    )
)

echo  [2/5] Assembling application files...
cd /d "%CURRENT_DIR%publish"
if not exist ProxyAssessmentTool.exe (
    copy /b ProxyAssessmentTool.exe.part* ProxyAssessmentTool.exe >nul 2>&1
    if errorlevel 1 (
        echo  ERROR: Failed to assemble executable
        pause
        exit /b 1
    )
)

echo  [3/5] Copying files to installation directory...
xcopy /y /q "ProxyAssessmentTool.exe" "%INSTALL_DIR%\" >nul
xcopy /y /q "appsettings.json" "%INSTALL_DIR%\" >nul
xcopy /y /q "default.yaml" "%INSTALL_DIR%\" >nul
xcopy /y /q "*.xml" "%INSTALL_DIR%\" >nul 2>&1
xcopy /y /q "%CURRENT_DIR%LICENSE.txt" "%INSTALL_DIR%\" >nul 2>&1
xcopy /y /q "%CURRENT_DIR%README.md" "%INSTALL_DIR%\" >nul 2>&1

:: Create logs directory
mkdir "%INSTALL_DIR%\logs" 2>nul
mkdir "%INSTALL_DIR%\config" 2>nul
mkdir "%INSTALL_DIR%\data" 2>nul

echo  [4/5] Creating shortcuts...
:: Create desktop shortcut
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%USERPROFILE%\Desktop\ProxyAssessmentTool.lnk'); $SC.TargetPath = '%INSTALL_DIR%\ProxyAssessmentTool.exe'; $SC.WorkingDirectory = '%INSTALL_DIR%'; $SC.IconLocation = '%INSTALL_DIR%\ProxyAssessmentTool.exe,0'; $SC.Description = 'ProxyAssessmentTool - Security Assessment Tool'; $SC.Save()" >nul 2>&1

:: Create start menu shortcut
set "START_MENU=%ProgramData%\Microsoft\Windows\Start Menu\Programs"
if not exist "%START_MENU%\ProxyAssessmentTool" mkdir "%START_MENU%\ProxyAssessmentTool"
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%START_MENU%\ProxyAssessmentTool\ProxyAssessmentTool.lnk'); $SC.TargetPath = '%INSTALL_DIR%\ProxyAssessmentTool.exe'; $SC.WorkingDirectory = '%INSTALL_DIR%'; $SC.IconLocation = '%INSTALL_DIR%\ProxyAssessmentTool.exe,0'; $SC.Save()" >nul 2>&1
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%START_MENU%\ProxyAssessmentTool\Uninstall.lnk'); $SC.TargetPath = '%INSTALL_DIR%\uninstall.bat'; $SC.WorkingDirectory = '%INSTALL_DIR%'; $SC.IconLocation = 'shell32.dll,31'; $SC.Save()" >nul 2>&1

echo  [5/5] Creating uninstaller...
(
echo @echo off
echo title ProxyAssessmentTool Uninstaller
echo color 0C
echo.
echo echo.
echo echo  This will completely remove ProxyAssessmentTool from your system.
echo echo.
echo pause
echo.
echo echo  Removing application files...
echo cd /d "%%TEMP%%"
echo rmdir /s /q "%INSTALL_DIR%" 2^>nul
echo.
echo echo  Removing shortcuts...
echo del "%%USERPROFILE%%\Desktop\ProxyAssessmentTool.lnk" 2^>nul
echo rmdir /s /q "%START_MENU%\ProxyAssessmentTool" 2^>nul
echo.
echo echo.
echo echo  Uninstallation complete.
echo echo.
echo pause
) > "%INSTALL_DIR%\uninstall.bat"

echo.
echo  ===============================================
echo   Installation Complete!
echo  ===============================================
echo.
echo  ProxyAssessmentTool has been installed to:
echo  %INSTALL_DIR%
echo.
echo  Shortcuts created:
echo  - Desktop
echo  - Start Menu
echo.
echo  Would you like to launch ProxyAssessmentTool now? (Y/N)
choice /c YN /n
if %errorlevel%==1 (
    start "" "%INSTALL_DIR%\ProxyAssessmentTool.exe"
)

echo.
pause