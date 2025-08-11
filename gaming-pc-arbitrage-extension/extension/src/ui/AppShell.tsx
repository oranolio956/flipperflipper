import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { 
  Search, 
  Command, 
  User, 
  Bell, 
  HelpCircle,
  Zap,
  WifiOff,
  Shield,
  ChevronLeft,
  Menu
} from 'lucide-react';
import { NavLink, Breadcrumbs } from './router/NavLink';
import { MAIN_NAV_ROUTES, SECONDARY_NAV_ROUTES, ROUTE_META } from './router/routes';
import { CommandPalette } from './commands/CommandPalette';
import { Toast } from './design/components/Toast';
import { cn } from './lib/utils';

export function AppShell() {
  const [isCommandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [isSidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isOffline, setOffline] = useState(!navigator.onLine);
  const [automationStatus, setAutomationStatus] = useState<'active' | 'paused' | 'off'>('off');
  const location = useLocation();

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(true);
      }
      if ((e.metaKey || e.ctrlKey) && e.key === '\\') {
        e.preventDefault();
        setSidebarCollapsed(!isSidebarCollapsed);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSidebarCollapsed]);

  // Online/offline status
  useEffect(() => {
    const handleOnline = () => setOffline(false);
    const handleOffline = () => setOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Load automation status
  useEffect(() => {
    chrome.storage.local.get(['automationEnabled'], (result) => {
      setAutomationStatus(result.automationEnabled ? 'active' : 'off');
    });
  }, []);

  const currentMeta = ROUTE_META[location.pathname as keyof typeof ROUTE_META];

  return (
    <div className="app-shell">
      {/* Skip to content link for accessibility */}
      <a href="#main-content" className="skip-to-content">
        Skip to main content
      </a>

      {/* Top Bar */}
      <header className="top-bar" role="banner">
        <div className="top-bar-left">
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarCollapsed(!isSidebarCollapsed)}
            aria-label={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isSidebarCollapsed ? <Menu size={20} /> : <ChevronLeft size={20} />}
          </button>
          <Breadcrumbs />
        </div>

        <div className="top-bar-center">
          <div className="search-bar">
            <Search size={16} className="search-icon" />
            <input
              type="search"
              placeholder="Search listings, deals, or comps..."
              className="search-input"
              aria-label="Global search"
            />
          </div>
        </div>

        <div className="top-bar-right">
          <button
            className="top-bar-button"
            onClick={() => setCommandPaletteOpen(true)}
            aria-label="Open command palette"
            title="⌘K"
          >
            <Command size={18} />
          </button>

          <button
            className="top-bar-button"
            aria-label="Notifications"
          >
            <Bell size={18} />
            <span className="notification-badge">3</span>
          </button>

          <button
            className="top-bar-button"
            aria-label="Help"
          >
            <HelpCircle size={18} />
          </button>

          <button
            className="top-bar-button user-menu"
            aria-label="User menu"
          >
            <User size={18} />
          </button>
        </div>
      </header>

      {/* Left Sidebar */}
      <nav 
        className={cn('sidebar', isSidebarCollapsed && 'sidebar-collapsed')}
        role="navigation"
        aria-label="Main navigation"
      >
        <div className="sidebar-header">
          <div className="app-logo">
            <Shield size={24} />
            {!isSidebarCollapsed && <span>PC Arbitrage</span>}
          </div>
        </div>

        <div className="sidebar-content">
          <div className="nav-section">
            <ul className="nav-list">
              {MAIN_NAV_ROUTES.map((route) => (
                <li key={route}>
                  <NavLink 
                    to={route} 
                    showIcon 
                    className={cn(
                      'sidebar-link',
                      isSidebarCollapsed && 'sidebar-link-collapsed'
                    )}
                  />
                </li>
              ))}
            </ul>
          </div>

          <div className="nav-section nav-section-secondary">
            <ul className="nav-list">
              {SECONDARY_NAV_ROUTES.map((route) => (
                <li key={route}>
                  <NavLink 
                    to={route} 
                    showIcon 
                    className={cn(
                      'sidebar-link',
                      isSidebarCollapsed && 'sidebar-link-collapsed'
                    )}
                  />
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Status Tray */}
        <div className="status-tray">
          <div 
            className={cn('status-item', automationStatus === 'active' && 'status-active')}
            title={`Max Auto is ${automationStatus}. Click to manage.`}
          >
            <Zap size={16} />
            {!isSidebarCollapsed && (
              <span className="status-label">
                Auto: {automationStatus}
              </span>
            )}
          </div>

          {isOffline && (
            <div className="status-item status-warning" title="Working offline">
              <WifiOff size={16} />
              {!isSidebarCollapsed && <span className="status-label">Offline</span>}
            </div>
          )}
        </div>
      </nav>

      {/* Main Content */}
      <main 
        id="main-content" 
        className="main-content"
        role="main"
        aria-label={currentMeta?.title}
      >
        <Outlet />
      </main>

      {/* Command Palette */}
      <CommandPalette 
        isOpen={isCommandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
      />

      {/* Global Toast Container */}
      <Toast />
    </div>
  );
}