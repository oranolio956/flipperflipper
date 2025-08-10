/**
 * Offers Background Handler
 * Manage follow-up alarms and notifications
 */

import { getThreadsNeedingFollowUp } from '@/lib/offerEngine';
import { db } from '@/lib/db';

/**
 * Handle offer follow-up alarm
 */
export async function handleOfferFollowUp() {
  try {
    const threads = await getThreadsNeedingFollowUp();
    
    for (const thread of threads) {
      // Get listing info
      const listing = await db.listings
        .where('id')
        .equals(thread.listingId)
        .first();
      
      if (!listing) continue;
      
      // Send notification
      chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('icons/icon-128.png'),
        title: 'Follow-up Needed',
        message: `Time to follow up on: ${listing.title}`,
        buttons: [
          { title: 'Open Listing' },
          { title: 'Snooze 1 Day' },
        ],
        requireInteraction: true,
      }, (notificationId) => {
        // Store thread ID for button handling
        chrome.storage.session.set({
          [`notification-${notificationId}`]: thread.id,
        });
      });
    }
  } catch (error) {
    console.error('Failed to handle offer follow-up:', error);
  }
}

/**
 * Initialize offer follow-up alarm
 */
export async function initializeOfferAlarms() {
  // Set alarm to check every hour
  chrome.alarms.create('offer-followup', {
    periodInMinutes: 60,
    delayInMinutes: 1,
  });
}

/**
 * Handle notification button clicks
 */
chrome.notifications.onButtonClicked.addListener(async (notificationId, buttonIndex) => {
  // Get thread ID from session storage
  const data = await chrome.storage.session.get(`notification-${notificationId}`);
  const threadId = data[`notification-${notificationId}`];
  
  if (!threadId) return;
  
  if (buttonIndex === 0) {
    // Open listing
    const thread = await db.threads.where('id').equals(threadId).first();
    if (thread) {
      const listing = await db.listings
        .where('id')
        .equals(thread.listingId)
        .first();
      
      if (listing) {
        chrome.tabs.create({ url: listing.url });
      }
    }
  } else if (buttonIndex === 1) {
    // Snooze 1 day
    const thread = await db.threads.where('id').equals(threadId).first();
    if (thread) {
      thread.nextFollowUpAt = new Date(Date.now() + 24 * 60 * 60 * 1000);
      await db.threads.update(thread._id!, thread);
    }
  }
  
  // Clear notification
  chrome.notifications.clear(notificationId);
  chrome.storage.session.remove(`notification-${notificationId}`);
});