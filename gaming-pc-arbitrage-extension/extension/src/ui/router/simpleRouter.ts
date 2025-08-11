/**
 * Lightweight router implementation with Apple-level performance
 * No external dependencies - pure TypeScript
 */

export interface Route {
  path: string;
  title: string;
  icon: string;
  testId: string;
  component: () => Promise<any>;
  meta?: {
    requiresAuth?: boolean;
    trackingName?: string;
    breadcrumb?: (params: Record<string, string>) => Array<{ label: string; href: string }>;
  };
}

export class SimpleRouter {
  private routes: Map<string, Route> = new Map();
  private currentPath: string = '/';
  private listeners: Set<(path: string) => void> = new Set();
  private params: Record<string, string> = {};
  
  constructor() {
    // Listen to hash changes for SPA routing
    if (typeof window !== 'undefined') {
      window.addEventListener('hashchange', this.handleHashChange);
      window.addEventListener('popstate', this.handlePopState);
      
      // Set initial path
      this.currentPath = this.getHashPath();
    }
  }
  
  private handleHashChange = () => {
    const newPath = this.getHashPath();
    if (newPath !== this.currentPath) {
      this.navigate(newPath);
    }
  };
  
  private handlePopState = () => {
    this.navigate(this.getHashPath());
  };
  
  private getHashPath(): string {
    if (typeof window === 'undefined') return '/';
    const hash = window.location.hash.slice(1); // Remove #
    return hash || '/';
  }
  
  register(pattern: string, route: Route) {
    this.routes.set(pattern, route);
  }
  
  navigate(path: string, replace = false) {
    this.currentPath = path;
    this.params = this.extractParams(path);
    
    if (typeof window !== 'undefined') {
      if (replace) {
        window.history.replaceState(null, '', `#${path}`);
      } else {
        window.history.pushState(null, '', `#${path}`);
      }
    }
    
    // Notify listeners
    this.listeners.forEach(listener => listener(path));
  }
  
  getCurrentPath(): string {
    return this.currentPath;
  }
  
  getParams(): Record<string, string> {
    return { ...this.params };
  }
  
  subscribe(listener: (path: string) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
  
  private extractParams(actualPath: string): Record<string, string> {
    const params: Record<string, string> = {};
    
    // Find matching route
    for (const [pattern, _] of this.routes) {
      const regex = this.patternToRegex(pattern);
      const match = actualPath.match(regex);
      
      if (match) {
        // Extract param names from pattern
        const paramNames = (pattern.match(/:(\w+)/g) || []).map(p => p.slice(1));
        
        // Map values to param names
        paramNames.forEach((name, index) => {
          params[name] = match[index + 1];
        });
        
        break;
      }
    }
    
    return params;
  }
  
  private patternToRegex(pattern: string): RegExp {
    const regexPattern = pattern
      .replace(/\//g, '\\/')
      .replace(/:(\w+)/g, '([^/]+)');
    return new RegExp(`^${regexPattern}$`);
  }
  
  getRoute(path: string): Route | null {
    // Try exact match first
    if (this.routes.has(path)) {
      return this.routes.get(path)!;
    }
    
    // Try pattern matching
    for (const [pattern, route] of this.routes) {
      const regex = this.patternToRegex(pattern);
      if (regex.test(path)) {
        return route;
      }
    }
    
    return null;
  }
  
  getAllRoutes(): Route[] {
    return Array.from(this.routes.values());
  }
  
  destroy() {
    if (typeof window !== 'undefined') {
      window.removeEventListener('hashchange', this.handleHashChange);
      window.removeEventListener('popstate', this.handlePopState);
    }
    this.listeners.clear();
    this.routes.clear();
  }
}

// Create singleton instance
export const router = new SimpleRouter();

// React hook for using the router
export function useRouter() {
  const [currentPath, setCurrentPath] = React.useState(router.getCurrentPath());
  
  React.useEffect(() => {
    return router.subscribe(setCurrentPath);
  }, []);
  
  return {
    currentPath,
    params: router.getParams(),
    navigate: router.navigate.bind(router),
    getRoute: router.getRoute.bind(router)
  };
}

// Link component that works with our router
export function Link({ 
  to, 
  children, 
  className,
  onClick,
  ...props 
}: { 
  to: string; 
  children: React.ReactNode;
  className?: string;
  onClick?: (e: React.MouseEvent) => void;
}) {
  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    onClick?.(e);
    router.navigate(to);
  };
  
  return (
    <a 
      href={`#${to}`} 
      onClick={handleClick}
      className={className}
      {...props}
    >
      {children}
    </a>
  );
}

// NavLink with active state
export function NavLink({
  to,
  children,
  className,
  activeClassName = '',
  ...props
}: {
  to: string;
  children: React.ReactNode;
  className?: string | ((isActive: boolean) => string);
  activeClassName?: string;
}) {
  const { currentPath } = useRouter();
  const isActive = currentPath === to || currentPath.startsWith(to + '/');
  
  const finalClassName = typeof className === 'function' 
    ? className(isActive)
    : `${className || ''} ${isActive ? activeClassName : ''}`.trim();
  
  return (
    <Link to={to} className={finalClassName} {...props}>
      {typeof children === 'function' ? children({ isActive }) : children}
    </Link>
  );
}