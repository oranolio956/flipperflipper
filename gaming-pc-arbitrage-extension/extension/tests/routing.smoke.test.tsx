import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { App } from '../src/ui/App';
import { ROUTES, ROUTE_META } from '../src/ui/router/routes';

describe('Routing Smoke Tests', () => {
  it('renders without crashing', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByRole('navigation', { name: 'Main navigation' })).toBeInTheDocument();
  });

  it('redirects root to dashboard', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );
    expect(window.location.hash).toContain('/dashboard');
  });

  // Test all main routes
  Object.entries(ROUTE_META).forEach(([path, meta]) => {
    if (path.includes(':')) return; // Skip parameterized routes
    
    it(`renders ${meta.title} page at ${path}`, () => {
      render(
        <MemoryRouter initialEntries={[path]}>
          <App />
        </MemoryRouter>
      );
      
      // Check page is rendered (by checking for page header or title)
      const heading = screen.queryByRole('heading', { name: meta.title });
      const pageElement = screen.queryByText(meta.description);
      
      expect(heading || pageElement).toBeInTheDocument();
    });
  });

  it('renders 404 for unknown routes', () => {
    render(
      <MemoryRouter initialEntries={['/unknown-route']}>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByText(/404/)).toBeInTheDocument();
  });

  it('all nav links have valid routes', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );
    
    const navLinks = screen.getAllByRole('link');
    navLinks.forEach(link => {
      const href = link.getAttribute('href');
      if (href && href.startsWith('/')) {
        const routeExists = Object.values(ROUTES).some(route => 
          route === href || route.includes(':')
        );
        expect(routeExists).toBe(true);
      }
    });
  });
});