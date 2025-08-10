/**
 * Watches Module
 * Price history tracking and saved search monitoring
 */

import { db } from './db';
import { generateId } from '@/core';
import type { Listing } from '@/core';

// Types
export interface PriceHistory {
  _id?: number;
  id: string;
  listingId: string;
  price: number;
  timestamp: Date;
}

export interface SavedSearch {
  _id?: number;
  id: string;
  name: string;
  url: string;
  filters: {
    minPrice?: number;
    maxPrice?: number;
    distance?: number;
    gpuTier?: string;
    cpuTier?: string;
    keywords?: string[];
  };
  cadenceMin: number; // 0 = manual
  lastRunAt?: Date;
  createdAt: Date;
  enabled: boolean;
}

export interface SavedSearchRun {
  _id?: number;
  id: string;
  searchId: string;
  timestamp: Date;
  resultsCount: number;
  topDeals: Array<{
    title: string;
    price: number;
    roi: number;
    url: string;
  }>;
}

// Extend database
declare module './db' {
  interface ArbitrageDB {
    priceHistory: Table<PriceHistory>;
    savedSearches: Table<SavedSearch>;
    savedSearchRuns: Table<SavedSearchRun>;
  }
}

/**
 * Record a price point for a listing
 */
export async function recordPrice(listingId: string, price: number): Promise<void> {
  const history: PriceHistory = {
    id: generateId(),
    listingId,
    price,
    timestamp: new Date(),
  };
  
  await db.priceHistory.add(history);
  
  // Prune old entries (keep last 100 per listing)
  const allHistory = await db.priceHistory
    .where('listingId')
    .equals(listingId)
    .sortBy('timestamp');
  
  if (allHistory.length > 100) {
    const toDelete = allHistory.slice(0, allHistory.length - 100);
    await db.priceHistory.bulkDelete(toDelete.map(h => h._id!));
  }
}

/**
 * Get price history for a listing
 */
export async function getPriceHistory(
  listingId: string,
  days = 30
): Promise<PriceHistory[]> {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);
  
  return db.priceHistory
    .where('listingId')
    .equals(listingId)
    .and(h => h.timestamp >= cutoff)
    .sortBy('timestamp');
}

/**
 * Add a saved search
 */
export async function addSavedSearch(search: Omit<SavedSearch, '_id' | 'id' | 'createdAt'>): Promise<SavedSearch> {
  const newSearch: SavedSearch = {
    ...search,
    id: generateId(),
    createdAt: new Date(),
  };
  
  const id = await db.savedSearches.add(newSearch);
  return { ...newSearch, _id: id };
}

/**
 * Get all saved searches
 */
export async function getSavedSearches(): Promise<SavedSearch[]> {
  return db.savedSearches.toArray();
}

/**
 * Update saved search
 */
export async function updateSavedSearch(
  id: string,
  updates: Partial<SavedSearch>
): Promise<void> {
  const search = await db.savedSearches.where('id').equals(id).first();
  if (search?._id) {
    await db.savedSearches.update(search._id, updates);
  }
}

/**
 * Delete saved search
 */
export async function deleteSavedSearch(id: string): Promise<void> {
  await db.savedSearches.where('id').equals(id).delete();
  // Also delete runs
  await db.savedSearchRuns.where('searchId').equals(id).delete();
}

/**
 * Run a saved search (opens URL and triggers scan)
 */
export async function runSavedSearch(searchId: string): Promise<void> {
  const search = await db.savedSearches.where('id').equals(searchId).first();
  if (!search) throw new Error('Search not found');
  
  // Update last run time
  await updateSavedSearch(searchId, { lastRunAt: new Date() });
  
  // Open search URL in current tab (user must confirm)
  const confirmed = confirm(`Open saved search "${search.name}"?\n\nThis will navigate to: ${search.url}`);
  if (!confirmed) return;
  
  // Get current tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab.id) return;
  
  // Navigate to search URL
  await chrome.tabs.update(tab.id, { url: search.url });
  
  // Wait for page load then trigger scan
  chrome.tabs.onUpdated.addListener(function listener(tabId, info) {
    if (tabId === tab.id && info.status === 'complete') {
      chrome.tabs.onUpdated.removeListener(listener);
      
      // Trigger scan after a delay
      setTimeout(() => {
        chrome.tabs.sendMessage(tab.id!, { 
          action: 'scanSearch',
          searchId: searchId,
        });
      }, 2000);
    }
  });
}

/**
 * Record search run results
 */
export async function recordSearchRun(
  searchId: string,
  results: Array<{ title: string; price: number; roi: number; url: string }>
): Promise<void> {
  const run: SavedSearchRun = {
    id: generateId(),
    searchId,
    timestamp: new Date(),
    resultsCount: results.length,
    topDeals: results.slice(0, 10), // Keep top 10
  };
  
  await db.savedSearchRuns.add(run);
}

/**
 * Get searches needing to run
 */
export async function getSearchesDue(): Promise<SavedSearch[]> {
  const searches = await db.savedSearches
    .where('enabled')
    .equals(1)
    .and(s => s.cadenceMin > 0)
    .toArray();
  
  return searches.filter(search => {
    if (!search.lastRunAt) return true;
    
    const nextRun = new Date(search.lastRunAt);
    nextRun.setMinutes(nextRun.getMinutes() + search.cadenceMin);
    
    return nextRun <= new Date();
  });
}

/**
 * Get sparkline data for price history
 */
export function getSparklineData(history: PriceHistory[]): string {
  if (history.length < 2) return '';
  
  // Normalize prices to 0-100 range
  const prices = history.map(h => h.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;
  
  const points = history.map((h, i) => {
    const x = (i / (history.length - 1)) * 100;
    const y = 100 - ((h.price - min) / range) * 100;
    return `${x},${y}`;
  });
  
  return points.join(' ');
}