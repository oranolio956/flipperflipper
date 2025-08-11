# ProxyAssessmentTool Universal Installer
# This script will find and install the application

Write-Host "`n=== ProxyAssessmentTool Installer ===" -ForegroundColor Cyan
Write-Host "This will install ProxyAssessmentTool on your system`n" -ForegroundColor Yellow

# Set up paths
$installDir = "$env:LOCALAPPDATA\ProxyAssessmentTool"
$desktopPath = [Environment]::GetFolderPath("Desktop")

# First, let's check if the files are already on your system
Write-Host "Checking for existing files..." -ForegroundColor Yellow

# Look for the installer files in common locations
$searchPaths = @(
    "$env:USERPROFILE\Downloads",
    "$env:USERPROFILE\Desktop",
    "$env:USERPROFILE\OneDrive\Desktop",
    "$env:USERPROFILE\OneDrive\Downloads",
    "C:\Temp",
    "$env:TEMP"
)

$foundFiles = $false
$publishDir = $null

foreach ($path in $searchPaths) {
    if (Test-Path $path) {
        Write-Host "Searching in: $path" -ForegroundColor Gray
        
        # Look for the publish folder or exe parts
        $exeParts = Get-ChildItem -Path $path -Recurse -Filter "ProxyAssessmentTool.exe.part1" -ErrorAction SilentlyContinue | Select-Object -First 1
        
        if ($exeParts) {
            $publishDir = $exeParts.DirectoryName
            $foundFiles = $true
            Write-Host "[FOUND] Located files in: $publishDir" -ForegroundColor Green
            break
        }
    }
}

# If files not found locally, download from GitHub
if (-not $foundFiles) {
    Write-Host "`nFiles not found locally. Downloading from GitHub..." -ForegroundColor Yellow
    
    $tempDir = "$env:TEMP\ProxyTool_Install"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    
    # Try different GitHub URLs
    $urls = @(
        "https://github.com/oranolio956/flipperflipperzero-ESP-chiptune/archive/refs/heads/main.zip",
        "https://github.com/oranolio956/flipperflipperzero-ESP-chiptune/archive/refs/heads/master.zip",
        "https://github.com/oranolio956/flipperflipperzero-ESP-chiptune/archive/refs/heads/proxy-assessment-tool-clean.zip"
    )
    
    $downloaded = $false
    foreach ($url in $urls) {
        Write-Host "Trying: $url" -ForegroundColor Gray
        try {
            $zipFile = "$tempDir\download.zip"
            Invoke-WebRequest -Uri $url -OutFile $zipFile -UseBasicParsing -ErrorAction Stop
            $downloaded = $true
            Write-Host "[OK] Download successful" -ForegroundColor Green
            break
        }
        catch {
            Write-Host "[SKIP] Not available" -ForegroundColor Yellow
        }
    }
    
    if ($downloaded) {
        Write-Host "`nExtracting files..." -ForegroundColor Yellow
        try {
            Expand-Archive -Path $zipFile -DestinationPath $tempDir -Force
            
            # Find the publish directory
            $exeParts = Get-ChildItem -Path $tempDir -Recurse -Filter "ProxyAssessmentTool.exe.part1" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($exeParts) {
                $publishDir = $exeParts.DirectoryName
                $foundFiles = $true
            }
        }
        catch {
            Write-Host "[ERROR] Failed to extract files" -ForegroundColor Red
        }
    }
}

# If still no files found, provide manual instructions
if (-not $foundFiles) {
    Write-Host "`n[ERROR] Could not find or download the installation files!" -ForegroundColor Red
    Write-Host "`nPlease follow these manual steps:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://github.com/oranolio956/flipperflipperzero-ESP-chiptune" -ForegroundColor Cyan
    Write-Host "2. Click the green 'Code' button and select 'Download ZIP'" -ForegroundColor Cyan
    Write-Host "3. Extract the ZIP file" -ForegroundColor Cyan
    Write-Host "4. Look for a folder called 'publish' or 'SHILLTIME\publish'" -ForegroundColor Cyan
    Write-Host "5. Run this script again after downloading`n" -ForegroundColor Cyan
    
    Read-Host "Press Enter to exit"
    exit
}

# Install the application
Write-Host "`nInstalling ProxyAssessmentTool..." -ForegroundColor Yellow

# Create installation directory
New-Item -ItemType Directory -Path $installDir -Force | Out-Null

# Copy all files
Write-Host "Copying files..." -ForegroundColor Gray
Get-ChildItem -Path $publishDir -File | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $installDir -Force
}

# Assemble the exe from parts
$exePath = "$installDir\ProxyAssessmentTool.exe"
if (Test-Path "$installDir\ProxyAssessmentTool.exe.part1") {
    Write-Host "Assembling executable..." -ForegroundColor Yellow
    
    # Get all parts in order
    $parts = Get-ChildItem -Path $installDir -Filter "ProxyAssessmentTool.exe.part*" | Sort-Object Name
    
    # Combine using cmd
    $cmd = "copy /b "
    $first = $true
    foreach ($part in $parts) {
        if (-not $first) { $cmd += "+" }
        $cmd += "`"$($part.FullName)`""
        $first = $false
    }
    $cmd += " `"$exePath`""
    
    cmd /c $cmd | Out-Null
    
    # Clean up part files
    Remove-Item "$installDir\*.part*" -Force
    
    Write-Host "[OK] Executable assembled" -ForegroundColor Green
}

# Create desktop shortcut
if (Test-Path $exePath) {
    Write-Host "Creating desktop shortcut..." -ForegroundColor Yellow
    
    $WshShell = New-Object -comObject WScript.Shell
    $shortcut = $WshShell.CreateShortcut("$desktopPath\ProxyAssessmentTool.lnk")
    $shortcut.TargetPath = $exePath
    $shortcut.WorkingDirectory = $installDir
    $shortcut.IconLocation = "$exePath,0"
    $shortcut.Description = "ProxyAssessmentTool - Security Assessment Platform"
    $shortcut.Save()
    
    Write-Host "[OK] Shortcut created" -ForegroundColor Green
}

# Success!
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "    INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nInstalled to: $installDir" -ForegroundColor Cyan
Write-Host "Desktop shortcut: ProxyAssessmentTool" -ForegroundColor Cyan

# Clean up temp files
if ($tempDir -and (Test-Path $tempDir)) {
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}

# Launch the application
Write-Host "`nLaunching ProxyAssessmentTool..." -ForegroundColor Yellow
if (Test-Path $exePath) {
    Start-Process $exePath
} else {
    Write-Host "[ERROR] Executable not found!" -ForegroundColor Red
}

Write-Host "`nPress Enter to exit..."
Read-Host