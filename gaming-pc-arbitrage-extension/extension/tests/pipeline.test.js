// Pipeline Integration Test v3.5.0
// Tests scanner → parser → pipeline flow with real data

window.runPipelineTest = async function() {
  console.log('🧪 Running Pipeline Integration Tests...\n');
  
  const results = [];
  
  // Test 1: Parser loaded
  console.log('Test 1: Checking parser...');
  results.push({
    test: 'Parser exists',
    pass: window.listingParser !== undefined,
    actual: typeof window.listingParser
  });
  
  // Test 2: Pipeline manager loaded
  console.log('Test 2: Checking pipeline manager...');
  results.push({
    test: 'Pipeline manager exists',
    pass: window.pipelineManager !== undefined,
    actual: typeof window.pipelineManager
  });
  
  // Test 3: Parse sample listing
  console.log('Test 3: Testing parser with sample data...');
  const sampleListing = {
    id: 'test_123',
    title: 'Gaming PC - RTX 3080, i7-12700K, 32GB RAM',
    description: 'High-end gaming PC built 6 months ago. Includes RTX 3080 12GB, Intel i7-12700K, 32GB DDR4 3600MHz, 1TB NVMe SSD, 850W Gold PSU. Runs all games at max settings. Must sell due to moving.',
    price: 1200,
    platform: 'facebook',
    url: 'https://facebook.com/marketplace/item/123',
    location: '5 miles away',
    foundAt: new Date().toISOString()
  };
  
  let parsed = null;
  try {
    parsed = window.listingParser.parse(sampleListing);
    results.push({
      test: 'Parser extracts CPU',
      pass: parsed.specs.cpu?.model === 'i7-12700K',
      actual: parsed.specs.cpu?.model || 'Not found'
    });
    
    results.push({
      test: 'Parser extracts GPU', 
      pass: parsed.specs.gpu?.model === 'RTX 3080',
      actual: parsed.specs.gpu?.model || 'Not found'
    });
    
    results.push({
      test: 'Parser extracts RAM',
      pass: parsed.specs.ram?.capacity === 32,
      actual: parsed.specs.ram?.capacity || 'Not found'
    });
    
    results.push({
      test: 'Parser calculates ROI',
      pass: parsed.analysis.roi > 0,
      actual: `${parsed.analysis.roi}%`
    });
    
    results.push({
      test: 'Parser assigns deal quality',
      pass: ['excellent', 'good', 'fair', 'poor'].includes(parsed.analysis.dealQuality),
      actual: parsed.analysis.dealQuality
    });
  } catch (e) {
    results.push({
      test: 'Parser works without error',
      pass: false,
      actual: e.message
    });
  }
  
  // Test 4: Add to pipeline
  console.log('Test 4: Testing pipeline addition...');
  let deal = null;
  try {
    if (parsed) {
      deal = await window.pipelineManager.addToPipeline(parsed);
      results.push({
        test: 'Deal added to pipeline',
        pass: deal && deal.dealId,
        actual: deal?.dealId || 'Failed'
      });
      
      results.push({
        test: 'Deal has correct stage',
        pass: deal?.stage === 'scanner',
        actual: deal?.stage || 'No stage'
      });
      
      results.push({
        test: 'Deal has tasks',
        pass: deal?.tasks?.length > 0,
        actual: `${deal?.tasks?.length || 0} tasks`
      });
    }
  } catch (e) {
    results.push({
      test: 'Pipeline addition works',
      pass: false,
      actual: e.message
    });
  }
  
  // Test 5: Stage transitions
  console.log('Test 5: Testing stage transitions...');
  if (deal) {
    try {
      const advanced = await window.pipelineManager.advanceStage(deal.dealId, 'analysis');
      results.push({
        test: 'Can advance to analysis',
        pass: advanced === true,
        actual: advanced ? 'Success' : 'Failed'
      });
      
      // Try invalid transition
      const invalid = await window.pipelineManager.advanceStage(deal.dealId, 'sold');
      results.push({
        test: 'Prevents invalid transitions',
        pass: invalid === false,
        actual: invalid ? 'Failed (allowed)' : 'Success (blocked)'
      });
    } catch (e) {
      results.push({
        test: 'Stage transitions work',
        pass: false,
        actual: e.message
      });
    }
  }
  
  // Test 6: Pipeline stats
  console.log('Test 6: Testing pipeline statistics...');
  const stats = window.pipelineManager.getStats();
  results.push({
    test: 'Stats structure valid',
    pass: stats.hasOwnProperty('totalDeals') && stats.hasOwnProperty('totalProfit'),
    actual: Object.keys(stats).join(', ')
  });
  
  // Test 7: Search functionality
  console.log('Test 7: Testing search...');
  if (deal) {
    const searchResults = window.pipelineManager.searchDeals('RTX');
    results.push({
      test: 'Search finds deals',
      pass: searchResults.length > 0,
      actual: `${searchResults.length} results`
    });
  }
  
  // Test 8: Event system
  console.log('Test 8: Testing events...');
  let eventReceived = false;
  const unsubscribe = window.pipelineManager.subscribe((event) => {
    eventReceived = true;
  });
  
  // Trigger an event by completing a task
  if (deal && deal.tasks.length > 0) {
    await window.pipelineManager.completeTask(deal.dealId, deal.tasks[0].id);
  }
  
  results.push({
    test: 'Events fire correctly',
    pass: eventReceived,
    actual: eventReceived ? 'Received' : 'Not received'
  });
  
  unsubscribe();
  
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

// Manual test with real scan
window.testRealScan = async function() {
  console.log('🔍 Testing Real Scan → Pipeline Flow...\n');
  
  // Ensure we're on a marketplace page
  const url = window.location.href;
  if (!url.includes('facebook.com/marketplace') && 
      !url.includes('craigslist.org') && 
      !url.includes('offerup.com')) {
    console.error('Please navigate to a marketplace page first!');
    return;
  }
  
  console.log('1️⃣ Injecting scanner...');
  
  // Simulate scan
  const scanner = new MarketplaceScanner('test_job_123');
  await scanner.scan();
  
  console.log('2️⃣ Scanner found', scanner.listings.length, 'listings');
  
  // Check if parser was used
  const hasParser = window.listingParser !== undefined;
  console.log('3️⃣ Parser available:', hasParser);
  
  // Check pipeline
  const hasPipeline = window.pipelineManager !== undefined;
  console.log('4️⃣ Pipeline available:', hasPipeline);
  
  // Get current deals
  if (hasPipeline) {
    const deals = window.pipelineManager.getDealsByStage();
    console.log('5️⃣ Current pipeline deals:', deals.length);
    
    // Show newest deal
    if (deals.length > 0) {
      const newest = deals[deals.length - 1];
      console.log('\n📦 Newest Deal:');
      console.log('- Title:', newest.title);
      console.log('- Price:', `$${newest.price}`);
      console.log('- Stage:', newest.stage);
      console.log('- ROI:', `${newest.analysis?.roi}%`);
      console.log('- CPU:', newest.specs?.cpu?.model);
      console.log('- GPU:', newest.specs?.gpu?.model);
    }
  }
};

// Check integration readiness
window.checkPipelineReady = function() {
  console.log('🔍 Checking Pipeline Integration...\n');
  
  const checks = {
    'Parser loaded': window.listingParser !== undefined,
    'Pipeline loaded': window.pipelineManager !== undefined,
    'Settings has pipeline config': window.settingsManager?.get()?.pipeline !== undefined,
    'Chrome storage available': chrome.storage !== undefined
  };
  
  console.log('System Checks:');
  Object.entries(checks).forEach(([name, ready]) => {
    console.log(`${ready ? '✅' : '❌'} ${name}`);
  });
  
  if (window.pipelineManager) {
    const stats = window.pipelineManager.getStats();
    console.log('\nPipeline Stats:');
    console.log('- Total deals:', stats.totalDeals);
    console.log('- Total invested:', `$${stats.totalInvested}`);
    console.log('- Total profit:', `$${stats.totalProfit}`);
    console.log('- Average ROI:', `${Math.round(stats.avgROI)}%`);
  }
  
  const ready = Object.values(checks).every(v => v);
  console.log(`\n${ready ? '✅' : '❌'} Pipeline ${ready ? 'ready' : 'not ready'}`);
  
  return ready;
};