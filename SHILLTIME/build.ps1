# ProxyAssessmentTool Build Script
# Requires: .NET 8 SDK, Windows SDK

param(
    [Parameter(Position=0)]
    [ValidateSet('Debug', 'Release')]
    [string]$Configuration = 'Release',
    
    [Parameter()]
    [switch]$Clean,
    
    [Parameter()]
    [switch]$Test,
    
    [Parameter()]
    [switch]$Package,
    
    [Parameter()]
    [switch]$Sign,
    
    [Parameter()]
    [string]$CertificateThumbprint = '',
    
    [Parameter()]
    [string]$OutputDirectory = './dist'
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

# Script configuration
$ProjectName = 'ProxyAssessmentTool'
$SolutionFile = "$ProjectName.sln"
$MainProject = "src/$ProjectName/$ProjectName.csproj"
$TestProject = "tests/$ProjectName.Tests/$ProjectName.Tests.csproj"

# Helper functions
function Write-Header {
    param([string]$Message)
    Write-Host "`n==== $Message ====" -ForegroundColor Cyan
}

function Test-DotNetSdk {
    Write-Header "Checking .NET SDK"
    
    $dotnetVersion = dotnet --version
    if ($LASTEXITCODE -ne 0) {
        throw ".NET SDK not found. Please install .NET 8 SDK."
    }
    
    if (-not $dotnetVersion.StartsWith('8.')) {
        throw ".NET 8 SDK required. Current version: $dotnetVersion"
    }
    
    Write-Host ".NET SDK $dotnetVersion found" -ForegroundColor Green
}

function Clean-Solution {
    Write-Header "Cleaning solution"
    
    dotnet clean $SolutionFile -c $Configuration
    if ($LASTEXITCODE -ne 0) {
        throw "Clean failed"
    }
    
    # Remove output directories
    @('bin', 'obj', $OutputDirectory) | ForEach-Object {
        if (Test-Path $_) {
            Remove-Item $_ -Recurse -Force
            Write-Host "Removed $_" -ForegroundColor Yellow
        }
    }
}

function Restore-Packages {
    Write-Header "Restoring NuGet packages"
    
    dotnet restore $SolutionFile
    if ($LASTEXITCODE -ne 0) {
        throw "Package restore failed"
    }
}

function Build-Solution {
    Write-Header "Building solution"
    
    $buildArgs = @(
        'build',
        $SolutionFile,
        '-c', $Configuration,
        '--no-restore',
        '-p:TreatWarningsAsErrors=true',
        '-p:AnalysisMode=AllEnabledByDefault'
    )
    
    dotnet @buildArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Build failed"
    }
    
    Write-Host "Build completed successfully" -ForegroundColor Green
}

function Run-Tests {
    Write-Header "Running tests"
    
    $testArgs = @(
        'test',
        $TestProject,
        '-c', $Configuration,
        '--no-build',
        '--logger:trx',
        '--results-directory', './test-results',
        '--collect:"XPlat Code Coverage"'
    )
    
    dotnet @testArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Tests failed"
    }
    
    Write-Host "All tests passed" -ForegroundColor Green
}

function Package-Application {
    Write-Header "Packaging application"
    
    # Create output directory
    New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
    
    # Publish self-contained executable
    $publishArgs = @(
        'publish',
        $MainProject,
        '-c', $Configuration,
        '-r', 'win-x64',
        '--self-contained', 'true',
        '-p:PublishSingleFile=true',
        '-p:PublishReadyToRun=true',
        '-p:IncludeNativeLibrariesForSelfExtract=true',
        '-p:EnableCompressionInSingleFile=true',
        '-o', "$OutputDirectory/exe"
    )
    
    dotnet @publishArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Publish failed"
    }
    
    # Copy configuration files
    Copy-Item "config/default.yaml" "$OutputDirectory/exe/" -Force
    
    # Copy data files
    New-Item -ItemType Directory -Force -Path "$OutputDirectory/exe/data" | Out-Null
    # Note: GeoIP databases would be copied here if available
    
    Write-Host "Application packaged to $OutputDirectory/exe" -ForegroundColor Green
}

function Sign-Executable {
    param([string]$ExePath)
    
    Write-Header "Signing executable"
    
    if (-not $CertificateThumbprint) {
        Write-Warning "No certificate thumbprint provided, skipping signing"
        return
    }
    
    $signtool = "${env:ProgramFiles(x86)}\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
    if (-not (Test-Path $signtool)) {
        throw "SignTool not found. Please install Windows SDK."
    }
    
    $signArgs = @(
        'sign',
        '/fd', 'SHA256',
        '/sha1', $CertificateThumbprint,
        '/t', 'http://timestamp.digicert.com',
        '/v',
        $ExePath
    )
    
    & $signtool @signArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Code signing failed"
    }
    
    Write-Host "Executable signed successfully" -ForegroundColor Green
}

function Create-Installer {
    Write-Header "Creating MSI installer"
    
    # This would use WiX Toolset or similar
    # Placeholder for installer creation
    Write-Warning "MSI installer creation not implemented in this example"
}

# Main build process
try {
    Write-Host "Building $ProjectName ($Configuration)" -ForegroundColor Magenta
    
    # Verify prerequisites
    Test-DotNetSdk
    
    # Clean if requested
    if ($Clean) {
        Clean-Solution
    }
    
    # Build steps
    Restore-Packages
    Build-Solution
    
    # Run tests if requested
    if ($Test) {
        Run-Tests
    }
    
    # Package if requested
    if ($Package) {
        Package-Application
        
        $exePath = "$OutputDirectory/exe/$ProjectName.exe"
        if ($Sign -and (Test-Path $exePath)) {
            Sign-Executable -ExePath $exePath
        }
        
        # Create installer
        # Create-Installer
    }
    
    Write-Host "`nBuild completed successfully!" -ForegroundColor Green
    
    # Display output location
    if ($Package) {
        Write-Host "`nOutput location: $((Resolve-Path $OutputDirectory).Path)" -ForegroundColor Cyan
        Get-ChildItem $OutputDirectory -Recurse -File | 
            Select-Object Name, Length, LastWriteTime |
            Format-Table -AutoSize
    }
}
catch {
    Write-Host "`nBuild failed: $_" -ForegroundColor Red
    exit 1
}

# Usage examples:
# .\build.ps1                    # Build Release configuration
# .\build.ps1 -Configuration Debug -Test  # Build Debug and run tests
# .\build.ps1 -Clean -Package -Sign -CertificateThumbprint "YOUR_CERT_THUMBPRINT"