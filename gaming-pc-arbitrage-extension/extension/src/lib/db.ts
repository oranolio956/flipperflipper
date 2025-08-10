/**
 * Dexie Database Layer with Encryption
 * Stores all extension data with versioned migrations
 */

import Dexie, { Table } from 'dexie';
import { encrypt, decrypt, applyEncryptionMiddleware } from 'dexie-encrypted';
import type { 
  Listing, 
  Deal, 
  Settings,
  AnalyticsEvent,
  MessageTemplate 
} from '@/core';

// Extended types for database
export interface DBListing extends Listing {
  _id?: number;
  _encrypted?: boolean;
}

export interface DBDeal extends Deal {
  _id?: number;
  _encrypted?: boolean;
}

export interface DBThread {
  _id?: number;
  id: string;
  listingId: string;
  sellerId: string;
  platform: string;
  messages: Array<{
    id: string;
    content: string;
    timestamp: Date;
    direction: 'sent' | 'received';
    template?: string;
  }>;
  lastMsgAt: Date;
  cadence: '1h' | '24h' | '3d';
  nextFollowUpAt?: Date;
  status: 'active' | 'archived';
}

export interface DBOffer {
  _id?: number;
  id: string;
  listingId: string;
  amount: number;
  message?: string;
  variantId?: string;
  timestamp: Date;
  status: 'draft' | 'sent' | 'countered' | 'accepted' | 'rejected' | 'expired';
  response?: string;
  threadId?: string;
}

export interface DBEvent extends AnalyticsEvent {
  _id?: number;
}

export interface DBPartsBin {
  _id?: number;
  name: string;
  category: string;
  cost: number;
  quantity: number;
  lastUpdated: Date;
}

export interface DBAttachment {
  _id?: number;
  dealId: string;
  type: 'receipt' | 'photo' | 'serial' | 'test';
  filename: string;
  data: ArrayBuffer; // Encrypted
  timestamp: Date;
}

export interface DBMigration {
  _id?: number;
  version: number;
  appliedAt: Date;
  description: string;
}

export interface DBUser {
  _id?: number;
  id: string;
  name: string;
  role: 'admin' | 'operator' | 'viewer';
  createdAt: Date;
  lastActive?: Date;
}

export interface DBAssignment {
  _id?: number;
  id: string;
  dealId: string;
  userId: string;
  createdAt: Date;
}

export interface DBExperiment {
  _id?: number;
  id: string;
  name: string;
  description: string;
  variants: Array<{
    id: string;
    impressions: number;
    successes: number;
    conversionRate: number;
  }>;
  promotedId?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface DBComp {
  _id?: number;
  id: string;
  source: 'ebay' | 'fb' | 'cl' | 'csv';
  title: string;
  price: number;
  currency: string;
  timestamp: Date;
  location?: { city?: string; state?: string };
  cpu?: string;
  gpu?: string;
  ram?: number;
  storage?: number;
  condition?: 'new' | 'used' | 'refurbished' | 'parts';
  url?: string;
  expiresAt: Date;
}

// Database class
export class ArbitrageDB extends Dexie {
  listings!: Table<DBListing>;
  deals!: Table<DBDeal>;
  threads!: Table<DBThread>;
  offers!: Table<DBOffer>;
  settings!: Table<Settings>;
  events!: Table<DBEvent>;
  partsBin!: Table<DBPartsBin>;
  attachments!: Table<DBAttachment>;
  migrations!: Table<DBMigration>;
  users!: Table<DBUser>;
  assignments!: Table<DBAssignment>;
  experiments!: Table<DBExperiment>;
  comps!: Table<DBComp>;

