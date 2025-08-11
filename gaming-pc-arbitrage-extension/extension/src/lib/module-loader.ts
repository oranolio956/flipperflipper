/**
 * Module Loader v3.8.0 - Dynamic Import System
 * Implements code splitting and lazy loading for performance
 */

export interface ModuleConfig {
  name: string;
  path: string;
  dependencies?: string[];
  preload?: boolean;
  critical?: boolean;
}

export class ModuleLoader {
  private static instance: ModuleLoader;
  private loadedModules: Map<string, any> = new Map();
  private loadingPromises: Map<string, Promise<any>> = new Map();
  private moduleConfigs: Map<string, ModuleConfig> = new Map();
  
  // Performance metrics
  private loadTimes: Map<string, number> = new Map();
  private moduleSize: Map<string, number> = new Map();
  
  private constructor() {
    this.initializeModuleConfigs();
  }
  
  static getInstance(): ModuleLoader {
    if (!ModuleLoader.instance) {
      ModuleLoader.instance = new ModuleLoader();
    }
    return ModuleLoader.instance;
  }
  
  private initializeModuleConfigs() {
    // Define module configurations
    const configs: ModuleConfig[] = [
      // Core modules (always loaded)
      {
        name: 'router',
        path: '/js/router.js',
        critical: true
      },
      {
        name: 'settings-manager',
        path: '/js/settings-manager.js',
        critical: true
      },
      
      // Feature modules (lazy loaded)
      {
        name: 'search-builder',
        path: '/js/search-builder.js',
        dependencies: ['settings-manager']
      },
      {
        name: 'automation-engine',
        path: '/js/automation-engine.js',
        dependencies: ['settings-manager']
      },
      {
        name: 'parser',
        path: '/js/parser.js',
        preload: true
      },
      {
        name: 'pipeline-manager',
        path: '/js/pipeline-manager.js',
        dependencies: ['parser']
      },
      {
        name: 'settings-ui',
        path: '/js/settings-ui.js',
        dependencies: ['settings-config', 'settings-manager']
      },
      {
        name: 'settings-config',
        path: '/js/settings-config.js'
      },
      
      // Analytics modules
      {
        name: 'analytics',
        path: '/js/analytics.js',
        dependencies: ['settings-manager']
      },
      {
        name: 'charts',
        path: '/js/charts.js',
        dependencies: ['analytics']
      }
    ];
    
    configs.forEach(config => {
      this.moduleConfigs.set(config.name, config);
    });
  }
  
  /**
   * Load a module dynamically
   */
  async load(moduleName: string): Promise<any> {
    // Return if already loaded
    if (this.loadedModules.has(moduleName)) {
      return this.loadedModules.get(moduleName);
    }
    
    // Return existing loading promise to avoid duplicate loads
    if (this.loadingPromises.has(moduleName)) {
      return this.loadingPromises.get(moduleName);
    }
    
    const config = this.moduleConfigs.get(moduleName);
    if (!config) {
      throw new Error(`Unknown module: ${moduleName}`);
    }
    
    // Create loading promise
    const loadPromise = this.loadModule(config);
    this.loadingPromises.set(moduleName, loadPromise);
    
    try {
      const module = await loadPromise;
      this.loadedModules.set(moduleName, module);
      this.loadingPromises.delete(moduleName);
      return module;
    } catch (error) {
      this.loadingPromises.delete(moduleName);
      throw error;
    }
  }
  
