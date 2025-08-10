/**
 * Performance Monitor
 * Track and optimize extension performance
 */

export interface PerformanceMetric {
  name: string;
  category: 'api' | 'parse' | 'storage' | 'ui' | 'compute';
  duration: number; // milliseconds
  timestamp: Date;
  metadata?: Record<string, any>;
}

export interface PerformanceReport {
  period: { start: Date; end: Date };
  metrics: {
    avgResponseTime: number;
    p95ResponseTime: number;
    slowestOperations: Array<{ name: string; avgDuration: number }>;
    errorRate: number;
  };
  bottlenecks: Array<{
    area: string;
    impact: 'high' | 'medium' | 'low';
    recommendation: string;
  }>;
  resourceUsage: {
    memory: { current: number; peak: number; limit: number };
    storage: { used: number; available: number };
    cpu: { utilization: number };
  };
}

export interface CacheStats {
  hits: number;
  misses: number;
  evictions: number;
  hitRate: number;
  memoryUsed: number;
}

// Performance tracking
class PerformanceTracker {
  private metrics: PerformanceMetric[] = [];
  private cache = new Map<string, { value: any; expires: number }>();
  private cacheStats: CacheStats = {
    hits: 0,
    misses: 0,
    evictions: 0,
    hitRate: 0,
    memoryUsed: 0,
  };

  /**
   * Measure operation performance
   */
  async measure<T>(
    name: string,
    category: PerformanceMetric['category'],
    operation: () => Promise<T>
  ): Promise<T> {
    const start = performance.now();
    let error: Error | null = null;
    
    try {
      const result = await operation();
      return result;
    } catch (e) {
      error = e as Error;
      throw e;
    } finally {
      const duration = performance.now() - start;
      this.recordMetric({
        name,
        category,
        duration,
        timestamp: new Date(),
        metadata: error ? { error: error.message } : undefined,
      });
    }
  }

  /**
   * Record metric
   */
  recordMetric(metric: PerformanceMetric): void {
    this.metrics.push(metric);
    
    // Keep only last 1000 metrics
    if (this.metrics.length > 1000) {
      this.metrics = this.metrics.slice(-1000);
    }
  }

  /**
   * Get metrics
   */
  getMetrics(since?: Date): PerformanceMetric[] {
    if (!since) return this.metrics;
    return this.metrics.filter(m => m.timestamp > since);
  }

  /**
   * Cache operation result
   */
  async cached<T>(
    key: string,
    ttl: number, // seconds
    operation: () => Promise<T>
  ): Promise<T> {
    const now = Date.now();
    const cached = this.cache.get(key);
    
    if (cached && cached.expires > now) {
      this.cacheStats.hits++;
      this.updateCacheStats();
      return cached.value;
    }
    
    this.cacheStats.misses++;
    const result = await operation();
    
    // Evict expired entries
    this.evictExpired();
    
    this.cache.set(key, {
      value: result,
      expires: now + ttl * 1000,
    });
    
    this.updateCacheStats();
    return result;
  }

  /**
   * Clear cache
   */
  clearCache(pattern?: string): void {
    if (pattern) {
      for (const key of this.cache.keys()) {
        if (key.includes(pattern)) {
          this.cache.delete(key);
        }
      }
    } else {
      this.cache.clear();
    }
    this.updateCacheStats();
  }

  /**
   * Get cache stats
   */
  getCacheStats(): CacheStats {
    return { ...this.cacheStats };
  }

  private evictExpired(): void {
    const now = Date.now();
    let evicted = 0;
    
    for (const [key, entry] of this.cache.entries()) {
      if (entry.expires < now) {
        this.cache.delete(key);
        evicted++;
      }
    }
    
    this.cacheStats.evictions += evicted;
  }

  private updateCacheStats(): void {
    const total = this.cacheStats.hits + this.cacheStats.misses;
    this.cacheStats.hitRate = total > 0 ? this.cacheStats.hits / total : 0;
    
    // Estimate memory usage
    let memoryUsed = 0;
    for (const [key, entry] of this.cache.entries()) {
      memoryUsed += key.length + JSON.stringify(entry.value).length;
    }
    this.cacheStats.memoryUsed = memoryUsed;
  }
}

// Global instance
export const performanceTracker = new PerformanceTracker();

/**
 * Generate performance report
 */
export function generatePerformanceReport(
  metrics: PerformanceMetric[],
  period: { start: Date; end: Date }
): PerformanceReport {
  // Filter metrics by period
  const periodMetrics = metrics.filter(m => 
    m.timestamp >= period.start && m.timestamp <= period.end
  );
  
  // Calculate average response time
  const durations = periodMetrics.map(m => m.duration);
  const avgResponseTime = durations.length > 0
    ? durations.reduce((a, b) => a + b, 0) / durations.length
    : 0;
  
  // Calculate p95
  const sortedDurations = [...durations].sort((a, b) => a - b);
  const p95Index = Math.floor(sortedDurations.length * 0.95);
  const p95ResponseTime = sortedDurations[p95Index] || 0;
  
  // Find slowest operations
  const operationDurations: Record<string, number[]> = {};
  periodMetrics.forEach(m => {
    if (!operationDurations[m.name]) {
      operationDurations[m.name] = [];
    }
    operationDurations[m.name].push(m.duration);
  });
  
  const slowestOperations = Object.entries(operationDurations)
    .map(([name, durations]) => ({
      name,
      avgDuration: durations.reduce((a, b) => a + b, 0) / durations.length,
    }))
    .sort((a, b) => b.avgDuration - a.avgDuration)
    .slice(0, 5);
  
  // Calculate error rate
  const errorMetrics = periodMetrics.filter(m => m.metadata?.error);
  const errorRate = periodMetrics.length > 0
    ? errorMetrics.length / periodMetrics.length
    : 0;
  
  // Identify bottlenecks
  const bottlenecks = identifyBottlenecks(periodMetrics);
  
  // Get resource usage
  const resourceUsage = getResourceUsage();
  
  return {
    period,
    metrics: {
      avgResponseTime,
      p95ResponseTime,
      slowestOperations,
      errorRate,
    },
    bottlenecks,
    resourceUsage,
  };
}

