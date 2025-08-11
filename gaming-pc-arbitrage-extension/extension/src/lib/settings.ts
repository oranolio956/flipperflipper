/**
 * Settings Manager - Apple-grade state management
 * All settings persist and drive real behavior changes
 */

export interface Settings {
  version: string;
  
  // Automation settings that control Max Auto behavior
  automation: {
    enabled: boolean;
    scanInterval: number; // minutes
    maxConcurrentTabs: number;
    pauseDuringActive: boolean;
    retryAttempts: number;
    retryDelay: number; // seconds
  };
  
  // Search configuration
  search: {
    savedSearches: Array<{
      id: string;
      name: string;
      url: string;
      enabled: boolean;
      interval: number; // minutes, can override global
      lastRun?: string;
      nextRun?: string;
      filters?: {
        minPrice?: number;
        maxPrice?: number;
        keywords?: string[];
        excludeKeywords?: string[];
      };
    }>;
    defaultFilters: {
      minPrice: number;
      maxPrice: number;
      minROI: number;
      maxDistance: number;
    };
  };
  
  // Pricing & valuation
  pricing: {
    defaultMarkup: number; // percentage
    includeShipping: boolean;
    includeFees: boolean;
    marketplaceFees: {
      facebook: number;
      craigslist: number;
      offerup: number;
    };
    pricingStrategy: 'aggressive' | 'moderate' | 'conservative';
  };
  
  // Notifications
  notifications: {
    enabled: boolean;
    sound: boolean;
    desktop: boolean;
    triggers: {
      newDeal: boolean;
      priceChange: boolean;
      autoScanComplete: boolean;
      errors: boolean;
    };
    quietHours: {
      enabled: boolean;
      start: string; // HH:MM
      end: string; // HH:MM
    };
  };
  
  // Display preferences
  display: {
    theme: 'light' | 'dark' | 'auto';
    compactMode: boolean;
    showAdvancedFeatures: boolean;
    defaultView: 'dashboard' | 'pipeline' | 'scanner';
  };
  
  // Privacy & data
  privacy: {
    analytics: boolean;
    crashReports: boolean;
    shareUsageData: boolean;
    dataRetention: number; // days
    autoBackup: boolean;
  };
  
  // Performance
  performance: {
    enablePrefetch: boolean;
    cacheLifetime: number; // minutes
    maxStorageSize: number; // MB
    throttleRequests: boolean;
  };
  
  // Developer options
  developer: {
    enabled: boolean;
    debugMode: boolean;
    logLevel: 'error' | 'warn' | 'info' | 'debug';
    showPerformanceMetrics: boolean;
  };
}

// Default settings with sensible values
export const DEFAULT_SETTINGS: Settings = {
  version: '3.2.0',
  
  automation: {
    enabled: false,
    scanInterval: 30,
    maxConcurrentTabs: 3,
    pauseDuringActive: true,
    retryAttempts: 3,
    retryDelay: 5
  },
  
  search: {
    savedSearches: [],
    defaultFilters: {
      minPrice: 100,
      maxPrice: 2000,
      minROI: 20,
      maxDistance: 25
    }
  },
  
  pricing: {
    defaultMarkup: 25,
    includeShipping: true,
    includeFees: true,
    marketplaceFees: {
      facebook: 5,
      craigslist: 0,
      offerup: 9.9
    },
    pricingStrategy: 'moderate'
  },
  
  notifications: {
    enabled: true,
    sound: false,
    desktop: true,
    triggers: {
      newDeal: true,
      priceChange: true,
      autoScanComplete: false,
      errors: true
    },
    quietHours: {
      enabled: false,
      start: '22:00',
      end: '08:00'
    }
  },
  
  display: {
    theme: 'auto',
    compactMode: false,
    showAdvancedFeatures: false,
    defaultView: 'dashboard'
  },
  
  privacy: {
    analytics: true,
    crashReports: true,
    shareUsageData: false,
    dataRetention: 90,
    autoBackup: true
  },
  
  performance: {
    enablePrefetch: true,
    cacheLifetime: 30,
    maxStorageSize: 100,
    throttleRequests: true
  },
  
  developer: {
    enabled: false,
    debugMode: false,
    logLevel: 'warn',
    showPerformanceMetrics: false
  }
};

/**
 * Settings Manager - Singleton for consistent state
 */
export class SettingsManager {
  private static instance: SettingsManager;
  private settings: Settings = DEFAULT_SETTINGS;
  private listeners: Set<(settings: Settings) => void> = new Set();
  private saveDebounceTimer: number | null = null;
  
  private constructor() {
    this.initialize();
  }
  
  static getInstance(): SettingsManager {
    if (!SettingsManager.instance) {
      SettingsManager.instance = new SettingsManager();
    }
    return SettingsManager.instance;
  }
  
  private async initialize() {
    // Load settings from storage
    await this.load();
    
    // Listen for changes from other parts of the extension
    chrome.storage.onChanged.addListener((changes, area) => {
      if (area === 'local' && changes.settings) {
        this.settings = changes.settings.newValue || DEFAULT_SETTINGS;
        this.notifyListeners();
      }
    });
  }
  
