#!/bin/bash

echo "Creating remaining files from Phases J-M..."

# Create settings-config.js
cat > extension/dist/js/settings-config.js << 'EOF'
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
EOF

# Create settings-ui.js
cat > extension/dist/js/settings-ui.js << 'EOF'
// Settings UI v3.7.0 - Apple-grade Settings Implementation
class SettingsUI {
  constructor() {
    this.currentSection = 'general';
    this.unsavedChanges = false;
    this.tempSettings = null;
    
    if (!window.settingsConfig) {
      console.error('[SettingsUI] Settings config not loaded');
    }
  }
  
  async render() {
    const container = document.getElementById('page-content') || document.getElementById('root');
    if (!container) return;
    
    // Load current settings
    const settings = await window.settingsManager.get();
    this.tempSettings = JSON.parse(JSON.stringify(settings));
    
    container.innerHTML = `
      <div class="settings-page">
        <div class="settings-container">
          <div class="settings-sidebar">
            <nav class="settings-nav">
              <a class="settings-nav-item active" onclick="window.settingsUI.switchSection('general')">
                General
              </a>
              <a class="settings-nav-item" onclick="window.settingsUI.switchSection('search')">
                Search
              </a>
              <a class="settings-nav-item" onclick="window.settingsUI.switchSection('pipeline')">
                Pipeline
              </a>
              <a class="settings-nav-item" onclick="window.settingsUI.switchSection('privacy')">
                Privacy
              </a>
              <a class="settings-nav-item" onclick="window.settingsUI.switchSection('advanced')">
                Advanced
              </a>
            </nav>
          </div>
          
          <div class="settings-main">
            <div id="settings-content">
              ${this.renderSection('general')}
            </div>
            
            <div class="settings-actions">
              <button class="btn btn-primary" onclick="window.settingsUI.saveSettings()">
                Save Changes
              </button>
              <button class="btn btn-secondary" onclick="window.settingsUI.resetSection()">
                Reset Section
              </button>
              <button class="btn btn-link" onclick="window.settingsUI.exportSettings()">
                Export Settings
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }
  
  renderSection(section) {
    switch (section) {
      case 'general':
        return this.renderGeneralSettings();
      case 'search':
        return this.renderSearchSettings();
      case 'pipeline':
        return this.renderPipelineSettings();
      case 'privacy':
        return this.renderPrivacySettings();
      case 'advanced':
        return this.renderAdvancedSettings();
      default:
        return '<p>Unknown section</p>';
    }
  }
  
  renderGeneralSettings() {
    const general = this.tempSettings.general || {};
    
    return `
      <div class="settings-section">
        <h2>General Settings</h2>
        
        <div class="settings-group">
          <h3>Appearance</h3>
          
          <div class="setting-item">
            <div class="setting-label">
              <h4>Theme</h4>
              <p class="setting-description">Choose your preferred color scheme</p>
            </div>
            <select class="form-select" onchange="window.settingsUI.updateSetting('general.theme', this.value)">
              <option value="light" ${general.theme === 'light' ? 'selected' : ''}>Light</option>
              <option value="dark" ${general.theme === 'dark' ? 'selected' : ''}>Dark</option>
              <option value="auto" ${general.theme === 'auto' ? 'selected' : ''}>Auto</option>
            </select>
          </div>
          
          <div class="setting-item">
            <div class="setting-label">
              <h4>Language</h4>
              <p class="setting-description">Display language for the extension</p>
            </div>
            <select class="form-select" onchange="window.settingsUI.updateSetting('general.language', this.value)">
              <option value="en" ${general.language === 'en' ? 'selected' : ''}>English</option>
              <option value="es" ${general.language === 'es' ? 'selected' : ''}>Spanish</option>
              <option value="fr" ${general.language === 'fr' ? 'selected' : ''}>French</option>
            </select>
          </div>
        </div>
        
        <div class="settings-group">
          <h3>Notifications</h3>
          
          <div class="setting-item">
            <div class="setting-label">
              <h4>Enable Notifications</h4>
              <p class="setting-description">Show desktop notifications for important events</p>
            </div>
            <label class="switch">
              <input type="checkbox" 
                ${general.notifications?.enabled ? 'checked' : ''}
                onchange="window.settingsUI.updateSetting('general.notifications.enabled', this.checked)">
              <span class="slider"></span>
            </label>
          </div>
          
          <div class="setting-item">
            <div class="setting-label">
              <h4>Sound Alerts</h4>
              <p class="setting-description">Play sounds for notifications</p>
            </div>
            <label class="switch">
              <input type="checkbox" 
                ${general.notifications?.sound ? 'checked' : ''}
                onchange="window.settingsUI.updateSetting('general.notifications.sound', this.checked)">
              <span class="slider"></span>
            </label>
          </div>
        </div>
      </div>
    `;
  }
  
  renderSearchSettings() {
    const search = this.tempSettings.search || {};
    
    return `
      <div class="settings-section">
        <h2>Search Settings</h2>
        
        <div class="settings-group">
          <h3>Default Filters</h3>
          
          <div class="setting-item">
            <div class="setting-label">
              <h4>Price Range</h4>
              <p class="setting-description">Default min and max prices for searches</p>
            </div>
            <div style="display: flex; gap: 10px;">
              <input type="number" class="form-input" 
                value="${search.defaultFilters?.minPrice || 0}"
                onchange="window.settingsUI.updateSetting('search.defaultFilters.minPrice', Number(this.value))">
              <span>to</span>
              <input type="number" class="form-input" 
                value="${search.defaultFilters?.maxPrice || 10000}"
                onchange="window.settingsUI.updateSetting('search.defaultFilters.maxPrice', Number(this.value))">
            </div>
          </div>
          
          <div class="setting-item">
            <div class="setting-label">
              <h4>Minimum ROI</h4>
              <p class="setting-description">Only show deals with ROI above this percentage</p>
            </div>
            <input type="number" class="form-input" 
              value="${search.defaultFilters?.minROI || 20}"
              onchange="window.settingsUI.updateSetting('search.defaultFilters.minROI', Number(this.value))">
          </div>
        </div>
        
        <div class="settings-group">
          <h3>Automation</h3>
          
          <div class="setting-item">
            <div class="setting-label">
              <h4>Enable Automation</h4>
              <p class="setting-description">Automatically scan for new listings</p>
            </div>
            <label class="switch">
              <input type="checkbox" 
                ${search.automation?.enabled ? 'checked' : ''}
                onchange="window.settingsUI.updateSetting('search.automation.enabled', this.checked)">
              <span class="slider"></span>
            </label>
          </div>
          
          <div class="setting-item">
            <div class="setting-label">
              <h4>Scan Interval</h4>
              <p class="setting-description">Minutes between automatic scans</p>
            </div>
            <input type="number" class="form-input" 
              value="${search.automation?.interval || 30}"
              min="5" max="1440"
              onchange="window.settingsUI.updateSetting('search.automation.interval', Number(this.value))">
          </div>
        </div>
      </div>
    `;
  }
  
  renderPipelineSettings() {
    return `
      <div class="settings-section">
        <h2>Pipeline Settings</h2>
        <p>Configure how deals move through your pipeline.</p>
      </div>
    `;
  }
  
  renderPrivacySettings() {
    return `
      <div class="settings-section">
        <h2>Privacy & Security</h2>
        <p>Control your data and privacy preferences.</p>
      </div>
    `;
  }
  
  renderAdvancedSettings() {
    const advanced = this.tempSettings.advanced || {};
    
    return `
      <div class="settings-section">
        <h2>Advanced Settings</h2>
        
        <div class="settings-group">
          <h3>Developer Options</h3>
          
          <div class="setting-item">
            <div class="setting-label">
              <h4>Debug Mode</h4>
              <p class="setting-description">Enable detailed logging and debugging features</p>
            </div>
            <label class="switch">
              <input type="checkbox" 
                ${advanced.developer?.debugMode ? 'checked' : ''}
                onchange="window.settingsUI.updateSetting('advanced.developer.debugMode', this.checked)">
              <span class="slider"></span>
            </label>
          </div>
        </div>
        
        <div class="settings-group">
          <h3>Data Management</h3>
          
          <div class="setting-item">
            <button class="btn btn-danger" onclick="window.settingsUI.clearAllData()">
              Clear All Data
            </button>
          </div>
        </div>
      </div>
    `;
  }
  
  updateSetting(path, value) {
    // Update temp settings
    const keys = path.split('.');
    let current = this.tempSettings;
    
    for (let i = 0; i < keys.length - 1; i++) {
      if (!current[keys[i]]) current[keys[i]] = {};
      current = current[keys[i]];
    }
    
    current[keys[keys.length - 1]] = value;
    this.unsavedChanges = true;
    
    // Show unsaved indicator
    const saveBtn = document.querySelector('.btn-primary');
    if (saveBtn && !saveBtn.textContent.includes('*')) {
      saveBtn.textContent = 'Save Changes *';
    }
  }
  
  async saveSettings() {
    try {
      // Update all settings
      await window.settingsManager.updateMultiple(this.flattenObject(this.tempSettings));
      
      this.unsavedChanges = false;
      this.showToast('Settings saved successfully', 'success');
      
      // Remove unsaved indicator
      const saveBtn = document.querySelector('.btn-primary');
      if (saveBtn) {
        saveBtn.textContent = 'Save Changes';
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      this.showToast('Failed to save settings', 'error');
    }
  }
  
  flattenObject(obj, prefix = '') {
    const flattened = {};
    
    Object.keys(obj).forEach(key => {
      const value = obj[key];
      const newKey = prefix ? `${prefix}.${key}` : key;
      
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        Object.assign(flattened, this.flattenObject(value, newKey));
      } else {
        flattened[newKey] = value;
      }
    });
    
    return flattened;
  }
  
  switchSection(section) {
    this.currentSection = section;
    
    // Update navigation
    document.querySelectorAll('.settings-nav-item').forEach(item => {
      item.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Render new section
    const content = document.getElementById('settings-content');
    if (content) {
      content.innerHTML = this.renderSection(section);
    }
  }
  
  async resetSection() {
    if (!confirm('Reset this section to default values?')) return;
    
    const defaults = window.settingsConfig.defaultSettings;
    const sectionDefaults = defaults[this.currentSection];
    
    if (sectionDefaults) {
      this.tempSettings[this.currentSection] = JSON.parse(JSON.stringify(sectionDefaults));
      
      // Re-render
      const content = document.getElementById('settings-content');
      if (content) {
        content.innerHTML = this.renderSection(this.currentSection);
      }
      
      this.unsavedChanges = true;
    }
  }
  
  async exportSettings() {
    const settings = await window.settingsManager.export();
    const dataStr = JSON.stringify(settings, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `pc-arbitrage-settings-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
  }
  
