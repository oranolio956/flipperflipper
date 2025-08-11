# ProxyAssessmentTool Simple PowerShell Installer
# Run this with: powershell -ExecutionPolicy Bypass -File SIMPLE_INSTALLER.ps1

$ErrorActionPreference = "Stop"

Write-Host "`nProxyAssessmentTool Simple Installer" -ForegroundColor Cyan
Write-Host "===================================`n" -ForegroundColor Cyan

# Configuration
$installDir = "$env:LOCALAPPDATA\ProxyAssessmentTool"
$tempDir = "$env:TEMP\ProxyAssessmentTool_$(Get-Random)"
$githubUrl = "https://github.com/oranolio956/flipperflipperzero-ESP-chiptune/archive/refs/heads/proxy-assessment-tool-clean.zip"
$zipFile = "$tempDir\download.zip"

try {
    # Create directories
    Write-Host "[1/6] Creating directories..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    Write-Host "      [OK] Directories created" -ForegroundColor Green

    # Download
    Write-Host "`n[2/6] Downloading from GitHub..." -ForegroundColor Yellow
    Write-Host "      This may take a few minutes..." -ForegroundColor Gray
    
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $webClient = New-Object System.Net.WebClient
    $webClient.Headers.Add("User-Agent", "ProxyAssessmentTool-Installer")
    
    try {
        $webClient.DownloadFile($githubUrl, $zipFile)
        $size = [math]::Round((Get-Item $zipFile).Length / 1MB, 2)
        Write-Host "      [OK] Downloaded $size MB" -ForegroundColor Green
    }
    catch {
        Write-Host "      [ERROR] Download failed: $_" -ForegroundColor Red
        throw
    }

    # Extract
    Write-Host "`n[3/6] Extracting files..." -ForegroundColor Yellow
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    
    try {
        [System.IO.Compression.ZipFile]::ExtractToDirectory($zipFile, $tempDir)
        Write-Host "      [OK] Files extracted" -ForegroundColor Green
    }
    catch {
        Write-Host "      [ERROR] Extraction failed, trying alternative method..." -ForegroundColor Yellow
        Expand-Archive -Path $zipFile -DestinationPath $tempDir -Force
        Write-Host "      [OK] Alternative extraction succeeded" -ForegroundColor Green
    }

    # Find files
    Write-Host "`n[4/6] Locating installation files..." -ForegroundColor Yellow
    
    $extractedFolder = Get-ChildItem -Path $tempDir -Directory | Select-Object -First 1
    if (-not $extractedFolder) {
        throw "No extracted folder found"
    }
    
    # Look for publish folder
    $publishDir = Get-ChildItem -Path $extractedFolder.FullName -Recurse -Directory | 
                  Where-Object { $_.Name -eq "publish" } | 
                  Select-Object -First 1
    
    if ($publishDir) {
        Write-Host "      [OK] Found published files" -ForegroundColor Green
        $sourceDir = $publishDir.FullName
    }
    else {
        # Look for INSTALL_ProxyAssessmentTool.bat location
        $installerBat = Get-ChildItem -Path $extractedFolder.FullName -Recurse -File | 
                        Where-Object { $_.Name -eq "INSTALL_ProxyAssessmentTool.bat" } | 
                        Select-Object -First 1
        
        if ($installerBat) {
            $sourceDir = $installerBat.DirectoryName
            Write-Host "      [OK] Found installer directory" -ForegroundColor Green
        }
        else {
            throw "No installation files found"
        }
    }

    # Copy files
    Write-Host "`n[5/6] Installing application..." -ForegroundColor Yellow
    
    # Copy all files
    Get-ChildItem -Path $sourceDir -File | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $installDir -Force
    }
    
    # Handle split exe if present
    $part1 = Join-Path $sourceDir "ProxyAssessmentTool.exe.part1"
    if (Test-Path $part1) {
        Write-Host "      Assembling split executable..." -ForegroundColor Yellow
        $parts = Get-ChildItem -Path $sourceDir -Filter "ProxyAssessmentTool.exe.part*" | Sort-Object Name
        $exePath = Join-Path $installDir "ProxyAssessmentTool.exe"
        
        $fileStream = [System.IO.File]::Create($exePath)
        foreach ($part in $parts) {
            $bytes = [System.IO.File]::ReadAllBytes($part.FullName)
            $fileStream.Write($bytes, 0, $bytes.Length)
        }
        $fileStream.Close()
        Write-Host "      [OK] Executable assembled" -ForegroundColor Green
    }
    
    Write-Host "      [OK] Files installed" -ForegroundColor Green

    # Create shortcuts
    Write-Host "`n[6/6] Creating shortcuts..." -ForegroundColor Yellow
    
    $exePath = Join-Path $installDir "ProxyAssessmentTool.exe"
    if (Test-Path $exePath) {
        $WshShell = New-Object -comObject WScript.Shell
        
        # Desktop shortcut
        try {
            $desktop = [Environment]::GetFolderPath("Desktop")
            $shortcut = $WshShell.CreateShortcut("$desktop\ProxyAssessmentTool.lnk")
            $shortcut.TargetPath = $exePath
            $shortcut.WorkingDirectory = $installDir
            $shortcut.Description = "ProxyAssessmentTool"
            $shortcut.Save()
            Write-Host "      [OK] Desktop shortcut created" -ForegroundColor Green
        }
        catch {
            Write-Host "      [WARNING] Could not create desktop shortcut" -ForegroundColor Yellow
        }
        
        # Start menu shortcut
        try {
            $startMenu = [Environment]::GetFolderPath("StartMenu")
            $folder = "$startMenu\Programs\ProxyAssessmentTool"
            New-Item -ItemType Directory -Path $folder -Force | Out-Null
            
            $shortcut = $WshShell.CreateShortcut("$folder\ProxyAssessmentTool.lnk")
            $shortcut.TargetPath = $exePath
            $shortcut.WorkingDirectory = $installDir
            $shortcut.Description = "ProxyAssessmentTool"
            $shortcut.Save()
            Write-Host "      [OK] Start menu shortcut created" -ForegroundColor Green
        }
        catch {
            Write-Host "      [WARNING] Could not create start menu shortcut" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "      [WARNING] Executable not found, shortcuts not created" -ForegroundColor Yellow
    }

    # Success
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "    INSTALLATION COMPLETE!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "`nInstalled to: $installDir" -ForegroundColor Cyan
    
    # Launch option
    if (Test-Path $exePath) {
        Write-Host "`nWould you like to launch ProxyAssessmentTool now? (Y/N): " -NoNewline -ForegroundColor Yellow
        $response = Read-Host
        if ($response -eq 'Y' -or $response -eq 'y') {
            Start-Process $exePath
        }
    }
}
catch {
    Write-Host "`n[ERROR] Installation failed: $_" -ForegroundColor Red
    Write-Host "`nPlease download manually from:" -ForegroundColor Yellow
    Write-Host $githubUrl -ForegroundColor Cyan
}
finally {
    # Cleanup
    if (Test-Path $tempDir) {
        Write-Host "`nCleaning up temporary files..." -ForegroundColor Gray
        Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "`nPress any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}