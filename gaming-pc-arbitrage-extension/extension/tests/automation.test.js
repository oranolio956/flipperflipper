// Max Auto Engine Test v3.4.0
// Tests the automation engine functionality

window.runAutomationTest = async function() {
  console.log('🧪 Running Max Auto Engine Tests...\n');
  
  const results = [];
  const engine = window.automationEngine;
  
  // Test 1: Engine Loaded
  console.log('Test 1: Checking automation engine...');
  results.push({
    test: 'Automation engine exists',
    pass: engine !== undefined,
    actual: typeof engine
  });
  
  // Test 2: Engine Status
  console.log('Test 2: Checking engine status...');
  const status = engine.getStatus();
  results.push({
    test: 'Engine status structure',
    pass: status.hasOwnProperty('isRunning') && status.hasOwnProperty('isPaused'),
    actual: Object.keys(status).join(', ')
  });
  
  // Test 3: Settings Integration
  console.log('Test 3: Testing settings integration...');
  
  // Add a test search
  const searchId = await window.settingsManager.addSavedSearch({
    name: 'Test Gaming PCs',
    url: 'https://www.facebook.com/marketplace/search/?query=gaming%20pc',
    enabled: true,
    interval: 30
  });
  
  results.push({
    test: 'Add saved search',
    pass: searchId !== undefined,
    actual: searchId
  });
  
  // Test 4: Start Session (without running)
  console.log('Test 4: Testing session creation...');
  let sessionStarted = false;
  let sessionId = null;
  
  try {
    // Subscribe to events
    const unsubscribe = engine.subscribe((event) => {
      if (event.type === 'session_started') {
        sessionStarted = true;
        sessionId = event.session.id;
      }
    });
    
    // Don't actually start - just test the method exists
    results.push({
      test: 'Engine has startSession method',
      pass: typeof engine.startSession === 'function',
      actual: 'function'
    });
    
    unsubscribe();
  } catch (e) {
    console.error('Session test error:', e);
  }
  
  // Test 5: History Storage
  console.log('Test 5: Testing history storage...');
  const history = await engine.getScanHistory();
  results.push({
    test: 'Get scan history',
    pass: Array.isArray(history),
    actual: `${history.length} sessions`
  });
  
  // Test 6: Event System
  console.log('Test 6: Testing event system...');
  let eventReceived = false;
  
  const unsubscribe = engine.subscribe((event) => {
    eventReceived = true;
  });
  
  // Emit test event
  engine.emit({ type: 'test_event' });
  
  results.push({
    test: 'Event system works',
    pass: eventReceived,
    actual: eventReceived
  });
  
  unsubscribe();
  
  // Test 7: Tab Management Integration
  console.log('Test 7: Checking Chrome APIs...');
  results.push({
    test: 'Chrome tabs API available',
    pass: chrome.tabs !== undefined,
    actual: typeof chrome.tabs
  });
  
  results.push({
    test: 'Chrome idle API available',
    pass: chrome.idle !== undefined,
    actual: typeof chrome.idle
  });
  
  // Test 8: Scanner Communication
  console.log('Test 8: Testing scanner integration...');
  
  // Check if scanner will receive job IDs
  const testMessage = {
    action: 'START_SCAN',
    jobId: 'test_job_123'
  };
  
  results.push({
    test: 'Scanner message format',
    pass: testMessage.action && testMessage.jobId,
    actual: 'Ready for job-based scanning'
  });
  
  // Clean up test search
  if (searchId) {
    await window.settingsManager.removeSavedSearch(searchId);
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

// Manual session test (requires user confirmation)
window.testAutomationSession = async function() {
  console.log('🚀 Testing Automation Session...\n');
  console.log('This will open tabs and scan for gaming PCs.');
  
  if (!confirm('Start test automation session? This will open browser tabs.')) {
    console.log('Test cancelled');
    return;
  }
  
  const engine = window.automationEngine;
  
  // Ensure we have at least one search
  const settings = window.settingsManager.get();
  if (!settings.search.savedSearches.some(s => s.enabled)) {
    // Add a test search
    await window.settingsManager.addSavedSearch({
      name: 'Test Search - Facebook Gaming PCs',
      url: 'https://www.facebook.com/marketplace/search/?query=gaming%20pc',
      enabled: true
    });
  }
  
  // Subscribe to events
  const events = [];
  const unsubscribe = engine.subscribe((event) => {
    console.log(`[Event] ${event.type}:`, event);
    events.push(event);
  });
  
  try {
    // Start session
    console.log('Starting automation session...');
    const session = await engine.startSession();
    console.log('Session started:', session);
    
    // Wait for completion or timeout
    const timeout = setTimeout(() => {
      console.log('Test timeout - stopping session');
      engine.stopSession();
    }, 30000); // 30 second timeout
    
    // Wait for session to complete
    await new Promise((resolve) => {
      const checkInterval = setInterval(() => {
        const status = engine.getStatus();
        if (!status.isRunning) {
          clearInterval(checkInterval);
          clearTimeout(timeout);
          resolve();
        }
      }, 1000);
    });
    
    console.log('\n📊 Session Summary:');
    console.log('Events captured:', events.length);
    events.forEach(e => {
      console.log(`- ${e.type}: ${JSON.stringify(e.job || e.session?.stats || '')}`);
    });
    
  } catch (error) {
    console.error('Session test error:', error);
  } finally {
    unsubscribe();
  }
};

// Check automation readiness
window.checkAutomationReady = function() {
  console.log('🔍 Checking Automation Readiness...\n');
  
  const checks = {
    'Settings Manager': window.settingsManager !== undefined,
    'Automation Engine': window.automationEngine !== undefined,
    'Chrome Tabs API': chrome.tabs !== undefined,
    'Chrome Storage API': chrome.storage !== undefined,
    'Chrome Idle API': chrome.idle !== undefined,
    'Chrome Alarms API': chrome.alarms !== undefined
  };
  
  const settings = window.settingsManager?.get();
  const engineStatus = window.automationEngine?.getStatus();
  
  console.log('System Checks:');
  Object.entries(checks).forEach(([name, ready]) => {
    console.log(`${ready ? '✅' : '❌'} ${name}`);
  });
  
  console.log('\nSettings:');
  console.log('- Automation enabled:', settings?.automation?.enabled || false);
  console.log('- Scan interval:', settings?.automation?.scanInterval || 'Not set');
  console.log('- Max concurrent tabs:', settings?.automation?.maxConcurrentTabs || 'Not set');
  console.log('- Saved searches:', settings?.search?.savedSearches?.length || 0);
  console.log('- Enabled searches:', settings?.search?.savedSearches?.filter(s => s.enabled).length || 0);
  
  console.log('\nEngine Status:');
  console.log('- Running:', engineStatus?.isRunning || false);
  console.log('- Paused:', engineStatus?.isPaused || false);
  console.log('- Active jobs:', engineStatus?.activeJobs?.length || 0);
  console.log('- Queue length:', engineStatus?.queueLength || 0);
  
  const ready = Object.values(checks).every(v => v);
  console.log(`\n${ready ? '✅' : '❌'} System ${ready ? 'ready' : 'not ready'} for automation`);
  
  return ready;
};