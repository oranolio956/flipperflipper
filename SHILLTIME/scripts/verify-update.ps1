param(
    [Parameter(Mandatory=$true)]
    [string]$PackagePath,
    
    [Parameter(Mandatory=$true)]
    [string]$ExpectedThumbprint
)

$ErrorActionPreference = "Stop"

Write-Host "Verifying Update Package" -ForegroundColor Cyan
Write-Host "=======================`n" -ForegroundColor Cyan

# Check file exists
if (-not (Test-Path $PackagePath)) {
    throw "Package file not found: $PackagePath"
}

# Verify digital signature
Write-Host "Checking digital signature..." -ForegroundColor Yellow
$sig = Get-AuthenticodeSignature -FilePath $PackagePath

if ($sig.Status -ne "Valid") {
    throw "Invalid signature status: $($sig.Status)"
}

$actualThumbprint = $sig.SignerCertificate.Thumbprint
if ($actualThumbprint -ne $ExpectedThumbprint.Replace(" ", "").ToUpper()) {
    throw "Certificate thumbprint mismatch. Expected: $ExpectedThumbprint, Actual: $actualThumbprint"
}

Write-Host "✓ Signature valid" -ForegroundColor Green
Write-Host "  Signer: $($sig.SignerCertificate.Subject)" -ForegroundColor Gray
Write-Host "  Thumbprint: $actualThumbprint" -ForegroundColor Gray

# Extract and verify manifest
Write-Host "`nExtracting manifest..." -ForegroundColor Yellow
Add-Type -Assembly System.IO.Compression.FileSystem
$tempDir = Join-Path $env:TEMP "verify_$([Guid]::NewGuid())"
New-Item -ItemType Directory -Force $tempDir | Out-Null

try {
    $zip = [System.IO.Compression.ZipFile]::OpenRead($PackagePath)
    $manifestEntry = $zip.Entries | Where-Object { $_.Name -eq "manifest.json" }
    
    if (-not $manifestEntry) {
        throw "Manifest not found in package"
    }
    
    $manifestPath = Join-Path $tempDir "manifest.json"
    [System.IO.Compression.ZipFileExtensions]::ExtractToFile($manifestEntry, $manifestPath)
    
    $manifest = Get-Content $manifestPath | ConvertFrom-Json
    
    Write-Host "✓ Manifest found" -ForegroundColor Green
    Write-Host "  Version: $($manifest.version)" -ForegroundColor Gray
    Write-Host "  Files: $($manifest.files.Count)" -ForegroundColor Gray
    Write-Host "  Publisher: $($manifest.publisherThumbprint)" -ForegroundColor Gray
    
    # Verify file hashes
    Write-Host "`nVerifying file integrity..." -ForegroundColor Yellow
    $errors = 0
    
    foreach ($file in $manifest.files) {
        $entry = $zip.Entries | Where-Object { $_.FullName -eq $file.path }
        if (-not $entry) {
            Write-Host "✗ Missing file: $($file.path)" -ForegroundColor Red
            $errors++
            continue
        }
        
        $tempFile = Join-Path $tempDir "temp_file"
        [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $tempFile, $true)
        
        $actualHash = (Get-FileHash -Path $tempFile -Algorithm SHA256).Hash
        if ($actualHash -ne $file.sha256.ToUpper()) {
            Write-Host "✗ Hash mismatch: $($file.path)" -ForegroundColor Red
            $errors++
        }
        
        Remove-Item $tempFile -Force
    }
    
    if ($errors -eq 0) {
        Write-Host "✓ All files verified successfully" -ForegroundColor Green
    } else {
        throw "$errors file(s) failed verification"
    }
    
} finally {
    $zip.Dispose()
    Remove-Item -Recurse -Force $tempDir
}

Write-Host "`n✓ Package verification complete!" -ForegroundColor Green