# ProxyAssessmentTool v2.0.0 Complete Installation Script
# This is the full-featured version with Obsidian Luxe UI

Write-Host @"

██████╗ ██████╗  ██████╗ ██╗  ██╗██╗   ██╗
██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝╚██╗ ██╔╝
██████╔╝██████╔╝██║   ██║ ╚███╔╝  ╚████╔╝ 
██╔═══╝ ██╔══██╗██║   ██║ ██╔██╗   ╚██╔╝  
██║     ██║  ██║╚██████╔╝██╔╝ ██╗   ██║   
╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   
                                           
    ASSESSMENT TOOL v2.0.0 INSTALLER
    
"@ -ForegroundColor Cyan

Write-Host "Installing ProxyAssessmentTool v2.0.0 Complete Edition..." -ForegroundColor Yellow
Write-Host ""

# Download and run the complete build script
try {
    $buildScript = (New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/oranolio956/flipperflipper/proxy-assessment-tool-clean/COMPLETE_PROXYASSESSMENTTOOL.ps1')
    
    $tempScript = [System.IO.Path]::GetTempFileName() + ".ps1"
    $buildScript | Out-File -FilePath $tempScript -Encoding UTF8
    
    & $tempScript -OutputPath "$env:USERPROFILE\Desktop\ProxyAssessmentTool_v2.exe"
    
    Remove-Item $tempScript -Force -ErrorAction SilentlyContinue
    
    Write-Host ""
    Write-Host "✓ Installation complete!" -ForegroundColor Green
    Write-Host "✓ The application has been saved to your Desktop" -ForegroundColor Green
    Write-Host ""
    Write-Host "Double-click ProxyAssessmentTool_v2.exe on your Desktop to run!" -ForegroundColor Cyan
}
catch {
    Write-Host "Installation failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative method:" -ForegroundColor Yellow
    Write-Host "1. Download: https://raw.githubusercontent.com/oranolio956/flipperflipper/proxy-assessment-tool-clean/COMPLETE_PROXYASSESSMENTTOOL.ps1" -ForegroundColor Gray
    Write-Host "2. Save as COMPLETE_PROXYASSESSMENTTOOL.ps1" -ForegroundColor Gray
    Write-Host "3. Right-click → Run with PowerShell" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")