  async load(): Promise<Settings> {
    try {
      const { settings } = await chrome.storage.local.get(['settings']);
      
      if (settings) {
        // Merge with defaults to handle new properties
        this.settings = this.mergeWithDefaults(settings);
      } else {
        // First run - save defaults
        await this.save();
      }
      
      return this.settings;
    } catch (error) {
      console.error('Failed to load settings:', error);
      return this.settings;
    }
  }
  
  private mergeWithDefaults(saved: Partial<Settings>): Settings {
    // Deep merge to preserve user settings while adding new defaults
    const merged = JSON.parse(JSON.stringify(DEFAULT_SETTINGS));
    
    const deepMerge = (target: any, source: any) => {
      for (const key in source) {
        if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
          target[key] = target[key] || {};
          deepMerge(target[key], source[key]);
        } else {
          target[key] = source[key];
        }
      }
    };
    
    deepMerge(merged, saved);
    merged.version = DEFAULT_SETTINGS.version; // Always update version
    
    return merged;
  }
  
  async save(immediate = false): Promise<void> {
    if (!immediate && this.saveDebounceTimer) {
      clearTimeout(this.saveDebounceTimer);
    }
    
    const doSave = async () => {
      try {
        await chrome.storage.local.set({ settings: this.settings });
        
        // Notify background script of changes
        chrome.runtime.sendMessage({
          action: 'SETTINGS_UPDATED',
          data: this.settings
        });
        
      } catch (error) {
        console.error('Failed to save settings:', error);
        throw error;
      }
    };
    
    if (immediate) {
      await doSave();
    } else {
      // Debounce saves to prevent excessive writes
      this.saveDebounceTimer = window.setTimeout(() => {
        doSave();
        this.saveDebounceTimer = null;
      }, 500);
    }
  }
  
  get(): Settings {
    return JSON.parse(JSON.stringify(this.settings)); // Return copy
  }
  
  async update(updates: Partial<Settings>): Promise<void> {
    const deepMerge = (target: any, source: any) => {
      for (const key in source) {
        if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
          target[key] = target[key] || {};
          deepMerge(target[key], source[key]);
        } else {
          target[key] = source[key];
        }
      }
    };
    
    deepMerge(this.settings, updates);
    this.notifyListeners();
    await this.save();
  }
  
  async reset(section?: keyof Settings): Promise<void> {
    if (section) {
      // Reset specific section
      this.settings[section] = JSON.parse(JSON.stringify(DEFAULT_SETTINGS[section]));
    } else {
      // Reset all settings
      this.settings = JSON.parse(JSON.stringify(DEFAULT_SETTINGS));
    }
    
    this.notifyListeners();
    await this.save(true); // Save immediately for reset
  }
  
  subscribe(listener: (settings: Settings) => void): () => void {
    this.listeners.add(listener);
    // Immediately call with current settings
    listener(this.get());
    
    // Return unsubscribe function
    return () => {
      this.listeners.delete(listener);
    };
  }
  
  private notifyListeners() {
    const current = this.get();
    this.listeners.forEach(listener => {
      try {
        listener(current);
      } catch (error) {
        console.error('Settings listener error:', error);
      }
    });
  }
  
  // Helper methods for common operations
  
  async enableAutomation(enabled: boolean): Promise<void> {
    await this.update({
      automation: { ...this.settings.automation, enabled }
    });
  }
  
  async addSavedSearch(search: Omit<Settings['search']['savedSearches'][0], 'id'>): Promise<void> {
    const newSearch = {
      ...search,
      id: `search_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    };
    
    const savedSearches = [...this.settings.search.savedSearches, newSearch];
    await this.update({
      search: { ...this.settings.search, savedSearches }
    });
  }
  
  async removeSavedSearch(id: string): Promise<void> {
    const savedSearches = this.settings.search.savedSearches.filter(s => s.id !== id);
    await this.update({
      search: { ...this.settings.search, savedSearches }
    });
  }
  
  async updateSavedSearch(id: string, updates: Partial<Settings['search']['savedSearches'][0]>): Promise<void> {
    const savedSearches = this.settings.search.savedSearches.map(search =>
      search.id === id ? { ...search, ...updates } : search
    );
    
    await this.update({
      search: { ...this.settings.search, savedSearches }
    });
  }
  
  // Export/Import functionality
  
  async export(): Promise<string> {
    const data = {
      settings: this.settings,
      exportDate: new Date().toISOString(),
      version: chrome.runtime.getManifest().version
    };
    
    return JSON.stringify(data, null, 2);
  }
  
  async import(jsonData: string): Promise<void> {
    try {
      const data = JSON.parse(jsonData);
      
      if (!data.settings) {
        throw new Error('Invalid settings file');
      }
      
      // Validate and merge with defaults
      this.settings = this.mergeWithDefaults(data.settings);
      this.notifyListeners();
      await this.save(true);
      
    } catch (error) {
      console.error('Failed to import settings:', error);
      throw new Error('Invalid settings file format');
    }
  }
}

// Export singleton instance
export const settingsManager = SettingsManager.getInstance();