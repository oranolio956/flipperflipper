import React, { useState, useEffect } from 'react';
import { RefreshCw, CheckCircle, AlertCircle, Download } from 'lucide-react';
import type { UpdateStatus } from '../../background/updateChecker';

export function VersionHUD() {
  const [updateStatus, setUpdateStatus] = useState<UpdateStatus | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isChecking, setIsChecking] = useState(false);

  useEffect(() => {
    loadUpdateStatus();
    
    // Listen for update notifications
    const handleMessage = (message: any) => {
      if (message.type === 'UPDATE_AVAILABLE') {
        setUpdateStatus(message.status);
      }
    };
    
    chrome.runtime.onMessage.addListener(handleMessage);
    return () => chrome.runtime.onMessage.removeListener(handleMessage);
  }, []);

  const loadUpdateStatus = async () => {
    try {
      const response = await chrome.runtime.sendMessage({ 
        action: 'GET_UPDATE_STATUS' 
      });
      if (response?.status) {
        setUpdateStatus(response.status);
      }
    } catch (error) {
      // Fallback to basic info
      const manifest = chrome.runtime.getManifest();
      setUpdateStatus({
        currentVersion: manifest.version,
        updateAvailable: false,
        lastCheck: new Date(),
        channel: 'production'
      });
    }
  };

  const checkForUpdates = async () => {
    setIsChecking(true);
    try {
      await chrome.runtime.sendMessage({ action: 'CHECK_FOR_UPDATES' });
      await loadUpdateStatus();
    } finally {
      setTimeout(() => setIsChecking(false), 1000);
    }
  };

  const applyUpdate = async () => {
    await chrome.runtime.sendMessage({ action: 'APPLY_UPDATE' });
  };

  if (!updateStatus) return null;

  const formatDate = (date: Date | string) => {
    const d = typeof date === 'string' ? new Date(date) : date;
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(d);
  };

  const getChannelColor = (channel: string) => {
    switch (channel) {
      case 'dev': return 'text-orange-600 bg-orange-50';
      case 'beta': return 'text-blue-600 bg-blue-50';
      default: return 'text-green-600 bg-green-50';
    }
  };

  return (
    <div 
      className="version-hud"
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      <div className="version-badge">
        {updateStatus.updateAvailable ? (
          <AlertCircle className="version-icon update-available" />
        ) : (
          <CheckCircle className="version-icon up-to-date" />
        )}
        <span className="version-text">
          v{updateStatus.currentVersion}
        </span>
        {updateStatus.buildHash && (
          <span className="build-hash">+{updateStatus.buildHash}</span>
        )}
        <span className={`channel-badge ${getChannelColor(updateStatus.channel)}`}>
          {updateStatus.channel}
        </span>
      </div>

      {isExpanded && (
        <div className="version-tooltip">
          <div className="tooltip-header">
            <h4>Extension Version</h4>
            <button 
              className="check-button"
              onClick={checkForUpdates}
              disabled={isChecking}
              title="Check for updates"
            >
              <RefreshCw className={`refresh-icon ${isChecking ? 'spinning' : ''}`} />
            </button>
          </div>

          <div className="version-details">
            <div className="detail-row">
              <span className="label">Current:</span>
              <span className="value">v{updateStatus.currentVersion}</span>
            </div>
            
            {updateStatus.updateAvailable && (
              <div className="detail-row highlight">
                <span className="label">Available:</span>
                <span className="value">v{updateStatus.latestVersion}</span>
              </div>
            )}

            <div className="detail-row">
              <span className="label">Channel:</span>
              <span className={`value ${getChannelColor(updateStatus.channel)}`}>
                {updateStatus.channel}
              </span>
            </div>

            <div className="detail-row">
              <span className="label">Last Check:</span>
              <span className="value">{formatDate(updateStatus.lastCheck)}</span>
            </div>

            {updateStatus.buildHash && (
              <div className="detail-row">
                <span className="label">Build:</span>
                <span className="value mono">{updateStatus.buildHash}</span>
              </div>
            )}
          </div>

          {updateStatus.updateAvailable && (
            <div className="update-actions">
              <button 
                className="update-button"
                onClick={applyUpdate}
              >
                <Download className="button-icon" />
                Update Now
              </button>
              {updateStatus.releaseNotes && (
                <div className="release-notes">
                  <h5>What's New:</h5>
                  <p>{updateStatus.releaseNotes}</p>
                </div>
              )}
            </div>
          )}

          <div className="update-info">
            {updateStatus.updateAvailable ? (
              <p className="update-message">
                🎉 A new version is available! Click "Update Now" or restart your browser.
              </p>
            ) : (
              <p className="status-message">
                ✅ You're running the latest version
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// CSS for the Version HUD
export const versionHUDStyles = `
.version-hud {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9999;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.version-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  padding: 6px 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.2s;
}

.version-badge:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.version-icon {
  width: 16px;
  height: 16px;
}

.version-icon.up-to-date {
  color: #10b981;
}

.version-icon.update-available {
  color: #f59e0b;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.version-text {
  font-size: 12px;
  font-weight: 500;
  color: #374151;
}

.build-hash {
  font-size: 11px;
  color: #6b7280;
  font-family: monospace;
}

.channel-badge {
  font-size: 10px;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 10px;
  text-transform: uppercase;
}

.version-tooltip {
  position: absolute;
  bottom: 100%;
  right: 0;
  margin-bottom: 8px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  min-width: 280px;
  animation: fadeIn 0.2s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.tooltip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.tooltip-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.check-button {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: #6b7280;
  transition: color 0.2s;
}

.check-button:hover:not(:disabled) {
  color: #3b82f6;
}

.check-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.refresh-icon {
  width: 16px;
  height: 16px;
}

.refresh-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.version-details {
  margin-bottom: 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 12px;
}

.detail-row.highlight {
  background: #fef3c7;
  margin: 0 -8px;
  padding: 4px 8px;
  border-radius: 4px;
}

.detail-row .label {
  color: #6b7280;
}

.detail-row .value {
  color: #111827;
  font-weight: 500;
}

.detail-row .value.mono {
  font-family: monospace;
  font-size: 11px;
}

.update-actions {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.update-button {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 8px 12px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.update-button:hover {
  background: #2563eb;
}

.button-icon {
  width: 14px;
  height: 14px;
}

.release-notes {
  margin-top: 12px;
  padding: 8px;
  background: #f3f4f6;
  border-radius: 4px;
}

.release-notes h5 {
  margin: 0 0 4px 0;
  font-size: 11px;
  font-weight: 600;
  color: #374151;
}

.release-notes p {
  margin: 0;
  font-size: 11px;
  color: #6b7280;
}

.update-info {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.update-message,
.status-message {
  margin: 0;
  font-size: 11px;
  color: #6b7280;
  text-align: center;
}
`;