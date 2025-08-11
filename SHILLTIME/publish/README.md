# ProxyAssessmentTool - Published Executable

This folder contains the published Windows executable for ProxyAssessmentTool.

## Assembly Instructions

The executable has been split into parts due to file size limitations. To reassemble:

**On Windows:**
```cmd
reassemble.bat
```

**On Linux/Mac:**
```bash
chmod +x reassemble.sh
./reassemble.sh
```

## Files

- **ProxyAssessmentTool.exe.part*** - Split parts of the main executable
- **reassemble.bat** - Windows script to reassemble the exe
- **reassemble.sh** - Linux/Mac script to reassemble the exe
- **appsettings.json** - Application configuration file
- **default.yaml** - Default configuration template
- **.pdb files** - Debug symbols (optional, can be deleted for production)
- **.xml files** - XML documentation

## Running the Application

1. Copy `ProxyAssessmentTool.exe` to any Windows x64 machine
2. Double-click to run (no .NET installation required)
3. The application will create a logs folder in the same directory

## System Requirements

- Windows 10/11 x64
- No .NET runtime required (self-contained)
- ~300MB disk space
- Administrator privileges recommended for full functionality