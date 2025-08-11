import { describe, it, expect, beforeEach, vi } from 'vitest';
import { MaxAutoEngine } from '../src/background/maxAutoEngine';
import { SavedSearch } from '../src/types';

// Mock chrome APIs
const mockChrome = {
  storage: {
    local: {
      get: vi.fn().mockResolvedValue({}),
      set: vi.fn().mockResolvedValue(undefined),
    },
  },
  runtime: {
    sendMessage: vi.fn().mockResolvedValue({}),
  },
  alarms: {
    create: vi.fn(),
    clear: vi.fn(),
    onAlarm: {
      addListener: vi.fn(),
    },
  },
  idle: {
    queryState: vi.fn().mockResolvedValue('idle'),
  },
  tabs: {
    create: vi.fn().mockResolvedValue({ id: 123 }),
    remove: vi.fn(),
    sendMessage: vi.fn().mockResolvedValue({ success: true, candidates: [] }),
    onUpdated: {
      addListener: vi.fn(),
      removeListener: vi.fn(),
    },
  },
  scripting: {
    executeScript: vi.fn().mockResolvedValue([]),
    insertCSS: vi.fn().mockResolvedValue([]),
  },
  notifications: {
    create: vi.fn(),
  },
};

// @ts-ignore
global.chrome = mockChrome;

