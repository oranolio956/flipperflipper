"""
Automated Backup System
Creates regular backups of database and config
"""

import os
import shutil
import gzip
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class BackupManager:
    """Automated backup system for critical files"""
    
    def __init__(self, backup_dir: str = 'backups'):
        """
        Initialize backup manager
        
        Args:
            backup_dir: Directory to store backups
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Set restrictive permissions
        os.chmod(self.backup_dir, 0o700)
    
    def create_backup(self, file_path: str, compress: bool = True) -> Optional[str]:
        """
        Create backup of a file
        
        Args:
            file_path: Path to file to backup
            compress: Whether to gzip compress
            
        Returns:
            Path to backup file or None if failed
        """
        if not os.path.exists(file_path):
            logger.warning(f"⚠️  File not found for backup: {file_path}")
            return None
        
        try:
            # Generate backup filename with timestamp
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            filename = Path(file_path).name
            backup_name = f"{filename}.{timestamp}"
            
            if compress:
                backup_name += '.gz'
                backup_path = self.backup_dir / backup_name
                
                # Compress and save
                with open(file_path, 'rb') as f_in:
                    with gzip.open(backup_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                backup_path = self.backup_dir / backup_name
                shutil.copy2(file_path, backup_path)
            
            logger.info(f"💾 Backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"❌ Backup failed for {file_path}: {e}")
            return None
    
    def backup_database(self) -> Optional[str]:
        """Backup the database file"""
        return self.create_backup('userbot_data.json', compress=True)
    
    def backup_config(self) -> Optional[str]:
        """Backup the config file"""
        return self.create_backup('config.json', compress=True)
    
    def backup_session(self) -> Optional[str]:
        """Backup the session file (encrypted!)"""
        session_files = [
            'userbot_session.session',
            'userbot_session.session-journal'
        ]
        
        backups = []
        for session_file in session_files:
            if os.path.exists(session_file):
                backup = self.create_backup(session_file, compress=False)
                if backup:
                    backups.append(backup)
        
        return backups
    
    def backup_all(self) -> dict:
        """Backup all critical files"""
        logger.info("📦 Starting full backup...")
        
        results = {
            'database': self.backup_database(),
            'config': self.backup_config(),
            'session': self.backup_session(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"✅ Backup complete: {success_count} files backed up")
        
        return results
    
    def restore_backup(self, backup_path: str, restore_to: str) -> bool:
        """
        Restore from backup
        
        Args:
            backup_path: Path to backup file
            restore_to: Path to restore to
            
        Returns:
            True if successful
        """
        try:
            if backup_path.endswith('.gz'):
                # Decompress
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(restore_to, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                shutil.copy2(backup_path, restore_to)
            
            logger.info(f"✅ Restored from backup: {backup_path} -> {restore_to}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            return False
    
    def list_backups(self, file_pattern: str = None) -> list:
        """
        List available backups
        
        Args:
            file_pattern: Filter by filename pattern
            
        Returns:
            List of backup files with metadata
        """
        backups = []
        
        for backup_file in sorted(self.backup_dir.iterdir(), reverse=True):
            if file_pattern and file_pattern not in backup_file.name:
                continue
            
            stat = backup_file.stat()
            backups.append({
                'path': str(backup_file),
                'name': backup_file.name,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc)
            })
        
        return backups
    
    def cleanup_old_backups(self, keep_count: int = 10):
        """
        Remove old backups, keeping only the most recent
        
        Args:
            keep_count: Number of backups to keep per file type
        """
        # Group backups by base filename
        backup_groups = {}
        
        for backup_file in self.backup_dir.iterdir():
            # Extract base filename (before timestamp)
            base_name = backup_file.name.split('.')[0]
            
            if base_name not in backup_groups:
                backup_groups[base_name] = []
            
            backup_groups[base_name].append(backup_file)
        
        # Keep only newest in each group
        removed_count = 0
        for base_name, backups in backup_groups.items():
            # Sort by modification time (newest first)
            sorted_backups = sorted(
                backups,
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Remove old ones
            for old_backup in sorted_backups[keep_count:]:
                try:
                    old_backup.unlink()
                    removed_count += 1
                    logger.debug(f"🗑️  Removed old backup: {old_backup.name}")
                except Exception as e:
                    logger.error(f"Error removing backup: {e}")
        
        if removed_count > 0:
            logger.info(f"🧹 Cleaned up {removed_count} old backups")
    
    def get_backup_stats(self) -> dict:
        """Get backup statistics"""
        backups = list(self.backup_dir.iterdir())
        
        total_size = sum(b.stat().st_size for b in backups)
        
        return {
            'count': len(backups),
            'total_size_mb': total_size / (1024 * 1024),
            'oldest': min((b.stat().st_mtime for b in backups), default=0),
            'newest': max((b.stat().st_mtime for b in backups), default=0)
        }


async def automated_backup_task(backup_manager: BackupManager):
    """Background task for automated backups"""
    while True:
        try:
            # Backup every hour
            await asyncio.sleep(3600)
            
            logger.info("🕐 Starting automated backup...")
            results = backup_manager.backup_all()
            
            # Cleanup old backups
            backup_manager.cleanup_old_backups(keep_count=24)  # Keep last 24 hours
            
            logger.info("✅ Automated backup complete")
            
        except Exception as e:
            logger.error(f"❌ Automated backup failed: {e}")
