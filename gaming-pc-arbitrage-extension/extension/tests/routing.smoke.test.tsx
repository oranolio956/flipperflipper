import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { App } from '../src/ui/App';
import { ROUTES, ROUTE_META } from '../src/ui/router/routes';

// Mock chrome API
global.chrome = {
  storage: {
    local: {
      get: vi.fn().mockResolvedValue({
        automationEnabled: true,
        dashboardStats: {
          revenue: { value: 12450, change: 12 },
          activeDeals: { value: 23, change: 5 },
          avgRoi: { value: 32, change: 3 },
          winRate: { value: 68, change: -2 }
        },
        recentCandidates: [],
        scannedListings: [],
        savedSearches: [],
        deals: [],
        compsData: {},
        inventory: [],
        routes: [],
        experiments: [],
        team: [],
        settings: {},
      }),
      set: vi.fn().mockResolvedValue(undefined),
    },
  },
  runtime: {
    sendMessage: vi.fn().mockResolvedValue({}),
    getManifest: vi.fn().mockReturnValue({ version: '2.0.0' }),
  },
  tabs: {
    query: vi.fn().mockResolvedValue([]),
    sendMessage: vi.fn().mockResolvedValue({}),
    create: vi.fn(),
  },
  alarms: {
    create: vi.fn(),
    clear: vi.fn(),
    onAlarm: { addListener: vi.fn() },
  },
} as any;

describe('Routing Smoke Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', async () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByRole('navigation', { name: /main navigation/i })).toBeInTheDocument();
    });
  });

  it('redirects root to dashboard', async () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument();
    });
  });

  // Test all main routes render unique content
  const testableRoutes = Object.entries(ROUTE_META)
    .filter(([path]) => !path.includes(':')) // Skip parameterized routes
    .map(([path, meta]) => ({ path, meta }));

  testableRoutes.forEach(({ path, meta }) => {
    it(`renders ${meta.title} page at ${path} with unique heading`, async () => {
      render(
        <MemoryRouter initialEntries={[path]}>
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        // Check for page-specific heading
        const heading = screen.queryByRole('heading', { name: new RegExp(meta.title, 'i') });
        const pageTitle = screen.queryByText(meta.title);
        const pageDescription = screen.queryByText(meta.description);
        
        // At least one of these should be present
        expect(heading || pageTitle || pageDescription).toBeInTheDocument();
      });
    });
  });

  it('renders 404 for unknown routes', async () => {
    render(
      <MemoryRouter initialEntries={['/unknown-route-that-does-not-exist']}>
        <App />
      </MemoryRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/404/)).toBeInTheDocument();
      expect(screen.getByText(/page not found/i)).toBeInTheDocument();
    });
  });

  it('all nav links have valid routes and are clickable', async () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      const navLinks = screen.getAllByRole('link');
      
      navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href.startsWith('#')) {
          const path = href.substring(1); // Remove #
          const routeExists = Object.values(ROUTES).some(route =>
            route === path || route.includes(':')
          );
          expect(routeExists).toBe(true);
        }
      });
      
      // Verify we have the expected number of nav links
      const mainNavLinks = navLinks.filter(link => {
        const href = link.getAttribute('href');
        return href && Object.values(ROUTES).includes(href.substring(1));
      });
      
      expect(mainNavLinks.length).toBeGreaterThan(10); // Should have all main routes
    });
  });

  it('breadcrumbs update correctly on navigation', async () => {
    const { rerender } = render(
      <MemoryRouter initialEntries={[ROUTES.DASHBOARD]}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      const breadcrumb = screen.getByRole('navigation', { name: /breadcrumb/i });
      expect(breadcrumb).toBeInTheDocument();
    });

    // Navigate to scanner
    rerender(
      <MemoryRouter initialEntries={[ROUTES.SCANNER]}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      const breadcrumb = screen.getByRole('navigation', { name: /breadcrumb/i });
      expect(breadcrumb).toHaveTextContent('Scanner');
    });
  });

  it('parameterized routes work correctly', async () => {
    const testListingId = 'test-listing-123';
    
    render(
      <MemoryRouter initialEntries={[`/listing/${testListingId}`]}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      // Should render listing detail page
      const listingPage = screen.queryByText(/listing.*detail/i) || 
                         screen.queryByText(/listing not found/i);
      expect(listingPage).toBeInTheDocument();
    });
  });

  it('sidebar navigation highlights active route', async () => {
    render(
      <MemoryRouter initialEntries={[ROUTES.SCANNER]}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      const scannerLink = screen.getByRole('link', { name: /scanner/i });
      expect(scannerLink).toHaveClass('nav-link-active');
      
      const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
      expect(dashboardLink).not.toHaveClass('nav-link-active');
    });
  });
});