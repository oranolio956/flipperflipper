@echo off
setlocal enabledelayedexpansion
mode con: cols=120 lines=40
color 0A

:: COSMIC PROXY ASSESSMENT TOOL INSTALLER
:: THE MOST INSANE INSTALLER IN THE GALAXY! 

:: Initialize sound system
powershell -c "[console]::beep(440,200)"

:: Clear screen with style
cls

:: Epic intro sequence
call :DISPLAY_ROCKET
timeout /t 2 /nobreak >nul

:: Main installer loop
:MAIN_MENU
cls
call :DRAW_PORTAL
echo.

:: Get user name for personalization
if not defined USERNAME set USERNAME=Space Traveler

echo                            [92m╔═══════════════════════════════════════════════════════╗[0m
echo                            [92m║[0m  [95mWELCOME %USERNAME% TO THE COSMIC INSTALLER![0m  [92m║[0m
echo                            [92m╚═══════════════════════════════════════════════════════╝[0m
echo.

:: Random space fact
call :RANDOM_SPACE_FACT

echo.
echo                                    [96m┌─────────────────────────┐[0m
echo                                    [96m│[0m  [93m⚡ POWER LEVELS ⚡[0m     [96m│[0m
echo                                    [96m└─────────────────────────┘[0m

:: Animated power bar
call :ANIMATE_POWER_BAR

echo.
echo                               [95m🎮 CHOOSE YOUR INSTALLATION MODE 🎮[0m
echo.
echo                        [36m[1][0m 🚀 [92mHYPERSPACE INSTALL[0m (Recommended)
echo                        [36m[2][0m 🛸 [93mQUANTUM TELEPORT[0m (Advanced)
echo                        [36m[3][0m 🌌 [94mGALACTIC REPAIR[0m (Fix Issues)
echo                        [36m[4][0m 💫 [95mCOSMIC UNINSTALL[0m (Remove)
echo                        [36m[5][0m 🌠 [91mABORT MISSION[0m (Exit)
echo.

:: Cool input prompt with animation
call :ANIMATED_PROMPT
set /p choice=

:: Sound effect for selection
powershell -c "[console]::beep(800,100)"

if "%choice%"=="1" goto :HYPERSPACE_INSTALL
if "%choice%"=="2" goto :QUANTUM_TELEPORT
if "%choice%"=="3" goto :GALACTIC_REPAIR
if "%choice%"=="4" goto :COSMIC_UNINSTALL
if "%choice%"=="5" goto :ABORT_MISSION

:: Invalid choice - fun error
call :INVALID_CHOICE
goto :MAIN_MENU

:HYPERSPACE_INSTALL
cls
call :DRAW_SPACESHIP
echo.
echo                          [92m🚀 INITIATING HYPERSPACE SEQUENCE 🚀[0m
echo.

:: Create directories with style
set "INSTALL_DIR=%LOCALAPPDATA%\ProxyAssessmentTool"
set "TEMP_DIR=%TEMP%\ProxyAssessmentTool_Cosmic_%RANDOM%"

call :CREATE_DIRECTORY "%INSTALL_DIR%" "QUANTUM FOLDER"
call :CREATE_DIRECTORY "%TEMP_DIR%" "TEMPORAL CACHE"

:: Download with epic progress
echo.
echo                        [96m📡 ESTABLISHING GALACTIC CONNECTION 📡[0m
echo.

:: Fixed GitHub URL
set "GITHUB_URL=https://github.com/oranolio956/flipperflipperzero-ESP-chiptune/archive/refs/heads/proxy-assessment-tool-clean.zip"
set "DOWNLOAD_FILE=%TEMP_DIR%\cosmic_payload.zip"

call :DOWNLOAD_WITH_STYLE "%GITHUB_URL%" "%DOWNLOAD_FILE%"

if %errorlevel% neq 0 (
    call :DOWNLOAD_FAILED
    goto :MAIN_MENU
)

:: Extract with animations
echo.
echo                        [95m⚡ DECOMPRESSING QUANTUM DATA ⚡[0m
echo.
call :EXTRACT_WITH_ANIMATION "%DOWNLOAD_FILE%" "%TEMP_DIR%"

:: Install files with effects
echo.
echo                        [93m🔧 ASSEMBLING COSMIC COMPONENTS 🔧[0m
echo.

:: Find and install files
call :INSTALL_COMPONENTS "%TEMP_DIR%" "%INSTALL_DIR%"

:: Create shortcuts with flair
call :CREATE_COSMIC_SHORTCUTS "%INSTALL_DIR%"

:: Final celebration
call :INSTALLATION_COMPLETE

goto :END

:ANIMATED_PROMPT
echo.
set "prompt=                              [96m>[0m [93m>[0m [92m>[0m "
for %%a in (M A K E Y O U R C H O I C E) do (
    set prompt=!prompt!%%a 
    <nul set /p =!prompt!
    powershell -c "[console]::beep(500,50)"
    timeout /t 0 >nul
)
echo  [91m<[0m [93m<[0m [96m<[0m
echo.
echo                                    [95m[[0m[96m?[0m[95m][0m 
exit /b

:ANIMATE_POWER_BAR
echo.
echo                          [90m[[0m
<nul set /p =                          [90m[[0m
for /l %%i in (1,1,30) do (
    set /a "color=%%i %% 6"
    if !color!==0 <nul set /p =[91m█[0m
    if !color!==1 <nul set /p =[93m█[0m
    if !color!==2 <nul set /p =[92m█[0m
    if !color!==3 <nul set /p =[96m█[0m
    if !color!==4 <nul set /p =[94m█[0m
    if !color!==5 <nul set /p =[95m█[0m
    powershell -c "[console]::beep(!random! %% 1000 + 200, 30)"
    timeout /t 0 >nul
)
echo [90m][0m [92m100%%[0m
echo.
exit /b

:DOWNLOAD_WITH_STYLE
set "url=%~1"
set "output=%~2"

:: Create visual download effect
echo.
for /l %%i in (1,1,5) do (
    echo                        [96m📡[0m          [93m◜◝[0m          [96m📡[0m
    timeout /t 0 >nul
    cls
    call :DRAW_PORTAL
    echo.
    echo                        [96m📡[0m          [93m◟◞[0m          [96m📡[0m
    timeout /t 0 >nul
)

:: Actual download with progress
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"try { ^
    $ProgressPreference = 'SilentlyContinue'; ^
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
    $webClient = New-Object System.Net.WebClient; ^
    $webClient.Headers.Add('User-Agent', 'CosmicInstaller/1.0'); ^
    Write-Host ''; ^
    Write-Host '                    '; ^
    $lastPercent = 0; ^
    $webClient.DownloadFileAsync('%url%', '%output%'); ^
    while ($webClient.IsBusy) { ^
        Start-Sleep -Milliseconds 100; ^
        if ($webClient.ResponseHeaders) { ^
            try { ^
                $totalBytes = [long]$webClient.ResponseHeaders['Content-Length']; ^
                $receivedBytes = (Get-Item '%output%' -ErrorAction SilentlyContinue).Length; ^
                if ($receivedBytes -and $totalBytes) { ^
                    $percent = [int](($receivedBytes / $totalBytes) * 100); ^
                    if ($percent -ne $lastPercent) { ^
                        $lastPercent = $percent; ^
                        Write-Host -NoNewline \"`r                    DOWNLOAD: [\"; ^
                        $filled = [int]($percent / 3.33); ^
                        for ($i = 0; $i -lt 30; $i++) { ^
                            if ($i -lt $filled) { ^
                                Write-Host -NoNewline '█' -ForegroundColor Green; ^
                            } else { ^
                                Write-Host -NoNewline '░' -ForegroundColor DarkGray; ^
                            } ^
                        } ^
                        Write-Host -NoNewline \"] $percent%% \"; ^
                        [console]::beep(200 + $percent * 5, 50); ^
                    } ^
                } ^
            } catch {} ^
        } ^
    } ^
    Write-Host ''; ^
    Write-Host '                    🎉 DOWNLOAD COMPLETE! 🎉' -ForegroundColor Green; ^
    exit 0; ^
} catch { ^
    Write-Host \"COSMIC ERROR: $_\" -ForegroundColor Red; ^
    exit 1; ^
}"

exit /b %errorlevel%

:EXTRACT_WITH_ANIMATION
set "zipfile=%~1"
set "destination=%~2"

echo.
for /l %%i in (1,1,10) do (
    set /a pos=%%i
    <nul set /p =                    
    for /l %%j in (1,1,!pos!) do <nul set /p = 
    echo [93m⚡[0m EXTRACTING QUANTUM PARTICLES [93m⚡[0m
    powershell -c "[console]::beep(300 + %%i * 50, 50)"
    timeout /t 0 >nul
    cls
    call :DRAW_PORTAL
    echo.
)

powershell -Command "Expand-Archive -Path '%zipfile%' -DestinationPath '%destination%' -Force"
exit /b

:INSTALL_COMPONENTS
set "source=%~1"
set "dest=%~2"

echo.
:: Find installer or parts
for /f "delims=" %%i in ('dir /s /b "%source%\*INSTALL_ProxyAssessmentTool.bat" 2^>nul') do (
    echo                    [92m✓[0m Found Original Installer Module
    call "%%i"
    exit /b
)

:: Direct installation
for /f "delims=" %%i in ('dir /s /b "%source%\*publish*" 2^>nul') do (
    set "pub_dir=%%i"
    echo                    [92m✓[0m Located Published Components
    
    :: Copy with effects
    for %%f in ("!pub_dir!\*.exe" "!pub_dir!\*.dll" "!pub_dir!\*.json") do (
        echo                    [96m»[0m Installing: %%~nxf
        copy "%%f" "%dest%\" >nul 2>&1
        powershell -c "[console]::beep(800, 30)"
    )
    
    :: Handle parts
    if exist "!pub_dir!\ProxyAssessmentTool.exe.part1" (
        echo                    [93m⚡[0m Assembling Quantum Executable
        copy /b "!pub_dir!\ProxyAssessmentTool.exe.part*" "%dest%\ProxyAssessmentTool.exe" >nul
    )
)
exit /b

:CREATE_COSMIC_SHORTCUTS
set "install_dir=%~1"

echo.
echo                    [95m🌟 CREATING COSMIC SHORTCUTS 🌟[0m

powershell -Command ^
"$WshShell = New-Object -comObject WScript.Shell; ^
$Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\ProxyAssessmentTool.lnk'); ^
$Shortcut.TargetPath = '%install_dir%\ProxyAssessmentTool.exe'; ^
$Shortcut.WorkingDirectory = '%install_dir%'; ^
$Shortcut.IconLocation = '%install_dir%\ProxyAssessmentTool.exe'; ^
$Shortcut.Description = 'Launch the Cosmic Proxy Assessment Tool'; ^
$Shortcut.Save()"

echo                    [92m✓[0m Desktop Portal Created!
exit /b

:INSTALLATION_COMPLETE
cls
call :DRAW_VICTORY
echo.
echo                    [92m🎊 INSTALLATION COMPLETE! 🎊[0m
echo.
echo                    [93mThe ProxyAssessmentTool has been[0m
echo                    [93msuccessfully deployed to your system![0m
echo.

:: Play victory tune
powershell -c "440,493,523,587,659,698,784,880 | % {[console]::beep($_, 200)}"

echo.
echo                    [96mPress any key to launch...[0m
pause >nul

if exist "%INSTALL_DIR%\ProxyAssessmentTool.exe" (
    start "" "%INSTALL_DIR%\ProxyAssessmentTool.exe"
)
exit /b

:DRAW_ROCKET
echo.
echo                                    [91m     /\[0m
echo                                    [91m    /  \[0m
echo                                    [93m   /    \[0m
echo                                    [93m  /      \[0m
echo                                    [96m |   PA   |[0m
echo                                    [96m |  TOOL  |[0m
echo                                    [94m |________|[0m
echo                                    [91m  \\    //[0m
echo                                    [93m   \\  //[0m
echo                                    [95m    \\//[0m
echo                                    [91m    🔥🔥[0m
echo.
exit /b

:DRAW_PORTAL
echo.
echo                         [95m        .  *  .   . *   .   .  *  .[0m
echo                         [94m    *  .  ◯  . * .  ◯  .  *  .  ◯  *[0m
echo                         [96m  .   ╱════════════════════════╲   .[0m
echo                         [96m *   ╱  ╱▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔╲  ╲  *[0m
echo                         [93m .  ╱  ╱   COSMIC PORTAL    ╲  ╲ .[0m
echo                         [92m   ╱  ╱  ==================  ╲  ╲[0m
echo                         [92m  ╱  ╱   INSTALLER  v3.0.0    ╲  ╲[0m
echo                         [91m ╱  ╱▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁╲  ╲[0m
echo                         [91m╱▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁╲[0m
echo                         [95m  *  .   .  *   .   . *  .  .  *[0m
exit /b

:DRAW_SPACESHIP
echo.
echo                              [96m         ▲[0m
echo                              [96m        ╱ ╲[0m
echo                              [94m       ╱   ╲[0m
echo                              [94m      ╱     ╲[0m
echo                              [92m     ╱  [■]  ╲[0m
echo                              [92m    ╱_________╲[0m
echo                              [93m   ╱___________╲[0m
echo                              [91m  🔥 🔥 🔥 🔥 🔥[0m
exit /b

:DRAW_VICTORY
echo.
echo                    [93m    *    .  *       .             *[0m
echo                    [92m *   .        *       ____     .      *[0m
echo                    [96m   .     *         _.='/^^^\='._     .[0m
echo                    [95m     *          _/=    ╰◡╯    =\_   *[0m
echo                    [94m  .      *     /=  SUCCESS!!!   =\     .[0m
echo                    [93m      .       /=    ▔▔▔▔▔▔▔▔    =\  *[0m
echo                    [92m   *     .   /= ╔══════════════╗ =\    .[0m
echo                    [91m     .      (=  ║ MISSION DONE ║  =)[0m
echo                    [95m  .     *    \= ╚══════════════╝ =/   *[0m
echo                    [94m    *   .     \=                =/  .[0m
echo                    [93m  *   .    .   '================'    *[0m
echo                    [92m      *  .   *       .      *    .   *[0m
exit /b

:RANDOM_SPACE_FACT
set /a fact=!random! %% 5
if !fact!==0 echo                    [95m💫 DID YOU KNOW: This installer can travel at warp speed! 💫[0m
if !fact!==1 echo                    [95m💫 FUN FACT: 100%% of users love cosmic installers! 💫[0m
if !fact!==2 echo                    [95m💫 SPACE TIP: Updates arrive faster than light! 💫[0m
if !fact!==3 echo                    [95m💫 COSMIC TRUTH: This is the coolest installer ever! 💫[0m
if !fact!==4 echo                    [95m💫 GALAXY NEWS: ProxyAssessmentTool rated #1 by aliens! 💫[0m
exit /b

:INVALID_CHOICE
cls
echo.
echo                         [91m⚠️  COSMIC ERROR DETECTED! ⚠️[0m
echo.
echo                    [93mThat option exists in a parallel[0m
echo                    [93muniverse, but not this one![0m
echo.
powershell -c "800,400,200,100 | % {[console]::beep($_, 100)}"
timeout /t 2 /nobreak >nul
exit /b

:DOWNLOAD_FAILED
cls
echo.
echo                    [91m🛸 TRANSMISSION INTERRUPTED! 🛸[0m
echo.
echo                    [93mThe cosmic connection was lost![0m
echo                    [93mPlease check your quantum internet.[0m
echo.
echo                    [96mManual coordinates:[0m
echo                    [94mhttps://github.com/oranolio956/flipperflipperzero-ESP-chiptune[0m
echo.
pause
exit /b

:QUANTUM_TELEPORT
cls
echo.
echo                    [93m🛸 QUANTUM TELEPORT ACTIVATED! 🛸[0m
echo                    [91mThis feature exists in the future![0m
echo                    [91mComing in version 4.0![0m
echo.
pause
goto :MAIN_MENU

:GALACTIC_REPAIR
cls
echo.
echo                    [94m🌌 SCANNING FOR ANOMALIES... 🌌[0m
timeout /t 2 /nobreak >nul
echo                    [92m✓ No black holes detected![0m
echo                    [92m✓ Wormholes stable![0m
echo                    [92m✓ Dark matter levels normal![0m
echo.
pause
goto :MAIN_MENU

:COSMIC_UNINSTALL
cls
echo.
echo                    [91m💫 REVERSING THE COSMOS... 💫[0m
echo                    [93mUninstall feature coming soon![0m
echo.
pause
goto :MAIN_MENU

:ABORT_MISSION
cls
call :DRAW_ROCKET
echo.
echo                    [91m🚀 MISSION ABORTED! 🚀[0m
echo                    [93mReturning to Earth...[0m
echo.
powershell -c "880,784,698,659,587,523,493,440 | % {[console]::beep($_, 150)}"
timeout /t 2 /nobreak >nul
exit /b

:CREATE_DIRECTORY
if not exist "%~1" mkdir "%~1"
echo                    [92m✓[0m Created %~2
powershell -c "[console]::beep(600, 50)"
exit /b

:END
:: Cleanup
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%" 2>nul
echo.
echo                    [95m🌟 Thank you for choosing[0m
echo                    [95m   COSMIC INSTALLER! 🌟[0m
echo.
timeout /t 3 /nobreak >nul
exit /b