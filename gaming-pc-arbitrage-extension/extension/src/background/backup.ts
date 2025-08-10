/**
 * Background Backup Handler
 * Automated backup with retention management
 */

import { db } from '@/lib/db';
import { getSettings } from '@/lib/settings';
import { exportAll } from '@arbitrage/data/backup';

const BACKUP_ALARM_NAME = 'auto-backup';

/**
 * Initialize backup alarms
 */
export async function initializeBackup(): Promise<void> {
  const settings = await getSettings();
  const backupConfig = settings.backup;
  
  if (backupConfig?.enabled && backupConfig?.frequency && backupConfig?.passphrase) {
    // Convert frequency to minutes
    const minutes = backupConfig.frequency === 'weekly' ? 7 * 24 * 60 : 30 * 24 * 60;
    
    await chrome.alarms.create(BACKUP_ALARM_NAME, {
      periodInMinutes: minutes,
      delayInMinutes: 1, // Start soon
    });
    
    console.log(`Backup scheduled every ${backupConfig.frequency}`);
  } else {
    // Clear alarm if disabled
    await chrome.alarms.clear(BACKUP_ALARM_NAME);
    console.log('Backup disabled');
  }
}

/**
 * Handle backup alarm
 */
export async function handleBackupAlarm(): Promise<void> {
  console.log('Running scheduled backup');
  
  try {
    const settings = await getSettings();
    const backupConfig = settings.backup;
    
    if (!backupConfig?.enabled || !backupConfig?.passphrase) {
      console.log('Backup not configured');
      return;
    }
    
    // Create backup
    const blob = await exportAll(db, {
      passphrase: backupConfig.passphrase,
      includeLogs: false,
    });
    
    // Generate filename
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `arbitrage-backup-${timestamp}.gpca.backup`;
    
    // Create blob URL and download
    const url = URL.createObjectURL(blob);
    
    try {
      await chrome.downloads.download({
        url,
        filename,
        saveAs: false, // Auto-save to downloads
      });
      
      console.log(`Backup saved: ${filename}`);
      
      // Log event
      await db.events.add({
        timestamp: Date.now(),
        category: 'system',
        name: 'backup_created',
        data: { filename, auto: true },
      });
      
      // Clean up old backups
      await cleanupOldBackups(backupConfig.retention || 5);
      
    } finally {
      // Clean up blob URL
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
  } catch (error) {
    console.error('Backup failed:', error);
    
    // Log error
    await db.events.add({
      timestamp: Date.now(),
      category: 'error',
      name: 'backup_failed',
      data: { error: String(error) },
    });
  }
}

/**
 * Manually trigger backup
 */
export async function triggerBackup(): Promise<string> {
  const settings = await getSettings();
  const backupConfig = settings.backup;
  
  if (!backupConfig?.passphrase) {
    throw new Error('Backup passphrase not configured');
  }
  
  // Create backup
  const blob = await exportAll(db, {
    passphrase: backupConfig.passphrase,
    includeLogs: true, // Include all data for manual backup
  });
  
  // Generate filename
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `arbitrage-backup-manual-${timestamp}.gpca.backup`;
  
  // Create blob URL and download
  const url = URL.createObjectURL(blob);
  
  try {
    await chrome.downloads.download({
      url,
      filename,
      saveAs: true, // Let user choose location
    });
    
    // Log event
    await db.events.add({
      timestamp: Date.now(),
      category: 'system',
      name: 'backup_created',
      data: { filename, auto: false },
    });
    
    return filename;
  } finally {
    // Clean up blob URL
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}

/**
 * Clean up old backup files
 */
async function cleanupOldBackups(retention: number): Promise<void> {
  try {
    // Get download history
    const downloads = await chrome.downloads.search({
      query: ['arbitrage-backup-*.gpca.backup'],
      orderBy: ['-startTime'],
      limit: 100,
    });
    
    // Filter to our backups
    const backups = downloads.filter(d => 
      d.filename?.includes('arbitrage-backup-') && 
      d.filename?.endsWith('.gpca.backup') &&
      d.state === 'complete'
    );
    
    // Remove old backups beyond retention
    if (backups.length > retention) {
      const toRemove = backups.slice(retention);
      
      for (const backup of toRemove) {
        try {
          await chrome.downloads.removeFile(backup.id);
          console.log(`Removed old backup: ${backup.filename}`);
        } catch (error) {
          console.error(`Failed to remove backup ${backup.filename}:`, error);
        }
      }
    }
  } catch (error) {
    console.error('Cleanup failed:', error);
  }
}