  private async loadModule(config: ModuleConfig): Promise<any> {
    const startTime = performance.now();
    
    // Load dependencies first
    if (config.dependencies) {
      await Promise.all(
        config.dependencies.map(dep => this.load(dep))
      );
    }
    
    try {
      // For TypeScript modules, try dynamic import first
      if (config.path.endsWith('.ts')) {
        const module = await import(config.path.replace('.ts', '.js'));
        this.recordMetrics(config.name, startTime);
        return module;
      }
      
      // For JavaScript modules, use script injection
      return new Promise((resolve, reject) => {
        // Check if already in DOM
        const existingScript = document.querySelector(`script[data-module="${config.name}"]`);
        if (existingScript) {
          // Module already loaded, get from window
          const module = (window as any)[config.name];
          if (module) {
            this.recordMetrics(config.name, startTime);
            resolve(module);
            return;
          }
        }
        
        const script = document.createElement('script');
        script.src = config.path;
        script.setAttribute('data-module', config.name);
        
        script.onload = () => {
          // Try to get module from window
          const module = (window as any)[config.name];
          this.recordMetrics(config.name, startTime);
          
          if (module) {
            resolve(module);
          } else {
            // Module loaded but not exposed on window
            // This is fine for side-effect modules
            resolve(true);
          }
        };
        
        script.onerror = () => {
          reject(new Error(`Failed to load module: ${config.name}`));
        };
        
        document.head.appendChild(script);
      });
    } catch (error) {
      console.error(`Failed to load module ${config.name}:`, error);
      throw error;
    }
  }
  
  /**
   * Preload modules that might be needed soon
   */
  async preload(moduleNames: string[]): Promise<void> {
    const preloadPromises = moduleNames.map(name => {
      const config = this.moduleConfigs.get(name);
      if (config && !this.loadedModules.has(name)) {
        return this.load(name).catch(err => {
          console.warn(`Failed to preload ${name}:`, err);
        });
      }
      return Promise.resolve();
    });
    
    await Promise.all(preloadPromises);
  }
  
  /**
   * Load critical modules required for app initialization
   */
  async loadCriticalModules(): Promise<void> {
    const criticalModules = Array.from(this.moduleConfigs.values())
      .filter(config => config.critical)
      .map(config => config.name);
    
    await Promise.all(criticalModules.map(name => this.load(name)));
  }
  
  /**
   * Load modules marked for preloading
   */
  async loadPreloadModules(): Promise<void> {
    const preloadModules = Array.from(this.moduleConfigs.values())
      .filter(config => config.preload && !config.critical)
      .map(config => config.name);
    
    // Use requestIdleCallback for non-critical preloads
    if ('requestIdleCallback' in window) {
      window.requestIdleCallback(() => {
        this.preload(preloadModules);
      }, { timeout: 2000 });
    } else {
      // Fallback to setTimeout
      setTimeout(() => {
        this.preload(preloadModules);
      }, 1000);
    }
  }
  
  /**
   * Get module loading metrics
   */
  getMetrics(): {
    loadTimes: { [key: string]: number };
    totalLoadTime: number;
    moduleCount: number;
    averageLoadTime: number;
  } {
    const loadTimes: { [key: string]: number } = {};
    let totalLoadTime = 0;
    
    this.loadTimes.forEach((time, module) => {
      loadTimes[module] = time;
      totalLoadTime += time;
    });
    
    return {
      loadTimes,
      totalLoadTime,
      moduleCount: this.loadTimes.size,
      averageLoadTime: this.loadTimes.size > 0 ? totalLoadTime / this.loadTimes.size : 0
    };
  }
  
  private recordMetrics(moduleName: string, startTime: number) {
    const loadTime = performance.now() - startTime;
    this.loadTimes.set(moduleName, loadTime);
    
    if (window.DEBUG_MODE) {
      console.log(`[ModuleLoader] ${moduleName} loaded in ${loadTime.toFixed(2)}ms`);
    }
  }
  
  /**
   * Clear a module from cache (useful for hot reloading in dev)
   */
  clearModule(moduleName: string) {
    this.loadedModules.delete(moduleName);
    this.loadingPromises.delete(moduleName);
    this.loadTimes.delete(moduleName);
    
    // Remove script tag if exists
    const script = document.querySelector(`script[data-module="${moduleName}"]`);
    if (script) {
      script.remove();
    }
  }
  
  /**
   * Check if a module is loaded
   */
  isLoaded(moduleName: string): boolean {
    return this.loadedModules.has(moduleName);
  }
  
  /**
   * Get loaded module
   */
  getModule(moduleName: string): any {
    return this.loadedModules.get(moduleName);
  }
}

// Export singleton instance
export const moduleLoader = ModuleLoader.getInstance();