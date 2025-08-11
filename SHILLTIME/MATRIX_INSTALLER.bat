@echo off
setlocal enabledelayedexpansion
mode con: cols=120 lines=50
title [MATRIX INSTALLER] ProxyAssessmentTool - Wake up, Neo...
color 0A

:: Initialize
set "chars=01"
set "install_dir=%LOCALAPPDATA%\ProxyAssessmentTool"
set "temp_dir=%TEMP%\ProxyAssessmentTool_%RANDOM%"

:: Matrix rain effect
:MATRIX_INTRO
cls
echo.
for /l %%i in (1,1,20) do (
    set "line="
    for /l %%j in (1,1,80) do (
        set /a "r=!random! %% 10"
        if !r! lss 3 (
            set /a "c=!random! %% 2"
            set "line=!line!!chars:~%c%,1!"
        ) else (
            set "line=!line! "
        )
    )
    echo !line!
)
timeout /t 1 >nul 2>&1

:: Wake up message
cls
echo.
echo.
for %%a in (W a k e " " u p , " " N e o . . .) do (
    <nul set /p =%%a
    timeout /t 0 >nul 2>&1
)
echo.
timeout /t 2 >nul 2>&1

echo.
for %%a in (T h e " " M a t r i x " " h a s " " y o u . . .) do (
    <nul set /p =%%a
    timeout /t 0 >nul 2>&1
)
echo.
timeout /t 2 >nul 2>&1

echo.
for %%a in (F o l l o w " " t h e " " w h i t e " " r a b b i t . . .) do (
    <nul set /p =%%a
    timeout /t 0 >nul 2>&1
)
echo.
timeout /t 3 >nul 2>&1

:MAIN_MENU
cls
call :DRAW_MATRIX_HEADER
echo.
echo                                  SYSTEM BREACH DETECTED
echo                              ===========================
echo.
echo                                 Choose your reality:
echo.
echo                            [1] TAKE THE RED PILL (Install)
echo                            [2] TAKE THE BLUE PILL (Exit)
echo                            [3] HACK THE MATRIX (Advanced)
echo                            [4] SYSTEM DIAGNOSTICS
echo                            [5] UNPLUG FROM MATRIX
echo.
echo                              ===========================
echo.
set /p "choice=                            Enter the code: "

if "%choice%"=="1" goto :RED_PILL
if "%choice%"=="2" goto :BLUE_PILL
if "%choice%"=="3" goto :HACK_MATRIX
if "%choice%"=="4" goto :DIAGNOSTICS
if "%choice%"=="5" goto :UNPLUG

echo.
echo                            INVALID CODE - TRY AGAIN
timeout /t 2 >nul 2>&1
goto :MAIN_MENU

:RED_PILL
cls
echo.
echo                            YOU TOOK THE RED PILL
echo                            ===================
echo.
echo                            Initializing reality...
call :LOADING_ANIMATION

:: Create directories
echo.
echo [SYSTEM] Creating neural pathways...
if not exist "%install_dir%" mkdir "%install_dir%" 2>nul
echo [OK] Neural network established
if not exist "%temp_dir%" mkdir "%temp_dir%" 2>nul
echo [OK] Temporary matrix created

:: Download
echo.
echo [SYSTEM] Connecting to the Source...
echo.

set "url=https://github.com/oranolio956/flipperflipperzero-ESP-chiptune/archive/refs/heads/proxy-assessment-tool-clean.zip"
set "zip_file=%temp_dir%\matrix_download.zip"

call :MATRIX_DOWNLOAD "%url%" "%zip_file%"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Connection to the Source failed!
    echo [ERROR] The Agents may be blocking us...
    pause
    goto :CLEANUP
)

:: Extract
echo.
echo [SYSTEM] Decoding the Matrix...
call :MATRIX_EXTRACT "%zip_file%" "%temp_dir%"

:: Install
echo.
echo [SYSTEM] Uploading skills...
call :INSTALL_SKILLS "%temp_dir%" "%install_dir%"

:: Success
echo.
call :MATRIX_SUCCESS
goto :CLEANUP

:LOADING_ANIMATION
echo.
echo                    LOADING THE MATRIX...
echo.
echo                    [
<nul set /p =                    [
for /l %%i in (1,1,40) do (
    set /a "r=!random! %% 4"
    if !r!==0 <nul set /p =#
    if !r!==1 <nul set /p =@
    if !r!==2 <nul set /p =*
    if !r!==3 <nul set /p =+
    timeout /t 0 >nul 2>&1
)
echo ]
echo.
echo                    [SYSTEM READY]
exit /b

:MATRIX_DOWNLOAD
set "url=%~1"
set "output=%~2"

echo [DOWNLOADING] Establishing secure channel...
echo.

powershell -NoProfile -Command ^
"try { ^
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
    $url = '%url%'; ^
    $output = '%output%'; ^
    $client = New-Object System.Net.WebClient; ^
    $client.Headers.Add('User-Agent', 'MatrixClient/1.0'); ^
    Write-Host '[' -NoNewline; ^
    $progress = 0; ^
    $client.DownloadFileAsync($url, $output); ^
    while ($client.IsBusy) { ^
        Start-Sleep -Milliseconds 100; ^
        $progress++; ^
        if ($progress %% 10 -eq 0) { ^
            Write-Host '=' -NoNewline -ForegroundColor Green; ^
        } ^
    } ^
    Write-Host '] DOWNLOAD COMPLETE' -ForegroundColor Green; ^
    exit 0; ^
} catch { ^
    Write-Host 'CONNECTION TERMINATED BY AGENTS!' -ForegroundColor Red; ^
    exit 1; ^
}"

