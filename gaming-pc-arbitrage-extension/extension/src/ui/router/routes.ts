// Type-safe routing system with compile-time route validation
// Inspired by Apple's NavigationStack patterns

export const ROUTES = {
  dashboard: {
    path: '/',
    title: 'Dashboard',
    icon: 'LayoutDashboard',
    testId: 'route-dashboard',
    component: () => import('../pages/Dashboard'),
    meta: {
      requiresAuth: false,
      trackingName: 'dashboard_view'
    }
  },
  scanner: {
    path: '/scanner',
    title: 'Scanner',
    icon: 'Scan',
    testId: 'route-scanner',
    component: () => import('../pages/Scanner'),
    meta: {
      requiresAuth: false,
      trackingName: 'scanner_view'
    }
  },
  pipeline: {
    path: '/pipeline',
    title: 'Pipeline',
    icon: 'GitBranch',
    testId: 'route-pipeline',
    component: () => import('../pages/Pipeline'),
    meta: {
      requiresAuth: false,
      trackingName: 'pipeline_view'
    }
  },
  automation: {
    path: '/automation',
    title: 'Automation',
    icon: 'Zap',
    testId: 'route-automation',
    component: () => import('../pages/AutomationCenter'),
    meta: {
      requiresAuth: false,
      trackingName: 'automation_view'
    }
  },
  inventory: {
    path: '/inventory',
    title: 'Inventory',
    icon: 'Package',
    testId: 'route-inventory',
    component: () => import('../pages/Inventory'),
    meta: {
      requiresAuth: false,
      trackingName: 'inventory_view'
    }
  },
  routes: {
    path: '/routes',
    title: 'Routes',
    icon: 'Map',
    testId: 'route-routes',
    component: () => import('../pages/Routes'),
    meta: {
      requiresAuth: false,
      trackingName: 'routes_view'
    }
  },
  finance: {
    path: '/finance',
    title: 'Finance',
    icon: 'DollarSign',
    testId: 'route-finance',
    component: () => import('../pages/Finance'),
    meta: {
      requiresAuth: false,
      trackingName: 'finance_view'
    }
  },
  comps: {
    path: '/comps',
    title: 'Comps',
    icon: 'BarChart3',
    testId: 'route-comps',
    component: () => import('../pages/Comps'),
    meta: {
      requiresAuth: false,
      trackingName: 'comps_view'
    }
  },
  analytics: {
    path: '/analytics',
    title: 'Analytics',
    icon: 'TrendingUp',
    testId: 'route-analytics',
    component: () => import('../pages/Analytics'),
    meta: {
      requiresAuth: false,
      trackingName: 'analytics_view'
    }
  },
  experiments: {
    path: '/experiments',
    title: 'Experiments',
    icon: 'Flask',
    testId: 'route-experiments',
    component: () => import('../pages/Experiments'),
    meta: {
      requiresAuth: false,
      trackingName: 'experiments_view'
    }
  },
  team: {
    path: '/team',
    title: 'Team',
    icon: 'Users',
    testId: 'route-team',
    component: () => import('../pages/Team'),
    meta: {
      requiresAuth: false,
      trackingName: 'team_view'
    }
  },
  settings: {
    path: '/settings',
    title: 'Settings',
    icon: 'Settings',
    testId: 'route-settings',
    component: () => import('../pages/Settings'),
    meta: {
      requiresAuth: false,
      trackingName: 'settings_view'
    }
  },
  integrations: {
    path: '/integrations',
    title: 'Integrations',
    icon: 'Plug',
    testId: 'route-integrations',
    component: () => import('../pages/Integrations'),
    meta: {
      requiresAuth: false,
      trackingName: 'integrations_view'
    }
  },
  help: {
    path: '/help',
    title: 'Help',
    icon: 'HelpCircle',
    testId: 'route-help',
    component: () => import('../pages/Help'),
    meta: {
      requiresAuth: false,
      trackingName: 'help_view'
    }
  },
  features: {
    path: '/features',
    title: 'Features',
    icon: 'Sparkles',
    testId: 'route-features',
    component: () => import('../pages/FeaturesIndex'),
    meta: {
      requiresAuth: false,
      trackingName: 'features_view'
    }
  },
  // Dynamic routes
  listing: {
    path: '/listing/:id',
    title: 'Listing Detail',
    icon: 'FileText',
    testId: 'route-listing-detail',
    component: () => import('../pages/ListingDetail'),
    meta: {
      requiresAuth: false,
      trackingName: 'listing_detail_view',
      breadcrumb: (params: { id: string }) => [
        { label: 'Pipeline', href: '/pipeline' },
        { label: 'Listing', href: `/listing/${params.id}` }
      ]
    }
  }
} as const;

// Type-safe route keys
export type RouteKey = keyof typeof ROUTES;
export type RoutePath = typeof ROUTES[RouteKey]['path'];

// Navigation groups for sidebar organization
export const NAV_GROUPS = [
  {
    label: 'Core',
    routes: ['dashboard', 'scanner', 'pipeline'] as const
  },
  {
    label: 'Operations', 
    routes: ['inventory', 'routes', 'finance'] as const
  },
  {
    label: 'Intelligence',
    routes: ['comps', 'analytics', 'experiments'] as const
  },
  {
    label: 'System',
    routes: ['automation', 'team', 'settings', 'integrations'] as const
  },
  {
    label: 'Support',
    routes: ['help', 'features'] as const
  }
] as const;

// Quick access routes for command palette
export const QUICK_ACCESS_ROUTES: RouteKey[] = [
  'dashboard',
  'scanner', 
  'pipeline',
  'settings'
];

// Helper to build type-safe routes with params
export function buildRoute<K extends RouteKey>(
  key: K,
  params?: K extends 'listing' ? { id: string } : never
): string {
  const route = ROUTES[key];
  if (!params) return route.path;
  
  let path = route.path;
  Object.entries(params).forEach(([key, value]) => {
    path = path.replace(`:${key}`, value);
  });
  return path;
}

// Route transition animations (60fps, Apple-style spring physics)
export const ROUTE_TRANSITIONS = {
  enter: {
    opacity: 0,
    x: 20,
    transition: {
      type: 'spring',
      stiffness: 380,
      damping: 30
    }
  },
  center: {
    opacity: 1,
    x: 0
  },
  exit: {
    opacity: 0,
    x: -20,
    transition: {
      type: 'spring', 
      stiffness: 380,
      damping: 30
    }
  }
} as const;

// Prefetch hints for performance
export const PREFETCH_ROUTES: RouteKey[] = [
  'scanner',
  'pipeline',
  'settings'
];

// Export route utils for testing
export const routeUtils = {
  isValidRoute: (path: string): boolean => {
    return Object.values(ROUTES).some(route => {
      const pattern = route.path.replace(/:[^/]+/g, '[^/]+');
      return new RegExp(`^${pattern}$`).test(path);
    });
  },
  
  getRouteByPath: (path: string): typeof ROUTES[RouteKey] | null => {
    return Object.values(ROUTES).find(route => {
      const pattern = route.path.replace(/:[^/]+/g, '[^/]+');
      return new RegExp(`^${pattern}$`).test(path);
    }) || null;
  },
  
  extractParams: (routePath: string, actualPath: string): Record<string, string> => {
    const params: Record<string, string> = {};
    const routeParts = routePath.split('/');
    const actualParts = actualPath.split('/');
    
    routeParts.forEach((part, index) => {
      if (part.startsWith(':')) {
        params[part.slice(1)] = actualParts[index];
      }
    });
    
    return params;
  }
};