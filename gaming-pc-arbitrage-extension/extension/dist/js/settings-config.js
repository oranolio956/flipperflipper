// Settings Configuration v3.7.0 - Production Implementation
const defaultSettings = {
  version: '3.7.0',
  lastUpdated: new Date().toISOString(),
  
  general: {
    theme: 'light',
    language: 'en',
    currency: 'USD',
    notifications: {
      enabled: true,
      sound: true,
      desktop: true,
      dealAlerts: true,
      systemAlerts: true
    },
    startup: {
      openDashboard: true,
      runAutomation: false,
      checkUpdates: true
    },
    display: {
      compactMode: false,
      showPrices: true,
      use24HourTime: false,
      dateFormat: 'MM/DD/YYYY'
    }
  },
  
  search: {
    defaultFilters: {
      minPrice: 100,
      maxPrice: 5000,
      minROI: 20,
      radius: 25,
      conditions: ['working', 'like new', 'good'],
      excludeKeywords: [],
      requiredKeywords: []
    },
    automation: {
      enabled: false,
      interval: 30,
      maxConcurrentTabs: 3,
      respectRateLimit: true,
      rateLimitDelay: 5,
      retryFailedScans: true,
      maxRetries: 3
    },
    platforms: {
      facebook: {
        enabled: true,
        defaultSort: 'date',
        daysSinceListed: 7
      },
      craigslist: {
        enabled: true,
        defaultCity: '',
        hasImageOnly: true
      },
      offerup: {
        enabled: true,
        negotiableOnly: false
      }
    },
    savedSearches: []
  },
  
  pipeline: {
    stages: {
      autoAdvance: false,
      requireNotes: false,
      taskReminders: true
    },
    automation: {
      autoAdd: false,
      minROIThreshold: 30,
      maxDealsPerDay: 10,
      duplicateDetection: true
    },
    defaults: {
      priority: 'normal',
      tags: [],
      profitMargin: 0.2
    },
    archiving: {
      autoArchive: true,
      daysBeforeArchive: 90,
      keepArchiveMonths: 12
    }
  },
  
  privacy: {
    dataCollection: {
      analytics: false,
      crashReports: false,
      usageStats: false
    },
    storage: {
      encryption: false,
      autoBackup: true,
      backupLocation: 'local',
      clearDataOnUninstall: false
    },
    permissions: {
      shareAnalytics: false,
      allowExport: true,
      requirePassword: false
    },
    marketplace: {
      hidePersonalInfo: true,
      useProxy: false,
      randomizeTimings: true,
      userAgent: 'default'
    }
  },
  
  advanced: {
    developer: {
      debugMode: false,
      verboseLogging: false,
      showDevTools: false,
      experimentalFeatures: false
    },
    performance: {
      cacheEnabled: true,
      cacheSize: 50,
      imageLoading: 'lazy',
      maxStorageSize: 100,
      compressData: true
    },
    sync: {
      enabled: false,
      syncInterval: 60,
      syncItems: {
        settings: true,
        searches: true,
        pipeline: true,
        history: false
      }
    },
    api: {
      endpoint: '',
      apiKey: '',
      timeout: 30,
      maxRetries: 3
    }
  }
};

class SettingsConfigManager {
  static validateSettings(settings) {
    // Basic validation
    return typeof settings === 'object' && settings !== null;
  }
  
  static exportSettings(settings, options = {}) {
    const exportData = {
      version: chrome.runtime.getManifest().version,
      exportDate: new Date().toISOString(),
      settings: settings
    };
    
    if (options.format === 'base64') {
      return btoa(JSON.stringify(exportData));
    }
    
    return JSON.stringify(exportData, null, 2);
  }
  
  static importSettings(data) {
    try {
      let parsed;
      
      // Try base64 decode first
      try {
        parsed = JSON.parse(atob(data));
      } catch {
        parsed = JSON.parse(data);
      }
      
      if (this.validateSettings(parsed.settings)) {
        return parsed.settings;
      }
      
      throw new Error('Invalid settings format');
    } catch (error) {
      throw new Error(`Import failed: ${error.message}`);
    }
  }
  
  static mergeWithDefaults(partial) {
    return this.deepMerge(defaultSettings, partial);
  }
  
  static deepMerge(target, source) {
    const output = Object.assign({}, target);
    
    if (this.isObject(target) && this.isObject(source)) {
      Object.keys(source).forEach(key => {
        if (this.isObject(source[key])) {
          if (!(key in target)) {
            Object.assign(output, { [key]: source[key] });
          } else {
            output[key] = this.deepMerge(target[key], source[key]);
          }
        } else {
          Object.assign(output, { [key]: source[key] });
        }
      });
    }
    
    return output;
  }
  
  static isObject(item) {
    return item && typeof item === 'object' && !Array.isArray(item);
  }
  
  static applyTheme(theme) {
    if (theme === 'auto') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      theme = prefersDark ? 'dark' : 'light';
    }
    
    document.documentElement.setAttribute('data-theme', theme);
  }
  
  static formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  }
  
  static formatDate(date, format = 'MM/DD/YYYY', use24Hour = false) {
    const d = new Date(date);
    const options = {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour12: !use24Hour
    };
    
    return d.toLocaleString('en-US', options);
  }
}

// Make available globally
window.settingsConfig = {
  defaultSettings,
  SettingsConfigManager
};
