/**
 * Automated Backup System
 * Handles scheduled backups with cloud sync capabilities
 */

import { BackupManager } from './backup';
import { db } from '../../../extension/lib/db';

export interface BackupSchedule {
  enabled: boolean;
  frequency: 'hourly' | 'daily' | 'weekly' | 'manual';
  time?: string; // For daily backups (HH:MM format)
  dayOfWeek?: number; // For weekly backups (0-6, Sunday-Saturday)
  lastBackup?: Date;
  nextBackup?: Date;
  retentionDays: number;
  cloudSync: boolean;
  encryptionEnabled: boolean;
}

export interface BackupStatus {
  inProgress: boolean;
  lastSuccess?: Date;
  lastError?: string;
  totalBackups: number;
  storageUsed: number; // bytes
  cloudSyncStatus?: 'synced' | 'pending' | 'error';
}

export interface BackupMetadata {
  id: string;
  timestamp: Date;
  version: string;
  size: number;
  checksum: string;
  encrypted: boolean;
  cloudUrl?: string;
  autoBackup: boolean;
  description?: string;
}

export class AutoBackupManager {
  private backupManager: BackupManager;
  private schedule: BackupSchedule;
  private status: BackupStatus;
  private intervalId?: number;
  private readonly BACKUP_KEY = 'autoBackupConfig';
  private readonly STATUS_KEY = 'backupStatus';
  private readonly METADATA_KEY = 'backupMetadata';

  constructor() {
    this.backupManager = new BackupManager();
    this.schedule = this.getDefaultSchedule();
    this.status = {
      inProgress: false,
      totalBackups: 0,
      storageUsed: 0
    };
  }

  /**
   * Initialize auto backup system
   */
  async initialize(): Promise<void> {
    // Load saved configuration
    await this.loadConfiguration();
    
    // Start scheduler if enabled
    if (this.schedule.enabled) {
      this.startScheduler();
    }

    // Clean old backups
    await this.cleanOldBackups();
  }

  /**
   * Configure backup schedule
   */
  async configureSchedule(schedule: Partial<BackupSchedule>): Promise<void> {
    this.schedule = { ...this.schedule, ...schedule };
    await this.saveConfiguration();

    // Restart scheduler if needed
    if (this.intervalId) {
      this.stopScheduler();
    }
    if (this.schedule.enabled) {
      this.startScheduler();
    }
  }

  /**
   * Perform manual backup
   */
  async performBackup(description?: string): Promise<BackupMetadata> {
    if (this.status.inProgress) {
      throw new Error('Backup already in progress');
    }

    this.status.inProgress = true;
    const startTime = Date.now();

    try {
      // Create backup
      const backupData = await this.backupManager.createBackup();
      
      // Generate metadata
      const metadata: BackupMetadata = {
        id: `backup_${Date.now()}`,
        timestamp: new Date(),
        version: chrome.runtime.getManifest().version,
        size: new Blob([JSON.stringify(backupData)]).size,
        checksum: await this.generateChecksum(backupData),
        encrypted: this.schedule.encryptionEnabled,
        autoBackup: false,
        description
      };

      // Encrypt if enabled
      let dataToStore = backupData;
      if (this.schedule.encryptionEnabled) {
        dataToStore = await this.encryptBackup(backupData);
      }

      // Store locally
      await this.storeBackup(metadata.id, dataToStore, metadata);

      // Cloud sync if enabled
      if (this.schedule.cloudSync) {
        try {
          metadata.cloudUrl = await this.syncToCloud(metadata.id, dataToStore);
          this.status.cloudSyncStatus = 'synced';
        } catch (error) {
          console.error('Cloud sync failed:', error);
          this.status.cloudSyncStatus = 'error';
          this.status.lastError = `Cloud sync failed: ${error}`;
        }
      }

      // Update status
      this.status.lastSuccess = new Date();
      this.status.totalBackups++;
      this.status.storageUsed += metadata.size;
      this.status.inProgress = false;
      await this.saveStatus();

      // Clean old backups
      await this.cleanOldBackups();

      // Notify success
      chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('icons/icon-48.png'),
        title: 'Backup Complete',
        message: `Data backed up successfully (${this.formatBytes(metadata.size)})`
      });

