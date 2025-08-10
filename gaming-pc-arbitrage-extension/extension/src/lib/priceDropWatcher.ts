/**
 * Price Drop Watcher
 * Monitor listings for price changes
 */

import { db } from './db';
import { generateId } from '@/core';
import type { DBWatchedListing } from './db';
import type { Listing } from '@/core';

/**
 * Add listing to watch list
 */
export async function watchListing(
  listing: Listing,
  dropThresholdPct: number = 10
): Promise<DBWatchedListing> {
  const existing = await db.watchedListings
    .where('listingId')
    .equals(listing.id)
    .first();
  
  if (existing) {
    return existing;
  }
  
  const watched: DBWatchedListing = {
    id: generateId(),
    listingId: listing.id,
    platform: listing.platform,
    url: listing.url,
    title: listing.title,
    lastSeenPrice: listing.price,
    originalPrice: listing.price,
    lowestPrice: listing.price,
    lastCheckedAt: new Date(),
    createdAt: new Date(),
    dropThresholdPct,
    priceHistory: [{
      price: listing.price,
      timestamp: new Date(),
    }],
    notified: false,
  };
  
  const id = await db.watchedListings.add(watched);
  return { ...watched, _id: id };
}

/**
 * Check if listing is watched
 */
export async function isWatched(listingId: string): Promise<boolean> {
  const count = await db.watchedListings
    .where('listingId')
    .equals(listingId)
    .count();
  
  return count > 0;
}

/**
 * Update watched listing price
 */
export async function updateWatchedPrice(
  listingId: string,
  newPrice: number
): Promise<{
  priceDropped: boolean;
  dropPercent: number;
  shouldNotify: boolean;
} | null> {
  const watched = await db.watchedListings
    .where('listingId')
    .equals(listingId)
    .first();
  
  if (!watched) {
    return null;
  }
  
  const priceDropped = newPrice < watched.lastSeenPrice;
  const dropPercent = ((watched.lastSeenPrice - newPrice) / watched.lastSeenPrice) * 100;
  const shouldNotify = !watched.notified && 
                      dropPercent >= watched.dropThresholdPct &&
                      priceDropped;
  
  // Update watched listing
  watched.lastSeenPrice = newPrice;
  watched.lastCheckedAt = new Date();
  watched.priceHistory.push({
    price: newPrice,
    timestamp: new Date(),
  });
  
  if (newPrice < watched.lowestPrice) {
    watched.lowestPrice = newPrice;
  }
  
  if (shouldNotify) {
    watched.notified = true;
  }
  
  await db.watchedListings.update(watched._id!, watched);
  
  return {
    priceDropped,
    dropPercent,
    shouldNotify,
  };
}

/**
 * Get all watched listings
 */
export async function getWatchedListings(): Promise<DBWatchedListing[]> {
  return db.watchedListings.toArray();
}

/**
 * Remove from watch list
 */
export async function unwatchListing(listingId: string): Promise<void> {
  await db.watchedListings
    .where('listingId')
    .equals(listingId)
    .delete();
}

/**
 * Get watched listings needing refresh
 */
export async function getListingsNeedingRefresh(
  maxAgeHours: number = 24
): Promise<DBWatchedListing[]> {
  const cutoff = new Date();
  cutoff.setHours(cutoff.getHours() - maxAgeHours);
  
  return db.watchedListings
    .where('lastCheckedAt')
    .below(cutoff)
    .toArray();
}

/**
 * Send price drop notification
 */
export async function sendPriceDropNotification(
  watched: DBWatchedListing,
  dropPercent: number
): Promise<void> {
  const dropAmount = watched.originalPrice - watched.lastSeenPrice;
  
  chrome.notifications.create({
    type: 'basic',
    iconUrl: chrome.runtime.getURL('icons/icon-128.png'),
    title: 'Price Drop Alert! 📉',
    message: `${watched.title} dropped ${Math.round(dropPercent)}% ($${dropAmount})`,
    buttons: [
      { title: 'View Listing' },
      { title: 'Stop Watching' },
    ],
    requireInteraction: true,
  }, (notificationId) => {
    // Store listing ID for button handling
    chrome.storage.session.set({
      [`price-drop-${notificationId}`]: watched.listingId,
    });
  });
}

/**
 * Handle notification button clicks
 */
chrome.notifications.onButtonClicked.addListener(async (notificationId, buttonIndex) => {
  if (!notificationId.startsWith('chrome-extension://')) return;
  
  const data = await chrome.storage.session.get(`price-drop-${notificationId}`);
  const listingId = data[`price-drop-${notificationId}`];
  
  if (!listingId) return;
  
  if (buttonIndex === 0) {
    // View listing
    const watched = await db.watchedListings
      .where('listingId')
      .equals(listingId)
      .first();
    
    if (watched) {
      chrome.tabs.create({ url: watched.url });
    }
  } else if (buttonIndex === 1) {
    // Stop watching
    await unwatchListing(listingId);
  }
  
  chrome.notifications.clear(notificationId);
  chrome.storage.session.remove(`price-drop-${notificationId}`);
});

/**
 * Get price drop statistics
 */
export async function getPriceDropStats(listingId: string) {
  const watched = await db.watchedListings
    .where('listingId')
    .equals(listingId)
    .first();
  
  if (!watched) return null;
  
  const totalDrop = watched.originalPrice - watched.lowestPrice;
  const totalDropPct = (totalDrop / watched.originalPrice) * 100;
  const currentDrop = watched.originalPrice - watched.lastSeenPrice;
  const currentDropPct = (currentDrop / watched.originalPrice) * 100;
  
  return {
    originalPrice: watched.originalPrice,
    currentPrice: watched.lastSeenPrice,
    lowestPrice: watched.lowestPrice,
    totalDrop,
    totalDropPct,
    currentDrop,
    currentDropPct,
    priceHistory: watched.priceHistory,
    daysWatched: Math.floor(
      (Date.now() - watched.createdAt.getTime()) / (1000 * 60 * 60 * 24)
    ),
  };
}