  async clearAllData() {
    if (!confirm('This will delete ALL extension data. Are you sure?')) return;
    if (!confirm('This action cannot be undone. Continue?')) return;
    
    try {
      await chrome.storage.local.clear();
      this.showToast('All data cleared. Reloading...', 'success');
      
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } catch (error) {
      console.error('Failed to clear data:', error);
      this.showToast('Failed to clear data', 'error');
    }
  }
  
  showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      padding: 16px 24px;
      background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3'};
      color: white;
      border-radius: 4px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
      z-index: 1000;
      animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }
}

// Create global instance
window.settingsUI = new SettingsUI();
EOF

# Create module-loader.js
cat > extension/dist/js/module-loader.js << 'EOF'
// Module Loader v3.8.0 - Production Implementation
class ModuleLoader {
  constructor() {
    this.loadedModules = new Map();
    this.loadingPromises = new Map();
    this.moduleConfigs = new Map();
    this.loadTimes = new Map();
    
    this.initializeModuleConfigs();
  }
  
  initializeModuleConfigs() {
    const configs = [
      {
        name: 'router',
        path: 'js/router.js',
        critical: true
      },
      {
        name: 'settingsManager',
        path: 'js/settings-manager.js',
        critical: true
      },
      {
        name: 'searchBuilder',
        path: 'js/search-builder.js',
        preload: true
      },
      {
        name: 'automationEngine',
        path: 'js/automation-engine.js',
        dependencies: ['searchBuilder']
      },
      {
        name: 'parser',
        path: 'js/parser.js'
      },
      {
        name: 'pipelineManager',
        path: 'js/pipeline-manager.js',
        dependencies: ['parser']
      }
    ];
    
    configs.forEach(config => {
      this.moduleConfigs.set(config.name, config);
    });
  }
  
