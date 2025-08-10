/**
 * Reliability Manager
 * Error handling, recovery, and fault tolerance
 */

export interface ErrorReport {
  id: string;
  timestamp: Date;
  error: {
    name: string;
    message: string;
    stack?: string;
  };
  context: {
    operation: string;
    platform?: string;
    userId?: string;
  };
  severity: 'critical' | 'high' | 'medium' | 'low';
  handled: boolean;
  recovery?: {
    attempted: boolean;
    successful: boolean;
    action: string;
  };
}

export interface HealthCheck {
  service: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  lastCheck: Date;
  latency?: number;
  error?: string;
}

export interface CircuitBreakerState {
  service: string;
  state: 'closed' | 'open' | 'half-open';
  failures: number;
  lastFailure?: Date;
  nextRetry?: Date;
}

/**
 * Error handler with recovery
 */
export class ErrorHandler {
  private errors: ErrorReport[] = [];
  private recoveryStrategies: Map<string, (error: Error, context: any) => Promise<boolean>> = new Map();
  
  /**
   * Handle error with recovery
   */
  async handle(
    error: Error,
    context: { operation: string; [key: string]: any },
    severity: ErrorReport['severity'] = 'medium'
  ): Promise<void> {
    const errorReport: ErrorReport = {
      id: generateErrorId(),
      timestamp: new Date(),
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack,
      },
      context,
      severity,
      handled: true,
    };
    
    // Attempt recovery
    const strategy = this.recoveryStrategies.get(context.operation);
    if (strategy) {
      try {
        const recovered = await strategy(error, context);
        errorReport.recovery = {
          attempted: true,
          successful: recovered,
          action: context.operation,
        };
      } catch (recoveryError) {
        errorReport.recovery = {
          attempted: true,
          successful: false,
          action: context.operation,
        };
      }
    }
    
    this.errors.push(errorReport);
    
    // Keep only last 100 errors
    if (this.errors.length > 100) {
      this.errors = this.errors.slice(-100);
    }
    
    // Log critical errors
    if (severity === 'critical') {
      console.error('[Critical Error]', errorReport);
    }
  }
  
  /**
   * Register recovery strategy
   */
  registerRecovery(
    operation: string,
    strategy: (error: Error, context: any) => Promise<boolean>
  ): void {
    this.recoveryStrategies.set(operation, strategy);
  }
  
  /**
   * Get error stats
   */
  getStats(since?: Date): {
    total: number;
    bySeverity: Record<string, number>;
    byOperation: Record<string, number>;
    recoveryRate: number;
  } {
    const filtered = since 
      ? this.errors.filter(e => e.timestamp > since)
      : this.errors;
    
    const bySeverity: Record<string, number> = {};
    const byOperation: Record<string, number> = {};
    let recovered = 0;
    let attempted = 0;
    
    filtered.forEach(error => {
      bySeverity[error.severity] = (bySeverity[error.severity] || 0) + 1;
      byOperation[error.context.operation] = (byOperation[error.context.operation] || 0) + 1;
      
      if (error.recovery?.attempted) {
        attempted++;
        if (error.recovery.successful) recovered++;
      }
    });
    
    return {
      total: filtered.length,
      bySeverity,
      byOperation,
      recoveryRate: attempted > 0 ? recovered / attempted : 0,
    };
  }
}

/**
 * Circuit breaker for fault tolerance
 */
export class CircuitBreaker {
  private states: Map<string, CircuitBreakerState> = new Map();
  private readonly defaultConfig = {
    threshold: 5,        // failures before opening
    timeout: 60000,      // 1 minute
    halfOpenTimeout: 30000, // 30 seconds
  };
  
  /**
   * Execute with circuit breaker
   */
  async execute<T>(
    service: string,
    operation: () => Promise<T>,
    config = this.defaultConfig
  ): Promise<T> {
    const state = this.getState(service);
    
    if (state.state === 'open') {
      if (state.nextRetry && new Date() < state.nextRetry) {
        throw new Error(`Circuit breaker open for ${service}`);
      }
      // Try half-open
      state.state = 'half-open';
    }
    
    try {
      const result = await operation();
      
      // Success - reset or close circuit
      if (state.state === 'half-open') {
        state.state = 'closed';
        state.failures = 0;
        state.lastFailure = undefined;
      }
      
      return result;
    } catch (error) {
      // Record failure
      state.failures++;
      state.lastFailure = new Date();
      
      // Check if should open circuit
      if (state.failures >= config.threshold) {
        state.state = 'open';
        state.nextRetry = new Date(Date.now() + config.timeout);
      }
      
      throw error;
    }
  }
  
  /**
   * Get circuit state
   */
  getState(service: string): CircuitBreakerState {
    if (!this.states.has(service)) {
      this.states.set(service, {
        service,
        state: 'closed',
        failures: 0,
      });
    }
    return this.states.get(service)!;
  }
  
  /**
   * Reset circuit
   */
  reset(service: string): void {
    this.states.delete(service);
  }
}

/**
 * Health monitor
 */
export class HealthMonitor {
  private checks: Map<string, HealthCheck> = new Map();
  private checkFunctions: Map<string, () => Promise<boolean>> = new Map();
  
