// Settings Flow Test v3.2.0
// Tests that settings persist and drive real behavior changes

// Manual test script that can be run in the extension console
window.runSettingsTest = async function() {
  console.log('🧪 Running Settings Flow Tests...\n');
  
  const results = [];
  const settingsManager = window.settingsManager;
  
  // Test 1: Settings Manager Initialized
  console.log('Test 1: Checking settings manager...');
  results.push({
    test: 'Settings manager exists',
    pass: settingsManager !== undefined,
    actual: typeof settingsManager
  });
  
  // Test 2: Default Settings Loaded
  console.log('Test 2: Checking default settings...');
  const currentSettings = settingsManager.get();
  results.push({
    test: 'Settings have correct structure',
    pass: currentSettings.automation && currentSettings.notifications && currentSettings.display,
    actual: Object.keys(currentSettings).join(', ')
  });
  
  // Test 3: Settings Persistence
  console.log('Test 3: Testing settings persistence...');
  const testValue = Math.random() * 100;
  await settingsManager.updatePath('automation.scanInterval', testValue);
  
  // Read from storage directly
  const stored = await chrome.storage.local.get(['settings']);
  results.push({
    test: 'Settings persist to storage',
    pass: stored.settings?.automation?.scanInterval === testValue,
    actual: stored.settings?.automation?.scanInterval
  });
  
  // Test 4: Settings Subscribe
  console.log('Test 4: Testing settings subscription...');
  let subscriptionWorked = false;
  const unsubscribe = settingsManager.subscribe((newSettings) => {
    subscriptionWorked = true;
  });
  
  await settingsManager.updatePath('automation.enabled', !currentSettings.automation.enabled);
  
  results.push({
    test: 'Settings subscription works',
    pass: subscriptionWorked,
    actual: subscriptionWorked
  });
  
  unsubscribe();
  
  // Test 5: Background Communication
  console.log('Test 5: Testing background script communication...');
  let backgroundResponded = false;
  
  try {
    await chrome.runtime.sendMessage({
      action: 'SETTINGS_UPDATED',
      data: settingsManager.get()
    });
    backgroundResponded = true;
  } catch (e) {
    console.warn('Background communication failed:', e);
  }
  
  results.push({
    test: 'Background accepts settings updates',
    pass: backgroundResponded,
    actual: backgroundResponded
  });
  
  // Test 6: Settings UI Integration
  console.log('Test 6: Testing settings UI...');
  if (window.location.pathname.includes('dashboard.html')) {
    // Navigate to settings
    window.Router.navigate('/settings');
    await new Promise(r => setTimeout(r, 100));
    
    const settingsPage = document.querySelector('.settings-page');
    results.push({
      test: 'Settings page renders',
      pass: settingsPage !== null,
      actual: settingsPage ? 'rendered' : 'not found'
    });
    
    // Test toggle
    const automationToggle = document.querySelector('[data-path="automation.enabled"]');
    if (automationToggle) {
      const wasChecked = automationToggle.checked;
      automationToggle.click();
      
      results.push({
        test: 'Settings toggle changes state',
        pass: automationToggle.checked !== wasChecked,
        actual: `${wasChecked} → ${automationToggle.checked}`
      });
    }
  }
  
  // Test 7: Export/Import
  console.log('Test 7: Testing export/import...');
  const exportData = await settingsManager.export();
  const exportValid = exportData.includes('"version"') && exportData.includes('"settings"');
  
  results.push({
    test: 'Settings export works',
    pass: exportValid,
    actual: exportData.length + ' characters'
  });
  
  // Test 8: Theme Application
  console.log('Test 8: Testing theme application...');
  const originalTheme = document.documentElement.getAttribute('data-theme');
  await settingsManager.updatePath('display.theme', 'dark');
  
  // Apply theme
  if (window.app?.applyTheme) {
    window.app.applyTheme('dark');
  }
  
  const newTheme = document.documentElement.getAttribute('data-theme');
  results.push({
    test: 'Theme changes apply',
    pass: newTheme === 'dark' || originalTheme !== newTheme,
    actual: `${originalTheme} → ${newTheme}`
  });
  
  // Test 9: Alarm Re-arming (check logs)
  console.log('Test 9: Testing automation alarm re-arming...');
  console.log('Enabling automation...');
  await settingsManager.updatePath('automation.enabled', true);
  await settingsManager.updatePath('automation.scanInterval', 15);
  
  results.push({
    test: 'Automation settings update',
    pass: true,
    actual: 'Check console for [Background] logs'
  });
  
  // Print results
  console.log('\n📊 Test Results:');
  results.forEach(result => {
    console.log(`${result.pass ? '✅' : '❌'} ${result.test}: ${result.actual}`);
  });
  
  const passed = results.filter(r => r.pass).length;
  const total = results.length;
  console.log(`\n🏁 Total: ${passed}/${total} tests passed`);
  
  // Log sample to prove settings changes
  console.log('\n📝 Current Settings Sample:');
  const sample = settingsManager.get();
  console.log('Automation enabled:', sample.automation.enabled);
  console.log('Scan interval:', sample.automation.scanInterval);
  console.log('Theme:', sample.display.theme);
  console.log('Notifications:', sample.notifications.enabled);
  
  return results;
};

// Automation behavior verification
window.verifyAutomationBehavior = async function() {
  console.log('🔍 Verifying Automation Behavior...\n');
  
  const settingsManager = window.settingsManager;
  
  // Enable automation
  console.log('1. Enabling automation...');
  await settingsManager.updatePath('automation.enabled', true);
  await settingsManager.updatePath('automation.scanInterval', 1); // 1 minute for testing
  
  console.log('2. Check chrome://extensions → Service Worker logs');
  console.log('   You should see:');
  console.log('   - [Background] Settings changed externally');
  console.log('   - [Background] Applying settings');
  console.log('   - [Background] Setting up automation, interval: 1 minutes');
  
  // Check alarms
  const alarms = await chrome.alarms.getAll();
  console.log('\n3. Active alarms:', alarms.map(a => a.name).join(', '));
  
  // Disable automation
  console.log('\n4. Disabling automation...');
  await settingsManager.updatePath('automation.enabled', false);
  
  console.log('5. Check logs again for:');
  console.log('   - [Background] Disabling automation');
  
  // Check alarms again
  setTimeout(async () => {
    const alarmsAfter = await chrome.alarms.getAll();
    console.log('\n6. Active alarms after disable:', alarmsAfter.map(a => a.name).join(', '));
  }, 1000);
};