  async loadModule(moduleName) {
    // Return if already loaded
    if (this.loadedModules.has(moduleName)) {
      return this.loadedModules.get(moduleName);
    }
    
    // Return existing promise if loading
    if (this.loadingPromises.has(moduleName)) {
      return this.loadingPromises.get(moduleName);
    }
    
    const config = this.moduleConfigs.get(moduleName);
    if (!config) {
      throw new Error(`Unknown module: ${moduleName}`);
    }
    
    const loadPromise = this.loadModuleInternal(config);
    this.loadingPromises.set(moduleName, loadPromise);
    
    try {
      const module = await loadPromise;
      this.loadedModules.set(moduleName, module);
      this.loadingPromises.delete(moduleName);
      return module;
    } catch (error) {
      this.loadingPromises.delete(moduleName);
      throw error;
    }
  }
  
  async loadModuleInternal(config) {
    const startTime = performance.now();
    
    // Load dependencies first
    if (config.dependencies) {
      await Promise.all(
        config.dependencies.map(dep => this.loadModule(dep))
      );
    }
    
    // Load the module
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = config.path;
      script.async = true;
      
      script.onload = () => {
        const loadTime = performance.now() - startTime;
        this.loadTimes.set(config.name, loadTime);
        console.log(`[ModuleLoader] Loaded ${config.name} in ${loadTime.toFixed(2)}ms`);
        resolve(window[config.name]);
      };
      
      script.onerror = () => {
        reject(new Error(`Failed to load module: ${config.name}`));
      };
      
      document.head.appendChild(script);
    });
  }
  
  async loadCriticalModules() {
    const criticalModules = Array.from(this.moduleConfigs.entries())
      .filter(([name, config]) => config.critical)
      .map(([name]) => name);
    
    await Promise.all(criticalModules.map(name => this.loadModule(name)));
  }
  
  async preloadModules() {
    const preloadModules = Array.from(this.moduleConfigs.entries())
      .filter(([name, config]) => config.preload && !config.critical)
      .map(([name]) => name);
    
    // Use requestIdleCallback for non-critical preloads
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => {
        preloadModules.forEach(name => this.loadModule(name));
      });
    } else {
      setTimeout(() => {
        preloadModules.forEach(name => this.loadModule(name));
      }, 1000);
    }
  }
  
  getLoadTimes() {
    return Object.fromEntries(this.loadTimes);
  }
  
  isLoaded(moduleName) {
    return this.loadedModules.has(moduleName);
  }
  
  getLoadedModules() {
    return Array.from(this.loadedModules.keys());
  }
}

