# ProxyAssessmentTool Update System Guide

## Overview

The ProxyAssessmentTool uses a secure, double-click update system with signed packages (.paup files).

## For Users

### Installing an Update

1. **Receive Update File**
   - You'll receive a `.paup` file (e.g., `ProxyAssessmentTool-2.0.0.paup`)

2. **Double-Click to Install**
   - Simply double-click the `.paup` file
   - The updater will launch automatically

3. **Verification**
   - The updater verifies the digital signature
   - You'll see the version and changelog

4. **Installation**
   - Click "Install Update"
   - The app will close if running
   - Files are updated atomically
   - The new version launches automatically

### Rollback

If an update causes issues:

1. **From the App**
   - Go to Help > View Update History
   - Select previous version
   - Click "Rollback"

2. **Manually**
   - Navigate to `%LOCALAPPDATA%\ProxyAssessmentTool`
   - Find backup folders (e.g., `app-2.0.0.backup-20240115120000`)
   - Delete current version folder
   - Rename backup to original

## For Developers

### Creating an Update Package

1. **Prerequisites**
   - Windows SDK with SignTool
   - Code signing certificate
   - PowerShell 5.0+

2. **Set Version**
   ```powershell
   $version = "2.0.0"
   $changelog = @"
   ## What's New in 2.0.0
   - New feature X
   - Fixed bug Y
   - Improved performance
   "@
   ```

3. **Build and Package**
   ```powershell
   .\scripts\make-update.ps1 -Version $version -Changelog $changelog
   ```

4. **With Custom Certificate**
   ```powershell
   .\scripts\make-update.ps1 -Version $version -CertThumbprint "YOUR_THUMBPRINT"
   ```

### Update Package Format

A `.paup` file is a ZIP archive containing:

```
ProxyAssessmentTool-2.0.0.paup
├── manifest.json
├── ProxyAssessmentTool.exe
├── ProxyAssessmentTool.Core.dll
├── ProxyAssessmentTool.Updater.exe
├── appsettings.json
├── config/
│   └── default.yaml
└── [other files...]
```

### Manifest Schema

```json
{
  "version": "2.0.0",
  "releaseDate": "2024-01-15T10:30:00Z",
  "minimumVersion": "1.0.0",
  "publisherThumbprint": "ABCD1234...",
  "files": [
    {
      "path": "ProxyAssessmentTool.exe",
      "sha256": "3B4A7F2C...",
      "size": 15728640,
      "executable": true
    }
  ],
  "changelog": "## What's New\n- Feature 1\n- Bug fixes"
}
```

### Security Features

1. **Code Signing**
   - All `.paup` files must be Authenticode signed
   - Publisher certificate thumbprint is verified

2. **Hash Verification**
   - Each file's SHA-256 hash is verified
   - Tampering is detected and blocked

3. **Atomic Installation**
   - Updates use versioned directories
   - Rollback is always possible
   - No partial updates

4. **Certificate Validation**
   - Full chain validation
   - Revocation checking
   - Expiration checking

### Testing Updates

1. **Create Test Package**
   ```powershell
   # Use test certificate
   .\scripts\make-update.ps1 -Version "2.0.0-beta1" -CertThumbprint "TEST_CERT"
   ```

2. **Verify Package**
   ```powershell
   .\scripts\verify-update.ps1 -PackagePath "update.paup" -ExpectedThumbprint "TEST_CERT"
   ```

3. **Test Scenarios**
   - Clean installation
   - Update over existing version
   - Rollback after update
   - Corrupted package handling
   - Running app during update

### File Association

The installer registers `.paup` files with:
- **Handler**: ProxyAssessmentTool.Updater.exe
- **Icon**: Update package icon
- **Action**: Open (launches updater)

### Command Line Usage

```bash
# Direct updater invocation
ProxyAssessmentTool.Updater.exe "C:\Updates\ProxyAssessmentTool-2.0.0.paup"

# From main app
ProxyAssessmentTool.exe --update "C:\Updates\ProxyAssessmentTool-2.0.0.paup"
```

## Troubleshooting

### "Invalid Signature" Error
- Ensure certificate hasn't expired
- Check certificate is trusted
- Verify thumbprint matches

### "Hash Mismatch" Error
- Package may be corrupted during download
- Regenerate the package
- Check antivirus interference

### "Access Denied" During Update
- Ensure app is not running
- Check file permissions
- Run updater as Administrator

### Update History Location
```
%LOCALAPPDATA%\ProxyAssessmentTool\UpdateHistory.json
```

## Best Practices

1. **Version Numbering**
   - Use semantic versioning (X.Y.Z)
   - Increment appropriately
   - Tag releases in source control

2. **Changelog**
   - Keep user-friendly
   - Highlight important changes
   - Include breaking changes warning

3. **Testing**
   - Test on clean system
   - Test upgrade scenarios
   - Verify rollback works

4. **Distribution**
   - Use secure channels
   - Provide hash for verification
   - Keep old versions available