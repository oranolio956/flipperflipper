/**
 * Dashboard Router Configuration
 */

import React from 'react';
import { createHashRouter, Navigate, Outlet } from 'react-router-dom';
import { Home, Package, BarChart3, Settings as SettingsIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Pipeline } from './pages/Pipeline';
import { ListingDetail } from './pages/ListingDetail';
import { Settings } from './pages/Settings';

// Layout component with navigation
function Layout() {
  const location = window.location.hash.slice(1) || '/';
  
  const navItems = [
    { path: '/pipeline', label: 'Pipeline', icon: Package },
    { path: '/analytics', label: 'Analytics', icon: BarChart3 },
    { path: '/settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-card">
        <div className="p-6">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Home className="h-6 w-6" />
            Arbitrage Pro
          </h1>
        </div>
        
        <nav className="px-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.startsWith(item.path);
            
            return (
              <a
                key={item.path}
                href={`#${item.path}`}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive 
                    ? 'bg-primary text-primary-foreground' 
                    : 'hover:bg-accent hover:text-accent-foreground'
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </a>
            );
          })}
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}

// Create router
export const router = createHashRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Navigate to="/pipeline" replace />,
      },
      {
        path: 'pipeline',
        element: <Pipeline />,
      },
      {
        path: 'pipeline/:dealId',
        element: <ListingDetail />,
      },
      {
        path: 'analytics',
        element: <Pipeline />, // Reuse pipeline with charts for now
      },
      {
        path: 'settings',
        element: <Settings />,
      },
    ],
  },
]);