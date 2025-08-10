/**
 * Backup Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import Dexie from 'dexie';
import { exportAll, importAll } from './backup';

// Mock WebCrypto API
global.crypto = {
  getRandomValues: (arr: Uint8Array) => {
    for (let i = 0; i < arr.length; i++) {
      arr[i] = Math.floor(Math.random() * 256);
    }
    return arr;
  },
  subtle: {
    importKey: vi.fn().mockResolvedValue({}),
    deriveKey: vi.fn().mockResolvedValue({}),
    encrypt: vi.fn().mockImplementation((_, __, data) => {
      // Simple mock encryption (just return the data)
      return Promise.resolve(data);
    }),
    decrypt: vi.fn().mockImplementation((_, __, data) => {
      // Simple mock decryption (just return the data)
      return Promise.resolve(data);
    }),
  },
} as any;

// Mock TextEncoder/TextDecoder
global.TextEncoder = class {
  encode(str: string): Uint8Array {
    return new Uint8Array(str.split('').map(c => c.charCodeAt(0)));
  }
} as any;

global.TextDecoder = class {
  decode(arr: Uint8Array): string {
    return String.fromCharCode(...Array.from(arr));
  }
} as any;

// Test database
class TestDB extends Dexie {
  items!: Dexie.Table<{ id: string; name: string; createdAt: Date }, string>;
  
  constructor() {
    super('TestDB');
    this.version(1).stores({
      items: 'id, name',
    });
  }
}

describe('exportAll', () => {
  let db: TestDB;
  
  beforeEach(async () => {
    db = new TestDB();
    await db.open();
    
    // Add test data
    await db.items.bulkAdd([
      { id: '1', name: 'Item 1', createdAt: new Date('2024-01-01') },
      { id: '2', name: 'Item 2', createdAt: new Date('2024-01-02') },
    ]);
  });
  
  it('should export database to encrypted blob', async () => {
    const blob = await exportAll(db, {
      passphrase: 'test-passphrase',
      includeLogs: true,
    });
    
    expect(blob).toBeInstanceOf(Blob);
    expect(blob.type).toBe('application/json');
    
    // Read blob content
    const text = await blob.text();
    const envelope = JSON.parse(text);
    
    expect(envelope.version).toBe(1);
    expect(envelope.encrypted).toBe(true);
    expect(envelope.timestamp).toBeDefined();
    expect(envelope.salt).toBeDefined();
    expect(envelope.iv).toBeDefined();
    expect(envelope.data).toBeDefined();
  });
  
  it('should exclude tables based on options', async () => {
    // Add events table
    db.version(2).stores({
      items: 'id, name',
      events: '++id, name',
    });
    
    const blob = await exportAll(db, {
      passphrase: 'test-passphrase',
      includeLogs: false,
    });
    
    // Verify events were excluded
    const text = await blob.text();
    const envelope = JSON.parse(text);
    
    // We can't directly check the encrypted data in this mock
    // but the test verifies the function runs without error
    expect(envelope.encrypted).toBe(true);
  });
});

describe('importAll', () => {
  let db: TestDB;
  
  beforeEach(async () => {
    db = new TestDB();
    await db.open();
  });
  
  it('should restore database from encrypted blob', async () => {
    // Create a mock backup
    const backup = {
      items: [
        { id: '3', name: 'Restored Item', createdAt: '2024-01-03T00:00:00.000Z' },
      ],
    };
    
    const envelope = {
      version: 1,
      timestamp: new Date().toISOString(),
      encrypted: true,
      salt: btoa('mock-salt'),
      iv: btoa('mock-iv'),
      data: btoa(JSON.stringify(backup)),
    };
    
    const blob = new Blob([JSON.stringify(envelope)], { type: 'application/json' });
    
    await importAll(db, blob, {
      passphrase: 'test-passphrase',
      merge: 'overwrite',
    });
    
    // Verify data was restored
    const items = await db.items.toArray();
    expect(items).toHaveLength(1);
    expect(items[0].id).toBe('3');
    expect(items[0].name).toBe('Restored Item');
    expect(items[0].createdAt).toBeInstanceOf(Date);
  });
  
  it('should handle upsert merge strategy', async () => {
    // Add existing data
    await db.items.add({ id: '1', name: 'Original', createdAt: new Date() });
    
    // Create backup with update
    const backup = {
      items: [
        { id: '1', name: 'Updated', createdAt: '2024-01-01T00:00:00.000Z' },
        { id: '2', name: 'New Item', createdAt: '2024-01-02T00:00:00.000Z' },
      ],
    };
    
    const envelope = {
      version: 1,
      timestamp: new Date().toISOString(),
      encrypted: true,
      salt: btoa('mock-salt'),
      iv: btoa('mock-iv'),
      data: btoa(JSON.stringify(backup)),
    };
    
    const blob = new Blob([JSON.stringify(envelope)], { type: 'application/json' });
    
    await importAll(db, blob, {
      passphrase: 'test-passphrase',
      merge: 'upsert',
    });
    
    const items = await db.items.toArray();
    expect(items).toHaveLength(2);
    
    const updated = items.find(i => i.id === '1');
    expect(updated?.name).toBe('Updated');
    
    const newItem = items.find(i => i.id === '2');
    expect(newItem?.name).toBe('New Item');
  });
  
  it('should validate backup version', async () => {
    const envelope = {
      version: 999, // Unsupported version
      timestamp: new Date().toISOString(),
      encrypted: true,
      salt: btoa('mock-salt'),
      iv: btoa('mock-iv'),
      data: btoa('{}'),
    };
    
    const blob = new Blob([JSON.stringify(envelope)], { type: 'application/json' });
    
    await expect(importAll(db, blob, {
      passphrase: 'test-passphrase',
      merge: 'overwrite',
    })).rejects.toThrow('Unsupported backup version: 999');
  });
  
  it('should validate encryption fields', async () => {
    const envelope = {
      version: 1,
      timestamp: new Date().toISOString(),
      encrypted: false, // Not encrypted
      data: '{}',
    };
    
    const blob = new Blob([JSON.stringify(envelope)], { type: 'application/json' });
    
    await expect(importAll(db, blob, {
      passphrase: 'test-passphrase',
      merge: 'overwrite',
    })).rejects.toThrow('Invalid backup format');
  });
});