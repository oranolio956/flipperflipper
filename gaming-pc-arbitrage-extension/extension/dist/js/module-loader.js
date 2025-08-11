// Module Loader v3.8.0 - Production Implementation
class ModuleLoader {
  constructor() {
    this.loadedModules = new Map();
    this.loadingPromises = new Map();
    this.moduleConfigs = new Map();
    this.loadTimes = new Map();
    
    this.initializeModuleConfigs();
  }
  
  initializeModuleConfigs() {
    const configs = [
      {
        name: 'router',
        path: 'js/router.js',
        critical: true
      },
      {
        name: 'settingsManager',
        path: 'js/settings-manager.js',
        critical: true
      },
      {
        name: 'searchBuilder',
        path: 'js/search-builder.js',
        preload: true
      },
      {
        name: 'automationEngine',
        path: 'js/automation-engine.js',
        dependencies: ['searchBuilder']
      },
      {
        name: 'parser',
        path: 'js/parser.js'
      },
      {
        name: 'pipelineManager',
        path: 'js/pipeline-manager.js',
        dependencies: ['parser']
      }
    ];
    
    configs.forEach(config => {
      this.moduleConfigs.set(config.name, config);
    });
  }
  
  async loadModule(moduleName) {
    // Return if already loaded
    if (this.loadedModules.has(moduleName)) {
      return this.loadedModules.get(moduleName);
    }
    
    // Return existing promise if loading
    if (this.loadingPromises.has(moduleName)) {
      return this.loadingPromises.get(moduleName);
    }
    
    const config = this.moduleConfigs.get(moduleName);
    if (!config) {
      throw new Error(`Unknown module: ${moduleName}`);
    }
    
    const loadPromise = this.loadModuleInternal(config);
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
  
  async loadModuleInternal(config) {
    const startTime = performance.now();
    
    // Load dependencies first
    if (config.dependencies) {
      await Promise.all(
        config.dependencies.map(dep => this.loadModule(dep))
      );
    }
    
    // Load the module
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = config.path;
      script.async = true;
      
      script.onload = () => {
        const loadTime = performance.now() - startTime;
        this.loadTimes.set(config.name, loadTime);
        console.log(`[ModuleLoader] Loaded ${config.name} in ${loadTime.toFixed(2)}ms`);
        resolve(window[config.name]);
      };
      
      script.onerror = () => {
        reject(new Error(`Failed to load module: ${config.name}`));
      };
      
      document.head.appendChild(script);
    });
  }
  
  async loadCriticalModules() {
    const criticalModules = Array.from(this.moduleConfigs.entries())
      .filter(([name, config]) => config.critical)
      .map(([name]) => name);
    
    await Promise.all(criticalModules.map(name => this.loadModule(name)));
  }
  
  async preloadModules() {
    const preloadModules = Array.from(this.moduleConfigs.entries())
      .filter(([name, config]) => config.preload && !config.critical)
      .map(([name]) => name);
    
    // Use requestIdleCallback for non-critical preloads
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => {
        preloadModules.forEach(name => this.loadModule(name));
      });
    } else {
      setTimeout(() => {
        preloadModules.forEach(name => this.loadModule(name));
      }, 1000);
    }
  }
  
  getLoadTimes() {
    return Object.fromEntries(this.loadTimes);
  }
  
  isLoaded(moduleName) {
    return this.loadedModules.has(moduleName);
  }
  
  getLoadedModules() {
    return Array.from(this.loadedModules.keys());
  }
}

// Create singleton instance
window.moduleLoader = new ModuleLoader();
