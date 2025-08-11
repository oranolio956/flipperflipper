// SettingsManager v3.5.0 - Centralized settings management
class SettingsManager {
  constructor() {
    this.settings = null;
    this.defaults = {
      general: {
        theme: 'auto',
        notifications: true,
        sound: true,
        language: 'en'
      },
      search: {
        defaultPlatform: 'all',
        minPrice: 0,
        maxPrice: 10000,
        radius: 25,
        sortBy: 'date',
        includeShipped: false
      },
      automation: {
        enabled: false,
        scanInterval: 30, // minutes
        maxConcurrentTabs: 3,
        autoClose: true,
        respectRateLimit: true
      },
      analysis: {
        profitThreshold: 20, // percentage
        includeShipping: true,
        taxRate: 0,
        feeRate: 10 // marketplace fees percentage
      },
      privacy: {
        saveHistory: true,
        clearOnExit: false,
        encryptStorage: false
      }
    };
    
    this.listeners = new Set();
    this.initialized = false;
  }
  
  // Initialize settings
  async init() {
    if (this.initialized) return this.settings;
    
    try {
      // Load from storage
      const stored = await chrome.storage.local.get(['settings']);
      
      if (stored.settings) {
        // Merge with defaults to ensure all keys exist
        this.settings = this.mergeDeep(this.defaults, stored.settings);
      } else {
        // First time - use defaults
        this.settings = { ...this.defaults };
        await this.save();
      }
      
      this.initialized = true;
      this.notifyListeners('init', this.settings);
      
      return this.settings;
    } catch (error) {
      console.error('[Settings] Failed to initialize:', error);
      this.settings = { ...this.defaults };
      return this.settings;
    }
  }
  
  // Get all settings or specific path
  get(path) {
    if (!this.initialized) {
      console.warn('[Settings] Accessing settings before initialization');
      return path ? this.getByPath(this.defaults, path) : this.defaults;
    }
    
    if (!path) return { ...this.settings };
    
    return this.getByPath(this.settings, path);
  }
  
  // Update settings
  async update(path, value) {
    if (!this.initialized) await this.init();
    
    const oldValue = this.getByPath(this.settings, path);
    this.setByPath(this.settings, path, value);
    
    await this.save();
    
    this.notifyListeners('update', {
      path,
      oldValue,
      newValue: value,
      settings: this.settings
    });
    
    return this.settings;
  }
  
  // Update multiple settings
  async updateMultiple(updates) {
    if (!this.initialized) await this.init();
    
    const changes = [];
    
    Object.entries(updates).forEach(([path, value]) => {
      const oldValue = this.getByPath(this.settings, path);
      this.setByPath(this.settings, path, value);
      changes.push({ path, oldValue, newValue: value });
    });
    
    await this.save();
    
    this.notifyListeners('updateMultiple', {
      changes,
      settings: this.settings
    });
    
    return this.settings;
  }
  
  // Reset to defaults
  async reset(path) {
    if (!this.initialized) await this.init();
    
    if (path) {
      const defaultValue = this.getByPath(this.defaults, path);
      await this.update(path, defaultValue);
    } else {
      this.settings = { ...this.defaults };
      await this.save();
      this.notifyListeners('reset', this.settings);
    }
    
    return this.settings;
  }
  
  // Save to storage
  async save() {
    try {
      await chrome.storage.local.set({ settings: this.settings });
      return true;
    } catch (error) {
      console.error('[Settings] Failed to save:', error);
      return false;
    }
  }
  
  // Add listener
  subscribe(callback) {
    this.listeners.add(callback);
    
    // Return unsubscribe function
    return () => {
      this.listeners.delete(callback);
    };
  }
  
  // Notify listeners
  notifyListeners(event, data) {
    this.listeners.forEach(callback => {
      try {
        callback(event, data);
      } catch (error) {
        console.error('[Settings] Listener error:', error);
      }
    });
  }
  
  // Helper: Get value by path
  getByPath(obj, path) {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  }
  
  // Helper: Set value by path
  setByPath(obj, path, value) {
    const keys = path.split('.');
    const lastKey = keys.pop();
    
    const target = keys.reduce((current, key) => {
      if (!current[key]) current[key] = {};
      return current[key];
    }, obj);
    
    target[lastKey] = value;
  }
  
  // Helper: Deep merge objects
  mergeDeep(target, source) {
    const output = { ...target };
    
    if (this.isObject(target) && this.isObject(source)) {
      Object.keys(source).forEach(key => {
        if (this.isObject(source[key])) {
          if (!(key in target)) {
            Object.assign(output, { [key]: source[key] });
          } else {
            output[key] = this.mergeDeep(target[key], source[key]);
          }
        } else {
          Object.assign(output, { [key]: source[key] });
        }
      });
    }
    
    return output;
  }
  
  // Helper: Check if object
  isObject(item) {
    return item && typeof item === 'object' && !Array.isArray(item);
  }
  
  // Export settings
  async export() {
    if (!this.initialized) await this.init();
    
    return {
      version: chrome.runtime.getManifest().version,
      timestamp: new Date().toISOString(),
      settings: this.settings
    };
  }
  
  // Import settings
  async import(data) {
    if (!data || !data.settings) {
      throw new Error('Invalid import data');
    }
    
    this.settings = this.mergeDeep(this.defaults, data.settings);
    await this.save();
    
    this.notifyListeners('import', this.settings);
    return this.settings;
  }
  
  // Validate setting value
  validate(path, value) {
    // Add validation rules as needed
    const validations = {
      'general.theme': ['auto', 'light', 'dark'],
      'search.radius': (v) => v >= 1 && v <= 500,
      'automation.scanInterval': (v) => v >= 5 && v <= 1440,
      'automation.maxConcurrentTabs': (v) => v >= 1 && v <= 10,
      'analysis.profitThreshold': (v) => v >= 0 && v <= 1000,
      'analysis.taxRate': (v) => v >= 0 && v <= 100,
      'analysis.feeRate': (v) => v >= 0 && v <= 100
    };
    
    const rule = validations[path];
    
    if (!rule) return true;
    
    if (Array.isArray(rule)) {
      return rule.includes(value);
    }
    
    if (typeof rule === 'function') {
      return rule(value);
    }
    
    return true;
  }
}

// Create singleton instance
window.settingsManager = new SettingsManager();