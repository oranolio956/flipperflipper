import React, { useEffect, useState } from 'react';
import { Save, RotateCcw, Download, Upload, Shield, Bell, Cpu, Search, DollarSign, MessageSquare, BarChart, Palette } from 'lucide-react';
import { settingsManager, Settings, DEFAULT_SETTINGS } from '@/lib/settings';
import { cn } from '@/lib/utils';

export default function Settings() {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [activeSection, setActiveSection] = useState('automation');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    await settingsManager.loadSettings();
    const currentSettings = settingsManager.getSettings();
    setSettings(currentSettings);
  };

  const updateSetting = <K extends keyof Settings>(
    section: K,
    field: keyof Settings[K],
    value: any
  ) => {
    const newSettings = {
      ...settings,
      [section]: {
        ...settings[section],
        [field]: value
      }
    };
    setSettings(newSettings);
    setHasChanges(true);
  };

  const saveSettings = async () => {
    setIsSaving(true);
    try {
      await settingsManager.saveSettings(settings);
      setHasChanges(false);
      // Show success toast
      chrome.runtime.sendMessage({
        action: 'SHOW_TOAST',
        message: 'Settings saved successfully',
        type: 'success'
      });
    } catch (error) {
      console.error('Failed to save settings:', error);
      chrome.runtime.sendMessage({
        action: 'SHOW_TOAST',
        message: 'Failed to save settings',
        type: 'error'
      });
    }
    setIsSaving(false);
  };

  const resetSettings = async () => {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
      await settingsManager.resetSettings();
      await loadSettings();
      setHasChanges(false);
    }
  };

  const exportSettings = () => {
    const json = settingsManager.exportSettings();
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pc-arbitrage-settings-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const importSettings = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/json';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        const text = await file.text();
        try {
          await settingsManager.importSettings(text);
          await loadSettings();
          setHasChanges(false);
          chrome.runtime.sendMessage({
            action: 'SHOW_TOAST',
            message: 'Settings imported successfully',
            type: 'success'
          });
        } catch (error) {
          chrome.runtime.sendMessage({
            action: 'SHOW_TOAST',
            message: 'Invalid settings file',
            type: 'error'
          });
        }
      }
    };
    input.click();
  };

  const sections = [
    { id: 'automation', label: 'Automation', icon: Cpu },
    { id: 'search', label: 'Search', icon: Search },
    { id: 'pricing', label: 'Pricing', icon: DollarSign },
    { id: 'messaging', label: 'Messaging', icon: MessageSquare },
    { id: 'risk', label: 'Risk', icon: Shield },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'privacy', label: 'Privacy', icon: Shield },
    { id: 'ui', label: 'Appearance', icon: Palette }
  ];

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 data-testid="page-title" className="text-3xl font-bold text-gray-900 dark:text-white">
          Settings
        </h1>
        <div className="flex items-center gap-3">
          <button
            onClick={exportSettings}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-700"
          >
            <Download className="w-4 h-4 mr-2 inline" />
            Export
          </button>
          <button
            onClick={importSettings}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-700"
          >
            <Upload className="w-4 h-4 mr-2 inline" />
            Import
          </button>
          <button
            onClick={resetSettings}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-700"
          >
            <RotateCcw className="w-4 h-4 mr-2 inline" />
            Reset
          </button>
          <button
            onClick={saveSettings}
            disabled={!hasChanges || isSaving}
            className={cn(
              "px-4 py-2 text-sm font-medium text-white rounded-md",
              hasChanges
                ? "bg-indigo-600 hover:bg-indigo-700"
                : "bg-gray-400 cursor-not-allowed"
            )}
          >
            <Save className="w-4 h-4 mr-2 inline" />
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      <div className="flex gap-8">
        {/* Sidebar */}
        <nav className="w-48 flex-shrink-0">
          <ul className="space-y-1">
            {sections.map((section) => {
              const Icon = section.icon;
              return (
                <li key={section.id}>
                  <button
                    onClick={() => setActiveSection(section.id)}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors",
                      activeSection === section.id
                        ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-400"
                        : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
                    )}
                  >
                    <Icon className="w-4 h-4" />
                    {section.label}
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Content */}
        <div className="flex-1 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          {activeSection === 'automation' && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold mb-4">Automation Settings</h2>
              
              <div className="space-y-4">
                <label className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Enable Max Auto</p>
                    <p className="text-sm text-gray-500">Automatically scan saved searches</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.automation.enabled}
                    onChange={(e) => updateSetting('automation', 'enabled', e.target.checked)}
                    className="w-4 h-4 text-indigo-600 rounded"
                  />
                </label>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Scan Interval (minutes)
                  </label>
                  <input
                    type="number"
                    min="5"
                    max="120"
                    value={settings.automation.scanInterval}
                    onChange={(e) => updateSetting('automation', 'scanInterval', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Max Tabs Per Batch
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={settings.automation.maxTabsPerBatch}
                    onChange={(e) => updateSetting('automation', 'maxTabsPerBatch', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>

                <label className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Pause During Active Use</p>
                    <p className="text-sm text-gray-500">Stop automation when you're using the browser</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.automation.pauseDuringActive}
                    onChange={(e) => updateSetting('automation', 'pauseDuringActive', e.target.checked)}
                    className="w-4 h-4 text-indigo-600 rounded"
                  />
                </label>
              </div>
            </div>
          )}

          {activeSection === 'search' && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold mb-4">Search Preferences</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Default Search Radius (miles)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={settings.search.defaultRadius}
                    onChange={(e) => updateSetting('search', 'defaultRadius', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Min Price ($)
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={settings.search.minPrice}
                      onChange={(e) => updateSetting('search', 'minPrice', parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Max Price ($)
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={settings.search.maxPrice}
                      onChange={(e) => updateSetting('search', 'maxPrice', parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Exclude Keywords (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={settings.search.excludeKeywords.join(', ')}
                    onChange={(e) => updateSetting('search', 'excludeKeywords', 
                      e.target.value.split(',').map(k => k.trim()).filter(k => k)
                    )}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600"
                    placeholder="parts, broken, repair"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Preferred Platforms
                  </label>
                  <div className="space-y-2">
                    {['facebook', 'craigslist', 'offerup'].map(platform => (
                      <label key={platform} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={settings.search.preferredPlatforms.includes(platform)}
                          onChange={(e) => {
                            const platforms = e.target.checked
                              ? [...settings.search.preferredPlatforms, platform]
                              : settings.search.preferredPlatforms.filter(p => p !== platform);
                            updateSetting('search', 'preferredPlatforms', platforms);
                          }}
                          className="w-4 h-4 text-indigo-600 rounded mr-2"
                        />
                        <span className="capitalize">{platform}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'pricing' && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold mb-4">Pricing Settings</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Default Profit Margin (%)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={settings.pricing.defaultMargin}
                    onChange={(e) => updateSetting('pricing', 'defaultMargin', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Tax Rate (%)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="20"
                    step="0.1"
                    value={settings.pricing.taxRate}
                    onChange={(e) => updateSetting('pricing', 'taxRate', parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Pricing Strategy
                  </label>
                  <select
                    value={settings.pricing.pricingStrategy}
                    onChange={(e) => updateSetting('pricing', 'pricingStrategy', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600"
                  >
                    <option value="aggressive">Aggressive (Quick Sale)</option>
                    <option value="moderate">Moderate (Balanced)</option>
                    <option value="conservative">Conservative (Max Profit)</option>
                  </select>
                </div>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.pricing.includeShipping}
                    onChange={(e) => updateSetting('pricing', 'includeShipping', e.target.checked)}
                    className="w-4 h-4 text-indigo-600 rounded mr-2"
                  />
                  <span>Include shipping costs in calculations</span>
                </label>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.pricing.includeFees}
                    onChange={(e) => updateSetting('pricing', 'includeFees', e.target.checked)}
                    className="w-4 h-4 text-indigo-600 rounded mr-2"
                  />
                  <span>Include platform fees in calculations</span>
                </label>
              </div>
            </div>
          )}

          {/* Add more sections as needed */}
        </div>
      </div>
    </div>
  );
}