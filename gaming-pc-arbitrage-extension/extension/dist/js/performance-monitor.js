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
