// Settings Test v3.7.0
// Tests for comprehensive settings system

window.runSettingsTest = async function() {
  console.log('🧪 Running Settings Tests...\n');
  
  const results = [];
  
  // Test 1: Settings config loaded
  console.log('Test 1: Checking settings config...');
  results.push({
    test: 'Settings config exists',
    pass: window.settingsConfig !== undefined,
    actual: typeof window.settingsConfig
  });
  
  // Test 2: Settings UI loaded
  console.log('Test 2: Checking settings UI...');
  results.push({
    test: 'Settings UI exists',
    pass: window.settingsUI !== undefined,
    actual: typeof window.settingsUI
  });
  
  // Test 3: Default settings structure
  console.log('Test 3: Validating default settings...');
  const defaults = window.settingsConfig?.defaultSettings;
  results.push({
    test: 'Default settings valid',
    pass: defaults && defaults.version && defaults.general && defaults.search,
    actual: defaults ? 'Valid structure' : 'Missing defaults'
  });
  
  // Test 4: Settings validation
  console.log('Test 4: Testing validation...');
  const invalidSettings = {
    version: '3.7.0',
    general: { theme: 'invalid-theme' },
    search: { defaultFilters: { minPrice: -100 } }
  };
  
  const validation = window.settingsConfig?.SettingsConfigManager.validateSettings(invalidSettings);
  results.push({
    test: 'Validation catches errors',
    pass: !validation.valid && validation.errors.length > 0,
    actual: `${validation.errors.length} errors found`
  });
  
  // Test 5: Theme application
  console.log('Test 5: Testing theme application...');
  const originalTheme = document.documentElement.getAttribute('data-theme');
  window.settingsConfig?.SettingsConfigManager.applyTheme('dark');
  const newTheme = document.documentElement.getAttribute('data-theme');
  
  results.push({
    test: 'Theme application works',
    pass: newTheme === 'dark',
    actual: `Theme changed to: ${newTheme}`
  });
  
  // Restore original theme
  if (originalTheme) {
    document.documentElement.setAttribute('data-theme', originalTheme);
  }
  
  // Test 6: Export/Import
  console.log('Test 6: Testing export/import...');
  const testSettings = window.settingsConfig?.defaultSettings;
  const exported = window.settingsConfig?.SettingsConfigManager.exportSettings(testSettings);
  const imported = window.settingsConfig?.SettingsConfigManager.importSettings(exported);
  
  results.push({
    test: 'Export/import preserves data',
    pass: imported && imported.version === testSettings.version,
    actual: imported ? 'Import successful' : 'Import failed'
  });
  
  // Test 7: Currency formatting
  console.log('Test 7: Testing currency formatting...');
  const formatted = window.settingsConfig?.SettingsConfigManager.formatCurrency(1234.56, 'USD');
  results.push({
    test: 'Currency formatting works',
    pass: formatted === '$1,234.56',
    actual: formatted
  });
  
  // Test 8: Date formatting
  console.log('Test 8: Testing date formatting...');
  const testDate = new Date('2024-01-15T14:30:00');
  const formattedDate = window.settingsConfig?.SettingsConfigManager.formatDate(testDate, 'MM/DD/YYYY');
  results.push({
    test: 'Date formatting works',
    pass: formattedDate === '01/15/2024',
    actual: formattedDate
  });
  
  // Test 9: Settings sections
  console.log('Test 9: Checking settings sections...');
  const sections = window.settingsConfig?.settingsSections || [];
  results.push({
    test: 'All settings sections defined',
    pass: sections.length === 5,
    actual: `${sections.length} sections: ${sections.map(s => s.id).join(', ')}`
  });
  
  // Test 10: Settings persistence
  console.log('Test 10: Testing settings persistence...');
  const currentSettings = window.settingsManager?.get();
  const testKey = `test_${Date.now()}`;
  
  if (currentSettings) {
    currentSettings.test = testKey;
    await window.settingsManager.save(currentSettings);
    
    const reloaded = window.settingsManager.get();
    results.push({
      test: 'Settings persist correctly',
      pass: reloaded.test === testKey,
      actual: reloaded.test ? 'Persisted' : 'Not persisted'
    });
    
    // Clean up
    delete currentSettings.test;
    await window.settingsManager.save(currentSettings);
  } else {
    results.push({
      test: 'Settings persist correctly',
      pass: false,
      actual: 'Settings manager not available'
    });
  }
  
  // Print results
  console.log('\n📊 Test Results:');
  results.forEach(result => {
    console.log(`${result.pass ? '✅' : '❌'} ${result.test}: ${result.actual}`);
  });
  
  const passed = results.filter(r => r.pass).length;
  const total = results.length;
  console.log(`\n🏁 Total: ${passed}/${total} tests passed`);
  
  return results;
};