  constructor() {
    super('ArbitrageDB');
    
    // Define schema versions
    this.version(1).stores({
      listings: '++_id, id, platform, [platform+externalId], metadata.createdAt, metadata.status',
      deals: '++_id, id, listingId, stage, metadata.createdAt',
      threads: '++_id, dealId, lastActivity',
      offers: '++_id, dealId, timestamp, status',
      settings: '++_id, version',
      events: '++_id, timestamp, category, name',
      partsBin: '++_id, name, category',
      attachments: '++_id, dealId, type, timestamp',
      migrations: '++_id, version, appliedAt',
    });
    
    // Version 2 - Add integrations
    this.version(2).stores({
      listings: '++_id, id, platform, [platform+externalId], metadata.createdAt, metadata.status',
      deals: '++_id, id, listingId, stage, metadata.createdAt',
      threads: '++_id, dealId, lastActivity',
      offers: '++_id, dealId, timestamp, status',
      settings: '++_id, version',
      events: '++_id, timestamp, category, name',
      partsBin: '++_id, name, category',
      attachments: '++_id, dealId, type, timestamp',
      migrations: '++_id, version, appliedAt',
    }).upgrade(async trans => {
      // Add integrations to existing settings
      await trans.settings.toCollection().modify(setting => {
        if (!setting.integrations) {
          setting.integrations = {
            sheets: {
              enabled: false,
              clientId: '',
              spreadsheetId: '',
              sync: {
                enabled: false,
                direction: 'both',
                cadenceMin: 60,
              },
              mappings: {},
            },
          };
        }
      });
    });
    
    // Version 3 - Add team mode
    this.version(3).stores({
      listings: '++_id, id, platform, [platform+externalId], metadata.createdAt, metadata.status',
      deals: '++_id, id, listingId, stage, metadata.createdAt',
      threads: '++_id, dealId, lastActivity',
      offers: '++_id, dealId, timestamp, status',
      settings: '++_id, version',
      events: '++_id, timestamp, category, name, actorUserId',
      partsBin: '++_id, name, category',
      attachments: '++_id, dealId, type, timestamp',
      migrations: '++_id, version, appliedAt',
      users: '++_id, id, name, role, createdAt',
      assignments: '++_id, id, dealId, userId, [dealId+userId]',
    }).upgrade(async trans => {
      // Create default admin user
      const adminUser = {
        id: 'user-admin',
        name: 'Admin',
        role: 'admin' as const,
        createdAt: new Date(),
      };
      await trans.users.add(adminUser);
      
      // Add team settings
      await trans.settings.toCollection().modify(setting => {
        if (!setting.team) {
          setting.team = {
            currentUserId: adminUser.id,
          };
        }
      });
    });
    
    // Version 4 - Add experiments
    this.version(4).stores({
      listings: '++_id, id, platform, [platform+externalId], metadata.createdAt, metadata.status',
      deals: '++_id, id, listingId, stage, metadata.createdAt',
      threads: '++_id, dealId, lastActivity',
      offers: '++_id, dealId, timestamp, status',
      settings: '++_id, version',
      events: '++_id, timestamp, category, name, actorUserId',
      partsBin: '++_id, name, category',
      attachments: '++_id, dealId, type, timestamp',
      migrations: '++_id, version, appliedAt',
      users: '++_id, id, name, role, createdAt',
      assignments: '++_id, id, dealId, userId, [dealId+userId]',
      experiments: '++_id, id, name, createdAt',
    }).upgrade(async trans => {
      // Create default negotiation experiment
      const defaultExperiment = {
        id: 'negotiation_openers',
        name: 'Opening Message Templates',
        description: 'Test different opening message styles',
        variants: [
          { id: 'opener_friendly', impressions: 0, successes: 0, conversionRate: 0 },
          { id: 'opener_direct', impressions: 0, successes: 0, conversionRate: 0 },
          { id: 'opener_curious', impressions: 0, successes: 0, conversionRate: 0 },
        ],
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      await trans.experiments.add(defaultExperiment);
    });
    
    // Version 5 - Add comps table
    this.version(5).stores({
      listings: '++_id, id, platform, [platform+externalId], metadata.createdAt, metadata.status',
      deals: '++_id, id, listingId, stage, metadata.createdAt',
      threads: '++_id, dealId, lastActivity',
      offers: '++_id, dealId, timestamp, status',
      settings: '++_id, version',
      events: '++_id, timestamp, category, name, actorUserId',
      partsBin: '++_id, name, category',
      attachments: '++_id, dealId, type, timestamp',
      migrations: '++_id, version, appliedAt',
      users: '++_id, id, name, role, createdAt',
      assignments: '++_id, id, dealId, userId, [dealId+userId]',
      experiments: '++_id, id, name, createdAt',
      comps: '++_id, id, source, [source+url], timestamp, expiresAt',
    });
    
    // Version 6 - Update offers and threads tables
    this.version(6).stores({
      listings: '++_id, id, platform, [platform+externalId], metadata.createdAt, metadata.status',
      deals: '++_id, id, listingId, stage, metadata.createdAt',
      threads: '++_id, id, listingId, sellerId, lastMsgAt, nextFollowUpAt',
      offers: '++_id, id, listingId, [listingId+amount], status, timestamp',
      settings: '++_id, version',
      events: '++_id, timestamp, category, name, actorUserId',
      partsBin: '++_id, name, category',
      attachments: '++_id, dealId, type, timestamp',
      migrations: '++_id, version, appliedAt',
      users: '++_id, id, name, role, createdAt',
      assignments: '++_id, id, dealId, userId, [dealId+userId]',
      experiments: '++_id, id, name, createdAt',
      comps: '++_id, id, source, [source+url], timestamp, expiresAt',
    });

    // Apply encryption middleware for sensitive fields
    applyEncryptionMiddleware(
      this,
      {
        listings: {
          type: encrypt,
          fields: ['seller.name', 'seller.id', 'seller.profileUrl'],
        },
        deals: {
          type: encrypt,
          fields: ['documentation.serialNumbers', 'documentation.receipts'],
        },
        attachments: {
          type: encrypt,
          fields: ['data'],
        },
      },
      async () => {
        // Generate or retrieve encryption key
        const key = await getOrCreateEncryptionKey();
        return key;
      }
    );
  }
}

// Encryption key management
async function getOrCreateEncryptionKey(): Promise<CryptoKey> {
  const keyName = 'arbitrage-db-key';
  
  // Try to get existing key from extension storage
  const stored = await chrome.storage.local.get(keyName);
  if (stored[keyName]) {
    const keyData = new Uint8Array(stored[keyName]);
    return await crypto.subtle.importKey(
      'raw',
      keyData,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt', 'decrypt']
    );
  }

  // Generate new key
  const key = await crypto.subtle.generateKey(
    { name: 'AES-GCM', length: 256 },
    true,
    ['encrypt', 'decrypt']
  );

  // Export and store
  const exported = await crypto.subtle.exportKey('raw', key);
  await chrome.storage.local.set({
    [keyName]: Array.from(new Uint8Array(exported)),
  });

  return key;
}

// Database instance
export const db = new ArbitrageDB();

// Helper functions

export async function saveParsedListing(listing: Listing): Promise<number> {
  // Check for existing listing
  const existing = await db.listings
    .where('[platform+externalId]')
    .equals([listing.platform, listing.externalId || ''])
    .first();

  if (existing) {
    // Update existing
    return await db.listings.update(existing._id!, listing);
  }

  // Create new
  return await db.listings.add(listing as DBListing);
}

export async function upsertDealStage(
  dealId: string, 
  newStage: Deal['stage'],
  reason?: string
): Promise<void> {
  await db.transaction('rw', db.deals, async () => {
    const deal = await db.deals.where('id').equals(dealId).first();
    if (!deal) throw new Error(`Deal ${dealId} not found`);

    // Update stage history
    deal.stageHistory.push({
      from: deal.stage,
      to: newStage,
      timestamp: new Date(),
      reason,
      automatic: false,
    });
    deal.stage = newStage;
    deal.metadata.updatedAt = new Date();

    await db.deals.update(deal._id!, deal);
  });
}

export async function logEvent(event: Omit<AnalyticsEvent, 'id' | 'timestamp'>): Promise<void> {
  await db.events.add({
    ...event,
    id: generateId(),
    timestamp: new Date(),
  } as DBEvent);
}

export async function exportJson(): Promise<string> {
  const data = {
    version: 1,
    exportedAt: new Date().toISOString(),
    listings: await db.listings.toArray(),
    deals: await db.deals.toArray(),
    threads: await db.threads.toArray(),
    offers: await db.offers.toArray(),
    settings: await db.settings.toArray(),
    events: await db.events.toArray(),
    partsBin: await db.partsBin.toArray(),
  };

  // Remove encrypted fields before export
  data.listings = data.listings.map(l => {
    const clean = { ...l };
    delete clean._id;
    delete clean._encrypted;
    // Decrypt seller info for export
    return clean;
  });

  return JSON.stringify(data, null, 2);
}

export async function importJson(jsonData: string): Promise<void> {
  const data = JSON.parse(jsonData);
  
  if (!data.version || data.version !== 1) {
    throw new Error('Unsupported import format version');
  }

  await db.transaction('rw', 
    db.listings, db.deals, db.threads, db.offers, 
    db.settings, db.events, db.partsBin,
    async () => {
      // Clear existing data
      await Promise.all([
        db.listings.clear(),
        db.deals.clear(),
        db.threads.clear(),
        db.offers.clear(),
        db.events.clear(),
        db.partsBin.clear(),
      ]);

      // Import new data
      if (data.listings) await db.listings.bulkAdd(data.listings);
      if (data.deals) await db.deals.bulkAdd(data.deals);
      if (data.threads) await db.threads.bulkAdd(data.threads);
      if (data.offers) await db.offers.bulkAdd(data.offers);
      if (data.events) await db.events.bulkAdd(data.events);
      if (data.partsBin) await db.partsBin.bulkAdd(data.partsBin);
      
      // Settings are merged, not replaced
      if (data.settings && data.settings[0]) {
        const current = await db.settings.toArray();
        if (current.length > 0) {
          await db.settings.update(current[0]._id!, data.settings[0]);
        } else {
          await db.settings.add(data.settings[0]);
        }
      }
    }
  );

  // Log import event
  await logEvent({
    name: 'data_imported',
    category: 'system',
    properties: { recordCount: Object.keys(data).length },
  });
}

// Query helpers

export async function dealsByStage(stage?: Deal['stage']): Promise<DBDeal[]> {
  if (stage) {
    return await db.deals.where('stage').equals(stage).toArray();
  }
  return await db.deals.toArray();
}

export async function listingsNeedingFollowUp(): Promise<DBListing[]> {
  const cutoffTime = new Date();
  cutoffTime.setHours(cutoffTime.getHours() - 24); // 24 hour window

  const listings = await db.listings
    .where('metadata.status')
    .equals('contacted')
    .toArray();

  // Filter for those needing follow-up
  return listings.filter(listing => {
    const deals = db.deals.where('listingId').equals(listing.id).toArray();
    // Logic: contacted but no recent activity
    return true; // Simplified for now
  });
}

export async function getActiveDeals(): Promise<DBDeal[]> {
  const inactiveStages: Deal['stage'][] = ['cancelled', 'completed', 'sold'];
  return await db.deals
    .filter(deal => !inactiveStages.includes(deal.stage))
    .toArray();
}

export async function getRecentEvents(days = 7): Promise<DBEvent[]> {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);
  
  return await db.events
    .where('timestamp')
    .above(cutoff)
    .reverse()
    .toArray();
}

// Utility function
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}