/**
 * Offer Engine
 * Manage multiple concurrent offers with smart anchoring
 */

import { db } from './db';
import { generateId } from '@/core';
import type { DBOffer, DBThread } from './db';
import type { CompStats } from '@/core/comps';

export interface OfferAnchors {
  open: number;      // Opening offer
  target: number;    // Target price
  walkaway: number;  // Minimum acceptable
}

/**
 * Suggest offer anchors based on FMV and risk
 */
export function suggestAnchors(
  fmv: number,
  riskScore: number,
  comps?: CompStats | null
): OfferAnchors {
  // Base margins
  let openMargin = 0.25;  // Start 25% below FMV
  let targetMargin = 0.15; // Target 15% below FMV
  let walkawayMargin = 0.05; // Walk at 5% below FMV
  
  // Adjust for risk
  if (riskScore > 50) {
    openMargin += 0.1;
    targetMargin += 0.08;
    walkawayMargin += 0.05;
  } else if (riskScore > 30) {
    openMargin += 0.05;
    targetMargin += 0.03;
    walkawayMargin += 0.02;
  }
  
  // Adjust for comp data
  if (comps && comps.n >= 5) {
    // If we have good comp data, be more aggressive
    const spread = (comps.p75 - comps.p25) / comps.median;
    if (spread > 0.2) {
      // High variance = more negotiation room
      openMargin += 0.05;
    }
  }
  
  return {
    open: Math.round(fmv * (1 - openMargin)),
    target: Math.round(fmv * (1 - targetMargin)),
    walkaway: Math.round(fmv * (1 - walkawayMargin)),
  };
}

/**
 * Calculate next follow-up time based on cadence
 */
export function calculateNextFollowUp(
  thread: Pick<DBThread, 'cadence' | 'lastMsgAt'>
): Date {
  const now = new Date();
  const lastMsg = new Date(thread.lastMsgAt);
  
  switch (thread.cadence) {
    case '1h':
      return new Date(lastMsg.getTime() + 60 * 60 * 1000);
    case '24h':
      return new Date(lastMsg.getTime() + 24 * 60 * 60 * 1000);
    case '3d':
      return new Date(lastMsg.getTime() + 3 * 24 * 60 * 60 * 1000);
    default:
      return new Date(lastMsg.getTime() + 24 * 60 * 60 * 1000);
  }
}

/**
 * Create a new offer
 */
export async function createOffer(
  listingId: string,
  amount: number,
  message?: string,
  variantId?: string
): Promise<DBOffer> {
  const offer: DBOffer = {
    id: generateId(),
    listingId,
    amount,
    message,
    variantId,
    timestamp: new Date(),
    status: 'draft',
  };
  
  const id = await db.offers.add(offer);
  return { ...offer, _id: id };
}

/**
 * Get all offers for a listing
 */
export async function getListingOffers(listingId: string): Promise<DBOffer[]> {
  return db.offers
    .where('listingId')
    .equals(listingId)
    .reverse()
    .sortBy('timestamp');
}

/**
 * Update offer status
 */
export async function updateOfferStatus(
  offerId: string,
  status: DBOffer['status'],
  response?: string
): Promise<void> {
  await db.offers
    .where('id')
    .equals(offerId)
    .modify({ status, response });
}

/**
 * Create or update thread
 */
export async function upsertThread(
  listingId: string,
  sellerId: string,
  platform: string,
  message: { content: string; direction: 'sent' | 'received' }
): Promise<DBThread> {
  const existing = await db.threads
    .where('listingId')
    .equals(listingId)
    .first();
  
  if (existing) {
    // Update existing thread
    existing.messages.push({
      id: generateId(),
      content: message.content,
      timestamp: new Date(),
      direction: message.direction,
    });
    existing.lastMsgAt = new Date();
    existing.nextFollowUpAt = calculateNextFollowUp(existing);
    
    await db.threads.update(existing._id!, existing);
    return existing;
  } else {
    // Create new thread
    const thread: DBThread = {
      id: generateId(),
      listingId,
      sellerId,
      platform,
      messages: [{
        id: generateId(),
        content: message.content,
        timestamp: new Date(),
        direction: message.direction,
      }],
      lastMsgAt: new Date(),
      cadence: '24h',
      nextFollowUpAt: new Date(Date.now() + 24 * 60 * 60 * 1000),
      status: 'active',
    };
    
    const id = await db.threads.add(thread);
    return { ...thread, _id: id };
  }
}

/**
 * Get threads needing follow-up
 */
export async function getThreadsNeedingFollowUp(): Promise<DBThread[]> {
  const now = new Date();
  return db.threads
    .where('nextFollowUpAt')
    .below(now)
    .and(thread => thread.status === 'active')
    .toArray();
}

/**
 * Calculate offer statistics for a listing
 */
export async function getOfferStats(listingId: string) {
  const offers = await getListingOffers(listingId);
  
  const sent = offers.filter(o => o.status === 'sent').length;
  const accepted = offers.filter(o => o.status === 'accepted').length;
  const rejected = offers.filter(o => o.status === 'rejected').length;
  const countered = offers.filter(o => o.status === 'countered').length;
  
  const amounts = offers.map(o => o.amount);
  const best = offers.find(o => o.status === 'accepted')?.amount || 
               (amounts.length > 0 ? Math.max(...amounts) : 0);
  
  return {
    total: offers.length,
    sent,
    accepted,
    rejected,
    countered,
    bestOffer: best,
    acceptRate: sent > 0 ? accepted / sent : 0,
  };
}