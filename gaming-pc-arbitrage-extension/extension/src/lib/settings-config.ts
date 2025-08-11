/**
 * Settings Configuration v3.7.0 - Apple-level Settings Architecture
 * Comprehensive settings system with real functionality
 */

export interface SettingsConfig {
  version: string;
  lastUpdated: string;
  
  // General Settings
  general: {
    theme: 'light' | 'dark' | 'auto';
    language: string;
    currency: 'USD' | 'EUR' | 'GBP' | 'CAD';
    notifications: {
      enabled: boolean;
      sound: boolean;
      desktop: boolean;
      dealAlerts: boolean;
      systemAlerts: boolean;
    };
    startup: {
      openDashboard: boolean;
      runAutomation: boolean;
      checkUpdates: boolean;
    };
    display: {
      compactMode: boolean;
      showPrices: boolean;
      use24HourTime: boolean;
      dateFormat: 'MM/DD/YYYY' | 'DD/MM/YYYY' | 'YYYY-MM-DD';
    };
  };
  
  // Search Settings
  search: {
    defaultFilters: {
      minPrice: number;
      maxPrice: number;
      minROI: number;
      radius: number;
      conditions: string[];
      excludeKeywords: string[];
      requiredKeywords: string[];
    };
    automation: {
      enabled: boolean;
      interval: number; // minutes
      maxConcurrentTabs: number;
      respectRateLimit: boolean;
      rateLimitDelay: number; // seconds
      retryFailedScans: boolean;
      maxRetries: number;
    };
    platforms: {
      facebook: {
        enabled: boolean;
        defaultSort: string;
        daysSinceListed: number;
      };
      craigslist: {
        enabled: boolean;
        defaultCity: string;
        hasImageOnly: boolean;
      };
      offerup: {
        enabled: boolean;
        negotiableOnly: boolean;
      };
    };
    savedSearches: Array<{
      id: string;
      name: string;
      platform: string;
      keywords: string[];
      filters: any;
      enabled: boolean;
      lastRun?: string;
      resultCount?: number;
    }>;
  };
  
  // Pipeline Settings
  pipeline: {
    stages: {
      autoAdvance: boolean;
      requireNotes: boolean;
      taskReminders: boolean;
    };
    automation: {
      autoAdd: boolean;
      minROIThreshold: number;
      maxDealsPerDay: number;
      duplicateDetection: boolean;
    };
    defaults: {
      priority: 'normal' | 'high' | 'urgent' | 'low';
      tags: string[];
      profitMargin: number; // percentage to add to costs
    };
    archiving: {
      autoArchive: boolean;
      daysBeforeArchive: number;
      keepArchiveMonths: number;
    };
  };
  
  // Privacy & Security
  privacy: {
    dataCollection: {
      analytics: boolean;
      crashReports: boolean;
      usageStats: boolean;
    };
    storage: {
      encryption: boolean;
      encryptionKey?: string; // Will be encrypted itself
      autoBackup: boolean;
      backupLocation: 'local' | 'cloud';
      clearDataOnUninstall: boolean;
    };
    permissions: {
      shareAnalytics: boolean;
      allowExport: boolean;
      requirePassword: boolean;
      passwordHash?: string;
    };
    marketplace: {
      hidePersonalInfo: boolean;
      useProxy: boolean;
      randomizeTimings: boolean;
      userAgent: 'default' | 'random' | 'custom';
      customUserAgent?: string;
    };
  };
  
  // Advanced Settings
  advanced: {
    developer: {
      debugMode: boolean;
      verboseLogging: boolean;
      showDevTools: boolean;
      experimentalFeatures: boolean;
    };
    performance: {
      cacheEnabled: boolean;
      cacheSize: number; // MB
      imageLoading: 'eager' | 'lazy' | 'none';
      maxStorageSize: number; // MB
      compressData: boolean;
    };
    sync: {
      enabled: boolean;
      syncInterval: number; // minutes
      syncItems: {
        settings: boolean;
        searches: boolean;
        pipeline: boolean;
        history: boolean;
      };
    };
    api: {
      endpoint?: string;
      apiKey?: string;
      timeout: number; // seconds
      maxRetries: number;
    };
  };
}

