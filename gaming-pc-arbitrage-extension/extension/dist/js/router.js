// SimpleRouter v3.5.0 - Lightweight hash-based router
class SimpleRouter {
  constructor() {
    this.routes = new Map();
    this.currentRoute = null;
    this.beforeRoute = null;
    this.afterRoute = null;
    this.notFound = null;
    this.baseTitle = document.title;
    
    // Bind navigation handler
    this.handleNavigation = this.handleNavigation.bind(this);
    
    // Start listening
    this.init();
  }
  
  init() {
    // Listen for hash changes
    window.addEventListener('hashchange', this.handleNavigation);
    window.addEventListener('popstate', this.handleNavigation);
    
    // Handle initial route
    this.handleNavigation();
  }
  
  // Register a route
  route(path, handler, options = {}) {
    this.routes.set(path, {
      handler,
      title: options.title,
      requiresAuth: options.requiresAuth || false,
      data: options.data || {}
    });
    return this;
  }
  
  // Register multiple routes
  routes(routeMap) {
    Object.entries(routeMap).forEach(([path, config]) => {
      if (typeof config === 'function') {
        this.route(path, config);
      } else {
        this.route(path, config.handler, config);
      }
    });
    return this;
  }
  
  // Navigate to a route
  navigate(path, options = {}) {
    if (options.replace) {
      window.location.replace(`#${path}`);
    } else {
      window.location.hash = path;
    }
  }
  
  // Handle navigation
  async handleNavigation(event) {
    const path = this.getCurrentPath();
    const route = this.findRoute(path);
    
    // Call before route hook
    if (this.beforeRoute) {
      const shouldContinue = await this.beforeRoute(path, route);
      if (shouldContinue === false) {
        if (event) event.preventDefault();
        return;
      }
    }
    
    // Handle route
    if (route) {
      try {
        // Update title
        if (route.title) {
          document.title = `${route.title} - ${this.baseTitle}`;
        }
        
        // Check auth if required
        if (route.requiresAuth && !this.checkAuth()) {
          this.navigate('/login');
          return;
        }
        
        // Execute handler
        const params = this.extractParams(path, route.pattern);
        await route.handler({
          path,
          params,
          query: this.getQueryParams(),
          route: route.data
        });
        
        this.currentRoute = path;
        
        // Call after route hook
        if (this.afterRoute) {
          await this.afterRoute(path, route);
        }
      } catch (error) {
        console.error('Route handler error:', error);
        if (this.errorHandler) {
          this.errorHandler(error, path);
        }
      }
    } else if (this.notFound) {
      this.notFound(path);
    } else {
      console.warn(`No route found for: ${path}`);
    }
  }
  
  // Get current path
  getCurrentPath() {
    return window.location.hash.slice(1) || '/';
  }
  
  // Find matching route
  findRoute(path) {
    // Direct match
    if (this.routes.has(path)) {
      return { ...this.routes.get(path), pattern: path };
    }
    
    // Pattern match (supports :param syntax)
    for (const [pattern, config] of this.routes) {
      if (this.matchPattern(path, pattern)) {
        return { ...config, pattern };
      }
    }
    
    return null;
  }
  
  // Match path against pattern
  matchPattern(path, pattern) {
    const pathParts = path.split('/').filter(Boolean);
    const patternParts = pattern.split('/').filter(Boolean);
    
    if (pathParts.length !== patternParts.length) {
      return false;
    }
    
    return patternParts.every((part, i) => {
      return part.startsWith(':') || part === pathParts[i];
    });
  }
  
  // Extract params from path
  extractParams(path, pattern) {
    const params = {};
    const pathParts = path.split('/').filter(Boolean);
    const patternParts = pattern.split('/').filter(Boolean);
    
    patternParts.forEach((part, i) => {
      if (part.startsWith(':')) {
        params[part.slice(1)] = pathParts[i];
      }
    });
    
    return params;
  }
  
  // Get query parameters
  getQueryParams() {
    const hash = window.location.hash;
    const queryIndex = hash.indexOf('?');
    
    if (queryIndex === -1) return {};
    
    const queryString = hash.slice(queryIndex + 1);
    const params = new URLSearchParams(queryString);
    const result = {};
    
    for (const [key, value] of params) {
      result[key] = value;
    }
    
    return result;
  }
  
  // Set hooks
  before(handler) {
    this.beforeRoute = handler;
    return this;
  }
  
  after(handler) {
    this.afterRoute = handler;
    return this;
  }
  
  notFoundHandler(handler) {
    this.notFound = handler;
    return this;
  }
  
  onError(handler) {
    this.errorHandler = handler;
    return this;
  }
  
  // Auth check (override this)
  checkAuth() {
    return true;
  }
  
  // Go back
  back() {
    window.history.back();
  }
  
  // Go forward
  forward() {
    window.history.forward();
  }
  
  // Remove all routes
  clear() {
    this.routes.clear();
    return this;
  }
  
  // Remove specific route
  remove(path) {
    this.routes.delete(path);
    return this;
  }
  
  // Get all routes
  getRoutes() {
    return Array.from(this.routes.entries()).map(([path, config]) => ({
      path,
      ...config
    }));
  }
  
  // Destroy router
  destroy() {
    window.removeEventListener('hashchange', this.handleNavigation);
    window.removeEventListener('popstate', this.handleNavigation);
    this.clear();
  }
}

// Create singleton instance
window.router = new SimpleRouter();