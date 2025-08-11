/**
 * Route definitions with type safety
 * Apple-grade navigation architecture
 */

export const ROUTES = {
  dashboard: {
    path: '/',
    title: 'Dashboard',
    icon: 'layout-dashboard',
    testId: 'route-dashboard'
  },
  scanner: {
    path: '/scanner',
    title: 'Scanner',
    icon: 'scan',
    testId: 'route-scanner'
  },
  pipeline: {
    path: '/pipeline',
    title: 'Pipeline',
    icon: 'git-pull-request',
    testId: 'route-pipeline'
  },
  inventory: {
    path: '/inventory',
    title: 'Inventory',
    icon: 'package',
    testId: 'route-inventory'
  },
  routes: {
    path: '/routes',
    title: 'Routes',
    icon: 'map-pin',
    testId: 'route-routes'
  },
  finance: {
    path: '/finance',
    title: 'Finance',
    icon: 'dollar-sign',
    testId: 'route-finance'
  },
  comps: {
    path: '/comps',
    title: 'Comps',
    icon: 'bar-chart-2',
    testId: 'route-comps'
  },
  analytics: {
    path: '/analytics',
    title: 'Analytics',
    icon: 'trending-up',
    testId: 'route-analytics'
  },
  experiments: {
    path: '/experiments',
    title: 'Experiments',
    icon: 'flask',
    testId: 'route-experiments'
  },
  automation: {
    path: '/automation',
    title: 'Automation',
    icon: 'cpu',
    testId: 'route-automation'
  },
  team: {
    path: '/team',
    title: 'Team',
    icon: 'users',
    testId: 'route-team'
  },
  settings: {
    path: '/settings',
    title: 'Settings',
    icon: 'settings',
    testId: 'route-settings'
  },
  integrations: {
    path: '/integrations',
    title: 'Integrations',
    icon: 'plug',
    testId: 'route-integrations'
  },
  help: {
    path: '/help',
    title: 'Help',
    icon: 'help-circle',
    testId: 'route-help'
  },
  features: {
    path: '/features',
    title: 'Features',
    icon: 'layers',
    testId: 'route-features'
  }
} as const;

export type RouteName = keyof typeof ROUTES;
export type Route = typeof ROUTES[RouteName];

// Type-safe route builder
export function buildRoute(name: RouteName, params?: Record<string, string>): string {
  const route = ROUTES[name];
  let path = route.path;
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      path = path.replace(`:${key}`, value);
    });
  }
  
  return path;
}

// Navigation groups for sidebar
export const NAV_GROUPS = [
  {
    label: 'Core',
    routes: ['dashboard', 'scanner', 'pipeline'] as RouteName[]
  },
  {
    label: 'Operations',
    routes: ['inventory', 'routes', 'finance'] as RouteName[]
  },
  {
    label: 'Intelligence',
    routes: ['comps', 'analytics', 'experiments'] as RouteName[]
  },
  {
    label: 'System',
    routes: ['automation', 'team', 'settings', 'integrations'] as RouteName[]
  },
  {
    label: 'Support',
    routes: ['help', 'features'] as RouteName[]
  }
];

// Quick access routes for command palette
export const QUICK_ACCESS_ROUTES = [
  'dashboard',
  'scanner',
  'pipeline',
  'automation',
  'settings'
] as RouteName[];