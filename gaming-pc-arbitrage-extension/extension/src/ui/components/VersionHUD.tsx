import React, { useEffect, useState } from 'react';
import { RefreshCw, CheckCircle, AlertCircle, Download } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VersionInfo {
  version: string;
  channel: 'stable' | 'beta' | 'dev';
  buildHash: string;
  updateStatus: 'checking' | 'current' | 'available' | 'error';
  lastCheck: string;
}

export function VersionHUD() {
  const [versionInfo, setVersionInfo] = useState<VersionInfo>({
    version: chrome.runtime.getManifest().version,
    channel: 'stable',
    buildHash: 'a7f2b9c',
    updateStatus: 'current',
    lastCheck: new Date().toISOString()
  });
  
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    // Load version info from storage
    chrome.storage.local.get(['versionInfo'], (result) => {
      if (result.versionInfo) {
        setVersionInfo(result.versionInfo);
      }
    });

    // Listen for update status changes
    const handleMessage = (message: any) => {
      if (message.action === 'UPDATE_STATUS_CHANGED') {
        setVersionInfo(prev => ({
          ...prev,
          updateStatus: message.status,
          lastCheck: new Date().toISOString()
        }));
      }
    };

    chrome.runtime.onMessage.addListener(handleMessage);
    return () => chrome.runtime.onMessage.removeListener(handleMessage);
  }, []);

  const checkForUpdates = () => {
    setVersionInfo(prev => ({ ...prev, updateStatus: 'checking' }));
    chrome.runtime.sendMessage({ action: 'CHECK_FOR_UPDATES' });
  };

  const getStatusIcon = () => {
    switch (versionInfo.updateStatus) {
      case 'checking':
        return <RefreshCw className="w-3 h-3 animate-spin" />;
      case 'current':
        return <CheckCircle className="w-3 h-3 text-green-500" />;
      case 'available':
        return <Download className="w-3 h-3 text-blue-500 animate-pulse" />;
      case 'error':
        return <AlertCircle className="w-3 h-3 text-red-500" />;
    }
  };

  const getStatusText = () => {
    switch (versionInfo.updateStatus) {
      case 'checking':
        return 'Checking for updates...';
      case 'current':
        return 'Up to date';
      case 'available':
        return 'Update available';
      case 'error':
        return 'Update check failed';
    }
  };

  return (
    <div
      className={cn(
        "fixed bottom-4 right-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg",
        "border border-gray-200 dark:border-gray-700 transition-all duration-200",
        isExpanded ? "w-64" : "w-auto"
      )}
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      <div className="px-3 py-2">
        <div className="flex items-center gap-2 text-xs">
          {getStatusIcon()}
          <span className="font-mono text-gray-600 dark:text-gray-400">
            v{versionInfo.version}
          </span>
          {versionInfo.channel !== 'stable' && (
            <span className={cn(
              "px-1.5 py-0.5 rounded text-xs font-medium",
              versionInfo.channel === 'beta' && "bg-blue-100 text-blue-700",
              versionInfo.channel === 'dev' && "bg-orange-100 text-orange-700"
            )}>
              {versionInfo.channel}
            </span>
          )}
        </div>
        
        {isExpanded && (
          <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
            <div className="space-y-1 text-xs text-gray-500 dark:text-gray-400">
              <div className="flex justify-between">
                <span>Status:</span>
                <span className="font-medium">{getStatusText()}</span>
              </div>
              <div className="flex justify-between">
                <span>Build:</span>
                <span className="font-mono">{versionInfo.buildHash}</span>
              </div>
              <div className="flex justify-between">
                <span>Last check:</span>
                <span>{new Date(versionInfo.lastCheck).toLocaleTimeString()}</span>
              </div>
            </div>
            
            {versionInfo.updateStatus !== 'checking' && (
              <button
                onClick={checkForUpdates}
                className="mt-2 w-full px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded transition-colors"
              >
                Check for updates
              </button>
            )}
            
            {versionInfo.updateStatus === 'available' && (
              <div className="mt-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded">
                <p className="text-xs text-blue-700 dark:text-blue-400">
                  A new version is available. Chrome will update automatically.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}