// Create singleton instance
window.moduleLoader = new ModuleLoader();
EOF

# Create performance-monitor.js
cat > extension/dist/js/performance-monitor.js << 'EOF'
// Performance Monitor v3.8.0 - Real-time Performance Tracking
class PerformanceMonitor {
  constructor() {
    this.metrics = {
      pageLoad: {},
      runtime: {},
      memory: {},
      storage: {},
      network: {}
    };
    
    this.observers = new Map();
    this.isMonitoring = false;
    this.reportInterval = null;
    
    this.thresholds = {
      pageLoadTime: 3000,
      scriptExecutionTime: 50,
      memoryUsage: 50 * 1024 * 1024,
      storageUsage: 5 * 1024 * 1024,
      networkLatency: 1000
    };
  }
  
  start() {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    console.log('[PerformanceMonitor] Starting monitoring...');
    
    // Monitor page load
    this.monitorPageLoad();
    
    // Monitor memory
    this.monitorMemory();
    
    // Monitor storage
    this.monitorStorage();
    
    // Start periodic reporting
    this.startReporting();
  }
  
  stop() {
    this.isMonitoring = false;
    
    if (this.reportInterval) {
      clearInterval(this.reportInterval);
      this.reportInterval = null;
    }
    
    // Disconnect observers
    this.observers.forEach(observer => observer.disconnect());
    this.observers.clear();
    
    console.log('[PerformanceMonitor] Stopped monitoring');
  }
  