  /**
   * Register health check
   */
  register(
    service: string,
    checkFn: () => Promise<boolean>
  ): void {
    this.checkFunctions.set(service, checkFn);
  }
  
  /**
   * Run health checks
   */
  async runChecks(): Promise<HealthCheck[]> {
    const results: HealthCheck[] = [];
    
    for (const [service, checkFn] of this.checkFunctions.entries()) {
      const start = Date.now();
      let status: HealthCheck['status'] = 'healthy';
      let error: string | undefined;
      
      try {
        const healthy = await checkFn();
        if (!healthy) {
          status = 'unhealthy';
        }
      } catch (e) {
        status = 'unhealthy';
        error = (e as Error).message;
      }
      
      const latency = Date.now() - start;
      
      const check: HealthCheck = {
        service,
        status,
        lastCheck: new Date(),
        latency,
        error,
      };
      
      this.checks.set(service, check);
      results.push(check);
    }
    
    return results;
  }
  
  /**
   * Get overall health
   */
  getHealth(): {
    status: 'healthy' | 'degraded' | 'unhealthy';
    services: HealthCheck[];
  } {
    const services = Array.from(this.checks.values());
    const unhealthy = services.filter(s => s.status === 'unhealthy');
    const degraded = services.filter(s => s.status === 'degraded');
    
    let status: 'healthy' | 'degraded' | 'unhealthy' = 'healthy';
    if (unhealthy.length > 0) status = 'unhealthy';
    else if (degraded.length > 0) status = 'degraded';
    
    return { status, services };
  }
}

/**
 * Retry with exponential backoff
 */
export async function retryWithBackoff<T>(
  operation: () => Promise<T>,
  options: {
    maxRetries?: number;
    initialDelay?: number;
    maxDelay?: number;
    factor?: number;
    onRetry?: (attempt: number, error: Error) => void;
  } = {}
): Promise<T> {
  const {
    maxRetries = 3,
    initialDelay = 1000,
    maxDelay = 30000,
    factor = 2,
    onRetry,
  } = options;
  
  let lastError: Error;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      
      if (attempt < maxRetries) {
        const delay = Math.min(
          initialDelay * Math.pow(factor, attempt),
          maxDelay
        );
        
        if (onRetry) {
          onRetry(attempt + 1, lastError);
        }
        
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  throw lastError!;
}

/**
 * Timeout wrapper
 */
export async function withTimeout<T>(
  operation: Promise<T>,
  timeoutMs: number,
  errorMessage = 'Operation timed out'
): Promise<T> {
  const timeout = new Promise<never>((_, reject) => {
    setTimeout(() => reject(new Error(errorMessage)), timeoutMs);
  });
  
  return Promise.race([operation, timeout]);
}

/**
 * Graceful degradation
 */
export class GracefulDegradation {
  private degradations: Map<string, { level: number; features: string[] }> = new Map();
  
  /**
   * Set degradation level
   */
  setDegradation(service: string, level: number): void {
    const features = this.getDisabledFeatures(service, level);
    this.degradations.set(service, { level, features });
  }
  
  /**
   * Check if feature is available
   */
  isFeatureAvailable(service: string, feature: string): boolean {
    const degradation = this.degradations.get(service);
    if (!degradation) return true;
    return !degradation.features.includes(feature);
  }
  
  /**
   * Get degradation status
   */
  getStatus(): Record<string, { level: number; features: string[] }> {
    const status: Record<string, any> = {};
    this.degradations.forEach((value, key) => {
      status[key] = value;
    });
    return status;
  }
  
  private getDisabledFeatures(service: string, level: number): string[] {
    // Define feature degradation by level
    const degradationMap: Record<string, Record<number, string[]>> = {
      'marketplace': {
        1: ['auto-refresh'],
        2: ['auto-refresh', 'price-history'],
        3: ['auto-refresh', 'price-history', 'competitor-tracking'],
      },
      'ml': {
        1: ['predictions'],
        2: ['predictions', 'anomaly-detection'],
        3: ['predictions', 'anomaly-detection', 'optimization'],
      },
    };
    
    return degradationMap[service]?.[level] || [];
  }
}

// Helper functions
function generateErrorId(): string {
  return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Global instances
export const errorHandler = new ErrorHandler();
export const circuitBreaker = new CircuitBreaker();
export const healthMonitor = new HealthMonitor();
export const gracefulDegradation = new GracefulDegradation();

// Register default recovery strategies
errorHandler.registerRecovery('parse', async (error, context) => {
  // Retry with fallback parser
  console.log('Attempting parse recovery');
  return false; // Placeholder
});

errorHandler.registerRecovery('storage', async (error, context) => {
  // Clear cache and retry
  console.log('Attempting storage recovery');
  return false; // Placeholder
});

// Register default health checks
healthMonitor.register('storage', async () => {
  // Check storage availability
  try {
    // Would check chrome.storage
    return true;
  } catch {
    return false;
  }
});

healthMonitor.register('memory', async () => {
  // Check memory usage
  if (performance.memory) {
    const usage = performance.memory.usedJSHeapSize / performance.memory.jsHeapSizeLimit;
    return usage < 0.9; // Less than 90%
  }
  return true;
});