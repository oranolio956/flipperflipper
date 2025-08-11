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
