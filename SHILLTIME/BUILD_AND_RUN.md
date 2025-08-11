# ProxyAssessmentTool - Build and Run Guide

## Quick Start - Using Pre-built Executable

The pre-built executable is located in the `publish/` folder, split into parts for GitHub compatibility.

### Step 1: Reassemble the Executable

Navigate to the `publish/` folder and run one of the reassembly scripts:

**Windows (Command Prompt):**
```cmd
cd publish
reassemble.bat
```

**Windows (PowerShell):**
```powershell
cd publish
.\reassemble.ps1
```

**Linux/Mac:**
```bash
cd publish
chmod +x reassemble.sh
./reassemble.sh
```

This will create `ProxyAssessmentTool.exe` (230MB).

### Step 2: Run the Application

Simply double-click `ProxyAssessmentTool.exe` or run from command line:
```cmd
ProxyAssessmentTool.exe
```

## Building from Source

### Prerequisites
- .NET 8 SDK
- Windows SDK (for WPF support)
- Visual Studio 2022 or VS Code (optional)

### Build Steps

1. **Clone the repository:**
```bash
git clone [repository-url]
cd SHILLTIME
```

2. **Build using the provided script:**
```bash
chmod +x publish_minimal.sh
./publish_minimal.sh
```

Or manually:

3. **Restore packages:**
```bash
dotnet restore
```

4. **Build the solution:**
```bash
dotnet build -c Release
```

5. **Publish as single executable:**
```bash
dotnet publish src/ProxyAssessmentTool/ProxyAssessmentTool.csproj -c Release -r win-x64 --self-contained -p:PublishSingleFile=true -o ./publish
```

## Features Implemented

### Core Functionality
- ✅ Dependency Injection with Microsoft.Extensions.Hosting
- ✅ Structured logging with Serilog
- ✅ WPF user interface with MVVM pattern
- ✅ Security features (MFA providers, session management)
- ✅ Connection pooling for performance
- ✅ Eligibility evaluation system
- ✅ Input validation framework

### Architecture
- ✅ Clean architecture with Core/UI separation
- ✅ Interface-based design for testability
- ✅ Service implementations for all major components
- ✅ Configuration management system
- ✅ Audit and evidence storage

### Services Implemented
- ConfigurationManager
- ConsentLedger
- AuditLogger
- EvidenceStore
- Orchestrator
- DiscoveryEngine
- ProtocolFingerprinter
- SafeValidator
- And many more...

## Configuration

The application uses:
- `appsettings.json` for application settings
- `default.yaml` for default configuration template
- Windows DPAPI for secure credential storage

## System Requirements

- **OS**: Windows 10/11 x64
- **Runtime**: Self-contained (no .NET installation required)
- **Disk Space**: ~300MB
- **RAM**: 512MB minimum
- **Privileges**: Administrator recommended for full functionality

## Troubleshooting

### Application won't start
1. Ensure you've reassembled the exe correctly
2. Check Windows Defender/antivirus isn't blocking it
3. Run as Administrator
4. Check the logs folder for error details

### Build errors
1. Ensure .NET 8 SDK is installed: `dotnet --version`
2. Clean and rebuild: `dotnet clean && dotnet build`
3. Delete `bin/` and `obj/` folders and retry

## Security Notice

This tool is designed for **authorized security assessments only**. Always ensure you have explicit written permission before running any assessments. The application includes multiple safety controls and consent verification mechanisms.

## Support

For issues or questions:
1. Check the logs in the application directory
2. Review the error messages in the UI
3. Consult the inline documentation (XML files)