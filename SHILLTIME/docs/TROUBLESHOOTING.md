# ProxyAssessmentTool Troubleshooting Guide

## White Screen Then Closes

If the application shows a white screen and then closes immediately:

### Immediate Steps

1. **Check Safe Mode**
   - The application should show a Safe Mode window with error details
   - If no window appears, check the Event Viewer

2. **Event Viewer**
   - Open Event Viewer (Win+R, type `eventvwr.msc`)
   - Navigate to Windows Logs > Application
   - Look for errors from "ProxyAssessmentTool" or ".NET Runtime"

3. **Check Logs**
   - Navigate to: `%LOCALAPPDATA%\ProxyAssessmentTool\logs`
   - Open the most recent `.ndjson` file
   - Look for entries with `"Level":"Fatal"` or `"Level":"Error"`

### Common Causes and Solutions

#### Missing .NET Runtime
- **Symptom**: Error about missing framework
- **Solution**: Install .NET 8 Desktop Runtime from Microsoft

#### Corrupted Installation
- **Symptom**: File not found errors in logs
- **Solution**: Reinstall the application

#### Permission Issues
- **Symptom**: Access denied errors
- **Solution**: 
  1. Run as Administrator once
  2. Check folder permissions on `%LOCALAPPDATA%\ProxyAssessmentTool`

#### Database Corruption
- **Symptom**: SQLite errors in logs
- **Solution**: 
  1. Close the application
  2. Delete `%LOCALAPPDATA%\ProxyAssessmentTool\data\app.db`
  3. Restart (database will be recreated)

### Diagnostic Commands

```powershell
# Enable detailed logging
set DOTNET_CLI_TELEMETRY_OPTOUT=1
set COMPlus_EnableEventLog=1

# Run with console output
ProxyAssessmentTool.exe --console

# Reset application
ProxyAssessmentTool.exe --reset
```

### Collecting Diagnostics

1. Open Safe Mode (if available)
2. Click "Copy Diagnostics"
3. Or run: `ProxyAssessmentTool.exe --collect-diagnostics`

This creates a ZIP file with:
- Recent logs
- System information
- Configuration files
- Startup health history

## Update Issues

### "Invalid Signature" Error
- **Cause**: Update package is not properly signed
- **Solution**: 
  1. Download update package again
  2. Verify publisher before installing
  3. Contact support if issue persists

### "Hash Mismatch" Error
- **Cause**: Update package is corrupted
- **Solution**: Download the update package again

### Update Fails to Apply
- **Cause**: Application is still running
- **Solution**:
  1. Close all instances of ProxyAssessmentTool
  2. Check Task Manager for remaining processes
  3. Try update again

### Rollback After Failed Update
1. Navigate to `%LOCALAPPDATA%\ProxyAssessmentTool`
2. Find the backup folder (e.g., `app-1.0.0.backup-20240115120000`)
3. Delete the current version folder
4. Rename backup folder to original name

## Performance Issues

### Slow Startup
- **Check**: StartupHealth.json shows high ElapsedMilliseconds
- **Solutions**:
  1. Check antivirus exclusions
  2. Verify disk health
  3. Clear temporary files

### High Memory Usage
- **Check**: Task Manager shows excessive memory
- **Solutions**:
  1. Check for memory leaks in logs
  2. Restart application
  3. Update to latest version

## Network Issues

### Proxy Discovery Fails
- **Check**: Firewall settings
- **Solutions**:
  1. Add firewall exception for ProxyAssessmentTool.exe
  2. Check network adapter settings
  3. Verify authorized IP ranges

### Cannot Reach Canary Endpoints
- **Check**: DNS resolution
- **Solutions**:
  1. Verify DNS settings
  2. Check proxy configuration
  3. Test with direct connection

## Contact Support

If the issue persists:
1. Collect diagnostics (see above)
2. Note the exact error message
3. Include:
   - Windows version
   - .NET version
   - Application version
   - Steps to reproduce
4. Send to: support@proxyassessmenttool.com