      return metadata;
    } catch (error) {
      this.status.inProgress = false;
      this.status.lastError = error instanceof Error ? error.message : 'Unknown error';
      await this.saveStatus();

      // Notify error
      chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('icons/icon-48.png'),
        title: 'Backup Failed',
        message: this.status.lastError
      });

      throw error;
    }
  }

  /**
   * Restore from backup
   */
  async restoreBackup(backupId: string): Promise<void> {
    try {
      // Get backup data
      const { backups = {} } = await chrome.storage.local.get('backups');
      const backupEntry = backups[backupId];
      
      if (!backupEntry) {
        throw new Error('Backup not found');
      }

      let backupData = backupEntry.data;

      // Decrypt if needed
      if (backupEntry.metadata.encrypted) {
        backupData = await this.decryptBackup(backupData);
      }

      // Verify checksum
      const checksum = await this.generateChecksum(backupData);
      if (checksum !== backupEntry.metadata.checksum) {
        throw new Error('Backup integrity check failed');
      }

      // Restore data
      await this.backupManager.restoreBackup(backupData);

      // Notify success
      chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('icons/icon-48.png'),
        title: 'Restore Complete',
        message: 'Data restored successfully'
      });
    } catch (error) {
      chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('icons/icon-48.png'),
        title: 'Restore Failed',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  }

  /**
   * List available backups
   */
  async listBackups(): Promise<BackupMetadata[]> {
    const { backupMetadata = {} } = await chrome.storage.local.get(this.METADATA_KEY);
    return Object.values(backupMetadata).sort((a: any, b: any) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }

  /**
   * Delete a backup
   */
  async deleteBackup(backupId: string): Promise<void> {
    const { backups = {}, backupMetadata = {} } = await chrome.storage.local.get([
      'backups',
      this.METADATA_KEY
    ]);

    delete backups[backupId];
    delete backupMetadata[backupId];

    await chrome.storage.local.set({ 
      backups,
      [this.METADATA_KEY]: backupMetadata 
    });

    // Update storage used
    await this.updateStorageUsed();
  }

  /**
   * Export backup to file
   */
  async exportBackup(backupId: string): Promise<Blob> {
    const { backups = {} } = await chrome.storage.local.get('backups');
    const backupEntry = backups[backupId];
    
    if (!backupEntry) {
      throw new Error('Backup not found');
    }

    const exportData = {
      metadata: backupEntry.metadata,
      data: backupEntry.data,
      exported: new Date().toISOString()
    };

    return new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
  }

  /**
   * Import backup from file
   */
  async importBackup(file: File): Promise<BackupMetadata> {
    const text = await file.text();
    const importData = JSON.parse(text);

    // Validate import data
    if (!importData.metadata || !importData.data) {
      throw new Error('Invalid backup file format');
    }

    // Generate new ID for imported backup
    const metadata: BackupMetadata = {
      ...importData.metadata,
      id: `import_${Date.now()}`,
      timestamp: new Date(),
      description: `Imported from ${file.name}`
    };

    // Store the backup
    await this.storeBackup(metadata.id, importData.data, metadata);

    return metadata;
  }

  /**
   * Private helper methods
   */
  private startScheduler(): void {
    // Calculate next backup time
    const nextBackupTime = this.calculateNextBackupTime();
    this.schedule.nextBackup = nextBackupTime;

    // Set up interval based on frequency
    const checkInterval = this.getCheckInterval();
    
    this.intervalId = window.setInterval(async () => {
      const now = new Date();
      if (this.schedule.nextBackup && now >= this.schedule.nextBackup) {
        await this.performScheduledBackup();
      }
    }, checkInterval);
  }

  private stopScheduler(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = undefined;
    }
  }

  private async performScheduledBackup(): Promise<void> {
    try {
      const metadata = await this.performBackup('Scheduled backup');
      metadata.autoBackup = true;
      
      // Update last backup time
      this.schedule.lastBackup = new Date();
      this.schedule.nextBackup = this.calculateNextBackupTime();
      await this.saveConfiguration();
    } catch (error) {
      console.error('Scheduled backup failed:', error);
    }
  }

  private calculateNextBackupTime(): Date {
    const now = new Date();
    let next = new Date(now);

    switch (this.schedule.frequency) {
      case 'hourly':
        next.setHours(next.getHours() + 1);
        next.setMinutes(0);
        next.setSeconds(0);
        break;
        
      case 'daily':
        next.setDate(next.getDate() + 1);
        if (this.schedule.time) {
          const [hours, minutes] = this.schedule.time.split(':').map(Number);
          next.setHours(hours);
          next.setMinutes(minutes);
        } else {
          next.setHours(3); // Default to 3 AM
          next.setMinutes(0);
        }
        next.setSeconds(0);
        break;
        
      case 'weekly':
        const daysUntilNext = (this.schedule.dayOfWeek || 0) - now.getDay();
        next.setDate(next.getDate() + (daysUntilNext <= 0 ? daysUntilNext + 7 : daysUntilNext));
        if (this.schedule.time) {
          const [hours, minutes] = this.schedule.time.split(':').map(Number);
          next.setHours(hours);
          next.setMinutes(minutes);
        } else {
          next.setHours(3);
          next.setMinutes(0);
        }
        next.setSeconds(0);
        break;
    }

    return next;
  }

  private getCheckInterval(): number {
    switch (this.schedule.frequency) {
      case 'hourly':
        return 60 * 1000; // Check every minute
      case 'daily':
      case 'weekly':
        return 5 * 60 * 1000; // Check every 5 minutes
      default:
        return 60 * 60 * 1000; // Check every hour
    }
  }

  private async cleanOldBackups(): Promise<void> {
    const backups = await this.listBackups();
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - this.schedule.retentionDays);

    for (const backup of backups) {
      if (new Date(backup.timestamp) < cutoffDate && backup.autoBackup) {
        await this.deleteBackup(backup.id);
      }
    }
  }

  private async storeBackup(
    id: string, 
    data: any, 
    metadata: BackupMetadata
  ): Promise<void> {
    const { backups = {}, backupMetadata = {} } = await chrome.storage.local.get([
      'backups',
      this.METADATA_KEY
    ]);

    backups[id] = { data, metadata };
    backupMetadata[id] = metadata;

    await chrome.storage.local.set({
      backups,
      [this.METADATA_KEY]: backupMetadata
    });
  }

  private async generateChecksum(data: any): Promise<string> {
    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(JSON.stringify(data));
    const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  private async encryptBackup(data: any): Promise<any> {
    // Simplified encryption - in production, use proper encryption
    const key = await this.getEncryptionKey();
    const encrypted = btoa(JSON.stringify(data));
    return { encrypted, iv: Date.now().toString() };
  }

  private async decryptBackup(encryptedData: any): Promise<any> {
    // Simplified decryption
    const decrypted = atob(encryptedData.encrypted);
    return JSON.parse(decrypted);
  }

  private async getEncryptionKey(): Promise<string> {
    const { encryptionKey } = await chrome.storage.local.get('encryptionKey');
    if (!encryptionKey) {
      const newKey = crypto.randomUUID();
      await chrome.storage.local.set({ encryptionKey: newKey });
      return newKey;
    }
    return encryptionKey;
  }

  private async syncToCloud(backupId: string, data: any): Promise<string> {
    // Placeholder for cloud sync
    // In production, integrate with Google Drive, Dropbox, etc.
    console.log('Cloud sync would upload backup:', backupId);
    return `cloud://backups/${backupId}`;
  }

  private async updateStorageUsed(): Promise<void> {
    const backups = await this.listBackups();
    this.status.storageUsed = backups.reduce((total, backup) => total + backup.size, 0);
    await this.saveStatus();
  }

  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  private getDefaultSchedule(): BackupSchedule {
    return {
      enabled: true,
      frequency: 'daily',
      time: '03:00',
      retentionDays: 30,
      cloudSync: false,
      encryptionEnabled: true
    };
  }

  private async loadConfiguration(): Promise<void> {
    const { 
      [this.BACKUP_KEY]: savedSchedule,
      [this.STATUS_KEY]: savedStatus 
    } = await chrome.storage.local.get([this.BACKUP_KEY, this.STATUS_KEY]);

    if (savedSchedule) {
      this.schedule = {
        ...this.schedule,
        ...savedSchedule,
        lastBackup: savedSchedule.lastBackup ? new Date(savedSchedule.lastBackup) : undefined,
        nextBackup: savedSchedule.nextBackup ? new Date(savedSchedule.nextBackup) : undefined
      };
    }

    if (savedStatus) {
      this.status = {
        ...this.status,
        ...savedStatus,
        lastSuccess: savedStatus.lastSuccess ? new Date(savedStatus.lastSuccess) : undefined
      };
    }
  }

  private async saveConfiguration(): Promise<void> {
    await chrome.storage.local.set({
      [this.BACKUP_KEY]: {
        ...this.schedule,
        lastBackup: this.schedule.lastBackup?.toISOString(),
        nextBackup: this.schedule.nextBackup?.toISOString()
      }
    });
  }

  private async saveStatus(): Promise<void> {
    await chrome.storage.local.set({
      [this.STATUS_KEY]: {
        ...this.status,
        lastSuccess: this.status.lastSuccess?.toISOString()
      }
    });
  }

  /**
   * Get current configuration and status
   */
  getConfiguration(): { schedule: BackupSchedule; status: BackupStatus } {
    return {
      schedule: { ...this.schedule },
      status: { ...this.status }
    };
  }
}

// Export singleton instance
export const autoBackupManager = new AutoBackupManager();