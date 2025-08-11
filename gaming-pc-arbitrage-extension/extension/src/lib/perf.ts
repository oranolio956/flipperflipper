/**
 * Performance monitoring utilities
 */

interface PerfMark {
  name: string;
  startTime: number;
  endTime?: number;
  duration?: number;
}

class PerformanceMonitor {
  private marks: Map<string, PerfMark> = new Map();
  private logs: Array<{ timestamp: number; message: string; data?: any }> = [];
  private readonly MAX_LOGS = 100; // Ring buffer size

  // Start a performance mark
  mark(name: string): void {
    this.marks.set(name, {
      name,
      startTime: performance.now(),
    });
  }

  // End a performance mark and calculate duration
  measure(name: string): number {
    const mark = this.marks.get(name);
    if (!mark) {
      console.warn(`No mark found for: ${name}`);
      return 0;
    }

    mark.endTime = performance.now();
    mark.duration = mark.endTime - mark.startTime;
    
    this.log(`Perf: ${name}`, { duration: `${mark.duration.toFixed(2)}ms` });
    
    return mark.duration;
  }

  // Get all marks
  getMarks(): PerfMark[] {
    return Array.from(this.marks.values());
  }

  // Clear marks
  clearMarks(): void {
    this.marks.clear();
  }

  // Ring buffer logging
  log(message: string, data?: any): void {
    this.logs.push({
      timestamp: Date.now(),
      message,
      data,
    });

    // Maintain ring buffer size
    if (this.logs.length > this.MAX_LOGS) {
      this.logs.shift();
    }
  }

  // Get logs
  getLogs(): typeof this.logs {
    return [...this.logs];
  }

  // Performance report
  generateReport(): string {
    const marks = this.getMarks();
    const completed = marks.filter(m => m.duration !== undefined);
    
    if (completed.length === 0) {
      return 'No performance measurements available';
    }

    const total = completed.reduce((sum, m) => sum + (m.duration || 0), 0);
    const avg = total / completed.length;

    let report = '=== Performance Report ===\n';
    report += `Total measurements: ${completed.length}\n`;
    report += `Total time: ${total.toFixed(2)}ms\n`;
    report += `Average time: ${avg.toFixed(2)}ms\n\n`;
    
    report += 'Measurements:\n';
    completed
      .sort((a, b) => (b.duration || 0) - (a.duration || 0))
      .forEach(mark => {
        report += `  ${mark.name}: ${mark.duration?.toFixed(2)}ms\n`;
      });

    return report;
  }
}

// Singleton instance
export const perfMonitor = new PerformanceMonitor();

// Debounce utility
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  
  return function debounced(...args: Parameters<T>) {
    if (timeout) clearTimeout(timeout);
    
    timeout = setTimeout(() => {
      func(...args);
    }, wait);
  };
}

// Throttle utility
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle = false;
  
  return function throttled(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  };
}

// Memoization utility
export function memoize<T extends (...args: any[]) => any>(
  func: T,
  keyGenerator?: (...args: Parameters<T>) => string
): T {
  const cache = new Map<string, ReturnType<T>>();
  
  return ((...args: Parameters<T>) => {
    const key = keyGenerator ? keyGenerator(...args) : JSON.stringify(args);
    
    if (cache.has(key)) {
      perfMonitor.log('Cache hit', { function: func.name, key });
      return cache.get(key)!;
    }
    
    perfMonitor.mark(`memoize-${func.name}`);
    const result = func(...args);
    perfMonitor.measure(`memoize-${func.name}`);
    
    cache.set(key, result);
    return result;
  }) as T;
}

// Performance guards for critical operations
export const performanceGuards = {
  // Check if overlay render is within budget
  checkOverlayTTI(duration: number): boolean {
    const BUDGET = 120; // 120ms budget
    if (duration > BUDGET) {
      perfMonitor.log('Performance budget exceeded', {
        operation: 'overlay TTI',
        duration: `${duration.toFixed(2)}ms`,
        budget: `${BUDGET}ms`,
      });
      return false;
    }
    return true;
  },

  // Check if bulk scan is within budget
  checkBulkScan(itemCount: number, duration: number): boolean {
    const BUDGET_PER_100 = 6000; // 6s per 100 items
    const budget = (itemCount / 100) * BUDGET_PER_100;
    
    if (duration > budget) {
      perfMonitor.log('Performance budget exceeded', {
        operation: 'bulk scan',
        duration: `${duration.toFixed(2)}ms`,
        budget: `${budget.toFixed(2)}ms`,
        itemCount,
      });
      return false;
    }
    return true;
  },

  // Get performance metrics
  getMetrics(): {
    overlayTTI: number | null;
    bulkScanRate: number | null;
    memoryUsage: number | null;
  } {
    const overlayMark = perfMonitor.getMarks().find(m => m.name === 'overlay-tti');
    const bulkScanMark = perfMonitor.getMarks().find(m => m.name === 'bulk-scan');
    
    return {
      overlayTTI: overlayMark?.duration || null,
      bulkScanRate: bulkScanMark ? (bulkScanMark.duration || 0) / 100 : null,
      memoryUsage: (performance as any).memory?.usedJSHeapSize || null,
    };
  },
};

// Auto-cleanup old marks every 5 minutes
setInterval(() => {
  const marks = perfMonitor.getMarks();
  const now = performance.now();
  
  marks.forEach(mark => {
    if (mark.endTime && now - mark.endTime > 300000) { // 5 minutes
      perfMonitor.clearMarks();
    }
  });
}, 300000);