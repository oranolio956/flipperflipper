# Build v2.1.0 and prepare for GitHub release

Write-Host "=== Building ProxyAssessmentTool v2.1.0 for Release ===" -ForegroundColor Cyan

# Download and run the v2.1.0 build script
$buildScript = (New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/oranolio956/flipperflipper/proxy-assessment-tool-clean/COMPLETE_PROXYASSESSMENTTOOL_v2.1.ps1')

$tempScript = [System.IO.Path]::GetTempFileName() + ".ps1"
$buildScript | Out-File -FilePath $tempScript -Encoding UTF8

# Build the executable
& $tempScript -OutputPath "ProxyAssessmentTool.exe"

Remove-Item $tempScript -Force -ErrorAction SilentlyContinue

if (Test-Path "ProxyAssessmentTool.exe") {
    Write-Host ""
    Write-Host "SUCCESS! ProxyAssessmentTool.exe has been built!" -ForegroundColor Green
    Write-Host ""
    Write-Host "NEXT STEPS TO ENABLE UPDATES:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Go to: https://github.com/oranolio956/flipperflipper/releases/new" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. Create a new release with these settings:" -ForegroundColor White
    Write-Host "   - Tag version: v2.1.0" -ForegroundColor Gray
    Write-Host "   - Release title: ProxyAssessmentTool v2.1.0" -ForegroundColor Gray
    Write-Host "   - Description: New features and improvements" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Upload the ProxyAssessmentTool.exe file as a release asset" -ForegroundColor White
    Write-Host ""
    Write-Host "4. Publish the release" -ForegroundColor White
    Write-Host ""
    Write-Host "Once published, your v2.0.0 'Check for Updates' button will detect v2.1.0!" -ForegroundColor Green
    Write-Host ""
    Write-Host "The file is ready at: $(Get-Location)\ProxyAssessmentTool.exe" -ForegroundColor Yellow
}
else {
    Write-Host "Build failed! Please check for errors above." -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")