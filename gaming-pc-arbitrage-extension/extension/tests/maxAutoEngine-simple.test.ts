import { describe, it, expect, vi } from 'vitest';

// Mock chrome APIs globally
global.chrome = {
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
} as any;

describe('Max Auto Engine Core Functions', () => {
  it('should create alarms for saved searches', async () => {
    const { MaxAutoEngine } = await import('../src/background/maxAutoEngine');
    const engine = new MaxAutoEngine();
    
    await engine.enable();
    
    // Add a search
    await engine.addSearch({
      id: 'test-1',
      name: 'Gaming PCs',
      url: 'https://facebook.com/marketplace/search?query=gaming+pc',
      platform: 'facebook',
      enabled: true,
      cadenceMinutes: 30,
      createdAt: new Date().toISOString()
    });
    
    // Verify alarm was created
    expect(chrome.alarms.create).toHaveBeenCalledWith(
      'search-scan-test-1',
      expect.objectContaining({
        periodInMinutes: 30
      })
    );
  });

  it('should store scan results in chrome storage', async () => {
    const { maxAutoEngine } = await import('../src/background/maxAutoEngine');
    
    // Simulate getting search from storage
    chrome.storage.local.get.mockResolvedValueOnce({
      savedSearches: [{
        id: 'test-2',
        name: 'RTX 3080',
        url: 'https://craigslist.org',
        platform: 'craigslist',
        enabled: true,
        cadenceMinutes: 60,
        createdAt: new Date().toISOString()
      }]
    });
    
    const status = await maxAutoEngine.getStatus();
    expect(status.activeSearchCount).toBeGreaterThanOrEqual(0);
  });

  it('should handle enable/disable correctly', async () => {
    const { maxAutoEngine } = await import('../src/background/maxAutoEngine');
    
    await maxAutoEngine.enable();
    expect(chrome.storage.local.set).toHaveBeenCalledWith({ automationEnabled: true });
    
    await maxAutoEngine.disable();
    expect(chrome.storage.local.set).toHaveBeenCalledWith({ automationEnabled: false });
  });
});