/**
 * Optimize storage usage
 */
export async function optimizeStorage(): Promise<{
  before: number;
  after: number;
  freed: number;
}> {
  const before = await getStorageUsage();
  
  // Clean old data
  await cleanOldData();
  
  // Compress large objects
  await compressLargeObjects();
  
  // Deduplicate
  await deduplicateData();
  
  const after = await getStorageUsage();
  
  return {
    before,
    after,
    freed: before - after,
  };
}

/**
 * Memory leak detector
 */
export class MemoryLeakDetector {
  private snapshots: Array<{ time: number; memory: number }> = [];
  private threshold = 50 * 1024 * 1024; // 50MB growth
  
  start(): void {
    // Take snapshots every minute
    setInterval(() => {
      this.takeSnapshot();
    }, 60000);
  }
  
  stop(): void {
    this.snapshots = [];
  }
  
  private takeSnapshot(): void {
    if ('memory' in performance && performance.memory) {
      this.snapshots.push({
        time: Date.now(),
        memory: performance.memory.usedJSHeapSize,
      });
      
      // Keep only last 60 snapshots (1 hour)
      if (this.snapshots.length > 60) {
        this.snapshots.shift();
      }
      
      this.detectLeak();
    }
  }
  
  private detectLeak(): void {
    if (this.snapshots.length < 10) return;
    
    const recent = this.snapshots.slice(-10);
    const growth = recent[recent.length - 1].memory - recent[0].memory;
    
    if (growth > this.threshold) {
      console.warn('Potential memory leak detected', {
        growth: `${(growth / 1024 / 1024).toFixed(2)}MB`,
        period: '10 minutes',
      });
    }
  }
}

/**
 * Debounce function for performance
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  
  return function(...args: Parameters<T>) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Throttle function for performance
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  
  return function(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

/**
 * Batch operations for efficiency
 */
export class BatchProcessor<T> {
  private queue: T[] = [];
  private processing = false;
  
  constructor(
    private processor: (items: T[]) => Promise<void>,
    private batchSize = 50,
    private delay = 100
  ) {}
  
  add(item: T): void {
    this.queue.push(item);
    this.process();
  }
  
  private async process(): Promise<void> {
    if (this.processing || this.queue.length === 0) return;
    
    this.processing = true;
    
    while (this.queue.length > 0) {
      const batch = this.queue.splice(0, this.batchSize);
      await this.processor(batch);
      
      if (this.queue.length > 0) {
        await new Promise(resolve => setTimeout(resolve, this.delay));
      }
    }
    
    this.processing = false;
  }
}

// Helper functions
function identifyBottlenecks(metrics: PerformanceMetric[]): PerformanceReport['bottlenecks'] {
  const bottlenecks: PerformanceReport['bottlenecks'] = [];
  
  // Group by category
  const byCategory: Record<string, PerformanceMetric[]> = {};
  metrics.forEach(m => {
    byCategory[m.category] = byCategory[m.category] || [];
    byCategory[m.category].push(m);
  });
  
  // Check each category
  for (const [category, categoryMetrics] of Object.entries(byCategory)) {
    const avgDuration = categoryMetrics.reduce((sum, m) => sum + m.duration, 0) / categoryMetrics.length;
    
    if (category === 'parse' && avgDuration > 500) {
      bottlenecks.push({
        area: 'DOM Parsing',
        impact: avgDuration > 1000 ? 'high' : 'medium',
        recommendation: 'Optimize selectors and reduce DOM traversal',
      });
    }
    
    if (category === 'storage' && avgDuration > 200) {
      bottlenecks.push({
        area: 'Storage Operations',
        impact: avgDuration > 500 ? 'high' : 'medium',
        recommendation: 'Batch storage operations and use caching',
      });
    }
    
    if (category === 'compute' && avgDuration > 1000) {
      bottlenecks.push({
        area: 'Computation',
        impact: 'high',
        recommendation: 'Move heavy computations to Web Workers',
      });
    }
  }
  
  return bottlenecks;
}

function getResourceUsage(): PerformanceReport['resourceUsage'] {
  const memory = ('memory' in performance && performance.memory) ? {
    current: performance.memory.usedJSHeapSize,
    peak: performance.memory.jsHeapSizeLimit,
    limit: performance.memory.jsHeapSizeLimit,
  } : {
    current: 0,
    peak: 0,
    limit: 0,
  };
  
  return {
    memory,
    storage: { used: 0, available: 0 }, // Would query chrome.storage
    cpu: { utilization: 0 }, // Placeholder
  };
}

async function getStorageUsage(): Promise<number> {
  // Placeholder - would use chrome.storage.local.getBytesInUse
  return 1024 * 1024 * 10; // 10MB
}

async function cleanOldData(): Promise<void> {
  // Clean data older than retention period
}

async function compressLargeObjects(): Promise<void> {
  // Compress large JSON objects
}

async function deduplicateData(): Promise<void> {
  // Remove duplicate entries
}