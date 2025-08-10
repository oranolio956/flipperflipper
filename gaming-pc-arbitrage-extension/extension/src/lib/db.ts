/**
 * Database Layer using Dexie
 * Handles all local storage operations
 */

import Dexie, { Table } from 'dexie';
import { Deal, Listing, Message } from '@arbitrage/core';

// Define database schema
export interface DBDeal extends Deal {
  id: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface DBListing extends Listing {
  id: string;
  savedAt: Date;
}

export interface DBMessage extends Message {
  dealId: string;
}

export interface CompRecord {
  id: string;
  platform: string;
  component: string;
  price: number;
  condition: string;
  soldDate: Date;
  location?: string;
  url?: string;
}

export interface AnalyticsEvent {
  id: string;
  name: string;
  category: string;
  timestamp: Date;
  properties?: Record<string, any>;
}

// Create database class
class ArbitrageDB extends Dexie {
  deals!: Table<DBDeal>;
  listings!: Table<DBListing>;
  messages!: Table<DBMessage>;
  comps!: Table<CompRecord>;
  events!: Table<AnalyticsEvent>;
  
  constructor() {
    super('ArbitrageDB');
    
    // Define schema
    this.version(1).stores({
      deals: 'id, listingId, platform, status, createdAt, updatedAt',
      listings: 'id, platform, savedAt, [platform+listingDate]',
      messages: 'id, dealId, timestamp',
      comps: 'id, [platform+component], soldDate, component',
      events: 'id, name, category, timestamp'
    });
  }
}

// Create database instance
export const db = new ArbitrageDB();

// Helper functions
export async function saveDeal(deal: Partial<Deal>): Promise<string> {
  const id = `deal-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  const dbDeal: DBDeal = {
    ...deal,
    id,
    createdAt: new Date(),
    updatedAt: new Date(),
    status: deal.status || 'watching',
    offers: deal.offers || [],
    messages: deal.messages || [],
    metadata: {
      createdAt: new Date(),
      updatedAt: new Date(),
      source: 'manual',
      version: 1,
      ...deal.metadata
    }
  } as DBDeal;
  
  await db.deals.add(dbDeal);
  return id;
}

export async function saveListing(listing: Listing): Promise<string> {
  const id = listing.id || `listing-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  const dbListing: DBListing = {
    ...listing,
    id,
    savedAt: new Date()
  };
  
  await db.listings.put(dbListing);
  return id;
}

export async function saveComp(comp: Omit<CompRecord, 'id'>): Promise<void> {
  const id = `comp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  await db.comps.add({ ...comp, id });
}

export async function getRecentComps(
  component: string, 
  days: number = 30
): Promise<CompRecord[]> {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);
  
  return db.comps
    .where('component')
    .equals(component)
    .and(comp => comp.soldDate > cutoff)
    .toArray();
}

export async function logEvent(event: Omit<AnalyticsEvent, 'id' | 'timestamp'>): Promise<void> {
  const id = `event-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  await db.events.add({
    ...event,
    id,
    timestamp: new Date()
  });
}

export async function getDealsInProgress(): Promise<DBDeal[]> {
  return db.deals
    .where('status')
    .anyOf('watching', 'evaluating', 'negotiating', 'scheduled')
    .toArray();
}

export async function exportData(): Promise<any> {
  const deals = await db.deals.toArray();
  const listings = await db.listings.toArray();
  const comps = await db.comps.toArray();
  
  return {
    version: '1.0',
    exportDate: new Date().toISOString(),
    data: {
      deals,
      listings,
      comps
    }
  };
}

export async function importData(data: any): Promise<void> {
  if (data.version !== '1.0') {
    throw new Error('Unsupported data version');
  }
  
  // Clear existing data
  await db.transaction('rw', db.deals, db.listings, db.comps, async () => {
    await db.deals.clear();
    await db.listings.clear();
    await db.comps.clear();
    
    // Import new data
    if (data.data.deals?.length) {
      await db.deals.bulkAdd(data.data.deals);
    }
    if (data.data.listings?.length) {
      await db.listings.bulkAdd(data.data.listings);
    }
    if (data.data.comps?.length) {
      await db.comps.bulkAdd(data.data.comps);
    }
  });
}

// Initialize database
db.open().catch(err => {
  console.error('Failed to open database:', err);
});