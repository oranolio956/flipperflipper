#!/bin/bash
#
# Enterprise Backup System
# Automated backup script for Oranolio RAT Elite C2 Framework
#

set -e  # Exit on error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/oranolio}"
APP_DIR="${APP_DIR:-/var/www/flipperflipper}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="oranolio_backup_${DATE}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

log "Starting backup: $BACKUP_NAME"

# Create temporary backup directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

log "Created temporary directory: $TEMP_DIR"

# Backup databases
log "Backing up databases..."
mkdir -p "$TEMP_DIR/databases"

if [ -d "$APP_DIR/Application" ]; then
    cp -r "$APP_DIR/Application"/*.db "$TEMP_DIR/databases/" 2>/dev/null || warning "No databases in Application/"
fi

if [ -d "$APP_DIR/data" ]; then
    cp -r "$APP_DIR/data"/*.db "$TEMP_DIR/databases/" 2>/dev/null || warning "No databases in data/"
fi

# Backup configuration files
log "Backing up configuration..."
mkdir -p "$TEMP_DIR/config"

for file in .env config.yaml config.py production_config.py; do
    if [ -f "$APP_DIR/$file" ]; then
        cp "$APP_DIR/$file" "$TEMP_DIR/config/"
    fi
done

# Backup SSL certificates
log "Backing up SSL certificates..."
if [ -d "$APP_DIR/certs" ]; then
    mkdir -p "$TEMP_DIR/certs"
    cp -r "$APP_DIR/certs"/* "$TEMP_DIR/certs/" 2>/dev/null || warning "No certificates found"
fi

# Backup logs (last 7 days only)
log "Backing up recent logs..."
if [ -d "$APP_DIR/logs" ]; then
    mkdir -p "$TEMP_DIR/logs"
    find "$APP_DIR/logs" -name "*.log" -mtime -7 -exec cp {} "$TEMP_DIR/logs/" \; 2>/dev/null || warning "No recent logs found"
fi

# Backup uploads (if any)
log "Backing up uploads..."
if [ -d "$APP_DIR/uploads" ]; then
    mkdir -p "$TEMP_DIR/uploads"
    cp -r "$APP_DIR/uploads"/* "$TEMP_DIR/uploads/" 2>/dev/null || warning "No uploads found"
fi

# Create backup metadata
log "Creating backup metadata..."
cat > "$TEMP_DIR/backup_info.txt" << EOF
Backup Information
==================
Backup Name: $BACKUP_NAME
Backup Date: $(date)
Hostname: $(hostname)
App Directory: $APP_DIR
Backup Directory: $BACKUP_DIR

Contents:
- Databases: $(find "$TEMP_DIR/databases" -type f 2>/dev/null | wc -l) files
- Configuration: $(find "$TEMP_DIR/config" -type f 2>/dev/null | wc -l) files
- Certificates: $(find "$TEMP_DIR/certs" -type f 2>/dev/null | wc -l) files
- Logs: $(find "$TEMP_DIR/logs" -type f 2>/dev/null | wc -l) files
- Uploads: $(find "$TEMP_DIR/uploads" -type f 2>/dev/null | wc -l) files

System Information:
- OS: $(uname -s)
- Kernel: $(uname -r)
- Python: $(python3 --version 2>&1)
EOF

# Create compressed archive
log "Creating compressed archive..."
cd "$TEMP_DIR"
tar -czf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" .

# Calculate checksum
log "Calculating checksum..."
cd "$BACKUP_DIR"
sha256sum "${BACKUP_NAME}.tar.gz" > "${BACKUP_NAME}.sha256"

# Get backup size
BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)

log "Backup created successfully: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})"

# Clean up old backups
log "Cleaning up old backups (older than $RETENTION_DAYS days)..."
DELETED=$(find "$BACKUP_DIR" -name "oranolio_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
find "$BACKUP_DIR" -name "oranolio_backup_*.sha256" -mtime +$RETENTION_DAYS -delete

if [ $DELETED -gt 0 ]; then
    log "Deleted $DELETED old backup(s)"
else
    log "No old backups to delete"
fi

# List current backups
log "Current backups:"
ls -lh "$BACKUP_DIR"/oranolio_backup_*.tar.gz 2>/dev/null | tail -5 || warning "No backups found"

# Send notification (if configured)
if [ -n "$BACKUP_NOTIFICATION_EMAIL" ]; then
    log "Sending notification email..."
    echo "Backup completed successfully: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})" | \
        mail -s "Oranolio Backup Success" "$BACKUP_NOTIFICATION_EMAIL" || warning "Failed to send email"
fi

log "Backup completed successfully!"
exit 0
