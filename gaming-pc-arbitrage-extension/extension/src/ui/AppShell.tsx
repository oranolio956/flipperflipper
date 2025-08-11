import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Scan, 
  GitPullRequest, 
  Package,
  MapPin,
  DollarSign,
  BarChart2,
  TrendingUp,
  Flask,
  Cpu,
  Users,
  Settings,
  Plug,
  HelpCircle,
  Layers,
  Menu,
  X
} from 'lucide-react';
import { NavLink } from './router/NavLink';
import { VersionHUD } from './components/VersionHUD';
import { ROUTES, NAV_GROUPS } from './router/routes';
import { cn } from '@/lib/utils';

const iconMap = {
  'layout-dashboard': LayoutDashboard,
  'scan': Scan,
  'git-pull-request': GitPullRequest,
  'package': Package,
  'map-pin': MapPin,
  'dollar-sign': DollarSign,
  'bar-chart-2': BarChart2,
  'trending-up': TrendingUp,
  'flask': Flask,
  'cpu': Cpu,
  'users': Users,
  'settings': Settings,
  'plug': Plug,
  'help-circle': HelpCircle,
  'layers': Layers
};

export function AppShell() {
  const [sidebarOpen, setSidebarOpen] = React.useState(true);
  const location = useLocation();

  // Find current page title
  const currentRoute = Object.values(ROUTES).find(r => r.path === location.pathname);
  const pageTitle = currentRoute?.title || 'Gaming PC Arbitrage';

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <aside 
        className={cn(
          "flex flex-col w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700",
          "transition-all duration-200 ease-in-out",
          !sidebarOpen && "-ml-64"
        )}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200 dark:border-gray-700">
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
            PC Arbitrage Pro
          </h1>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4">
          {NAV_GROUPS.map((group) => (
            <div key={group.label} className="mb-6">
              <h2 className="px-6 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                {group.label}
              </h2>
              <div className="px-3">
                {group.routes.map((routeName) => {
                  const route = ROUTES[routeName];
                  const Icon = iconMap[route.icon as keyof typeof iconMap];
                  
                  return (
                    <NavLink
                      key={routeName}
                      to={route.path}
                      icon={Icon && <Icon className="w-4 h-4" />}
                      data-testid={route.testId}
                    >
                      {route.title}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Version HUD */}
        <VersionHUD />
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        {/* Top bar */}
        <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="h-full px-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <Menu className="w-5 h-5" />
              </button>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {pageTitle}
              </h2>
            </div>
            
            {/* Quick actions */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => chrome.runtime.sendMessage({ action: 'openDashboard' })}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
                data-testid="dashboard-button"
              >
                Dashboard
              </button>
              <button
                onClick={() => chrome.runtime.sendMessage({ action: 'openSettings' })}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
                data-testid="settings-button"
              >
                Settings
              </button>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-6 py-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}