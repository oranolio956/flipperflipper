// Optimization Test v3.8.0
// Tests for performance optimization systems

window.runOptimizationTest = async function() {
  console.log('🚀 Running Optimization Tests...\n');
  
  const results = [];
  
  // Test 1: Module loader exists
  console.log('Test 1: Checking module loader...');
  results.push({
    test: 'Module loader exists',
    pass: window.moduleLoader !== undefined,
    actual: typeof window.moduleLoader
  });
  
  // Test 2: Performance monitor exists
  console.log('Test 2: Checking performance monitor...');
  results.push({
    test: 'Performance monitor exists',
    pass: window.performanceMonitor !== undefined,
    actual: typeof window.performanceMonitor
  });
  
  // Test 3: Resource optimizer exists
  console.log('Test 3: Checking resource optimizer...');
  results.push({
    test: 'Resource optimizer exists',
    pass: window.resourceOptimizer !== undefined,
    actual: typeof window.resourceOptimizer
  });
  
  // Test 4: Module loading performance
  console.log('Test 4: Testing module loading...');
  const moduleStart = performance.now();
  
  try {
    // Load a test module
    await window.moduleLoader.load('settingsConfig');
    const loadTime = performance.now() - moduleStart;
    
    results.push({
      test: 'Module loads quickly',
      pass: loadTime < 100, // Should load in under 100ms
      actual: `${loadTime.toFixed(2)}ms`
    });
  } catch (e) {
    results.push({
      test: 'Module loads quickly',
      pass: false,
      actual: `Error: ${e.message}`
    });
  }
  
  // Test 5: Module caching
  console.log('Test 5: Testing module caching...');
  const cacheStart = performance.now();
  await window.moduleLoader.load('settingsConfig'); // Should be cached
  const cacheTime = performance.now() - cacheStart;
  
  results.push({
    test: 'Cached module loads instantly',
    pass: cacheTime < 5, // Should be near instant
    actual: `${cacheTime.toFixed(2)}ms`
  });
  
  // Test 6: Lazy loading
  console.log('Test 6: Testing lazy loading...');
  const lazyModules = ['analytics', 'charts'];
  let lazyLoadSuccess = true;
  
  for (const module of lazyModules) {
    if (window.moduleLoader.isLoaded(module)) {
      lazyLoadSuccess = false;
      break;
    }
  }
  
  results.push({
    test: 'Non-critical modules not loaded initially',
    pass: lazyLoadSuccess,
    actual: lazyLoadSuccess ? 'Not loaded' : 'Already loaded'
  });
  
  // Test 7: Performance metrics collection
  console.log('Test 7: Testing performance metrics...');
  window.performanceMonitor.start();
  
  // Wait a bit for metrics
  await new Promise(resolve => setTimeout(resolve, 100));
  
  const metrics = window.performanceMonitor.getMetrics();
  results.push({
    test: 'Performance metrics collected',
    pass: metrics && Object.keys(metrics).length > 0,
    actual: `${Object.keys(metrics).length} metric categories`
  });
  
  // Test 8: Image optimization
  console.log('Test 8: Testing image optimization...');
  const testImageUrl = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==';
  
  try {
    const optimized = await window.resourceOptimizer.optimizeImage(testImageUrl);
    results.push({
      test: 'Image optimization works',
      pass: optimized !== null,
      actual: optimized ? 'Optimized' : 'Failed'
    });
  } catch (e) {
    results.push({
      test: 'Image optimization works',
      pass: false,
      actual: `Error: ${e.message}`
    });
  }
  
  // Test 9: Data compression
  console.log('Test 9: Testing data compression...');
  const testData = Array(50).fill(null).map((_, i) => ({
    id: i,
    title: `Test Item ${i}`,
    price: 100 + i,
    platform: 'facebook',
    timestamp: Date.now()
  }));
  
  const compressed = window.resourceOptimizer.compressData(testData);
  const originalSize = JSON.stringify(testData).length;
  const compressedSize = JSON.stringify(compressed).length;
  
  results.push({
    test: 'Data compression reduces size',
    pass: compressedSize < originalSize,
    actual: `${((originalSize - compressedSize) / originalSize * 100).toFixed(1)}% reduction`
  });
  
  // Test 10: Memory optimization
  console.log('Test 10: Testing memory optimization...');
  const optimizations = window.resourceOptimizer.optimizeMemory();
  
  results.push({
    test: 'Memory optimization runs',
    pass: Array.isArray(optimizations),
    actual: `${optimizations.length} optimizations`
  });
  
  // Print results
  console.log('\n📊 Test Results:');
  results.forEach(result => {
    console.log(`${result.pass ? '✅' : '❌'} ${result.test}: ${result.actual}`);
  });
  
  const passed = results.filter(r => r.pass).length;
  const total = results.length;
  console.log(`\n🏁 Total: ${passed}/${total} tests passed`);
  
  // Stop performance monitor
  window.performanceMonitor.stop();
  
  return results;
};

// Test performance impact
window.testPerformanceImpact = async function() {
  console.log('📈 Testing Performance Impact...\n');
  
  // Baseline: Load all modules at once
  console.log('1️⃣ Baseline: Loading all modules synchronously');
  const baselineStart = performance.now();
  
  const allModules = [
    'router', 'settingsManager', 'searchBuilder', 
    'automationEngine', 'parser', 'pipelineManager',
    'settingsUI', 'settingsConfig'
  ];
  
  // Clear cache first
  allModules.forEach(m => window.moduleLoader.clearModule(m));
  
  // Load all at once
  for (const module of allModules) {
    const script = document.createElement('script');
    script.src = `js/${module.replace(/([A-Z])/g, '-$1').toLowerCase().replace(/^-/, '')}.js`;
    document.head.appendChild(script);
    await new Promise(resolve => script.onload = resolve);
  }
  
  const baselineTime = performance.now() - baselineStart;
  console.log(`Baseline load time: ${baselineTime.toFixed(2)}ms`);
  
  // Optimized: Use module loader
  console.log('\n2️⃣ Optimized: Using module loader with lazy loading');
  
  // Clear and reload
  location.reload();
};

