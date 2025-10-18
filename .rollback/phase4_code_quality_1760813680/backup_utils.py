#!/usr/bin/env python3
"""
Backup and restore utilities for Stitch configuration
"""
import os
import json
import zipfile
import hashlib
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from config import Config
import logging

logger = logging.getLogger(__name__)

class BackupManager:
    """Handle backup and restore of configuration files"""
    
    BACKUP_VERSION = "1.0"
    SUPPORTED_VERSIONS = ["1.0"]
    
    @classmethod
    def create_backup(cls):
        """Create a backup ZIP file of all configuration files"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
                backup_path = temp_file.name
            
            # Create metadata
            metadata = {
                'version': cls.BACKUP_VERSION,
                'created_at': datetime.now().isoformat(),
                'app_version': Config.APP_VERSION,
                'files': []
            }
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                # Backup .ini files from Application/Stitch_Vars
                stitch_vars_dir = Config.APPLICATION_DIR / 'Stitch_Vars'
                if stitch_vars_dir.exists():
                    for ini_file in stitch_vars_dir.glob('*.ini'):
                        if ini_file.exists():
                            arcname = f'Stitch_Vars/{ini_file.name}'
                            backup_zip.write(ini_file, arcname)
                            
                            # Calculate checksum
                            with open(ini_file, 'rb') as f:
                                file_hash = hashlib.sha256(f.read()).hexdigest()
                            
                            metadata['files'].append({
                                'name': arcname,
                                'size': ini_file.stat().st_size,
                                'checksum': file_hash
                            })
                
                # Backup API keys if they exist
                if Config.API_KEYS_FILE.exists():
                    arcname = 'api_keys.json'
                    backup_zip.write(Config.API_KEYS_FILE, arcname)
                    
                    with open(Config.API_KEYS_FILE, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    
                    metadata['files'].append({
                        'name': arcname,
                        'size': Config.API_KEYS_FILE.stat().st_size,
                        'checksum': file_hash
                    })
                
                # Backup secret key if it exists
                if Config.SECRET_KEY_FILE.exists():
                    arcname = 'secret_key'
                    backup_zip.write(Config.SECRET_KEY_FILE, arcname)
                    
                    with open(Config.SECRET_KEY_FILE, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    
                    metadata['files'].append({
                        'name': arcname,
                        'size': Config.SECRET_KEY_FILE.stat().st_size,
                        'checksum': file_hash
                    })
                
                # Backup environment configuration (as documentation)
                env_config = {
                    'note': 'These are the current environment settings. Set them in your environment before restoring.',
                    'settings': {
                        'STITCH_ADMIN_USER': Config.ADMIN_USER or '<not set>',
                        'STITCH_ADMIN_PASSWORD': '<redacted>' if Config.ADMIN_PASSWORD else '<not set>',
                        'STITCH_ENABLE_HTTPS': str(Config.ENABLE_HTTPS),
                        'STITCH_MAX_LOGIN_ATTEMPTS': str(Config.MAX_LOGIN_ATTEMPTS),
                        'STITCH_LOGIN_LOCKOUT_MINUTES': str(Config.LOGIN_LOCKOUT_MINUTES),
                        'STITCH_COMMANDS_PER_MINUTE': str(Config.COMMANDS_PER_MINUTE),
                        'STITCH_WEBSOCKET_UPDATE_INTERVAL': str(Config.WEBSOCKET_UPDATE_INTERVAL),
                        'STITCH_ENABLE_API_KEYS': str(Config.ENABLE_API_KEYS),
                        'STITCH_ENABLE_FAILED_LOGIN_ALERTS': str(Config.ENABLE_FAILED_LOGIN_ALERTS),
                    }
                }
                backup_zip.writestr('environment_config.json', json.dumps(env_config, indent=2))
                
                # Optionally backup logs
                if Config.BACKUP_INCLUDE_LOGS and Config.LOG_FILE.exists():
                    arcname = 'logs/stitch_web.log'
                    backup_zip.write(Config.LOG_FILE, arcname)
                    
                    with open(Config.LOG_FILE, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    
                    metadata['files'].append({
                        'name': arcname,
                        'size': Config.LOG_FILE.stat().st_size,
                        'checksum': file_hash
                    })
                
                # Add metadata to backup
                backup_zip.writestr('backup_metadata.json', json.dumps(metadata, indent=2))
            
            # Generate final filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            final_filename = f'stitch_backup_{timestamp}.zip'
            
            return backup_path, final_filename, metadata
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    @classmethod
    def validate_backup(cls, backup_path):
        """Validate a backup file before restoration"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as backup_zip:
                # Check for metadata
                if 'backup_metadata.json' not in backup_zip.namelist():
                    return False, "Invalid backup: missing metadata"
                
                # Load and validate metadata
                metadata_content = backup_zip.read('backup_metadata.json')
                metadata = json.loads(metadata_content)
                
                # Check version compatibility
                if metadata.get('version') not in cls.SUPPORTED_VERSIONS:
                    return False, f"Unsupported backup version: {metadata.get('version')}"
                
                # Verify file checksums
                for file_info in metadata.get('files', []):
                    file_name = file_info['name']
                    expected_checksum = file_info['checksum']
                    
                    if file_name in backup_zip.namelist():
                        file_content = backup_zip.read(file_name)
                        actual_checksum = hashlib.sha256(file_content).hexdigest()
                        
                        if actual_checksum != expected_checksum:
                            return False, f"Checksum mismatch for {file_name}"
                    else:
                        return False, f"Missing file in backup: {file_name}"
                
                return True, metadata
                
        except zipfile.BadZipFile:
            return False, "Invalid ZIP file"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @classmethod
    def restore_backup(cls, backup_path):
        """Restore configuration from a backup file"""
        try:
            # Validate backup first
            is_valid, result = cls.validate_backup(backup_path)
            if not is_valid:
                return False, result
            
            metadata = result
            
            # Create backup of current configuration
            backup_dir = Config.APPLICATION_DIR / 'backups' / 'pre_restore'
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pre_restore_dir = backup_dir / f'pre_restore_{timestamp}'
            pre_restore_dir.mkdir(exist_ok=True)
            
            # Backup current files
            files_backed_up = []
            
            # Backup current .ini files
            stitch_vars_dir = Config.APPLICATION_DIR / 'Stitch_Vars'
            if stitch_vars_dir.exists():
                for ini_file in stitch_vars_dir.glob('*.ini'):
                    if ini_file.exists():
                        backup_path_dst = pre_restore_dir / 'Stitch_Vars' / ini_file.name
                        backup_path_dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(ini_file, backup_path_dst)
                        files_backed_up.append(str(ini_file))
            
            # Backup API keys
            if Config.API_KEYS_FILE.exists():
                backup_path_dst = pre_restore_dir / 'api_keys.json'
                shutil.copy2(Config.API_KEYS_FILE, backup_path_dst)
                files_backed_up.append(str(Config.API_KEYS_FILE))
            
            # Backup secret key
            if Config.SECRET_KEY_FILE.exists():
                backup_path_dst = pre_restore_dir / 'secret_key'
                shutil.copy2(Config.SECRET_KEY_FILE, backup_path_dst)
                files_backed_up.append(str(Config.SECRET_KEY_FILE))
            
            logger.info(f"Created pre-restore backup at {pre_restore_dir}")
            
            # Extract and restore files
            restored_files = []
            
            with zipfile.ZipFile(backup_path, 'r') as backup_zip:
                for file_info in metadata['files']:
                    file_name = file_info['name']
                    
                    # Determine destination path
                    if file_name.startswith('Stitch_Vars/'):
                        dest_path = Config.APPLICATION_DIR / file_name
                    elif file_name == 'api_keys.json':
                        dest_path = Config.API_KEYS_FILE
                    elif file_name == 'secret_key':
                        dest_path = Config.SECRET_KEY_FILE
                    elif file_name.startswith('logs/'):
                        # Skip logs during restore
                        continue
                    else:
                        # Skip unknown files
                        continue
                    
                    # Create parent directories
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Extract file
                    file_content = backup_zip.read(file_name)
                    with open(dest_path, 'wb') as f:
                        f.write(file_content)
                    
                    # Set appropriate permissions
                    if file_name in ['api_keys.json', 'secret_key']:
                        try:
                            os.chmod(dest_path, 0o600)
                        except:
                            pass  # Windows doesn't support chmod
                    
                    restored_files.append(str(dest_path))
                    logger.info(f"Restored {file_name} to {dest_path}")
            
            return True, {
                'message': 'Backup restored successfully',
                'restored_files': restored_files,
                'pre_restore_backup': str(pre_restore_dir),
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False, f"Restore error: {str(e)}"
    
    @classmethod
    def list_backups(cls):
        """List available backup files"""
        backup_dir = Config.APPLICATION_DIR / 'backups'
        if not backup_dir.exists():
            return []
        
        backups = []
        for backup_file in backup_dir.glob('stitch_backup_*.zip'):
            try:
                # Get file info
                stat = backup_file.stat()
                
                # Try to read metadata
                metadata = None
                try:
                    with zipfile.ZipFile(backup_file, 'r') as zf:
                        if 'backup_metadata.json' in zf.namelist():
                            metadata = json.loads(zf.read('backup_metadata.json'))
                except:
                    pass
                
                backups.append({
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'metadata': metadata
                })
            except:
                continue
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        
        return backups
    
    @classmethod
    def cleanup_old_backups(cls, keep_count=10):
        """Remove old backup files, keeping only the most recent ones"""
        backups = cls.list_backups()
        
        if len(backups) <= keep_count:
            return
        
        # Delete older backups
        for backup in backups[keep_count:]:
            try:
                os.remove(backup['path'])
                logger.info(f"Deleted old backup: {backup['filename']}")
            except Exception as e:
                logger.error(f"Failed to delete backup {backup['filename']}: {e}")