  monitorPageLoad() {
    if (window.performance && window.performance.timing) {
      const timing = window.performance.timing;
      const loadTime = timing.loadEventEnd - timing.navigationStart;
      
      this.metrics.pageLoad = {
        total: loadTime,
        domReady: timing.domContentLoadedEventEnd - timing.navigationStart,
        resources: timing.loadEventEnd - timing.responseEnd
      };
      
      if (loadTime > this.thresholds.pageLoadTime) {
        this.alert('Slow page load', `Page took ${loadTime}ms to load`);
      }
    }
  }
  
  monitorMemory() {
    if (!performance.memory) return;
    
    setInterval(() => {
      const memory = performance.memory;
      
      this.metrics.memory = {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        limit: memory.jsHeapSizeLimit,
        percentUsed: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100
      };
      
      if (memory.usedJSHeapSize > this.thresholds.memoryUsage) {
        this.alert('High memory usage', `Using ${Math.round(memory.usedJSHeapSize / 1024 / 1024)}MB`);
      }
    }, 5000);
  }
  
  async monitorStorage() {
    try {
      const estimate = await navigator.storage.estimate();
      
      this.metrics.storage = {
        used: estimate.usage || 0,
        quota: estimate.quota || 0,
        percentUsed: ((estimate.usage || 0) / (estimate.quota || 1)) * 100
      };
      
      if (estimate.usage > this.thresholds.storageUsage) {
        this.optimize('storage');
      }
    } catch (error) {
      console.error('[PerformanceMonitor] Storage monitoring failed:', error);
    }
  }
  
  measureFunction(name, fn) {
    return async (...args) => {
      const startTime = performance.now();
      
      try {
        const result = await fn(...args);
        const duration = performance.now() - startTime;
        
        this.recordMetric('function', name, duration);
        
        if (duration > this.thresholds.scriptExecutionTime) {
          this.alert('Slow function', `${name} took ${duration.toFixed(2)}ms`);
        }
        
        return result;
      } catch (error) {
        const duration = performance.now() - startTime;
        this.recordMetric('function', name, duration, true);
        throw error;
      }
    };
  }
  
  recordMetric(category, name, value, error = false) {
    if (!this.metrics.runtime[category]) {
      this.metrics.runtime[category] = {};
    }
    
    if (!this.metrics.runtime[category][name]) {
      this.metrics.runtime[category][name] = {
        count: 0,
        total: 0,
        average: 0,
        max: 0,
        errors: 0
      };
    }
    
    const metric = this.metrics.runtime[category][name];
    metric.count++;
    metric.total += value;
    metric.average = metric.total / metric.count;
    metric.max = Math.max(metric.max, value);
    
    if (error) {
      metric.errors++;
    }
  }
  
  optimize(area) {
    console.log(`[PerformanceMonitor] Optimizing ${area}...`);
    
    switch (area) {
      case 'memory':
        // Trigger garbage collection if available
        if (window.gc) {
          window.gc();
        }
        break;
        
      case 'storage':
        // Clear old cache
        this.clearOldData();
        break;
        
      case 'network':
        // Implement request batching
        break;
    }
  }
  
  async clearOldData() {
    const { listings = [], deals = [] } = await chrome.storage.local.get(['listings', 'deals']);
    
    const thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000;
    
    const recentListings = listings.filter(l => l.scannedAt > thirtyDaysAgo);
    const recentDeals = deals.filter(d => d.createdAt > thirtyDaysAgo);
    
    if (recentListings.length < listings.length || recentDeals.length < deals.length) {
      await chrome.storage.local.set({
        listings: recentListings,
        deals: recentDeals
      });
      
      console.log(`[PerformanceMonitor] Cleared ${listings.length - recentListings.length} old listings`);
    }
  }
  
