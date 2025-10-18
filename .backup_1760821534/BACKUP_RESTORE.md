# Backup & Restore Guide for Stitch RAT

## What to Backup

### Critical Data
1. **Connection History**: `Application/Stitch_Files/hist.ini`
2. **Downloaded Files**: `Application/Stitch_Files/`
3. **SSL Certificates**: `ssl_certificates/` (if using custom certs)
4. **Environment Secrets**: Document your Replit Secrets settings

### Configuration Files
- `.env` (if used)
- `replit.md` (project documentation)
- Custom SSL certificates

## Backup Methods

### Method 1: Manual Backup (Recommended)
```bash
# Create backup directory with timestamp
BACKUP_DIR="stitch_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup connection history
cp Application/Stitch_Files/hist.ini "$BACKUP_DIR/"

# Backup downloaded files
cp -r Application/Stitch_Files/*.* "$BACKUP_DIR/files/" 2>/dev/null || true

# Backup SSL certificates (if exists)
cp -r ssl_certificates "$BACKUP_DIR/" 2>/dev/null || true

# Backup documentation
cp replit.md "$BACKUP_DIR/"

# Create archive
tar -czf "${BACKUP_DIR}.tar.gz" "$BACKUP_DIR"
echo "✅ Backup created: ${BACKUP_DIR}.tar.gz"
```

### Method 2: Git-based Backup
```bash
# Commit critical config changes
git add Application/Stitch_Files/hist.ini replit.md
git commit -m "Backup: $(date +%Y-%m-%d)"

# Tag important milestones
git tag -a "backup-$(date +%Y%m%d)" -m "Backup checkpoint"
```

### Method 3: Replit Automatic Checkpoints
Replit automatically creates checkpoints during your session. Use the Rollback feature to restore to previous states:
1. Click "History" tab in Replit
2. Select a checkpoint
3. Click "Rollback" to restore

## Restore Process

### Restore from Manual Backup
```bash
# Extract backup archive
tar -xzf stitch_backup_YYYYMMDD_HHMMSS.tar.gz

# Restore connection history
cp stitch_backup_*/hist.ini Application/Stitch_Files/

# Restore files
cp -r stitch_backup_*/files/* Application/Stitch_Files/

# Restore SSL certificates
cp -r stitch_backup_*/ssl_certificates .

# Restart the server
python3 web_app_real.py
```

### Restore Replit Secrets
If you need to restore secrets:
1. Go to Secrets tab (🔒 icon)
2. Re-add:
   - `STITCH_ADMIN_USER`
   - `STITCH_ADMIN_PASSWORD`
   - `STITCH_SECRET_KEY` (for session persistence)
3. Restart the workflow

## Best Practices

### Regular Backups
- **Daily**: If actively using in production
- **Before major changes**: Always backup before updates
- **After critical operations**: Backup after important target connections

### What NOT to Backup
- ❌ Session data (temporary)
- ❌ Debug logs (regenerated)
- ❌ Python cache (`__pycache__`)
- ❌ Temporary files

### Security Considerations
- 🔒 **Encrypt backups** if they contain sensitive connection data
- 🔒 **Store offsite** - don't keep backups only on Replit
- 🔒 **Rotate backups** - don't keep unlimited backup history
- 🔒 **Test restores** - verify backups work before you need them

## Automated Backup Script

Create `backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="backups/stitch_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup critical files
cp Application/Stitch_Files/hist.ini "$BACKUP_DIR/" 2>/dev/null || true
cp replit.md "$BACKUP_DIR/" 2>/dev/null || true

# Create compressed archive
tar -czf "${BACKUP_DIR}.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

# Keep only last 10 backups
cd backups && ls -t stitch_*.tar.gz | tail -n +11 | xargs rm -f 2>/dev/null || true

echo "✅ Backup complete: ${BACKUP_DIR}.tar.gz"
```

Make it executable: `chmod +x backup.sh`

Run it: `./backup.sh`

## Disaster Recovery

If everything breaks:
1. Use Replit's Rollback feature (History tab)
2. Restore from your latest manual backup
3. Reinstall dependencies: `pip install -r requirements.txt`
4. Restart workflows

## Cloud Backup Options
Consider backing up to:
- **GitHub**: Version control for code and config
- **External storage**: Download backups to your local machine
- **Cloud storage**: S3, Google Drive, Dropbox

## Questions?
See `HOW_TO_LOGIN.md` for credential recovery or contact support.
