import React, { useEffect } from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './AppShell';
import { ROUTES } from './router/routes';

// Pages
import { Dashboard } from './pages/Dashboard';
import { Scanner } from './pages/Scanner';
import { Pipeline } from './pages/Pipeline';
import { ListingDetail } from './pages/ListingDetail';
import { Comps } from './pages/Comps';
import { Finance } from './pages/Finance';
import { Inventory } from './pages/Inventory';
import { RoutesPlanner } from './pages/Routes';
import { Analytics } from './pages/Analytics';
import { Experiments } from './pages/Experiments';
import { Team } from './pages/Team';
import { Settings } from './pages/Settings';
import { AutomationCenter } from './pages/AutomationCenter';
import { Help } from './pages/Help';

// Styles
import './design/tokens.css';
import './styles/app.css';

export function App() {
  // Load theme preference
  useEffect(() => {
    const theme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', theme);
  }, []);

  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<Navigate to={ROUTES.DASHBOARD} replace />} />
          <Route path={ROUTES.DASHBOARD} element={<Dashboard />} />
          <Route path={ROUTES.SCANNER} element={<Scanner />} />
          <Route path={ROUTES.PIPELINE} element={<Pipeline />} />
          <Route path={ROUTES.LISTING_DETAIL} element={<ListingDetail />} />
          <Route path={ROUTES.COMPS} element={<Comps />} />
          <Route path={ROUTES.FINANCE} element={<Finance />} />
          <Route path={ROUTES.INVENTORY} element={<Inventory />} />
          <Route path={ROUTES.ROUTES_PLANNER} element={<RoutesPlanner />} />
          <Route path={ROUTES.ANALYTICS} element={<Analytics />} />
          <Route path={ROUTES.EXPERIMENTS} element={<Experiments />} />
          <Route path={ROUTES.TEAM} element={<Team />} />
          <Route path={ROUTES.SETTINGS} element={<Settings />} />
          <Route path={ROUTES.AUTOMATION} element={<AutomationCenter />} />
          <Route path={ROUTES.HELP} element={<Help />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}

// 404 Page
function NotFound() {
  return (
    <div className="not-found">
      <h1>404 - Page Not Found</h1>
      <p>The page you're looking for doesn't exist.</p>
      <a href={ROUTES.DASHBOARD}>Go to Dashboard</a>
    </div>
  );
}