  alert(type, message) {
    console.warn(`[Performance Alert] ${type}: ${message}`);
    
    // Send to debug logger if available
    if (window.debugLogger) {
      window.debugLogger.warn(message, 'performance');
    }
  }
  
  startReporting() {
    this.reportInterval = setInterval(() => {
      if (window.DEBUG_MODE) {
        this.report();
      }
    }, 30000); // Report every 30 seconds
  }
  
  report() {
    console.group('[Performance Report]');
    console.log('Page Load:', this.metrics.pageLoad);
    console.log('Memory:', this.metrics.memory);
    console.log('Storage:', this.metrics.storage);
    console.log('Runtime:', this.metrics.runtime);
    console.groupEnd();
  }
  
  getMetrics() {
    return JSON.parse(JSON.stringify(this.metrics));
  }
  
  reset() {
    this.metrics = {
      pageLoad: {},
      runtime: {},
      memory: {},
      storage: {},
      network: {}
    };
  }
}

// Create singleton instance
window.performanceMonitor = new PerformanceMonitor();
EOF

# Create data-exporter.js (simplified version)
cat > extension/dist/js/data-exporter.js << 'EOF'
// Data Exporter v3.9.0 - Multi-format Export System
class DataExporter {
  constructor() {
    this.exportFormats = {
      csv: this.exportCSV.bind(this),
      json: this.exportJSON.bind(this)
    };
  }
  
  async export(dataType, format = 'csv') {
    try {
      console.log(`[Exporter] Exporting ${dataType} as ${format}`);
      
      const data = await this.getData(dataType);
      if (!data || data.length === 0) {
        throw new Error(`No ${dataType} data available to export`);
      }
      
      const exportHandler = this.exportFormats[format];
      if (!exportHandler) {
        throw new Error(`Unsupported format: ${format}`);
      }
      
      return await exportHandler(data, dataType);
    } catch (error) {
      console.error('[Exporter] Export failed:', error);
      throw error;
    }
  }
  
  async getData(dataType) {
    const dataMap = {
      listings: 'listings',
      deals: 'deals',
      settings: 'settings'
    };
    
    const storageKey = dataMap[dataType];
    if (!storageKey) {
      throw new Error(`Unknown data type: ${dataType}`);
    }
    
    const result = await chrome.storage.local.get(storageKey);
    let data = result[storageKey] || [];
    
    return Array.isArray(data) ? data : [data];
  }
  
  async exportCSV(data, dataType) {
    const headers = this.getHeaders(data[0], dataType);
    const rows = [];
    
    // Add headers
    rows.push(headers.map(h => this.escapeCSV(h.label)).join(','));
    
    // Convert data to rows
    for (const item of data) {
      const row = headers.map(header => {
        const value = this.getNestedValue(item, header.key);
        return this.escapeCSV(this.formatValue(value, header.type));
      });
      rows.push(row.join(','));
    }
    
    // Create CSV content
    const csvContent = rows.join('\n');
    const blob = new Blob(['\ufeff' + csvContent], { 
      type: 'text/csv;charset=utf-8;' 
    });
    
    // Download file
    const filename = `${dataType}_export_${this.getTimestamp()}.csv`;
    this.downloadFile(blob, filename);
    
    return {
      format: 'csv',
      filename: filename,
      rows: data.length
    };
  }
  
