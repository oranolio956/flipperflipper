/**
 * Settings Manager
 * Merges core defaults with user overrides and provides reactive updates
 */

import { getDefaultSettings, Settings, validateSettings } from '@/core';
import { db } from './db';

// Settings cache
let settingsCache: Settings | null = null;

// Subscribers for reactive updates
type SettingsListener = (settings: Settings) => void;
const listeners = new Set<SettingsListener>();

// Initialize settings on first load
export async function initializeSettings(): Promise<void> {
  const stored = await db.settings.toArray();
  
  if (stored.length === 0) {
    // First run - use defaults
    const defaults = getDefaultSettings();
    await db.settings.add(defaults);
    settingsCache = defaults;
  } else {
    // Load existing settings
    settingsCache = stored[0];
  }
  
  // Watch for changes from other contexts
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local' && changes.settings) {
      const newSettings = changes.settings.newValue;
      if (newSettings) {
        settingsCache = newSettings;
        notifyListeners();
      }
    }
  });
}

// Get current settings
export async function getSettings(): Promise<Settings> {
  if (!settingsCache) {
    await initializeSettings();
  }
  
  return settingsCache!;
}

// Update settings (partial or full)
export async function setSettings(
  updates: Partial<Settings>, 
  merge = true
): Promise<Settings> {
  const current = await getSettings();
  
  // Merge or replace
  const newSettings = merge 
    ? { ...current, ...updates }
    : updates as Settings;
  
  // Validate
  const validated = validateSettings(newSettings);
  
  // Save to database
  const stored = await db.settings.toArray();
  if (stored.length > 0) {
    await db.settings.update(stored[0]._id!, validated);
  } else {
    await db.settings.add(validated);
  }
  
  // Update cache
  settingsCache = validated;
  
  // Sync to chrome.storage for cross-context updates
  await chrome.storage.local.set({ settings: validated });
  
  // Notify listeners
  notifyListeners();
  
  return validated;
}

// Subscribe to settings changes
export function subscribe(listener: SettingsListener): () => void {
  listeners.add(listener);
  
  // Return unsubscribe function
  return () => {
    listeners.delete(listener);
  };
}

// Notify all listeners of changes
function notifyListeners(): void {
  if (!settingsCache) return;
  
  for (const listener of listeners) {
    try {
      listener(settingsCache);
    } catch (error) {
      console.error('Settings listener error:', error);
    }
  }
}

// Get specific setting value with type safety
export async function getSetting<K extends keyof Settings>(
  key: K
): Promise<Settings[K]> {
  const settings = await getSettings();
  return settings[key];
}

// Update specific setting
export async function setSetting<K extends keyof Settings>(
  key: K,
  value: Settings[K]
): Promise<void> {
  await setSettings({ [key]: value });
}

// Reset to defaults
export async function resetToDefaults(): Promise<Settings> {
  const defaults = getDefaultSettings();
  return await setSettings(defaults, false);
}

// Export settings as JSON
export async function exportSettings(): Promise<string> {
  const settings = await getSettings();
  return JSON.stringify(settings, null, 2);
}

// Import settings from JSON
export async function importSettings(json: string): Promise<Settings> {
  const parsed = JSON.parse(json);
  return await setSettings(parsed, false);
}

// Helpers for common setting groups

export async function getFinancialSettings() {
  const settings = await getSettings();
  return settings.financial;
}

export async function getRiskSettings() {
  const settings = await getSettings();
  return settings.risk_tolerance;
}

export async function getGeographySettings() {
  const settings = await getSettings();
  return settings.geography;
}

export async function getAutomationMode() {
  const settings = await getSettings();
  return settings.automation.mode;
}

export async function setAutomationMode(
  mode: Settings['automation']['mode']
): Promise<void> {
  const current = await getSettings();
  await setSettings({
    automation: {
      ...current.automation,
      mode,
    },
  });
}

// Feature flag helpers
export async function isFeatureEnabled(feature: keyof Settings['features']): Promise<boolean> {
  const settings = await getSettings();
  return settings.features[feature] ?? false;
}

export async function toggleFeature(
  feature: keyof Settings['features'], 
  enabled?: boolean
): Promise<void> {
  const settings = await getSettings();
  const newState = enabled ?? !settings.features[feature];
  
  await setSettings({
    features: {
      ...settings.features,
      [feature]: newState,
    },
  });
}