/**
 * Saved Searches Manager
 * Manages user's saved marketplace searches for automated scanning
 */

import { generateId } from '../../ui/lib/utils';

export interface SavedSearch {
  id: string;
  name: string;
  url: string;
  platform: 'facebook' | 'craigslist' | 'offerup';
  enabled: boolean;
  cadenceMinutes: number; // How often to scan
  filters: {
    minPrice?: number;
    maxPrice?: number;
    keywords?: string[];
    excludeKeywords?: string[];
    radius?: number;
  };
  lastScanned?: Date;
  nextScan?: Date;
  resultsCount: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface AutomationSettings {
  enabled: boolean;
  maxTabsOpen: number;
  closeTabsAfterScan: boolean;
  notifyOnNewFinds: boolean;
  pauseDuringActiveUse: boolean;
}

class SavedSearchesManager {
  private readonly STORAGE_KEY = 'savedSearches';
  private readonly SETTINGS_KEY = 'automationSettings';
  private readonly ALARM_PREFIX = 'search-scan-';

  async getAll(): Promise<SavedSearch[]> {
    const { [this.STORAGE_KEY]: searches } = await chrome.storage.local.get([this.STORAGE_KEY]);
    return searches || [];
  }

  async get(id: string): Promise<SavedSearch | null> {
    const searches = await this.getAll();
    return searches.find(s => s.id === id) || null;
  }

  async create(search: Omit<SavedSearch, 'id' | 'createdAt' | 'updatedAt' | 'resultsCount'>): Promise<SavedSearch> {
    const newSearch: SavedSearch = {
      ...search,
      id: generateId('search'),
      resultsCount: 0,
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    const searches = await this.getAll();
    searches.push(newSearch);
    await chrome.storage.local.set({ [this.STORAGE_KEY]: searches });

    // Schedule alarm if enabled
    if (newSearch.enabled) {
      await this.scheduleAlarm(newSearch);
    }

    return newSearch;
  }

  async update(id: string, updates: Partial<SavedSearch>): Promise<SavedSearch | null> {
    const searches = await this.getAll();
    const index = searches.findIndex(s => s.id === id);
    
    if (index === -1) return null;

    const oldSearch = searches[index];
    const updatedSearch = {
      ...oldSearch,
      ...updates,
      id: oldSearch.id, // Prevent ID change
      updatedAt: new Date(),
    };

    searches[index] = updatedSearch;
    await chrome.storage.local.set({ [this.STORAGE_KEY]: searches });

    // Update alarm scheduling
    if (updatedSearch.enabled !== oldSearch.enabled || 
        updatedSearch.cadenceMinutes !== oldSearch.cadenceMinutes) {
      if (updatedSearch.enabled) {
        await this.scheduleAlarm(updatedSearch);
      } else {
        await this.cancelAlarm(updatedSearch.id);
      }
    }

    return updatedSearch;
  }

  async delete(id: string): Promise<boolean> {
    const searches = await this.getAll();
    const filtered = searches.filter(s => s.id !== id);
    
    if (filtered.length === searches.length) return false;

    await chrome.storage.local.set({ [this.STORAGE_KEY]: filtered });
    await this.cancelAlarm(id);
    
    return true;
  }

  async getSettings(): Promise<AutomationSettings> {
    const { [this.SETTINGS_KEY]: settings } = await chrome.storage.local.get([this.SETTINGS_KEY]);
    return settings || {
      enabled: false,
      maxTabsOpen: 3,
      closeTabsAfterScan: true,
      notifyOnNewFinds: true,
      pauseDuringActiveUse: true,
    };
  }

  async updateSettings(updates: Partial<AutomationSettings>): Promise<AutomationSettings> {
    const current = await this.getSettings();
    const updated = { ...current, ...updates };
    await chrome.storage.local.set({ [this.SETTINGS_KEY]: updated });

    // If automation was toggled, update all alarms
    if (updates.enabled !== undefined && updates.enabled !== current.enabled) {
      if (updates.enabled) {
        await this.scheduleAllAlarms();
      } else {
        await this.cancelAllAlarms();
      }
    }

    return updated;
  }

  // Alarm Management
  private async scheduleAlarm(search: SavedSearch): Promise<void> {
    const alarmName = `${this.ALARM_PREFIX}${search.id}`;
    
    // Create alarm
    await chrome.alarms.create(alarmName, {
      delayInMinutes: 1, // Start soon
      periodInMinutes: search.cadenceMinutes,
    });
  }

  private async cancelAlarm(searchId: string): Promise<void> {
    const alarmName = `${this.ALARM_PREFIX}${searchId}`;
    await chrome.alarms.clear(alarmName);
  }

  private async scheduleAllAlarms(): Promise<void> {
    const searches = await this.getAll();
    const enabled = searches.filter(s => s.enabled);
    
    for (const search of enabled) {
      await this.scheduleAlarm(search);
    }
  }

  private async cancelAllAlarms(): Promise<void> {
    const searches = await this.getAll();
    
    for (const search of searches) {
      await this.cancelAlarm(search.id);
    }
  }

  // Scan Management
  async recordScan(searchId: string, resultsCount: number): Promise<void> {
    await this.update(searchId, {
      lastScanned: new Date(),
      nextScan: new Date(Date.now() + (await this.get(searchId))!.cadenceMinutes * 60 * 1000),
      resultsCount,
    });
  }

  async getScheduledScans(): Promise<SavedSearch[]> {
    const searches = await this.getAll();
    const settings = await this.getSettings();
    
    if (!settings.enabled) return [];
    
    return searches
      .filter(s => s.enabled)
      .sort((a, b) => {
        const aNext = a.nextScan?.getTime() || 0;
        const bNext = b.nextScan?.getTime() || 0;
        return aNext - bNext;
      });
  }

  // Platform-specific URL validation
  validateSearchUrl(url: string): { valid: boolean; platform?: SavedSearch['platform']; error?: string } {
    try {
      const urlObj = new URL(url);
      
      if (urlObj.hostname.includes('facebook.com') && urlObj.pathname.includes('marketplace')) {
        return { valid: true, platform: 'facebook' };
      }
      
      if (urlObj.hostname.includes('craigslist.org') && urlObj.pathname.includes('search')) {
        return { valid: true, platform: 'craigslist' };
      }
      
      if (urlObj.hostname.includes('offerup.com')) {
        return { valid: true, platform: 'offerup' };
      }
      
      return { valid: false, error: 'URL must be a marketplace search from Facebook, Craigslist, or OfferUp' };
    } catch {
      return { valid: false, error: 'Invalid URL format' };
    }
  }
}

export const savedSearchesManager = new SavedSearchesManager();