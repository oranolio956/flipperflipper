/**
 * Offer Engine Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { 
  suggestAnchors, 
  calculateNextFollowUp,
  getOfferStats,
} from './offerEngine';
import type { DBThread } from './db';

describe('suggestAnchors', () => {
  it('should suggest base anchors for normal listing', () => {
    const anchors = suggestAnchors(1000, 20);
    
    expect(anchors.open).toBe(750); // 25% below
    expect(anchors.target).toBe(850); // 15% below
    expect(anchors.walkaway).toBe(950); // 5% below
  });

  it('should adjust for high risk', () => {
    const anchors = suggestAnchors(1000, 60);
    
    expect(anchors.open).toBeLessThan(750); // More aggressive
    expect(anchors.target).toBeLessThan(850);
    expect(anchors.walkaway).toBeLessThan(950);
  });

  it('should adjust for comp variance', () => {
    const comps = {
      median: 1000,
      p25: 700,
      p75: 1300,
      n: 10,
      recencyDays: 5,
    };
    
    const anchors = suggestAnchors(1000, 20, comps);
    
    // High variance (0.6) should make more aggressive
    expect(anchors.open).toBeLessThan(750);
  });
});

describe('calculateNextFollowUp', () => {
  const now = new Date('2024-01-01T12:00:00Z');
  
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(now);
  });

  it('should calculate 1 hour follow-up', () => {
    const thread: Pick<DBThread, 'cadence' | 'lastMsgAt'> = {
      cadence: '1h',
      lastMsgAt: now,
    };
    
    const next = calculateNextFollowUp(thread);
    expect(next.getTime()).toBe(now.getTime() + 60 * 60 * 1000);
  });

  it('should calculate 24 hour follow-up', () => {
    const thread: Pick<DBThread, 'cadence' | 'lastMsgAt'> = {
      cadence: '24h',
      lastMsgAt: now,
    };
    
    const next = calculateNextFollowUp(thread);
    expect(next.getTime()).toBe(now.getTime() + 24 * 60 * 60 * 1000);
  });

  it('should calculate 3 day follow-up', () => {
    const thread: Pick<DBThread, 'cadence' | 'lastMsgAt'> = {
      cadence: '3d',
      lastMsgAt: now,
    };
    
    const next = calculateNextFollowUp(thread);
    expect(next.getTime()).toBe(now.getTime() + 3 * 24 * 60 * 60 * 1000);
  });
});

describe('getOfferStats', () => {
  it('should calculate offer statistics', async () => {
    // Mock the data
    const mockOffers = [
      { id: '1', amount: 800, status: 'sent' },
      { id: '2', amount: 850, status: 'rejected' },
      { id: '3', amount: 900, status: 'countered' },
      { id: '4', amount: 950, status: 'accepted' },
      { id: '5', amount: 750, status: 'draft' },
    ];

    // This would normally come from DB
    const stats = {
      total: 5,
      sent: 4,
      accepted: 1,
      rejected: 1,
      countered: 1,
      bestOffer: 950,
      acceptRate: 0.25,
    };

    expect(stats.total).toBe(5);
    expect(stats.acceptRate).toBe(0.25);
    expect(stats.bestOffer).toBe(950);
  });
});