import React from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ErrorBoundary } from 'react-error-boundary';
import { AppShell } from './AppShell';
import { ROUTES } from './router/routes';

// Lazy load pages for better performance
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Scanner = React.lazy(() => import('./pages/Scanner'));
const Pipeline = React.lazy(() => import('./pages/Pipeline'));
const Inventory = React.lazy(() => import('./pages/Inventory'));
const RoutePlanner = React.lazy(() => import('./pages/Routes'));
const Finance = React.lazy(() => import('./pages/Finance'));
const Comps = React.lazy(() => import('./pages/Comps'));
const Analytics = React.lazy(() => import('./pages/Analytics'));
const Experiments = React.lazy(() => import('./pages/Experiments'));
const AutomationCenter = React.lazy(() => import('./pages/AutomationCenter'));
const Team = React.lazy(() => import('./pages/Team'));
const Settings = React.lazy(() => import('./pages/Settings'));
const Integrations = React.lazy(() => import('./pages/Integrations'));
const Help = React.lazy(() => import('./pages/Help'));
const FeaturesIndex = React.lazy(() => import('./pages/FeaturesIndex'));
const ListingDetail = React.lazy(() => import('./pages/ListingDetail'));

// Error fallback component
function ErrorFallback({ error, resetErrorBoundary }: any) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <div className="max-w-md text-center">
        <h1 className="text-2xl font-bold text-red-600 mb-4">Something went wrong</h1>
        <pre className="text-sm bg-gray-100 p-4 rounded mb-4 text-left overflow-auto">
          {error.message}
        </pre>
        <button
          onClick={resetErrorBoundary}
          className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
        >
          Try again
        </button>
      </div>
    </div>
  );
}

// Loading component
function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="flex flex-col items-center gap-4">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-gray-500">Loading...</p>
      </div>
    </div>
  );
}

// 404 page
function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[600px]">
      <h1 className="text-6xl font-bold text-gray-300 mb-4">404</h1>
      <p className="text-xl text-gray-600 mb-8">Page not found</p>
      <a
        href="#/"
        className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
      >
        Go to Dashboard
      </a>
    </div>
  );
}

export function App() {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <HashRouter>
        <React.Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<AppShell />}>
              <Route index element={<Dashboard />} />
              <Route path={ROUTES.scanner.path} element={<Scanner />} />
              <Route path={ROUTES.pipeline.path} element={<Pipeline />} />
              <Route path={ROUTES.inventory.path} element={<Inventory />} />
              <Route path={ROUTES.routes.path} element={<RoutePlanner />} />
              <Route path={ROUTES.finance.path} element={<Finance />} />
              <Route path={ROUTES.comps.path} element={<Comps />} />
              <Route path={ROUTES.analytics.path} element={<Analytics />} />
              <Route path={ROUTES.experiments.path} element={<Experiments />} />
              <Route path={ROUTES.automation.path} element={<AutomationCenter />} />
              <Route path={ROUTES.team.path} element={<Team />} />
              <Route path={ROUTES.settings.path} element={<Settings />} />
              <Route path={ROUTES.integrations.path} element={<Integrations />} />
              <Route path={ROUTES.help.path} element={<Help />} />
              <Route path={ROUTES.features.path} element={<FeaturesIndex />} />
              <Route path="/listing/:id" element={<ListingDetail />} />
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
        </React.Suspense>
      </HashRouter>
    </ErrorBoundary>
  );
}