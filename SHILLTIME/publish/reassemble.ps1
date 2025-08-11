Write-Host "Reassembling ProxyAssessmentTool.exe..." -ForegroundColor Green

$parts = Get-ChildItem -Path "ProxyAssessmentTool.exe.part*" | Sort-Object Name
$outputFile = "ProxyAssessmentTool.exe"

# Remove existing file if it exists
if (Test-Path $outputFile) {
    Remove-Item $outputFile
}

# Combine all parts
$outputStream = [System.IO.File]::OpenWrite($outputFile)
foreach ($part in $parts) {
    Write-Host "Processing $($part.Name)..."
    $bytes = [System.IO.File]::ReadAllBytes($part.FullName)
    $outputStream.Write($bytes, 0, $bytes.Length)
}
$outputStream.Close()

Write-Host "Done! ProxyAssessmentTool.exe has been created." -ForegroundColor Green
Write-Host "File size: $((Get-Item $outputFile).Length / 1MB) MB"