// Monitor real-time performance
window.monitorRealTime = function(duration = 30000) {
  console.log(`📊 Monitoring real-time performance for ${duration/1000} seconds...\n`);
  
  window.performanceMonitor.start();
  
  const interval = setInterval(() => {
    const metrics = window.performanceMonitor.getMetrics();
    console.log('Current metrics:', {
      memory: metrics.memory?.percentUsed?.toFixed(1) + '%' || 'N/A',
      avgLatency: metrics.network?.avgLatency?.toFixed(0) + 'ms' || 'N/A',
      storage: metrics.storage?.percentUsed?.toFixed(1) + '%' || 'N/A'
    });
  }, 5000);
  
  setTimeout(() => {
    clearInterval(interval);
    window.performanceMonitor.stop();
    console.log('\n✅ Monitoring complete');
  }, duration);
};

// Test optimization strategies
window.testOptimizationStrategies = async function() {
  console.log('🔧 Testing Optimization Strategies...\n');
  
  // 1. Test image lazy loading
  console.log('1️⃣ Testing image lazy loading');
  
  // Create test images
  const container = document.createElement('div');
  container.style.height = '2000px';
  container.innerHTML = `
    <img data-lazy="https://via.placeholder.com/300x200" alt="Test 1" style="display: block; margin: 1000px 0;">
    <img data-lazy="https://via.placeholder.com/300x200" alt="Test 2" style="display: block;">
  `;
  document.body.appendChild(container);
  
  // Setup lazy loading
  window.resourceOptimizer.setupLazyLoading();
  
  console.log('✅ Lazy loading setup complete');
  
  // 2. Test storage optimization
  console.log('\n2️⃣ Testing storage optimization');
  
  // Add test data
  const testListings = Array(100).fill(null).map((_, i) => ({
    id: `test_${i}`,
    title: `Gaming PC ${i}`,
    price: 500 + Math.random() * 1000,
    description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
    specs: {
      cpu: 'Intel i7',
      gpu: 'RTX 3080',
      ram: '16GB',
      storage: '1TB SSD'
    }
  }));
  
  await chrome.storage.local.set({ testListings });
  
  // Optimize
  const result = await window.resourceOptimizer.optimizeStorage();
  console.log('✅ Storage optimized:', result);
  
  // 3. Test performance under load
  console.log('\n3️⃣ Testing performance under load');
  
  // Simulate heavy operation
  const heavyOperation = () => {
    const start = performance.now();
    let sum = 0;
    for (let i = 0; i < 1000000; i++) {
      sum += Math.sqrt(i);
    }
    return performance.now() - start;
  };
  
  // Run with monitoring
  window.performanceMonitor.start();
  const operationTime = heavyOperation();
  
  console.log(`✅ Heavy operation completed in ${operationTime.toFixed(2)}ms`);
  
  // Check if it was detected as a long task
  const metrics = window.performanceMonitor.getMetrics();
  const longTasks = metrics.runtime?.longTasks || [];
  console.log(`Long tasks detected: ${longTasks.length}`);
  
  // Cleanup
  document.body.removeChild(container);
  await chrome.storage.local.remove('testListings');
  window.performanceMonitor.stop();
  
  return true;
};

// Check optimization readiness
window.checkOptimizationReadiness = function() {
  console.log('🔍 Checking Optimization System...\n');
  
  const checks = {
    'Module loader ready': window.moduleLoader !== undefined,
    'Performance monitor ready': window.performanceMonitor !== undefined,
    'Resource optimizer ready': window.resourceOptimizer !== undefined,
    'Can load modules': typeof window.moduleLoader?.load === 'function',
    'Can monitor performance': typeof window.performanceMonitor?.start === 'function',
    'Can optimize resources': typeof window.resourceOptimizer?.optimizeImage === 'function'
  };
  
  console.log('System Checks:');
  Object.entries(checks).forEach(([name, ready]) => {
    console.log(`${ready ? '✅' : '❌'} ${name}`);
  });
  
  // Get current stats
  if (window.moduleLoader) {
    const moduleMetrics = window.moduleLoader.getMetrics();
    console.log('\nModule Loader Stats:');
    console.log(`- Modules loaded: ${moduleMetrics.moduleCount}`);
    console.log(`- Average load time: ${moduleMetrics.averageLoadTime.toFixed(2)}ms`);
    console.log(`- Total load time: ${moduleMetrics.totalLoadTime.toFixed(2)}ms`);
  }
  
  if (window.resourceOptimizer) {
    const optimizerStats = window.resourceOptimizer.getStats();
    console.log('\nResource Optimizer Stats:');
    console.log(`- Image cache: ${optimizerStats.imageCache.entries} entries`);
    console.log(`- Cache size: ${optimizerStats.imageCache.size}`);
    console.log(`- Data compression: ${optimizerStats.settings.enableDataCompression ? 'Enabled' : 'Disabled'}`);
  }
  
  const ready = Object.values(checks).every(v => v);
  console.log(`\n${ready ? '✅' : '❌'} Optimization system ${ready ? 'ready' : 'not ready'}`);
  
  return ready;
};