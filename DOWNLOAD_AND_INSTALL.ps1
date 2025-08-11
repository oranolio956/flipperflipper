# ProxyAssessmentTool Direct Installer
# This downloads and installs the app directly

Write-Host "`nProxyAssessmentTool Direct Installer" -ForegroundColor Green
Write-Host "===================================`n" -ForegroundColor Green

# Set up paths
$installDir = "$env:LOCALAPPDATA\ProxyAssessmentTool"
$tempDir = "$env:TEMP\ProxyTool_$(Get-Random)"
$zipUrl = "https://github.com/oranolio956/flipperflipperzero-ESP-chiptune/archive/refs/heads/proxy-assessment-tool-clean.zip"
$zipFile = "$tempDir\download.zip"

try {
    # Create directories
    Write-Host "[1/6] Creating directories..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    Write-Host "      [OK] Directories ready" -ForegroundColor Green

    # Download the repository
    Write-Host "`n[2/6] Downloading from GitHub..." -ForegroundColor Yellow
    Write-Host "      This will take a moment..." -ForegroundColor Gray
    
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    
    $webClient = New-Object System.Net.WebClient
    $webClient.Headers.Add("User-Agent", "Mozilla/5.0")
    
    try {
        $webClient.DownloadFile($zipUrl, $zipFile)
        $size = [math]::Round((Get-Item $zipFile).Length / 1MB, 2)
        Write-Host "      [OK] Downloaded $size MB" -ForegroundColor Green
    }
    catch {
        Write-Host "      [ERROR] Download failed!" -ForegroundColor Red
        Write-Host "      Error: $_" -ForegroundColor Red
        throw
    }

    # Extract files
    Write-Host "`n[3/6] Extracting files..." -ForegroundColor Yellow
    
    # Try built-in extraction first
    try {
        Expand-Archive -Path $zipFile -DestinationPath $tempDir -Force
        Write-Host "      [OK] Files extracted" -ForegroundColor Green
    }
    catch {
        # Fallback to .NET method
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::ExtractToDirectory($zipFile, $tempDir)
        Write-Host "      [OK] Files extracted (fallback method)" -ForegroundColor Green
    }

    # Find the publish folder
    Write-Host "`n[4/6] Locating application files..." -ForegroundColor Yellow
    
    $publishPath = Get-ChildItem -Path $tempDir -Recurse -Directory | 
                   Where-Object { $_.Name -eq "publish" } | 
                   Select-Object -First 1
    
    if (-not $publishPath) {
        # Look for the exe parts directly
        $exePart = Get-ChildItem -Path $tempDir -Recurse -File | 
                   Where-Object { $_.Name -eq "ProxyAssessmentTool.exe.part1" } | 
                   Select-Object -First 1
        
        if ($exePart) {
            $publishPath = $exePart.Directory
            Write-Host "      [OK] Found executable parts" -ForegroundColor Green
        }
        else {
            throw "Could not find application files!"
        }
    }
    else {
        Write-Host "      [OK] Found publish directory" -ForegroundColor Green
    }

    # Copy files
    Write-Host "`n[5/6] Installing application..." -ForegroundColor Yellow
    
    # Copy all files from publish directory
    Get-ChildItem -Path $publishPath.FullName -File | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $installDir -Force
    }
    
    # Assemble the exe if it's in parts
    $part1 = Join-Path $installDir "ProxyAssessmentTool.exe.part1"
    if (Test-Path $part1) {
        Write-Host "      Assembling executable..." -ForegroundColor Yellow
        
        $exePath = Join-Path $installDir "ProxyAssessmentTool.exe"
        $parts = Get-ChildItem -Path $installDir -Filter "ProxyAssessmentTool.exe.part*" | Sort-Object Name
        
        # Use cmd to combine binary files
        $cmd = "copy /b "
        $first = $true
        foreach ($part in $parts) {
            if (-not $first) { $cmd += "+" }
            $cmd += "`"$($part.FullName)`""
            $first = $false
        }
        $cmd += " `"$exePath`""
        
        cmd /c $cmd | Out-Null
        
        # Clean up parts
        Remove-Item -Path "$installDir\*.part*" -Force
        
        Write-Host "      [OK] Executable assembled" -ForegroundColor Green
    }
    
    Write-Host "      [OK] Application installed" -ForegroundColor Green

    # Create shortcuts
    Write-Host "`n[6/6] Creating shortcuts..." -ForegroundColor Yellow
    
    $exePath = Join-Path $installDir "ProxyAssessmentTool.exe"
    if (Test-Path $exePath) {
        $WshShell = New-Object -comObject WScript.Shell
        
        # Desktop shortcut
        $desktop = [Environment]::GetFolderPath("Desktop")
        $shortcut = $WshShell.CreateShortcut("$desktop\ProxyAssessmentTool.lnk")
        $shortcut.TargetPath = $exePath
        $shortcut.WorkingDirectory = $installDir
        $shortcut.IconLocation = "$exePath,0"
        $shortcut.Description = "ProxyAssessmentTool - Security Assessment Platform"
        $shortcut.Save()
        Write-Host "      [OK] Desktop shortcut created" -ForegroundColor Green
        
        # Start menu shortcut
        try {
            $startMenu = [Environment]::GetFolderPath("StartMenu")
            $folder = "$startMenu\Programs\ProxyAssessmentTool"
            New-Item -ItemType Directory -Path $folder -Force | Out-Null
            
            $shortcut = $WshShell.CreateShortcut("$folder\ProxyAssessmentTool.lnk")
            $shortcut.TargetPath = $exePath
            $shortcut.WorkingDirectory = $installDir
            $shortcut.IconLocation = "$exePath,0"
            $shortcut.Description = "ProxyAssessmentTool - Security Assessment Platform"
            $shortcut.Save()
            Write-Host "      [OK] Start menu shortcut created" -ForegroundColor Green
        }
        catch {
            Write-Host "      [WARNING] Could not create start menu shortcut" -ForegroundColor Yellow
        }
    }

    # Success!
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "    INSTALLATION COMPLETE!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "`nInstalled to: $installDir" -ForegroundColor Cyan
    Write-Host "`nYou can find ProxyAssessmentTool on your desktop!" -ForegroundColor Yellow
    
    # Ask to launch
    Write-Host "`nLaunch ProxyAssessmentTool now? (Y/N): " -NoNewline -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq 'Y' -or $response -eq 'y') {
        Start-Process $exePath
    }
}
catch {
    Write-Host "`n[ERROR] Installation failed!" -ForegroundColor Red
    Write-Host "Error details: $_" -ForegroundColor Red
    Write-Host "`nYou can try downloading manually from:" -ForegroundColor Yellow
    Write-Host $zipUrl -ForegroundColor Cyan
}
finally {
    # Cleanup
    if (Test-Path $tempDir) {
        Write-Host "`nCleaning up..." -ForegroundColor Gray
        Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "`nPress any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}