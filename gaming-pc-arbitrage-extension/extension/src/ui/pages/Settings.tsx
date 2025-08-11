import React, { useState, useEffect, useCallback } from 'react';
import { settingsManager, Settings } from '@/lib/settings';
import { cn } from '@/lib/utils';
import { 
  Save, 
  RotateCcw, 
  Download, 
  Upload,
  Check,
  AlertCircle,
  Moon,
  Sun,
  Monitor
} from 'lucide-react';

/**
 * Settings Page - Apple-grade settings UI with real persistence
 * Every change here affects actual extension behavior
 */
export function Settings() {
  const [settings, setSettings] = useState<Settings>(settingsManager.get());
  const [activeTab, setActiveTab] = useState('automation');
  const [hasChanges, setHasChanges] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  // Subscribe to settings changes
  useEffect(() => {
    const unsubscribe = settingsManager.subscribe((newSettings) => {
      setSettings(newSettings);
      setHasChanges(false);
    });

    return unsubscribe;
  }, []);

  // Show temporary message
  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  // Handle setting changes
  const updateSetting = useCallback((path: string, value: any) => {
    const newSettings = JSON.parse(JSON.stringify(settings));
    
    // Navigate to the nested property
    const keys = path.split('.');
    let current = newSettings;
    
    for (let i = 0; i < keys.length - 1; i++) {
      current = current[keys[i]];
    }
    
    current[keys[keys.length - 1]] = value;
    
    setSettings(newSettings);
    setHasChanges(true);
  }, [settings]);

  // Save all changes
  const saveChanges = async () => {
    setSaving(true);
    try {
      await settingsManager.update(settings);
      showMessage('success', 'Settings saved successfully');
      setHasChanges(false);
    } catch (error) {
      showMessage('error', 'Failed to save settings');
      console.error('Save error:', error);
    } finally {
      setSaving(false);
    }
  };

  // Reset section or all
  const handleReset = async (section?: keyof Settings) => {
    if (confirm(`Reset ${section || 'all'} settings to defaults?`)) {
      try {
        await settingsManager.reset(section);
        showMessage('success', `${section || 'All'} settings reset to defaults`);
      } catch (error) {
        showMessage('error', 'Failed to reset settings');
      }
    }
  };

  // Export settings
  const handleExport = async () => {
    try {
      const data = await settingsManager.export();
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `arbitrage-settings-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
      showMessage('success', 'Settings exported');
    } catch (error) {
      showMessage('error', 'Failed to export settings');
    }
  };

  // Import settings
  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      try {
        const text = await file.text();
        await settingsManager.import(text);
        showMessage('success', 'Settings imported successfully');
      } catch (error) {
        showMessage('error', 'Failed to import settings - invalid format');
      }
    };
    input.click();
  };

  const tabs = [
    { id: 'automation', label: 'Automation', icon: '🤖' },
    { id: 'search', label: 'Search', icon: '🔍' },
    { id: 'pricing', label: 'Pricing', icon: '💰' },
    { id: 'notifications', label: 'Notifications', icon: '🔔' },
    { id: 'display', label: 'Display', icon: '🎨' },
    { id: 'privacy', label: 'Privacy', icon: '🔒' },
    { id: 'performance', label: 'Performance', icon: '⚡' },
    { id: 'developer', label: 'Developer', icon: '🛠️' }
  ];

  return (
    <div className="settings-page">
      <div className="settings-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Configure your arbitrage assistant</p>
        </div>
        
        <div className="settings-actions">
          <button
            className="btn btn-secondary"
            onClick={() => handleReset()}
            title="Reset all settings"
          >
            <RotateCcw className="w-4 h-4" />
            Reset All
          </button>
          
          <button
            className="btn btn-secondary"
            onClick={handleExport}
            title="Export settings"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
          
          <button
            className="btn btn-secondary"
            onClick={handleImport}
            title="Import settings"
          >
            <Upload className="w-4 h-4" />
            Import
          </button>
          
          <button
            className={cn(
              "btn btn-primary",
              saving && "opacity-50 cursor-not-allowed"
            )}
            onClick={saveChanges}
            disabled={!hasChanges || saving}
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {message && (
        <div className={cn(
          "settings-message",
          message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
        )}>
          {message.type === 'success' ? <Check className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          {message.text}
        </div>
      )}

      <div className="settings-content">
        <div className="settings-tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={cn(
                "settings-tab",
                activeTab === tab.id && "active"
              )}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
            </button>
          ))}
        </div>

        <div className="settings-panel">
          {activeTab === 'automation' && (
            <AutomationSettings 
              settings={settings.automation} 
              onChange={(value) => updateSetting('automation', value)}
              onReset={() => handleReset('automation')}
            />
          )}
          
          {activeTab === 'search' && (
            <SearchSettings 
              settings={settings.search} 
              onChange={(value) => updateSetting('search', value)}
              onReset={() => handleReset('search')}
            />
          )}
          
          {activeTab === 'pricing' && (
            <PricingSettings 
              settings={settings.pricing} 
              onChange={(value) => updateSetting('pricing', value)}
              onReset={() => handleReset('pricing')}
            />
          )}
          
          {activeTab === 'notifications' && (
            <NotificationSettings 
              settings={settings.notifications} 
              onChange={(value) => updateSetting('notifications', value)}
              onReset={() => handleReset('notifications')}
            />
          )}
          
          {activeTab === 'display' && (
            <DisplaySettings 
              settings={settings.display} 
              onChange={(value) => updateSetting('display', value)}
              onReset={() => handleReset('display')}
            />
          )}
          
          {activeTab === 'privacy' && (
            <PrivacySettings 
              settings={settings.privacy} 
              onChange={(value) => updateSetting('privacy', value)}
              onReset={() => handleReset('privacy')}
            />
          )}
          
          {activeTab === 'performance' && (
            <PerformanceSettings 
              settings={settings.performance} 
              onChange={(value) => updateSetting('performance', value)}
              onReset={() => handleReset('performance')}
            />
          )}
          
          {activeTab === 'developer' && (
            <DeveloperSettings 
              settings={settings.developer} 
              onChange={(value) => updateSetting('developer', value)}
              onReset={() => handleReset('developer')}
            />
          )}
        </div>
      </div>
    </div>
  );
}

// Automation Settings Panel
function AutomationSettings({ 
  settings, 
  onChange,
  onReset 
}: { 
  settings: Settings['automation'];
  onChange: (value: Settings['automation']) => void;
  onReset: () => void;
}) {
  return (
    <div className="settings-section">
      <div className="section-header">
        <h2>Automation Settings</h2>
        <button className="btn-text" onClick={onReset}>Reset Section</button>
      </div>

      <div className="setting-group">
        <label className="toggle-setting">
          <div>
            <span className="setting-label">Enable Max Auto</span>
            <span className="setting-description">
              Automatically scan saved searches on schedule
            </span>
          </div>
          <input
            type="checkbox"
            checked={settings.enabled}
            onChange={(e) => onChange({ ...settings, enabled: e.target.checked })}
            className="toggle"
          />
        </label>
      </div>

      <div className="setting-group">
        <label className="input-setting">
          <span className="setting-label">Scan Interval</span>
          <span className="setting-description">
            How often to run automated scans (minutes)
          </span>
          <input
            type="number"
            min="5"
            max="360"
            value={settings.scanInterval}
            onChange={(e) => onChange({ ...settings, scanInterval: parseInt(e.target.value) || 30 })}
            className="input-number"
          />
        </label>
      </div>

      <div className="setting-group">
        <label className="input-setting">
          <span className="setting-label">Max Concurrent Tabs</span>
          <span className="setting-description">
            Maximum number of tabs to open simultaneously
          </span>
          <input
            type="range"
            min="1"
            max="10"
            value={settings.maxConcurrentTabs}
            onChange={(e) => onChange({ ...settings, maxConcurrentTabs: parseInt(e.target.value) })}
            className="input-range"
          />
          <span className="range-value">{settings.maxConcurrentTabs}</span>
        </label>
      </div>

      <div className="setting-group">
        <label className="toggle-setting">
          <div>
            <span className="setting-label">Pause During Active Use</span>
            <span className="setting-description">
              Stop automation when you're actively using the browser
            </span>
          </div>
          <input
            type="checkbox"
            checked={settings.pauseDuringActive}
            onChange={(e) => onChange({ ...settings, pauseDuringActive: e.target.checked })}
            className="toggle"
          />
        </label>
      </div>

      <div className="setting-group">
        <label className="input-setting">
          <span className="setting-label">Retry Attempts</span>
          <span className="setting-description">
            Number of times to retry failed scans
          </span>
          <input
            type="number"
            min="0"
            max="10"
            value={settings.retryAttempts}
            onChange={(e) => onChange({ ...settings, retryAttempts: parseInt(e.target.value) || 3 })}
            className="input-number"
          />
        </label>
      </div>
    </div>
  );
}

// Display Settings Panel
function DisplaySettings({ 
  settings, 
  onChange,
  onReset 
}: { 
  settings: Settings['display'];
  onChange: (value: Settings['display']) => void;
  onReset: () => void;
}) {
  return (
    <div className="settings-section">
      <div className="section-header">
        <h2>Display Settings</h2>
        <button className="btn-text" onClick={onReset}>Reset Section</button>
      </div>

      <div className="setting-group">
        <label className="setting-label">Theme</label>
        <div className="theme-selector">
          <button
            className={cn("theme-option", settings.theme === 'light' && "active")}
            onClick={() => onChange({ ...settings, theme: 'light' })}
          >
            <Sun className="w-4 h-4" />
            Light
          </button>
          <button
            className={cn("theme-option", settings.theme === 'dark' && "active")}
            onClick={() => onChange({ ...settings, theme: 'dark' })}
          >
            <Moon className="w-4 h-4" />
            Dark
          </button>
          <button
            className={cn("theme-option", settings.theme === 'auto' && "active")}
            onClick={() => onChange({ ...settings, theme: 'auto' })}
          >
            <Monitor className="w-4 h-4" />
            Auto
          </button>
        </div>
      </div>

      <div className="setting-group">
        <label className="toggle-setting">
          <div>
            <span className="setting-label">Compact Mode</span>
            <span className="setting-description">
              Show more information in less space
            </span>
          </div>
          <input
            type="checkbox"
            checked={settings.compactMode}
            onChange={(e) => onChange({ ...settings, compactMode: e.target.checked })}
            className="toggle"
          />
        </label>
      </div>

      <div className="setting-group">
        <label className="toggle-setting">
          <div>
            <span className="setting-label">Show Advanced Features</span>
            <span className="setting-description">
              Enable power user features and complex options
            </span>
          </div>
          <input
            type="checkbox"
            checked={settings.showAdvancedFeatures}
            onChange={(e) => onChange({ ...settings, showAdvancedFeatures: e.target.checked })}
            className="toggle"
          />
        </label>
      </div>

      <div className="setting-group">
        <label className="input-setting">
          <span className="setting-label">Default View</span>
          <span className="setting-description">
            Which page to show when opening the extension
          </span>
          <select
            value={settings.defaultView}
            onChange={(e) => onChange({ ...settings, defaultView: e.target.value as any })}
            className="input-select"
          >
            <option value="dashboard">Dashboard</option>
            <option value="pipeline">Pipeline</option>
            <option value="scanner">Scanner</option>
          </select>
        </label>
      </div>
    </div>
  );
}

// Add other setting panels (SearchSettings, PricingSettings, etc.)
// For brevity, I'm showing the pattern - you'd implement all of them similarly

// Notification Settings Panel
function NotificationSettings({ 
  settings, 
  onChange,
  onReset 
}: { 
  settings: Settings['notifications'];
  onChange: (value: Settings['notifications']) => void;
  onReset: () => void;
}) {
  return (
    <div className="settings-section">
      <div className="section-header">
        <h2>Notification Settings</h2>
        <button className="btn-text" onClick={onReset}>Reset Section</button>
      </div>

      <div className="setting-group">
        <label className="toggle-setting">
          <div>
            <span className="setting-label">Enable Notifications</span>
            <span className="setting-description">
              Show notifications for important events
            </span>
          </div>
          <input
            type="checkbox"
            checked={settings.enabled}
            onChange={(e) => onChange({ ...settings, enabled: e.target.checked })}
            className="toggle"
          />
        </label>
      </div>

      {settings.enabled && (
        <>
          <div className="setting-group">
            <label className="toggle-setting">
              <div>
                <span className="setting-label">Desktop Notifications</span>
                <span className="setting-description">
                  Show system notifications (requires permission)
                </span>
              </div>
              <input
                type="checkbox"
                checked={settings.desktop}
                onChange={(e) => {
                  if (e.target.checked && Notification.permission === 'default') {
                    Notification.requestPermission();
                  }
                  onChange({ ...settings, desktop: e.target.checked });
                }}
                className="toggle"
              />
            </label>
          </div>

          <div className="setting-group">
            <label className="toggle-setting">
              <div>
                <span className="setting-label">Sound Alerts</span>
                <span className="setting-description">
                  Play sound when notifications appear
                </span>
              </div>
              <input
                type="checkbox"
                checked={settings.sound}
                onChange={(e) => onChange({ ...settings, sound: e.target.checked })}
                className="toggle"
              />
            </label>
          </div>

          <div className="setting-subsection">
            <h3>Notification Triggers</h3>
            
            <label className="toggle-setting">
              <div>
                <span className="setting-label">New Deals</span>
                <span className="setting-description">
                  When new profitable deals are found
                </span>
              </div>
              <input
                type="checkbox"
                checked={settings.triggers.newDeal}
                onChange={(e) => onChange({ 
                  ...settings, 
                  triggers: { ...settings.triggers, newDeal: e.target.checked }
                })}
                className="toggle"
              />
            </label>

            <label className="toggle-setting">
              <div>
                <span className="setting-label">Price Changes</span>
                <span className="setting-description">
                  When tracked listings change price
                </span>
              </div>
              <input
                type="checkbox"
                checked={settings.triggers.priceChange}
                onChange={(e) => onChange({ 
                  ...settings, 
                  triggers: { ...settings.triggers, priceChange: e.target.checked }
                })}
                className="toggle"
              />
            </label>
          </div>

          <div className="setting-subsection">
            <h3>Quiet Hours</h3>
            
            <label className="toggle-setting">
              <div>
                <span className="setting-label">Enable Quiet Hours</span>
                <span className="setting-description">
                  Mute notifications during specific hours
                </span>
              </div>
              <input
                type="checkbox"
                checked={settings.quietHours.enabled}
                onChange={(e) => onChange({ 
                  ...settings, 
                  quietHours: { ...settings.quietHours, enabled: e.target.checked }
                })}
                className="toggle"
              />
            </label>

            {settings.quietHours.enabled && (
              <div className="time-range">
                <input
                  type="time"
                  value={settings.quietHours.start}
                  onChange={(e) => onChange({ 
                    ...settings, 
                    quietHours: { ...settings.quietHours, start: e.target.value }
                  })}
                  className="input-time"
                />
                <span>to</span>
                <input
                  type="time"
                  value={settings.quietHours.end}
                  onChange={(e) => onChange({ 
                    ...settings, 
                    quietHours: { ...settings.quietHours, end: e.target.value }
                  })}
                  className="input-time"
                />
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

// Placeholder components for other settings panels
function SearchSettings({ settings, onChange, onReset }: any) {
  return <div className="settings-section">Search settings coming soon...</div>;
}

function PricingSettings({ settings, onChange, onReset }: any) {
  return <div className="settings-section">Pricing settings coming soon...</div>;
}

function PrivacySettings({ settings, onChange, onReset }: any) {
  return <div className="settings-section">Privacy settings coming soon...</div>;
}

function PerformanceSettings({ settings, onChange, onReset }: any) {
  return <div className="settings-section">Performance settings coming soon...</div>;
}

function DeveloperSettings({ settings, onChange, onReset }: any) {
  return <div className="settings-section">Developer settings coming soon...</div>;
}