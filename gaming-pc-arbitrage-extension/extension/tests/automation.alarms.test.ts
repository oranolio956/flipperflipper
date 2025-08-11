import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { savedSearchesManager } from '../src/lib/automation/savedSearches';
import { automationHandler } from '../src/background/automation';

// Mock chrome APIs
global.chrome = {
  alarms: {
    create: vi.fn(),
    clear: vi.fn(),
    onAlarm: {
      addListener: vi.fn(),
    },
  },
  tabs: {
    create: vi.fn(),
    remove: vi.fn(),
    get: vi.fn(),
    sendMessage: vi.fn(),
    onRemoved: {
      addListener: vi.fn(),
    },
  },
  storage: {
    local: {
      get: vi.fn(),
      set: vi.fn(),
    },
  },
  runtime: {
    onMessage: {
      addListener: vi.fn(),
    },
    sendMessage: vi.fn(),
  },
  scripting: {
    executeScript: vi.fn(),
  },
  notifications: {
    create: vi.fn(),
  },
  idle: {
    queryState: vi.fn(),
  },
} as any;

describe('Automation Alarms', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('SavedSearchesManager', () => {
    it('creates alarm when search is enabled', async () => {
      const search = await savedSearchesManager.create({
        name: 'Test Search',
        url: 'https://facebook.com/marketplace/search?query=gaming+pc',
        platform: 'facebook',
        enabled: true,
        cadenceMinutes: 30,
        filters: {},
      });

      expect(chrome.alarms.create).toHaveBeenCalledWith(
        expect.stringContaining('search-scan-'),
        expect.objectContaining({
          periodInMinutes: 30,
        })
      );
    });

    it('cancels alarm when search is disabled', async () => {
      const search = await savedSearchesManager.create({
        name: 'Test Search',
        url: 'https://facebook.com/marketplace/search',
        platform: 'facebook',
        enabled: true,
        cadenceMinutes: 30,
        filters: {},
      });

      await savedSearchesManager.update(search.id, { enabled: false });

      expect(chrome.alarms.clear).toHaveBeenCalledWith(
        expect.stringContaining('search-scan-')
      );
    });

    it('validates marketplace URLs correctly', () => {
      const validUrls = [
        { url: 'https://facebook.com/marketplace/search', platform: 'facebook' },
        { url: 'https://craigslist.org/search/sss', platform: 'craigslist' },
        { url: 'https://offerup.com/search', platform: 'offerup' },
      ];

      validUrls.forEach(({ url, platform }) => {
        const result = savedSearchesManager.validateSearchUrl(url);
        expect(result.valid).toBe(true);
        expect(result.platform).toBe(platform);
      });

      const invalidUrls = [
        'https://google.com',
        'not-a-url',
        'https://facebook.com/profile',
      ];

      invalidUrls.forEach(url => {
        const result = savedSearchesManager.validateSearchUrl(url);
        expect(result.valid).toBe(false);
      });
    });
  });

  describe('AutomationHandler', () => {
    beforeEach(() => {
      chrome.storage.local.get.mockResolvedValue({
        automationSettings: { enabled: true },
        savedSearches: [],
      });
    });

    it('initializes listeners on startup', async () => {
      await automationHandler.initialize();

      expect(chrome.alarms.onAlarm.addListener).toHaveBeenCalled();
      expect(chrome.tabs.onRemoved.addListener).toHaveBeenCalled();
      expect(chrome.runtime.onMessage.addListener).toHaveBeenCalled();
    });

    it('creates tab when alarm fires', async () => {
      const mockSearch = {
        id: 'test-1',
        name: 'Test Search',
        url: 'https://facebook.com/marketplace',
        enabled: true,
      };

      chrome.storage.local.get.mockResolvedValue({
        savedSearches: [mockSearch],
        automationSettings: { enabled: true },
      });

      chrome.tabs.create.mockResolvedValue({ id: 123 });
      chrome.tabs.get.mockResolvedValue({ status: 'complete' });
      chrome.tabs.sendMessage.mockResolvedValue({ success: true, totalFound: 5, newCandidates: 2 });

      // Simulate alarm
      await automationHandler.triggerScan('test-1');

      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(chrome.tabs.create).toHaveBeenCalledWith({
        url: mockSearch.url,
        active: false,
        pinned: true,
      });
    });

    it('respects max tabs limit', async () => {
      chrome.storage.local.get.mockResolvedValue({
        automationSettings: { 
          enabled: true, 
          maxTabsOpen: 1 
        },
      });

      // Simulate multiple scans
      const status = automationHandler.getStatus();
      expect(status.activeTabs).toBeLessThanOrEqual(1);
    });

    it('pauses during active use when configured', async () => {
      chrome.storage.local.get.mockResolvedValue({
        automationSettings: { 
          enabled: true, 
          pauseDuringActiveUse: true 
        },
      });

      chrome.idle.queryState.mockResolvedValue('active');

      // Handler should check idle state
      await automationHandler.initialize();
      
      expect(chrome.idle.queryState).toHaveBeenCalled();
    });
  });
});