exit /b %errorlevel%

:MATRIX_EXTRACT
set "zip=%~1"
set "dest=%~2"

echo [EXTRACTING] Decrypting data streams...

powershell -Command ^
"Add-Type -AssemblyName System.IO.Compression.FileSystem; ^
[System.IO.Compression.ZipFile]::ExtractToDirectory('%zip%', '%dest%'); ^
Write-Host '[OK] Matrix decoded successfully' -ForegroundColor Green"

exit /b

:INSTALL_SKILLS
set "source=%~1"
set "dest=%~2"

echo [INSTALLING] Uploading knowledge to brain...

:: Find installer
for /f "delims=" %%i in ('dir /s /b "%source%\*INSTALL_ProxyAssessmentTool.bat" 2^>nul') do (
    echo [OK] Original training program found
    call "%%i"
    exit /b
)

:: Direct install
for /f "delims=" %%i in ('dir /s /b "%source%\*publish" 2^>nul') do (
    set "pub_dir=%%i"
    echo [OK] Skills package located
    
    :: Copy files with Matrix effect
    for %%f in ("!pub_dir!\*.exe" "!pub_dir!\*.dll" "!pub_dir!\*.json") do (
        echo [UPLOAD] %%~nxf
        copy "%%f" "%dest%\" >nul 2>&1
    )
    
    :: Handle parts
    if exist "!pub_dir!\ProxyAssessmentTool.exe.part1" (
        echo [MERGING] Assembling consciousness...
        copy /b "!pub_dir!\ProxyAssessmentTool.exe.part*" "%dest%\ProxyAssessmentTool.exe" >nul
    )
)

:: Create shortcut
echo [CREATING] Neural link to desktop...
powershell -Command ^
"$WshShell = New-Object -comObject WScript.Shell; ^
$Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\ProxyAssessmentTool.lnk'); ^
$Shortcut.TargetPath = '%dest%\ProxyAssessmentTool.exe'; ^
$Shortcut.Description = 'Enter the Matrix'; ^
$Shortcut.Save()"

echo [OK] Neural link established
exit /b

:MATRIX_SUCCESS
echo.
echo =====================================================
echo.
echo                    WELCOME TO THE REAL WORLD
echo.
echo           You are now unplugged from the Matrix
echo         ProxyAssessmentTool has been downloaded
echo              directly into your consciousness
echo.
echo =====================================================
echo.
echo Installation Path: %install_dir%
echo.
echo Press any key to use your new abilities...
pause >nul

if exist "%install_dir%\ProxyAssessmentTool.exe" (
    start "" "%install_dir%\ProxyAssessmentTool.exe"
)
exit /b

:BLUE_PILL
cls
echo.
echo                    You took the blue pill...
echo                    The story ends.
echo                    You wake up in your bed
echo                    and believe whatever you want to believe.
echo.
timeout /t 3 >nul 2>&1
exit /b

:HACK_MATRIX
cls
echo.
echo                    ACCESS DENIED
echo                    =============
echo                    
echo                    INSUFFICIENT PRIVILEGES
echo                    AGENT SMITH HAS BEEN NOTIFIED
echo.
pause
goto :MAIN_MENU

:DIAGNOSTICS
cls
echo.
echo                    SYSTEM DIAGNOSTICS
echo                    =================
echo.
echo Scanning reality matrix...
timeout /t 1 >nul 2>&1
echo [OK] Reality stable
echo [OK] No glitches detected
echo [OK] Agents not present
echo [OK] You are not in a simulation (probably)
echo.
pause
goto :MAIN_MENU

:UNPLUG
cls
echo.
echo                    UNPLUGGING...
echo                    ============
echo.
echo Warning: Once unplugged, there is no going back.
echo.
pause
goto :CLEANUP

:DRAW_MATRIX_HEADER
echo.
echo    0100110101000001010101000101001001001001010110000010000001001001010011100101001101010100
echo    +------------------------------------------------------------------------------+
echo    ^|   ___  ___  ___ _____ ____  _____  __    _____ _   _  ____ _____  ___  _    ^|
echo    ^|  ^|  \/  ^| / _ \_   _^|  _ \^|_ _^| \/ ^|   ^|_   _^| \ ^| ^|/ ___^|_   _^|/ _ \^| ^|   ^|
echo    ^|  ^| ^|\/^| ^|^| ^| ^| ^|^| ^| ^| ^|_) ^| ^| ^| ^|  /\ ^|     ^| ^| ^|  \^| ^|\___ \ ^| ^| ^| ^| ^| ^| ^|   ^|
echo    ^|  ^| ^|  ^| ^|^| ^|_^| ^|^| ^| ^|  _ < _^| ^|_^| ^|/ \^|    _^| ^|_^| ^|\  ^| ___) ^|^| ^| ^| ^|_^| ^| ^|___^|
echo    ^|  ^|_^|  ^|_^| \___/ ^|_^| ^|_^| \_\___/^|_/  \^|   ^|_____^|_^| \_^|____/ ^|_^|  \___/^|_____^|
echo    +------------------------------------------------------------------------------+
echo    1011001010110010101100101011001010110010101100101011001010110010101100101011001
echo.
exit /b

:CLEANUP
if exist "%temp_dir%" rmdir /s /q "%temp_dir%" 2>nul
echo.
echo                    Cleaning up the Matrix...
echo                    Goodbye.
echo.
timeout /t 2 >nul 2>&1
exit /b