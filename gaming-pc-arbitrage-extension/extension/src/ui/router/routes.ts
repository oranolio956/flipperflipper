/**
 * Centralized route definitions for type-safe navigation
 */

export const ROUTES = {
  HOME: '/',
  DASHBOARD: '/dashboard',
  SCANNER: '/scanner',
  PIPELINE: '/pipeline',
  LISTING_DETAIL: '/listing/:id',
  COMPS: '/comps',
  FINANCE: '/finance',
  INVENTORY: '/inventory',
  ROUTES_PLANNER: '/routes',
  ANALYTICS: '/analytics',
  EXPERIMENTS: '/experiments',
  TEAM: '/team',
  SETTINGS: '/settings',
  AUTOMATION: '/automation',
  HELP: '/help',
} as const;

export type RoutePath = typeof ROUTES[keyof typeof ROUTES];

// Route metadata for navigation and breadcrumbs
export const ROUTE_META = {
  [ROUTES.HOME]: {
    title: 'Home',
    icon: 'Home',
    description: 'Overview and quick actions',
  },
  [ROUTES.DASHBOARD]: {
    title: 'Dashboard',
    icon: 'LayoutDashboard',
    description: 'Performance metrics and insights at a glance',
  },
  [ROUTES.SCANNER]: {
    title: 'Scanner',
    icon: 'Scan',
    description: 'Scan and triage marketplace listings',
  },
  [ROUTES.PIPELINE]: {
    title: 'Deal Pipeline',
    icon: 'GitPullRequest',
    description: 'Track deals through stages',
  },
  [ROUTES.LISTING_DETAIL]: {
    title: 'Listing',
    icon: 'FileText',
    description: 'Detailed listing analysis',
    hidden: true, // Don't show in main nav
  },
  [ROUTES.COMPS]: {
    title: 'Comps',
    icon: 'BarChart3',
    description: 'Component pricing database',
  },
  [ROUTES.FINANCE]: {
    title: 'Finance',
    icon: 'DollarSign',
    description: 'P&L and cash flow tracking',
  },
  [ROUTES.INVENTORY]: {
    title: 'Inventory',
    icon: 'Package',
    description: 'Parts and systems tracking',
  },
  [ROUTES.ROUTES_PLANNER]: {
    title: 'Routes',
    icon: 'Route',
    description: 'Multi-stop pickup planning',
  },
  [ROUTES.ANALYTICS]: {
    title: 'Analytics',
    icon: 'TrendingUp',
    description: 'Performance insights and trends',
  },
  [ROUTES.EXPERIMENTS]: {
    title: 'Experiments',
    icon: 'FlaskConical',
    description: 'A/B test results',
  },
  [ROUTES.TEAM]: {
    title: 'Team',
    icon: 'Users',
    description: 'Manage team members',
  },
  [ROUTES.SETTINGS]: {
    title: 'Settings',
    icon: 'Settings',
    description: 'Configure your preferences',
  },
  [ROUTES.AUTOMATION]: {
    title: 'Automation Center',
    icon: 'Zap',
    description: 'Max Auto controls and status',
  },
  [ROUTES.HELP]: {
    title: 'Help',
    icon: 'HelpCircle',
    description: 'Guides and support',
  },
} as const;

// Helper to build parameterized routes
export function buildRoute(route: string, params: Record<string, string>): string {
  let path = route;
  Object.entries(params).forEach(([key, value]) => {
    path = path.replace(`:${key}`, value);
  });
  return path;
}

// Main navigation items (order matters)
export const MAIN_NAV_ROUTES = [
  ROUTES.DASHBOARD,
  ROUTES.SCANNER,
  ROUTES.PIPELINE,
  ROUTES.COMPS,
  ROUTES.FINANCE,
  ROUTES.INVENTORY,
  ROUTES.ROUTES_PLANNER,
  ROUTES.ANALYTICS,
] as const;

export const SECONDARY_NAV_ROUTES = [
  ROUTES.EXPERIMENTS,
  ROUTES.TEAM,
  ROUTES.AUTOMATION,
  ROUTES.SETTINGS,
  ROUTES.HELP,
] as const;