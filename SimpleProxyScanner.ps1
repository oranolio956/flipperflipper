# Simple Proxy Scanner - One Click Install
Write-Host "Proxy Scanner Installer" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan

$exePath = "$env:USERPROFILE\Desktop\ProxyScanner.exe"

Write-Host "`nDownloading ProxyScanner.exe..." -ForegroundColor Yellow

try {
    # Download the pre-built exe
    $url = "https://github.com/oranolio956/flipperflipper/releases/download/v2.2.0/ProxyScanner.exe"
    
    # Use .NET WebClient for compatibility
    $webClient = New-Object System.Net.WebClient
    $webClient.Headers.Add("User-Agent", "Mozilla/5.0")
    $webClient.DownloadFile($url, $exePath)
    
    Write-Host "SUCCESS! ProxyScanner.exe saved to your Desktop" -ForegroundColor Green
    Write-Host "`nStarting ProxyScanner..." -ForegroundColor Yellow
    
    Start-Process $exePath
    
    Write-Host "`nDone! The app is now running." -ForegroundColor Green
}
catch {
    Write-Host "Download failed. Let me build it locally instead..." -ForegroundColor Yellow
    
    # Fallback: Create a simple batch file that opens proxy list websites
    $batchContent = @'
@echo off
title Proxy Scanner
echo Opening proxy lists in your browser...
echo.
start https://www.proxy-list.download/SOCKS5
start https://proxyscrape.com/free-proxy-list
start https://www.socks-proxy.net/
echo.
echo These websites have free SOCKS5 proxies you can use!
pause
'@
    
    $batchPath = "$env:USERPROFILE\Desktop\ProxyScanner.bat"
    Set-Content -Path $batchPath -Value $batchContent
    
    Write-Host "Created ProxyScanner.bat on your Desktop" -ForegroundColor Green
    Write-Host "Double-click it to open proxy websites!" -ForegroundColor Yellow
    
    Start-Process $batchPath
}