/**
 * Competition Signals Tests
 */

import { describe, it, expect } from 'vitest';
import { computeCompetitionScore, extractSignalsFromListing } from './signals';

describe('computeCompetitionScore', () => {
  it('should score low competition for stale listing', () => {
    const signals = {
      daysLive: 20,
      commentCount: 2,
      interestedCount: 1,
    };
    
    const score = computeCompetitionScore(signals);
    
    expect(score.score).toBeLessThan(30);
    expect(score.reasons).toContain('Listed 2+ weeks (stale)');
    expect(score.tips).toContain('Seller may be more flexible');
  });

  it('should score high competition for fresh listing with activity', () => {
    const signals = {
      daysLive: 0,
      commentCount: 25,
      interestedCount: 15,
    };
    
    const score = computeCompetitionScore(signals);
    
    expect(score.score).toBeGreaterThan(60);
    expect(score.reasons).toContain('Fresh listing (<24h)');
    expect(score.reasons).toContain('High comment activity (25)');
    expect(score.tips).toContain('Act fast - many buyers engaged');
  });

  it('should reduce score for relisted items', () => {
    const baseSignals = {
      daysLive: 5,
      commentCount: 10,
    };
    
    const withoutRelist = computeCompetitionScore(baseSignals);
    const withRelist = computeCompetitionScore({
      ...baseSignals,
      relistCount: 2,
    });
    
    expect(withRelist.score).toBeLessThan(withoutRelist.score);
    expect(withRelist.tips).toContain('Previous buyers fell through - negotiate harder');
  });

  it('should identify high-volume sellers', () => {
    const signals = {
      daysLive: 3,
      sellerListingCount: 30,
    };
    
    const score = computeCompetitionScore(signals);
    
    expect(score.reasons).toContain('High-volume seller');
    expect(score.tips).toContain('Likely a reseller - less emotional attachment');
  });

  it('should detect price drops as low competition signal', () => {
    const signals = {
      daysLive: 7,
      priceDrops: 2,
    };
    
    const score = computeCompetitionScore(signals);
    
    expect(score.reasons).toContain('Price dropped 2 times');
    expect(score.tips).toContain('Seller motivated - room for negotiation');
  });

  it('should cap score at 0-100', () => {
    const highSignals = {
      daysLive: 0,
      commentCount: 100,
      interestedCount: 50,
      viewCount: 1000,
    };
    
    const lowSignals = {
      daysLive: 30,
      commentCount: 0,
      relistCount: 5,
      priceDrops: 3,
    };
    
    const highScore = computeCompetitionScore(highSignals);
    const lowScore = computeCompetitionScore(lowSignals);
    
    expect(highScore.score).toBe(100);
    expect(lowScore.score).toBe(0);
  });
});

describe('extractSignalsFromListing', () => {
  it('should extract signals from listing object', () => {
    const listing = {
      metadata: {
        createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3 days ago
        relistCount: 1,
      },
      engagement: {
        commentCount: 15,
        interestedCount: 8,
        viewCount: 250,
      },
    };
    
    const signals = extractSignalsFromListing(listing);
    
    expect(signals.daysLive).toBe(3);
    expect(signals.commentCount).toBe(15);
    expect(signals.interestedCount).toBe(8);
    expect(signals.viewCount).toBe(250);
    expect(signals.relistCount).toBe(1);
  });

  it('should handle missing data gracefully', () => {
    const listing = {};
    
    const signals = extractSignalsFromListing(listing);
    
    expect(signals.daysLive).toBe(0);
    expect(signals.commentCount).toBeUndefined();
    expect(signals.interestedCount).toBeUndefined();
  });
});