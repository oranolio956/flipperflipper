param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [string]$CertThumbprint = "YOUR_CERTIFICATE_THUMBPRINT_HERE",
    
    [Parameter(Mandatory=$false)]
    [string]$Changelog = "Bug fixes and improvements"
)

$ErrorActionPreference = "Stop"

Write-Host "Building ProxyAssessmentTool Update Package v$Version" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# Validate version
if (-not ($Version -match '^\d+\.\d+\.\d+$')) {
    throw "Version must be in format X.Y.Z"
}

# Set paths
$projectDir = Split-Path -Parent $PSScriptRoot
$mainProject = Join-Path $projectDir "src\ProxyAssessmentTool\ProxyAssessmentTool.csproj"
$publishDir = Join-Path $projectDir "publish\app"
$packageDir = Join-Path $projectDir "publish\package"
$outputPath = Join-Path $projectDir "publish\ProxyAssessmentTool-$Version.paup"

# Clean previous builds
Write-Host "`nCleaning previous builds..." -ForegroundColor Yellow
if (Test-Path $publishDir) { Remove-Item -Recurse -Force $publishDir }
if (Test-Path $packageDir) { Remove-Item -Recurse -Force $packageDir }
New-Item -ItemType Directory -Force $publishDir | Out-Null
New-Item -ItemType Directory -Force $packageDir | Out-Null

# Build and publish
Write-Host "Building application..." -ForegroundColor Yellow
dotnet publish $mainProject `
    -c Release `
    -r win-x64 `
    --self-contained `
    -p:PublishSingleFile=true `
    -p:IncludeNativeLibrariesForSelfExtract=true `
    -p:EnableCompressionInSingleFile=true `
    -p:Version=$Version `
    -p:AssemblyVersion=$Version `
    -p:FileVersion=$Version `
    -o $publishDir

if ($LASTEXITCODE -ne 0) {
    throw "Build failed"
}

# Create manifest
Write-Host "`nCreating update manifest..." -ForegroundColor Yellow
$manifest = @{
    version = $Version
    releaseDate = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    minimumVersion = "1.0.0"
    publisherThumbprint = $CertThumbprint
    changelog = $Changelog
    files = @()
}

# Calculate file hashes and add to manifest
Get-ChildItem -Path $publishDir -File -Recurse | ForEach-Object {
    $relativePath = $_.FullName.Substring($publishDir.Length + 1).Replace('\', '/')
    $hash = (Get-FileHash -Path $_.FullName -Algorithm SHA256).Hash
    
    $manifest.files += @{
        path = $relativePath
        sha256 = $hash
        size = $_.Length
        executable = $_.Extension -in @('.exe', '.dll')
    }
    
    # Copy file to package
    $targetPath = Join-Path $packageDir $relativePath
    $targetDir = Split-Path -Parent $targetPath
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Force $targetDir | Out-Null
    }
    Copy-Item $_.FullName $targetPath
}

# Save manifest
$manifestPath = Join-Path $packageDir "manifest.json"
$manifest | ConvertTo-Json -Depth 10 | Set-Content $manifestPath

# Create ZIP package
Write-Host "Creating update package..." -ForegroundColor Yellow
Add-Type -Assembly System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($packageDir, $outputPath)

# Sign the package
Write-Host "Signing package..." -ForegroundColor Yellow
$signTool = "${env:ProgramFiles(x86)}\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe"
if (Test-Path $signTool) {
    & $signTool sign /sha1 $CertThumbprint /t http://timestamp.digicert.com /fd SHA256 $outputPath
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Failed to sign package - continuing anyway"
    }
} else {
    Write-Warning "SignTool not found - package will not be signed"
}

# Cleanup temp directories
Remove-Item -Recurse -Force $publishDir
Remove-Item -Recurse -Force $packageDir

Write-Host "`nUpdate package created successfully!" -ForegroundColor Green
Write-Host "Output: $outputPath" -ForegroundColor Green
Write-Host "Size: $([Math]::Round((Get-Item $outputPath).Length / 1MB, 2)) MB" -ForegroundColor Green

# Verify the package
Write-Host "`nVerifying package..." -ForegroundColor Yellow
& (Join-Path $PSScriptRoot "verify-update.ps1") -PackagePath $outputPath -ExpectedThumbprint $CertThumbprint