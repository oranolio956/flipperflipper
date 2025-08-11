// Search Builder Test v3.6.0
// Tests URL generation and search configuration

window.runSearchBuilderTest = async function() {
  console.log('🧪 Running Search Builder Tests...\n');
  
  const results = [];
  
  // Test 1: Search builder loaded
  console.log('Test 1: Checking search builder...');
  results.push({
    test: 'Search builder exists',
    pass: window.searchBuilder !== undefined,
    actual: typeof window.searchBuilder
  });
  
  // Test 2: Default search creation
  console.log('Test 2: Creating default searches...');
  const platforms = ['facebook', 'craigslist', 'offerup'];
  
  for (const platform of platforms) {
    const search = window.searchBuilder.createDefaultSearch(platform);
    results.push({
      test: `Default ${platform} search valid`,
      pass: search.platform === platform && search.keywords.length > 0,
      actual: `${search.keywords.length} keywords`
    });
  }
  
  // Test 3: Facebook URL generation
  console.log('Test 3: Testing Facebook URL generation...');
  const fbParams = {
    platform: 'facebook',
    keywords: ['gaming pc', 'rtx 3080'],
    minPrice: 500,
    maxPrice: 1500,
    location: { radius: 25 },
    condition: ['used', 'like-new'],
    facebook: {
      sortBy: 'date',
      daysSinceListed: 7,
      delivery: 'local'
    }
  };
  
  const fbUrl = window.searchBuilder.buildUrl(fbParams);
  results.push({
    test: 'Facebook URL contains keywords',
    pass: fbUrl.includes('query=gaming+pc+rtx+3080'),
    actual: fbUrl.includes('query=') ? 'Keywords included' : 'Missing keywords'
  });
  
  results.push({
    test: 'Facebook URL contains price range',
    pass: fbUrl.includes('minPrice=500') && fbUrl.includes('maxPrice=1500'),
    actual: fbUrl.includes('minPrice') ? 'Price range included' : 'Missing prices'
  });
  
  // Test 4: Craigslist URL generation
  console.log('Test 4: Testing Craigslist URL generation...');
  const clParams = {
    platform: 'craigslist',
    keywords: ['gaming computer'],
    minPrice: 300,
    maxPrice: 2000,
    location: { city: 'seattle', radius: 50 },
    craigslist: {
      section: 'sya',
      hasImage: true
    }
  };
  
  const clUrl = window.searchBuilder.buildUrl(clParams);
  results.push({
    test: 'Craigslist URL contains city',
    pass: clUrl.includes('seattle.craigslist.org'),
    actual: clUrl.split('.')[0].split('//')[1] || 'No city'
  });
  
  results.push({
    test: 'Craigslist URL has image filter',
    pass: clUrl.includes('hasPic=1'),
    actual: clUrl.includes('hasPic') ? 'Image filter on' : 'No image filter'
  });
  
  // Test 5: OfferUp URL generation
  console.log('Test 5: Testing OfferUp URL generation...');
  const ouParams = {
    platform: 'offerup',
    keywords: ['gaming pc'],
    minPrice: 400,
    maxPrice: 1200,
    offerup: {
      radius: 30,
      priceNegotiable: true,
      sellerType: 'owner'
    }
  };
  
  const ouUrl = window.searchBuilder.buildUrl(ouParams);
  results.push({
    test: 'OfferUp URL valid',
    pass: ouUrl.startsWith('https://offerup.com/search'),
    actual: ouUrl.split('?')[0]
  });
  
  // Test 6: Keyword suggestions
  console.log('Test 6: Testing keyword suggestions...');
  const suggestions = window.searchBuilder.suggestKeywords('gaming', 'facebook');
  results.push({
    test: 'Keyword suggestions generated',
    pass: suggestions.length > 0 && suggestions.includes('gaming'),
    actual: `${suggestions.length} suggestions`
  });
  
  // Test 7: Validation
  console.log('Test 7: Testing validation...');
  const invalidParams = {
    platform: 'facebook',
    keywords: [], // No keywords
    minPrice: 2000,
    maxPrice: 1000 // Min > Max
  };
  
  const validation = window.searchBuilder.validateParameters(invalidParams);
  results.push({
    test: 'Validation catches errors',
    pass: !validation.valid && validation.errors.length >= 2,
    actual: `${validation.errors.length} errors found`
  });
  
  // Test 8: Export/Import
  console.log('Test 8: Testing export/import...');
  const exportStr = window.searchBuilder.exportSearch(fbParams);
  const imported = window.searchBuilder.importSearch(exportStr);
  
  results.push({
    test: 'Export/import preserves data',
    pass: imported && imported.keywords.join(',') === fbParams.keywords.join(','),
    actual: imported ? 'Import successful' : 'Import failed'
  });
  
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

// Test search creation flow
window.testSearchCreation = async function() {
  console.log('🔍 Testing Search Creation Flow...\n');
  
  // 1. Create a search
  const search = {
    platform: 'facebook',
    keywords: ['rtx 4090', 'gaming pc'],
    minPrice: 1000,
    maxPrice: 3000,
    location: { radius: 50 },
    condition: ['used'],
    name: 'High-end RTX 4090 PCs',
    interval: 30,
    notifications: true,
    enabled: true,
    facebook: {
      sortBy: 'date',
      daysSinceListed: 3
    }
  };
  
  console.log('1️⃣ Created search configuration');
  console.log(search);
  
  // 2. Validate
  const validation = window.searchBuilder.validateParameters(search);
  console.log('\n2️⃣ Validation:', validation.valid ? '✅ Passed' : `❌ Failed: ${validation.errors.join(', ')}`);
  
  // 3. Build URL
  const url = window.searchBuilder.buildUrl(search);
  console.log('\n3️⃣ Generated URL:');
  console.log(url);
  
  // 4. Save to settings
  if (window.settingsManager) {
    const settings = window.settingsManager.get();
    if (!settings.search) settings.search = { savedSearches: [] };
    
    search.id = `search_${Date.now()}`;
    search.created = new Date().toISOString();
    settings.search.savedSearches.push(search);
    
    await window.settingsManager.save(settings);
    console.log('\n4️⃣ Saved to settings ✅');
    console.log('Total saved searches:', settings.search.savedSearches.length);
  }
  
  // 5. Test the URL
  console.log('\n5️⃣ To test the search:');
  console.log('- Copy this URL:', url);
  console.log('- Open in new tab');
  console.log('- Extension will auto-scan when loaded');
  
  return { search, url };
};

// Check if search builder is properly integrated
window.checkSearchBuilderIntegration = function() {
  console.log('🔍 Checking Search Builder Integration...\n');
  
  const checks = {
    'Search builder loaded': window.searchBuilder !== undefined,
    'Settings manager loaded': window.settingsManager !== undefined,
    'Dashboard loaded': window.dashboard !== undefined,
    'Can create searches': typeof window.searchBuilder?.createDefaultSearch === 'function',
    'Can build URLs': typeof window.searchBuilder?.buildUrl === 'function',
    'Can validate': typeof window.searchBuilder?.validateParameters === 'function'
  };
  
  console.log('System Checks:');
  Object.entries(checks).forEach(([name, ready]) => {
    console.log(`${ready ? '✅' : '❌'} ${name}`);
  });
  
  // Check saved searches
  if (window.settingsManager) {
    const settings = window.settingsManager.get();
    const searches = settings.search?.savedSearches || [];
    console.log(`\nSaved searches: ${searches.length}`);
    
    searches.forEach((search, i) => {
      console.log(`${i + 1}. ${search.name || 'Unnamed'} (${search.platform}) - ${search.enabled ? 'Enabled' : 'Disabled'}`);
    });
  }
  
  const ready = Object.values(checks).every(v => v);
  console.log(`\n${ready ? '✅' : '❌'} Search builder ${ready ? 'ready' : 'not ready'}`);
  
  return ready;
};