describe('MaxAutoEngine', () => {
  let engine: MaxAutoEngine;

  beforeEach(() => {
    vi.clearAllMocks();
    engine = new MaxAutoEngine();
  });

  describe('Initialization', () => {
    it('should initialize with stored state', async () => {
      const mockSearches: SavedSearch[] = [{
        id: 'search-1',
        name: 'RTX 3080 PCs',
        url: 'https://facebook.com/marketplace/search?query=rtx+3080',
        platform: 'facebook',
        enabled: true,
        cadenceMinutes: 30,
        createdAt: new Date().toISOString()
      }];

      mockChrome.storage.local.get.mockResolvedValueOnce({
        automationEnabled: true,
        savedSearches: mockSearches,
        lastRunTimes: { 'search-1': Date.now() - 1000000 }
      });

      await engine.initialize();

      expect(mockChrome.alarms.onAlarm.addListener).toHaveBeenCalled();
      const status = await engine.getStatus();
      expect(status.enabled).toBe(true);
      expect(status.activeSearchCount).toBe(1);
    });
  });

  describe('Enable/Disable', () => {
    it('should enable automation and schedule searches', async () => {
      await engine.enable();

      expect(mockChrome.storage.local.set).toHaveBeenCalledWith({ automationEnabled: true });
      expect(mockChrome.runtime.sendMessage).toHaveBeenCalledWith({
        type: 'AUTOMATION_STATUS_CHANGED',
        status: 'active'
      });
    });

    it('should disable automation and clear alarms', async () => {
      // Add a search first
      const search: SavedSearch = {
        id: 'search-1',
        name: 'Test Search',
        url: 'https://example.com',
        platform: 'facebook',
        enabled: true,
        cadenceMinutes: 30,
        createdAt: new Date().toISOString()
      };
      
      await engine.addSearch(search);
      await engine.disable();

      expect(mockChrome.storage.local.set).toHaveBeenCalledWith({ automationEnabled: false });
      expect(mockChrome.alarms.clear).toHaveBeenCalledWith('search-scan-search-1');
      expect(mockChrome.runtime.sendMessage).toHaveBeenCalledWith({
        type: 'AUTOMATION_STATUS_CHANGED',
        status: 'off'
      });
    });
  });

  describe('Search Management', () => {
    it('should add a search and schedule it when enabled', async () => {
      await engine.enable();
      
      const search: SavedSearch = {
        id: 'search-2',
        name: 'Gaming PCs under $1000',
        url: 'https://craigslist.org/search/sss?query=gaming+pc&max_price=1000',
        platform: 'craigslist',
        enabled: true,
        cadenceMinutes: 60,
        createdAt: new Date().toISOString()
      };

      await engine.addSearch(search);

      expect(mockChrome.storage.local.set).toHaveBeenCalledWith({
        savedSearches: expect.arrayContaining([search])
      });
      expect(mockChrome.alarms.create).toHaveBeenCalledWith(
        'search-scan-search-2',
        expect.objectContaining({
          periodInMinutes: 60
        })
      );
    });

    it('should not schedule disabled searches', async () => {
      await engine.enable();
      
      const search: SavedSearch = {
        id: 'search-3',
        name: 'Disabled Search',
        url: 'https://example.com',
        platform: 'offerup',
        enabled: false,
        cadenceMinutes: 30,
        createdAt: new Date().toISOString()
      };

      await engine.addSearch(search);

      expect(mockChrome.alarms.create).not.toHaveBeenCalledWith(
        'search-scan-search-3',
        expect.any(Object)
      );
    });
  });

  describe('Scanning', () => {
    it('should execute scan when user is idle', async () => {
      const search: SavedSearch = {
        id: 'search-4',
        name: 'Test Scan',
        url: 'https://facebook.com/marketplace',
        platform: 'facebook',
        enabled: true,
        cadenceMinutes: 30,
        createdAt: new Date().toISOString()
      };

      await engine.addSearch(search);
      mockChrome.idle.queryState.mockResolvedValueOnce('idle');
      
      // Mock tab creation and loading
      const mockTab = { id: 456, status: 'complete' };
      mockChrome.tabs.create.mockResolvedValueOnce(mockTab);
      
      // Mock successful scan response
      mockChrome.tabs.sendMessage.mockResolvedValueOnce({
        success: true,
        candidates: [
          { id: 'listing-1', title: 'Gaming PC', price: 800, roi: 0.35 }
        ]
      });

      // Wait for tab to "load"
      const updateListeners = [];
      mockChrome.tabs.onUpdated.addListener.mockImplementation((listener) => {
        updateListeners.push(listener);
        // Simulate tab loaded
        setTimeout(() => listener(456, { status: 'complete' }), 0);
      });

      await engine.testScan('search-4');

      // Verify tab creation
      expect(mockChrome.tabs.create).toHaveBeenCalledWith({
        url: search.url,
        active: false,
        pinned: true
      });

      // Verify scan message sent
      expect(mockChrome.tabs.sendMessage).toHaveBeenCalledWith(
        456,
        expect.objectContaining({
          action: 'SCAN_PAGE',
          searchId: 'search-4',
          autoScan: true
        })
      );

      // Verify results stored
      expect(mockChrome.storage.local.set).toHaveBeenCalledWith(
        expect.objectContaining({
          scannedListings: expect.arrayContaining([
            expect.objectContaining({
              id: 'listing-1',
              foundVia: 'Test Scan',
              autoScanned: true
            })
          ])
        })
      );
    });

    it('should postpone scan when user is active', async () => {
      mockChrome.idle.queryState.mockResolvedValueOnce('active');
      
      const search: SavedSearch = {
        id: 'search-5',
        name: 'Active User Test',
        url: 'https://example.com',
        platform: 'facebook',
        enabled: true,
        cadenceMinutes: 30,
        createdAt: new Date().toISOString()
      };

      await engine.addSearch(search);
      await engine.enable();

      // Should reschedule for later
      expect(mockChrome.alarms.create).toHaveBeenCalledWith(
        'search-scan-search-5',
        expect.objectContaining({
          delayInMinutes: 5
        })
      );
    });
  });

  describe('Notifications', () => {
    it('should notify on high-value finds', async () => {
      const search: SavedSearch = {
        id: 'search-6',
        name: 'High Value Search',
        url: 'https://example.com',
        platform: 'facebook',
        enabled: true,
        cadenceMinutes: 30,
        createdAt: new Date().toISOString()
      };

      await engine.addSearch(search);
      
      // Mock high-value scan results
      mockChrome.tabs.sendMessage.mockResolvedValueOnce({
        success: true,
        candidates: [
          { id: 'listing-2', title: 'RTX 4090 Build', price: 2000, roi: 0.45 },
          { id: 'listing-3', title: 'i9 Gaming PC', price: 1500, roi: 0.38 }
        ]
      });

      await engine.testScan('search-6');

      // Should create notification for high ROI finds
      expect(mockChrome.notifications.create).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'basic',
          title: 'New High-Value Find!',
          message: expect.stringContaining('45% ROI')
        })
      );
    });
  });

  describe('Logging', () => {
    it('should log scan events', async () => {
      const search: SavedSearch = {
        id: 'search-7',
        name: 'Log Test',
        url: 'https://example.com',
        platform: 'facebook',
        enabled: true,
        cadenceMinutes: 30,
        createdAt: new Date().toISOString()
      };

      await engine.addSearch(search);
      await engine.testScan('search-7');

      const logs = await engine.getLogs();
      
      // Should have scan_started and scan_completed/failed events
      expect(logs.length).toBeGreaterThan(0);
      expect(logs[0].type).toMatch(/scan_(started|completed|failed)/);
      expect(logs[0].searchId).toBe('search-7');
    });
  });
});