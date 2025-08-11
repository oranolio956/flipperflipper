import { ROUTES, ROUTE_META, buildRoute, MAIN_NAV_ROUTES } from '../src/ui/router/routes';

describe('Route Configuration Tests', () => {
  test('all routes are defined', () => {
    expect(Object.keys(ROUTES).length).toBeGreaterThan(10);
    expect(ROUTES.DASHBOARD).toBe('/dashboard');
    expect(ROUTES.SCANNER).toBe('/scanner');
    expect(ROUTES.LISTING_DETAIL).toBe('/listing/:id');
  });

  test('all routes have metadata', () => {
    Object.values(ROUTES).forEach(route => {
      if (!route.includes(':')) {
        expect(ROUTE_META[route]).toBeDefined();
        expect(ROUTE_META[route].title).toBeTruthy();
        expect(ROUTE_META[route].icon).toBeTruthy();
        expect(ROUTE_META[route].description).toBeTruthy();
      }
    });
  });

  test('buildRoute correctly replaces parameters', () => {
    const result = buildRoute(ROUTES.LISTING_DETAIL, { id: 'test-123' });
    expect(result).toBe('/listing/test-123');
  });

  test('main nav routes are correctly ordered', () => {
    expect(MAIN_NAV_ROUTES[0]).toBe(ROUTES.DASHBOARD);
    expect(MAIN_NAV_ROUTES[1]).toBe(ROUTES.SCANNER);
    expect(MAIN_NAV_ROUTES[2]).toBe(ROUTES.PIPELINE);
  });
});