/**
 * Test Setup
 * Mock Chrome APIs and global test utilities
 */

import { vi } from 'vitest';
import '@testing-library/jest-dom';

// Mock Chrome Storage API
const mockStorage = {
  local: {
    get: vi.fn().mockResolvedValue({}),
    set: vi.fn().mockResolvedValue(undefined),
    remove: vi.fn().mockResolvedValue(undefined),
    clear: vi.fn().mockResolvedValue(undefined),
    getBytesInUse: vi.fn().mockResolvedValue(0),
  },
  sync: {
    get: vi.fn().mockResolvedValue({}),
    set: vi.fn().mockResolvedValue(undefined),
    remove: vi.fn().mockResolvedValue(undefined),
    clear: vi.fn().mockResolvedValue(undefined),
  },
  onChanged: {
    addListener: vi.fn(),
    removeListener: vi.fn(),
  },
};

// Mock Chrome Runtime API
const mockRuntime = {
  sendMessage: vi.fn().mockResolvedValue(undefined),
  onMessage: {
    addListener: vi.fn(),
    removeListener: vi.fn(),
  },
  getURL: vi.fn((path) => `chrome-extension://mock-id/${path}`),
  getManifest: vi.fn(() => ({ version: '1.0.0', manifest_version: 3 })),
  id: 'mock-extension-id',
};

// Mock Chrome Tabs API
const mockTabs = {
  query: vi.fn().mockResolvedValue([]),
  create: vi.fn().mockResolvedValue({ id: 1 }),
  update: vi.fn().mockResolvedValue({}),
  remove: vi.fn().mockResolvedValue(undefined),
  sendMessage: vi.fn().mockResolvedValue(undefined),
  onUpdated: {
    addListener: vi.fn(),
    removeListener: vi.fn(),
  },
};

// Mock Chrome Alarms API
const mockAlarms = {
  create: vi.fn(),
  clear: vi.fn(),
  clearAll: vi.fn(),
  get: vi.fn().mockResolvedValue(null),
  getAll: vi.fn().mockResolvedValue([]),
  onAlarm: {
    addListener: vi.fn(),
    removeListener: vi.fn(),
  },
};

// Mock Chrome Notifications API
const mockNotifications = {
  create: vi.fn((id, options, callback) => {
    if (callback) callback('notification-id');
    return Promise.resolve('notification-id');
  }),
  clear: vi.fn().mockResolvedValue(true),
  update: vi.fn().mockResolvedValue(true),
};

// Global Chrome mock
global.chrome = {
  storage: mockStorage,
  runtime: mockRuntime,
  tabs: mockTabs,
  alarms: mockAlarms,
  notifications: mockNotifications,
} as any;

// Mock performance.memory
Object.defineProperty(performance, 'memory', {
  value: {
    usedJSHeapSize: 1000000,
    totalJSHeapSize: 2000000,
    jsHeapSizeLimit: 4000000,
  },
  writable: true,
});

// Mock IndexedDB
const mockIndexedDB = {
  open: vi.fn(() => ({
    onsuccess: vi.fn(),
    onerror: vi.fn(),
    onupgradeneeded: vi.fn(),
  })),
  deleteDatabase: vi.fn(),
};

global.indexedDB = mockIndexedDB as any;

// Mock fetch for testing
global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  json: async () => ({}),
  text: async () => '',
  blob: async () => new Blob(),
});

// Mock crypto for testing
global.crypto = {
  ...global.crypto,
  randomUUID: () => 'mock-uuid-' + Math.random().toString(36).substring(7),
  subtle: {
    encrypt: vi.fn().mockResolvedValue(new ArrayBuffer(8)),
    decrypt: vi.fn().mockResolvedValue(new ArrayBuffer(8)),
    generateKey: vi.fn().mockResolvedValue({}),
    importKey: vi.fn().mockResolvedValue({}),
    exportKey: vi.fn().mockResolvedValue({}),
    digest: vi.fn().mockResolvedValue(new ArrayBuffer(32)),
  } as any,
};

// Helper to reset all mocks
export function resetAllMocks() {
  vi.clearAllMocks();
  
  // Reset storage to empty
  mockStorage.local.get.mockResolvedValue({});
  mockStorage.sync.get.mockResolvedValue({});
  
  // Reset tabs
  mockTabs.query.mockResolvedValue([]);
  
  // Reset fetch
  (global.fetch as any).mockResolvedValue({
    ok: true,
    json: async () => ({}),
    text: async () => '',
    blob: async () => new Blob(),
  });
}

// Helper to mock storage data
export function mockStorageData(data: Record<string, any>) {
  mockStorage.local.get.mockImplementation((keys) => {
    if (!keys) return Promise.resolve(data);
    if (typeof keys === 'string') {
      return Promise.resolve({ [keys]: data[keys] });
    }
    if (Array.isArray(keys)) {
      const result: Record<string, any> = {};
      keys.forEach(key => {
        if (key in data) result[key] = data[key];
      });
      return Promise.resolve(result);
    }
    return Promise.resolve({});
  });
}

// Helper to mock Chrome message
export function mockChromeMessage(response: any) {
  mockRuntime.sendMessage.mockResolvedValueOnce(response);
}

// Helper to simulate message from background
export function simulateBackgroundMessage(message: any, sendResponse?: (response: any) => void) {
  const listeners = (mockRuntime.onMessage.addListener as any).mock.calls;
  if (listeners.length > 0) {
    const listener = listeners[listeners.length - 1][0];
    listener(message, { id: 'mock-sender' }, sendResponse || (() => {}));
  }
}

// Test data factories
export function createMockDeal(overrides = {}) {
  return {
    id: 'deal-' + Math.random().toString(36).substring(7),
    listingId: 'listing-123',
    stage: 'evaluating',
    askingPrice: 1000,
    metadata: {
      createdAt: new Date(),
      updatedAt: new Date(),
      source: 'test',
      version: 1,
    },
    ...overrides,
  };
}

export function createMockListing(overrides = {}) {
  return {
    id: 'listing-' + Math.random().toString(36).substring(7),
    url: 'https://example.com/listing',
    title: 'Gaming PC',
    price: 1200,
    location: 'Test City',
    platform: 'facebook',
    parsedSpecs: {
      cpu: 'i7-12700K',
      gpu: 'RTX 3080',
      ram: '32GB',
      storage: '1TB SSD',
    },
    metadata: {
      parsedAt: new Date(),
      lastChecked: new Date(),
    },
    ...overrides,
  };
}

export function createMockUser(overrides = {}) {
  return {
    id: 'user-123',
    email: 'test@example.com',
    settings: {
      notifications: true,
      autoRefresh: false,
    },
    ...overrides,
  };
}

// Wait for async operations
export async function waitForAsync() {
  await new Promise(resolve => setTimeout(resolve, 0));
}

// Setup before each test
beforeEach(() => {
  resetAllMocks();
});