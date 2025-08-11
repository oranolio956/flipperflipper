import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { App } from '../src/ui/App';
import { ROUTES, NAV_GROUPS } from '../src/ui/router/routes';

describe('Routing Smoke Test', () => {
  it('renders without crashing', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );
  });

  it('displays Dashboard by default', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );
    
    // Wait for lazy load
    const heading = await screen.findByTestId('page-title');
    expect(heading).toHaveTextContent('Dashboard');
  });

  it('navigates to all main routes', async () => {
    const user = userEvent.setup();
    
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );

    // Test each route group
    for (const group of NAV_GROUPS) {
      for (const routeName of group.routes) {
        const route = ROUTES[routeName];
        
        // Click the nav link
        const navLink = await screen.findByTestId(route.testId);
        await user.click(navLink);
        
        // Verify page loaded
        const heading = await screen.findByTestId('page-title');
        expect(heading).toHaveTextContent(route.title);
        
        // Verify nav link is active
        expect(navLink).toHaveClass('bg-indigo-50');
      }
    }
  });

  it('Dashboard and Settings buttons work', async () => {
    const user = userEvent.setup();
    
    render(
      <MemoryRouter initialEntries={['/scanner']}>
        <App />
      </MemoryRouter>
    );

    // Click Dashboard button
    const dashboardBtn = await screen.findByTestId('dashboard-button');
    await user.click(dashboardBtn);
    
    let heading = await screen.findByTestId('page-title');
    expect(heading).toHaveTextContent('Dashboard');

    // Click Settings button
    const settingsBtn = await screen.findByTestId('settings-button');
    await user.click(settingsBtn);
    
    heading = await screen.findByTestId('page-title');
    expect(heading).toHaveTextContent('Settings');
  });

  it('shows 404 for unknown routes', async () => {
    render(
      <MemoryRouter initialEntries={['/unknown-route']}>
        <App />
      </MemoryRouter>
    );

    const notFound = await screen.findByText('404');
    expect(notFound).toBeInTheDocument();
  });
});