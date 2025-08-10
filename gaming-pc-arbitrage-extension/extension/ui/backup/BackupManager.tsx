/**
 * Backup Manager Component
 * UI for managing automated backups and restore operations
 */

import React, { useState, useEffect } from 'react';
import { autoBackupManager } from '@arbitrage/core';
import type { BackupSchedule, BackupStatus, BackupMetadata } from '@arbitrage/core';

export const BackupManagerUI: React.FC = () => {
  const [schedule, setSchedule] = useState<BackupSchedule | null>(null);
  const [status, setStatus] = useState<BackupStatus | null>(null);
  const [backups, setBackups] = useState<BackupMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'schedule' | 'backups'>('schedule');
  const [selectedBackup, setSelectedBackup] = useState<BackupMetadata | null>(null);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      await autoBackupManager.initialize();
      const config = autoBackupManager.getConfiguration();
      setSchedule(config.schedule);
      setStatus(config.status);
      
      const backupList = await autoBackupManager.listBackups();
      setBackups(backupList);
      
      setLoading(false);
    } catch (error) {
      console.error('Failed to load backup data:', error);
      setLoading(false);
    }
  };

  const handleScheduleUpdate = async (updates: Partial<BackupSchedule>) => {
    try {
      await autoBackupManager.configureSchedule(updates);
      await loadData();
      
      chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('icons/icon-48.png'),
        title: 'Backup Settings Updated',
        message: 'Your backup schedule has been updated'
      });
    } catch (error) {
      console.error('Failed to update schedule:', error);
    }
  };

  const handleManualBackup = async () => {
    try {
      await autoBackupManager.performBackup('Manual backup');
      await loadData();
    } catch (error) {
      console.error('Manual backup failed:', error);
    }
  };

  const handleRestore = async (backupId: string) => {
    if (!confirm('Are you sure you want to restore from this backup? This will overwrite current data.')) {
      return;
    }

    try {
      await autoBackupManager.restoreBackup(backupId);
      await loadData();
    } catch (error) {
      console.error('Restore failed:', error);
    }
  };

  const handleExport = async (backupId: string) => {
    try {
      const blob = await autoBackupManager.exportBackup(backupId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `backup_${backupId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      await autoBackupManager.importBackup(file);
      await loadData();
    } catch (error) {
      console.error('Import failed:', error);
    }
  };

  const handleDelete = async (backupId: string) => {
    if (!confirm('Are you sure you want to delete this backup?')) {
      return;
    }

    try {
      await autoBackupManager.deleteBackup(backupId);
      await loadData();
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  if (loading || !schedule || !status) {
    return (
      <div className="backup-manager loading">
        <div className="spinner"></div>
        <p>Loading backup settings...</p>
      </div>
    );
  }

  const formatDate = (date: Date | string | undefined) => {
    if (!date) return 'Never';
    const d = new Date(date);
    return d.toLocaleString();
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="backup-manager">
      <div className="header">
        <h2>Backup & Restore</h2>
        <div className="header-actions">
          <button 
            className="backup-now-btn"
            onClick={handleManualBackup}
            disabled={status.inProgress}
          >
            {status.inProgress ? 'Backing up...' : 'Backup Now'}
          </button>
        </div>
      </div>

      <div className="status-bar">
        <div className="status-item">
          <span className="label">Last Backup:</span>
          <span className="value">{formatDate(status.lastSuccess)}</span>
        </div>
        <div className="status-item">
          <span className="label">Next Backup:</span>
          <span className="value">{formatDate(schedule.nextBackup)}</span>
        </div>
        <div className="status-item">
          <span className="label">Total Backups:</span>
          <span className="value">{status.totalBackups}</span>
        </div>
        <div className="status-item">
          <span className="label">Storage Used:</span>
          <span className="value">{formatBytes(status.storageUsed)}</span>
        </div>
      </div>

      {status.lastError && (
        <div className="error-message">
          <span>⚠️ Last Error: {status.lastError}</span>
        </div>
      )}

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'schedule' ? 'active' : ''}`}
          onClick={() => setActiveTab('schedule')}
        >
          Schedule Settings
        </button>
        <button 
          className={`tab ${activeTab === 'backups' ? 'active' : ''}`}
          onClick={() => setActiveTab('backups')}
        >
          Backup History ({backups.length})
        </button>
      </div>

      {activeTab === 'schedule' && (
        <div className="schedule-settings">
          <div className="setting-group">
            <label className="toggle-setting">
              <input
                type="checkbox"
                checked={schedule.enabled}
                onChange={(e) => handleScheduleUpdate({ enabled: e.target.checked })}
              />
              <span>Enable Automatic Backups</span>
            </label>
          </div>

          <div className="setting-group">
            <label>Backup Frequency</label>
            <select
              value={schedule.frequency}
              onChange={(e) => handleScheduleUpdate({ 
                frequency: e.target.value as BackupSchedule['frequency'] 
              })}
              disabled={!schedule.enabled}
            >
              <option value="hourly">Every Hour</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="manual">Manual Only</option>
            </select>
          </div>

          {schedule.frequency === 'daily' && (
            <div className="setting-group">
              <label>Backup Time</label>
              <input
                type="time"
                value={schedule.time || '03:00'}
                onChange={(e) => handleScheduleUpdate({ time: e.target.value })}
                disabled={!schedule.enabled}
              />
            </div>
          )}

          {schedule.frequency === 'weekly' && (
            <>
              <div className="setting-group">
                <label>Day of Week</label>
                <select
                  value={schedule.dayOfWeek || 0}
                  onChange={(e) => handleScheduleUpdate({ 
                    dayOfWeek: parseInt(e.target.value) 
                  })}
                  disabled={!schedule.enabled}
                >
                  <option value="0">Sunday</option>
                  <option value="1">Monday</option>
                  <option value="2">Tuesday</option>
                  <option value="3">Wednesday</option>
                  <option value="4">Thursday</option>
                  <option value="5">Friday</option>
                  <option value="6">Saturday</option>
                </select>
              </div>
              <div className="setting-group">
                <label>Backup Time</label>
                <input
                  type="time"
                  value={schedule.time || '03:00'}
                  onChange={(e) => handleScheduleUpdate({ time: e.target.value })}
                  disabled={!schedule.enabled}
                />
              </div>
            </>
          )}

          <div className="setting-group">
            <label>Retention Period</label>
            <select
              value={schedule.retentionDays}
              onChange={(e) => handleScheduleUpdate({ 
                retentionDays: parseInt(e.target.value) 
              })}
            >
              <option value="7">7 days</option>
              <option value="14">14 days</option>
              <option value="30">30 days</option>
              <option value="60">60 days</option>
              <option value="90">90 days</option>
              <option value="365">1 year</option>
            </select>
          </div>

          <div className="setting-group">
            <label className="toggle-setting">
              <input
                type="checkbox"
                checked={schedule.encryptionEnabled}
                onChange={(e) => handleScheduleUpdate({ 
                  encryptionEnabled: e.target.checked 
                })}
              />
              <span>Enable Encryption</span>
            </label>
            <small>Protects your backup data with encryption</small>
          </div>

          <div className="setting-group">
            <label className="toggle-setting">
              <input
                type="checkbox"
                checked={schedule.cloudSync}
                onChange={(e) => handleScheduleUpdate({ 
                  cloudSync: e.target.checked 
                })}
              />
              <span>Enable Cloud Sync</span>
            </label>
            <small>Sync backups to cloud storage (requires setup)</small>
            {schedule.cloudSync && status.cloudSyncStatus && (
              <div className={`cloud-status ${status.cloudSyncStatus}`}>
                Cloud sync: {status.cloudSyncStatus}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'backups' && (
        <div className="backups-list">
          <div className="list-header">
            <input
              type="file"
              accept=".json"
              onChange={handleImport}
              style={{ display: 'none' }}
              id="import-input"
            />
            <label htmlFor="import-input" className="import-btn">
              📥 Import Backup
            </label>
          </div>

          {backups.length === 0 ? (
            <div className="empty-state">
              <p>No backups available yet</p>
              <button onClick={handleManualBackup}>Create First Backup</button>
            </div>
          ) : (
            <div className="backup-items">
              {backups.map(backup => (
                <div key={backup.id} className="backup-item">
                  <div className="backup-info">
                    <div className="backup-main">
                      <span className="backup-date">
                        {formatDate(backup.timestamp)}
                      </span>
                      {backup.autoBackup && (
                        <span className="auto-badge">Auto</span>
                      )}
                      {backup.encrypted && (
                        <span className="encrypted-badge">🔒</span>
                      )}
                    </div>
                    <div className="backup-meta">
                      <span>Size: {formatBytes(backup.size)}</span>
                      <span>Version: {backup.version}</span>
                      {backup.description && (
                        <span>{backup.description}</span>
                      )}
                    </div>
                  </div>
                  <div className="backup-actions">
                    <button
                      className="restore-btn"
                      onClick={() => handleRestore(backup.id)}
                      title="Restore this backup"
                    >
                      ↩️
                    </button>
                    <button
                      className="export-btn"
                      onClick={() => handleExport(backup.id)}
                      title="Export to file"
                    >
                      💾
                    </button>
                    <button
                      className="delete-btn"
                      onClick={() => handleDelete(backup.id)}
                      title="Delete backup"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <style jsx>{`
        .backup-manager {
          padding: 20px;
          max-width: 800px;
          margin: 0 auto;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .header h2 {
          margin: 0;
          font-size: 24px;
        }

        .backup-now-btn {
          background: #2196f3;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 6px;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .backup-now-btn:hover:not(:disabled) {
          background: #1976d2;
        }

        .backup-now-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .status-bar {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          padding: 20px;
          background: #f5f5f5;
          border-radius: 8px;
          margin-bottom: 20px;
        }

        .status-item {
          display: flex;
          flex-direction: column;
        }

        .status-item .label {
          font-size: 12px;
          color: #666;
          margin-bottom: 4px;
        }

        .status-item .value {
          font-size: 16px;
          font-weight: 600;
          color: #333;
        }

        .error-message {
          background: #ffebee;
          color: #c62828;
          padding: 12px;
          border-radius: 6px;
          margin-bottom: 20px;
        }

        .tabs {
          display: flex;
          gap: 0;
          margin-bottom: 20px;
          border-bottom: 2px solid #e0e0e0;
        }

        .tab {
          background: none;
          border: none;
          padding: 12px 24px;
          font-size: 14px;
          cursor: pointer;
          position: relative;
          transition: all 0.2s;
        }

        .tab.active {
          color: #2196f3;
        }

        .tab.active::after {
          content: '';
          position: absolute;
          bottom: -2px;
          left: 0;
          right: 0;
          height: 2px;
          background: #2196f3;
        }

        .schedule-settings {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .setting-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .setting-group label {
          font-size: 14px;
          font-weight: 500;
          color: #333;
        }

        .setting-group select,
        .setting-group input[type="time"] {
          padding: 8px 12px;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-size: 14px;
        }

        .setting-group small {
          font-size: 12px;
          color: #666;
        }

        .toggle-setting {
          display: flex;
          align-items: center;
          gap: 10px;
          cursor: pointer;
        }

        .toggle-setting input[type="checkbox"] {
          width: 18px;
          height: 18px;
          cursor: pointer;
        }

        .cloud-status {
          margin-top: 8px;
          padding: 6px 12px;
          border-radius: 4px;
          font-size: 12px;
          display: inline-block;
        }

        .cloud-status.synced {
          background: #e8f5e9;
          color: #2e7d32;
        }

        .cloud-status.pending {
          background: #fff3e0;
          color: #e65100;
        }

        .cloud-status.error {
          background: #ffebee;
          color: #c62828;
        }

        .backups-list {
          display: flex;
          flex-direction: column;
          gap: 15px;
        }

        .list-header {
          display: flex;
          justify-content: flex-end;
        }

        .import-btn {
          background: #f5f5f5;
          padding: 8px 16px;
          border-radius: 6px;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .import-btn:hover {
          background: #e0e0e0;
        }

        .empty-state {
          text-align: center;
          padding: 60px 20px;
          color: #666;
        }

        .empty-state p {
          margin-bottom: 20px;
        }

        .empty-state button {
          background: #2196f3;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 6px;
          font-size: 14px;
          cursor: pointer;
        }

        .backup-items {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .backup-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 15px;
          background: white;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          transition: all 0.2s;
        }

        .backup-item:hover {
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .backup-info {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .backup-main {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .backup-date {
          font-size: 16px;
          font-weight: 500;
        }

        .auto-badge {
          background: #e3f2fd;
          color: #1565c0;
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 11px;
        }

        .encrypted-badge {
          font-size: 16px;
        }

        .backup-meta {
          display: flex;
          gap: 15px;
          font-size: 12px;
          color: #666;
        }

        .backup-actions {
          display: flex;
          gap: 8px;
        }

        .backup-actions button {
          width: 36px;
          height: 36px;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 16px;
          transition: all 0.2s;
        }

        .restore-btn {
          background: #4caf50;
          color: white;
        }

        .restore-btn:hover {
          background: #388e3c;
        }

        .export-btn {
          background: #f5f5f5;
        }

        .export-btn:hover {
          background: #e0e0e0;
        }

        .delete-btn {
          background: #ffebee;
          color: #c62828;
        }

        .delete-btn:hover {
          background: #ffcdd2;
        }

        .loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 400px;
        }

        .spinner {
          width: 48px;
          height: 48px;
          border: 4px solid #f3f3f3;
          border-top: 4px solid #2196f3;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 20px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};