/**
 * Calendar Integration
 * Generate and download ICS files for deal events
 */

import { db } from './db';
import { getSettings } from './settings';
import {
  buildIcsEvent,
  generateEventUid,
  type ICSEvent,
} from '@arbitrage/integrations/calendar/ics';

/**
 * Save ICS file using Chrome downloads API
 */
export async function saveIcsFile(icsContent: string, filename: string): Promise<void> {
  // Create blob URL
  const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  
  try {
    // Download the file
    await chrome.downloads.download({
      url,
      filename,
      saveAs: true,
    });
  } finally {
    // Clean up blob URL
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}

/**
 * Create pickup event ICS
 */
export async function createPickupIcs(dealId: string): Promise<void> {
  const deal = await db.deals.where('id').equals(dealId).first();
  if (!deal) throw new Error('Deal not found');
  
  const settings = await getSettings();
  
  // Get pickup details
  const pickupDate = deal.pickupScheduled || new Date();
  const duration = 30; // 30 minutes default
  
  const event: ICSEvent = {
    uid: generateEventUid(dealId, 'pickup'),
    title: `Pickup: ${deal.listing.title}`,
    description: [
      `Seller: ${deal.listing.seller?.name || 'Unknown'}`,
      `Price: $${deal.listing.price}`,
      `Phone: ${deal.listing.seller?.phone || 'Not provided'}`,
      '',
      'Safety Reminders:',
      '- Meet in public place',
      '- Bring cash in envelope',
      '- Test before buying',
      '- Take photos of serial numbers',
      '',
      `Deal ID: ${dealId}`,
    ].join('\\n'),
    location: deal.pickupLocation || deal.listing.location?.address || 
              `${deal.listing.location?.city}, ${deal.listing.location?.state}`,
    start: pickupDate,
    end: new Date(pickupDate.getTime() + duration * 60 * 1000),
    url: deal.listing.url,
    alarms: [
      { minutes: 60, description: 'Pickup in 1 hour' },
      { minutes: 15, description: 'Pickup in 15 minutes' },
    ],
  };
  
  const icsContent = buildIcsEvent(event);
  const filename = `pickup-${deal.listing.title.replace(/[^a-z0-9]/gi, '-')}.ics`;
  
  await saveIcsFile(icsContent, filename);
}

/**
 * Create follow-up reminder ICS
 */
export async function createFollowUpIcs(dealId: string): Promise<void> {
  const deal = await db.deals.where('id').equals(dealId).first();
  if (!deal) throw new Error('Deal not found');
  
  const settings = await getSettings();
  const followUpDate = new Date();
  
  // Set follow-up time based on settings
  const cadence = settings.operations?.follow_up_cadence_hours || 24;
  followUpDate.setHours(followUpDate.getHours() + cadence);
  
  const event: ICSEvent = {
    uid: generateEventUid(dealId, 'followup'),
    title: `Follow up: ${deal.listing.title}`,
    description: [
      `Seller: ${deal.listing.seller?.name || 'Unknown'}`,
      `Stage: ${deal.stage}`,
      `Last contact: ${deal.lastContact || 'Never'}`,
      '',
      'Suggested message:',
      '"Hi! Just following up on the gaming PC. Is it still available?"',
      '',
      `Deal ID: ${dealId}`,
    ].join('\\n'),
    start: followUpDate,
    end: new Date(followUpDate.getTime() + 15 * 60 * 1000), // 15 min
    url: deal.listing.url,
    alarms: [
      { minutes: 0, description: 'Time to follow up' },
    ],
  };
  
  const icsContent = buildIcsEvent(event);
  const filename = `followup-${deal.listing.title.replace(/[^a-z0-9]/gi, '-')}.ics`;
  
  await saveIcsFile(icsContent, filename);
}

/**
 * Create batch pickup events for route
 */
export async function createRouteIcs(dealIds: string[]): Promise<void> {
  const deals = await db.deals.where('id').anyOf(dealIds).toArray();
  if (deals.length === 0) return;
  
  const events: ICSEvent[] = [];
  let currentTime = new Date();
  currentTime.setHours(10, 0, 0, 0); // Start at 10 AM
  
  for (const deal of deals) {
    const event: ICSEvent = {
      uid: generateEventUid(deal.id, 'pickup'),
      title: `Pickup ${events.length + 1}: ${deal.listing.title}`,
      description: [
        `Seller: ${deal.listing.seller?.name || 'Unknown'}`,
        `Price: $${deal.listing.price}`,
        `Address: ${deal.pickupLocation || deal.listing.location?.address || 'See listing'}`,
        '',
        `Stop ${events.length + 1} of ${deals.length}`,
      ].join('\\n'),
      location: deal.pickupLocation || 
                `${deal.listing.location?.city}, ${deal.listing.location?.state}`,
      start: new Date(currentTime),
      end: new Date(currentTime.getTime() + 30 * 60 * 1000), // 30 min per stop
      url: deal.listing.url,
      alarms: [
        { minutes: 15, description: 'Next pickup in 15 minutes' },
      ],
    };
    
    events.push(event);
    
    // Add 45 minutes between stops (30 min pickup + 15 min travel)
    currentTime = new Date(currentTime.getTime() + 45 * 60 * 1000);
  }
  
  // Use buildIcsCalendar for multiple events
  const { buildIcsCalendar } = await import('@arbitrage/integrations/calendar/ics');
  const icsContent = buildIcsCalendar(events);
  const filename = `route-${new Date().toISOString().split('T')[0]}.ics`;
  
  await saveIcsFile(icsContent, filename);
}