  async exportJSON(data, dataType) {
    const exportData = {
      metadata: {
        type: dataType,
        exportDate: new Date().toISOString(),
        version: chrome.runtime.getManifest().version,
        count: data.length
      },
      data: data
    };
    
    const jsonString = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonString], { 
      type: 'application/json' 
    });
    
    const filename = `${dataType}_export_${this.getTimestamp()}.json`;
    this.downloadFile(blob, filename);
    
    return {
      format: 'json',
      filename: filename,
      records: data.length
    };
  }
  
  getHeaders(sample, dataType) {
    const headerConfigs = {
      listings: [
        { key: 'id', label: 'ID', type: 'string' },
        { key: 'title', label: 'Title', type: 'string' },
        { key: 'price', label: 'Price', type: 'currency' },
        { key: 'platform', label: 'Platform', type: 'string' },
        { key: 'location', label: 'Location', type: 'string' },
        { key: 'url', label: 'URL', type: 'url' },
        { key: 'scannedAt', label: 'Scanned At', type: 'datetime' }
      ],
      deals: [
        { key: 'id', label: 'Deal ID', type: 'string' },
        { key: 'listing.title', label: 'Title', type: 'string' },
        { key: 'stage', label: 'Stage', type: 'string' },
        { key: 'listing.price', label: 'Ask Price', type: 'currency' },
        { key: 'createdAt', label: 'Created', type: 'datetime' }
      ]
    };
    
    return headerConfigs[dataType] || [];
  }
  
  getNestedValue(obj, path) {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  }
  
  formatValue(value, type) {
    if (value === null || value === undefined) return '';
    
    switch (type) {
      case 'currency':
        return typeof value === 'number' ? `$${value.toFixed(2)}` : value;
      case 'datetime':
        return value instanceof Date ? value.toLocaleString() : 
               typeof value === 'string' ? new Date(value).toLocaleString() : value;
      default:
        return String(value);
    }
  }
  
  escapeCSV(value) {
    if (typeof value !== 'string') value = String(value);
    
    if (value.includes('"') || value.includes(',') || value.includes('\n')) {
      return `"${value.replace(/"/g, '""')}"`;
    }
    
    return value;
  }
  
  getTimestamp() {
    const now = new Date();
    return now.toISOString().replace(/[:.]/g, '-').slice(0, -5);
  }
  
  downloadFile(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
}

// Create singleton instance
window.dataExporter = new DataExporter();
EOF

# Create onboarding.js (simplified version)
cat > extension/dist/js/onboarding.js << 'EOF'
// Onboarding v3.11.0 - First-Time User Experience
class Onboarding {
  constructor() {
    this.currentStep = 0;
    this.steps = [
      {
        id: 'welcome',
        title: 'Welcome to PC Arbitrage Pro',
        content: this.renderWelcome.bind(this)
      },
      {
        id: 'settings',
        title: 'Configure Your Preferences',
        content: this.renderSettings.bind(this)
      },
      {
        id: 'complete',
        title: 'You\'re All Set!',
        content: this.renderComplete.bind(this)
      }
    ];
  }
  
  async start() {
    const { onboardingCompleted } = await chrome.storage.local.get('onboardingCompleted');
    if (onboardingCompleted) {
      console.log('[Onboarding] Already completed');
      return;
    }
    
    chrome.tabs.create({
      url: chrome.runtime.getURL('onboarding.html')
    });
  }
  
  init(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      console.error('[Onboarding] Container not found');
      return;
    }
    