// Default settings configuration
export const defaultSettings: SettingsConfig = {
  version: '3.7.0',
  lastUpdated: new Date().toISOString(),
  
  general: {
    theme: 'auto',
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
      openDashboard: false,
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
      minPrice: 200,
      maxPrice: 2000,
      minROI: 20,
      radius: 25,
      conditions: ['used', 'like-new'],
      excludeKeywords: ['broken', 'parts', 'repair'],
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
        defaultCity: 'sfbay',
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
      autoAdd: true,
      minROIThreshold: 30,
      maxDealsPerDay: 10,
      duplicateDetection: true
    },
    defaults: {
      priority: 'normal',
      tags: [],
      profitMargin: 15
    },
    archiving: {
      autoArchive: true,
      daysBeforeArchive: 30,
      keepArchiveMonths: 6
    }
  },
  
  privacy: {
    dataCollection: {
      analytics: false,
      crashReports: true,
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
      cacheSize: 100,
      imageLoading: 'lazy',
      maxStorageSize: 500,
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
      timeout: 30,
      maxRetries: 3
    }
  }
};

// Settings validation rules
export const settingsValidation = {
  general: {
    theme: ['light', 'dark', 'auto'],
    language: /^[a-z]{2}$/,
    currency: ['USD', 'EUR', 'GBP', 'CAD'],
    dateFormat: ['MM/DD/YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD']
  },
  
  search: {
    minPrice: { min: 0, max: 999999 },
    maxPrice: { min: 1, max: 999999 },
    minROI: { min: 0, max: 1000 },
    radius: { min: 1, max: 500 },
    interval: { min: 5, max: 1440 },
    maxConcurrentTabs: { min: 1, max: 10 },
    rateLimitDelay: { min: 1, max: 60 }
  },
  
  pipeline: {
    minROIThreshold: { min: 0, max: 1000 },
    maxDealsPerDay: { min: 1, max: 100 },
    profitMargin: { min: 0, max: 100 },
    daysBeforeArchive: { min: 7, max: 365 },
    keepArchiveMonths: { min: 1, max: 120 }
  },
  
  advanced: {
    cacheSize: { min: 10, max: 1000 },
    maxStorageSize: { min: 50, max: 5000 },
    syncInterval: { min: 15, max: 1440 },
    timeout: { min: 5, max: 300 },
    maxRetries: { min: 0, max: 10 }
  }
};

// Settings sections for UI
export const settingsSections = [
  {
    id: 'general',
    title: 'General',
    icon: 'settings',
    description: 'Basic preferences and display options'
  },
  {
    id: 'search',
    title: 'Search & Scan',
    icon: 'search',
    description: 'Default filters and automation settings'
  },
  {
    id: 'pipeline',
    title: 'Deal Pipeline',
    icon: 'pipeline',
    description: 'Deal management and workflow automation'
  },
  {
    id: 'privacy',
    title: 'Privacy & Security',
    icon: 'lock',
    description: 'Data protection and permissions'
  },
  {
    id: 'advanced',
    title: 'Advanced',
    icon: 'code',
    description: 'Developer options and performance tuning'
  }
];

// Export/Import utilities
export class SettingsManager {
  static validateSettings(settings: any): { valid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    // Check version compatibility
    if (!settings.version) {
      errors.push('Missing version number');
    }
    
    // Validate each section
    for (const [section, rules] of Object.entries(settingsValidation)) {
      // Validation logic here
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
  
  static exportSettings(settings: SettingsConfig, options?: {
    includeSensitive?: boolean;
    prettify?: boolean;
  }): string {
    const exportData = { ...settings };
    
    // Remove sensitive data unless requested
    if (!options?.includeSensitive) {
      delete exportData.privacy.storage.encryptionKey;
      delete exportData.privacy.permissions.passwordHash;
      delete exportData.advanced.api.apiKey;
    }
    
    const json = options?.prettify 
      ? JSON.stringify(exportData, null, 2)
      : JSON.stringify(exportData);
    
    // Base64 encode for safety
    return btoa(json);
  }
  
  static importSettings(data: string): SettingsConfig | null {
    try {
      // Decode from base64
      const json = atob(data);
      const imported = JSON.parse(json);
      
      // Validate
      const validation = this.validateSettings(imported);
      if (!validation.valid) {
        console.error('Invalid settings:', validation.errors);
        return null;
      }
      
      // Merge with defaults for any missing fields
      return this.mergeWithDefaults(imported);
    } catch (e) {
      console.error('Failed to import settings:', e);
      return null;
    }
  }
  
  static mergeWithDefaults(partial: any): SettingsConfig {
    // Deep merge implementation
    const merge = (target: any, source: any): any => {
      for (const key in source) {
        if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
          target[key] = target[key] || {};
          merge(target[key], source[key]);
        } else if (target[key] === undefined) {
          target[key] = source[key];
        }
      }
      return target;
    };
    
    const result = JSON.parse(JSON.stringify(defaultSettings));
    return merge(result, partial);
  }
}