// Test individual settings features
window.testSettingsFeatures = async function() {
  console.log('🔧 Testing Settings Features...\n');
  
  // 1. Test notification settings
  console.log('1️⃣ Testing notification settings');
  const settings = window.settingsManager?.get() || window.settingsConfig?.defaultSettings;
  
  // Toggle notifications
  settings.general.notifications.enabled = true;
  settings.general.notifications.dealAlerts = true;
  
  // Send test notification
  chrome.runtime.sendMessage({
    action: 'SHOW_NOTIFICATION',
    notification: {
      title: 'Test Deal Alert',
      message: 'RTX 4090 Gaming PC - 45% ROI!',
      type: 'deal',
      priority: 2
    }
  });
  
  console.log('✅ Notification test sent');
  
  // 2. Test automation settings
  console.log('\n2️⃣ Testing automation settings');
  settings.search.automation.enabled = true;
  settings.search.automation.interval = 60;
  
  chrome.runtime.sendMessage({
    action: 'SETTINGS_UPDATED',
    settings: settings
  });
  
  console.log('✅ Automation settings updated');
  
  // 3. Test theme switching
  console.log('\n3️⃣ Testing theme switching');
  const themes = ['light', 'dark', 'auto'];
  
  for (const theme of themes) {
    window.settingsConfig?.SettingsConfigManager.applyTheme(theme);
    console.log(`Applied theme: ${theme}`);
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  // 4. Test exclude keywords
  console.log('\n4️⃣ Testing exclude keywords');
  settings.search.defaultFilters.excludeKeywords = ['broken', 'parts', 'repair', 'damaged'];
  console.log('Exclude keywords:', settings.search.defaultFilters.excludeKeywords);
  
  // 5. Test pipeline settings
  console.log('\n5️⃣ Testing pipeline settings');
  settings.pipeline.automation.autoAdd = true;
  settings.pipeline.automation.minROIThreshold = 35;
  console.log('Auto-add threshold:', settings.pipeline.automation.minROIThreshold + '%');
  
  return settings;
};

// Check settings integration
window.checkSettingsIntegration = function() {
  console.log('🔍 Checking Settings Integration...\n');
  
  const checks = {
    'Settings config loaded': window.settingsConfig !== undefined,
    'Settings UI loaded': window.settingsUI !== undefined,
    'Settings manager loaded': window.settingsManager !== undefined,
    'Can validate settings': typeof window.settingsConfig?.SettingsConfigManager?.validateSettings === 'function',
    'Can export settings': typeof window.settingsConfig?.SettingsConfigManager?.exportSettings === 'function',
    'Can apply theme': typeof window.settingsConfig?.SettingsConfigManager?.applyTheme === 'function'
  };
  
  console.log('System Checks:');
  Object.entries(checks).forEach(([name, ready]) => {
    console.log(`${ready ? '✅' : '❌'} ${name}`);
  });
  
  // Check current settings
  if (window.settingsManager) {
    const settings = window.settingsManager.get();
    console.log('\nCurrent Settings Summary:');
    console.log(`- Theme: ${settings.general?.theme || 'auto'}`);
    console.log(`- Notifications: ${settings.general?.notifications?.enabled ? 'Enabled' : 'Disabled'}`);
    console.log(`- Automation: ${settings.search?.automation?.enabled ? 'Enabled' : 'Disabled'}`);
    console.log(`- Pipeline auto-add: ${settings.pipeline?.automation?.autoAdd ? 'Enabled' : 'Disabled'}`);
    console.log(`- Debug mode: ${settings.advanced?.developer?.debugMode ? 'Enabled' : 'Disabled'}`);
  }
  
  const ready = Object.values(checks).every(v => v);
  console.log(`\n${ready ? '✅' : '❌'} Settings system ${ready ? 'ready' : 'not ready'}`);
  
  return ready;
};

// Test settings UI rendering
window.testSettingsUI = function() {
  console.log('🎨 Testing Settings UI...\n');
  
  if (!window.settingsUI) {
    console.error('❌ Settings UI not loaded');
    return;
  }
  
  // Render settings
  const html = window.settingsUI.render();
  console.log('✅ Settings HTML generated:', html.length + ' characters');
  
  // Test section switching
  const sections = ['general', 'search', 'pipeline', 'privacy', 'advanced'];
  sections.forEach(section => {
    const sectionHtml = window.settingsUI.renderSection(section);
    console.log(`✅ ${section} section: ${sectionHtml.length} characters`);
  });
  
  // Test setting updates
  window.settingsUI.updateSetting('general.theme', 'dark');
  console.log('✅ Theme updated to dark');
  console.log('Unsaved changes:', window.settingsUI.unsavedChanges);
  
  return true;
};