    this.render();
  }
  
  render() {
    const step = this.steps[this.currentStep];
    
    this.container.innerHTML = `
      <div style="max-width: 600px; margin: 50px auto; padding: 40px; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
        <h1 style="text-align: center; margin-bottom: 30px;">${step.title}</h1>
        <div style="margin-bottom: 40px;">
          ${step.content()}
        </div>
        <div style="display: flex; justify-content: space-between;">
          ${this.currentStep > 0 ? `
            <button onclick="window.onboarding.previousStep()" style="padding: 12px 24px; background: #e0e0e0; border: none; border-radius: 8px; cursor: pointer;">
              Back
            </button>
          ` : '<div></div>'}
          <button onclick="window.onboarding.nextStep()" style="padding: 12px 32px; background: #1976d2; color: white; border: none; border-radius: 8px; cursor: pointer;">
            ${this.currentStep < this.steps.length - 1 ? 'Continue' : 'Get Started'}
          </button>
        </div>
      </div>
    `;
  }
  
  renderWelcome() {
    return `
      <div style="text-align: center;">
        <p style="font-size: 18px; line-height: 1.6; color: #666;">
          Turn your marketplace expertise into profit with intelligent PC arbitrage tools.
        </p>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 40px;">
          <div style="padding: 20px; background: #f5f5f5; border-radius: 8px;">
            <h3 style="margin: 0 0 10px 0;">🔍 Smart Scanning</h3>
            <p style="margin: 0; color: #666;">Automatically find profitable deals</p>
          </div>
          <div style="padding: 20px; background: #f5f5f5; border-radius: 8px;">
            <h3 style="margin: 0 0 10px 0;">💰 Profit Analysis</h3>
            <p style="margin: 0; color: #666;">Calculate ROI instantly</p>
          </div>
          <div style="padding: 20px; background: #f5f5f5; border-radius: 8px;">
            <h3 style="margin: 0 0 10px 0;">📊 Deal Pipeline</h3>
            <p style="margin: 0; color: #666;">Track deals from find to sold</p>
          </div>
          <div style="padding: 20px; background: #f5f5f5; border-radius: 8px;">
            <h3 style="margin: 0 0 10px 0;">🚀 Automation</h3>
            <p style="margin: 0; color: #666;">Save hours with smart tools</p>
          </div>
        </div>
      </div>
    `;
  }
  
  renderSettings() {
    return `
      <div>
        <p style="color: #666; margin-bottom: 30px;">Let's configure some basic settings to get you started.</p>
        
        <div style="margin-bottom: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: 500;">Your Budget Range</label>
          <div style="display: flex; gap: 10px; align-items: center;">
            <input type="number" id="minBudget" placeholder="Min" value="200" style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
            <span>to</span>
            <input type="number" id="maxBudget" placeholder="Max" value="1000" style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
          </div>
        </div>
        
        <div style="margin-bottom: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: 500;">Minimum ROI Target</label>
          <select id="targetROI" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
            <option value="20">20% or more</option>
            <option value="30" selected>30% or more</option>
            <option value="50">50% or more</option>
          </select>
        </div>
        
        <div style="margin-bottom: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: 500;">Preferred Platforms</label>
          <div style="display: flex; gap: 15px;">
            <label style="display: flex; align-items: center; gap: 5px;">
              <input type="checkbox" value="facebook" checked> Facebook Marketplace
            </label>
            <label style="display: flex; align-items: center; gap: 5px;">
              <input type="checkbox" value="craigslist" checked> Craigslist
            </label>
          </div>
        </div>
      </div>
    `;
  }
  
  renderComplete() {
    return `
      <div style="text-align: center;">
        <div style="font-size: 48px; margin-bottom: 20px;">🎉</div>
        <p style="font-size: 18px; color: #666; margin-bottom: 30px;">
          You're all set! Your dashboard is ready to help you find profitable PC deals.
        </p>
        <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; text-align: left;">
          <h3 style="margin: 0 0 15px 0;">Quick Tips:</h3>
          <ul style="margin: 0; padding-left: 20px;">
            <li style="margin-bottom: 8px;">Visit any marketplace and click our extension icon to scan deals</li>
            <li style="margin-bottom: 8px;">Star promising deals to track them in your pipeline</li>
            <li style="margin-bottom: 8px;">Check the dashboard daily for new opportunities</li>
          </ul>
        </div>
      </div>
    `;
  }
  
  nextStep() {
    if (this.currentStep < this.steps.length - 1) {
      this.saveStepData();
      this.currentStep++;
      this.render();
    } else {
      this.complete();
    }
  }
  
  previousStep() {
    if (this.currentStep > 0) {
      this.currentStep--;
      this.render();
    }
  }
  
  saveStepData() {
    // Save settings from step 2
    if (this.currentStep === 1) {
      const settings = {
        budget: {
          min: parseInt(document.getElementById('minBudget')?.value) || 200,
          max: parseInt(document.getElementById('maxBudget')?.value) || 1000
        },
        targetROI: parseInt(document.getElementById('targetROI')?.value) || 30
      };
      
      // Save to storage
      chrome.storage.local.set({ onboardingSettings: settings });
    }
  }
  
  async complete() {
    await chrome.storage.local.set({ onboardingCompleted: true });
    
    // Open dashboard
    chrome.tabs.create({
      url: chrome.runtime.getURL('dashboard.html')
    });
    
    // Close onboarding tab
    window.close();
  }
}

// Create singleton instance
window.onboarding = new Onboarding();
EOF

echo "All remaining files created successfully!"
EOF