/**
 * Analytics Tests
 */

import { describe, it, expect } from 'vitest';
import {
  cohortsByMonth,
  seasonalityFactors,
  priceElasticity,
  demandScoreByComponent,
  marginTrend,
} from './index';
import type { Deal } from '../types';

// Test fixtures
const createDeal = (overrides: Partial<Deal> = {}): Deal => ({
  id: 'deal-1',
  listingId: 'listing-1',
  stage: 'sold',
  listing: {
    id: 'listing-1',
    platform: 'facebook',
    externalId: 'fb-123',
    url: 'https://facebook.com/item/123',
    title: 'Gaming PC',
    description: 'Test PC',
    price: 1000,
    location: { city: 'Denver', state: 'CO' },
    images: [],
    seller: { name: 'Seller', id: 'seller-1' },
    components: {
      cpu: { model: 'i7-10700K', condition: 'used' },
      gpu: { model: 'RTX 3070', vram: 8, condition: 'used' },
    },
    metadata: {
      createdAt: new Date('2024-01-01'),
      lastSeen: new Date('2024-01-01'),
      priceHistory: [],
    },
  },
  metrics: {
    estimatedProfit: 200,
    roi: 0.25,
    dealScore: 80,
  },
  history: [],
  metadata: {
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-15'),
  },
  soldAt: new Date('2024-01-15'),
  soldPrice: 900,
  ...overrides,
});

describe('cohortsByMonth', () => {
  it('should group deals by acquisition month', () => {
    const deals = [
      createDeal({ metadata: { createdAt: new Date('2024-01-15'), updatedAt: new Date() } }),
      createDeal({ metadata: { createdAt: new Date('2024-01-20'), updatedAt: new Date() } }),
      createDeal({ metadata: { createdAt: new Date('2024-02-10'), updatedAt: new Date() } }),
    ];
    
    const cohorts = cohortsByMonth(deals);
    
    expect(cohorts).toHaveLength(2);
    expect(cohorts[0].month).toBe('2024-01');
    expect(cohorts[0].acquired).toBe(2);
    expect(cohorts[0].sold).toBe(2);
    expect(cohorts[1].month).toBe('2024-02');
    expect(cohorts[1].acquired).toBe(1);
  });

  it('should calculate average metrics correctly', () => {
    const deals = [
      createDeal({ metrics: { roi: 0.20, estimatedProfit: 200, dealScore: 80 } }),
      createDeal({ metrics: { roi: 0.30, estimatedProfit: 300, dealScore: 90 } }),
    ];
    
    const cohorts = cohortsByMonth(deals);
    
    expect(cohorts[0].avgMarginPct).toBe(25); // (0.20 + 0.30) / 2 * 100
    expect(cohorts[0].avgTurnTime).toBe(14); // 15 days - 1 day
  });
});

describe('seasonalityFactors', () => {
  it('should calculate weekday factors', () => {
    const deals = [
      createDeal({ soldAt: new Date('2024-01-01'), soldPrice: 1000 }), // Monday
      createDeal({ soldAt: new Date('2024-01-02'), soldPrice: 1000 }), // Tuesday
      createDeal({ soldAt: new Date('2024-01-03'), soldPrice: 2000 }), // Wednesday
    ];
    
    const factors = seasonalityFactors(deals);
    
    expect(factors.weekday).toHaveLength(7);
    expect(factors.weekday[3]).toBeGreaterThan(1); // Wednesday has higher revenue
  });

  it('should handle empty data', () => {
    const factors = seasonalityFactors([]);
    
    expect(factors.weekday).toEqual(new Array(7).fill(1));
    expect(factors.month).toEqual(new Array(12).fill(1));
  });
});

describe('priceElasticity', () => {
  it('should calculate linear regression', () => {
    const deals = [
      createDeal({ listing: { ...createDeal().listing, price: 1000 }, soldPrice: 950, soldAt: new Date('2024-01-05') }),
      createDeal({ listing: { ...createDeal().listing, price: 1000 }, soldPrice: 900, soldAt: new Date('2024-01-10') }),
      createDeal({ listing: { ...createDeal().listing, price: 1000 }, soldPrice: 850, soldAt: new Date('2024-01-15') }),
    ];
    
    const elasticity = priceElasticity(deals);
    
    expect(elasticity.slope).toBeGreaterThan(0); // More discount = more days
    expect(elasticity.r2).toBeGreaterThan(0);
    expect(elasticity.r2).toBeLessThanOrEqual(1);
  });

  it('should handle insufficient data', () => {
    const elasticity = priceElasticity([createDeal()]);
    
    expect(elasticity.slope).toBe(0);
    expect(elasticity.intercept).toBe(0);
    expect(elasticity.r2).toBe(0);
  });
});

describe('demandScoreByComponent', () => {
  it('should rank components by velocity × margin', () => {
    const deals = [
      createDeal({ 
        listing: { 
          ...createDeal().listing, 
          components: { gpu: { model: 'RTX 3070', vram: 8, condition: 'used' } } 
        },
        metrics: { roi: 0.30, estimatedProfit: 300, dealScore: 90 }
      }),
      createDeal({ 
        listing: { 
          ...createDeal().listing, 
          components: { gpu: { model: 'RTX 3060', vram: 12, condition: 'used' } } 
        },
        metrics: { roi: 0.20, estimatedProfit: 200, dealScore: 70 }
      }),
    ];
    
    const scores = demandScoreByComponent(deals);
    
    expect(scores).toHaveLength(2);
    expect(scores[0].component).toContain('RTX 3070'); // Higher margin
    expect(scores[0].score).toBeGreaterThan(scores[1].score);
  });
});

describe('marginTrend', () => {
  it('should calculate rolling average', () => {
    const deals = [
      createDeal({ soldAt: new Date('2024-01-01'), metrics: { roi: 0.20, estimatedProfit: 200, dealScore: 80 } }),
      createDeal({ soldAt: new Date('2024-01-15'), metrics: { roi: 0.30, estimatedProfit: 300, dealScore: 90 } }),
      createDeal({ soldAt: new Date('2024-02-01'), metrics: { roi: 0.25, estimatedProfit: 250, dealScore: 85 } }),
    ];
    
    const trend = marginTrend(deals, 30);
    
    expect(trend.length).toBeGreaterThan(0);
    expect(trend[0].marginPct).toBeCloseTo(25); // Average of first window
    expect(trend[0].dealCount).toBeGreaterThan(0);
  });

  it('should handle empty data', () => {
    const trend = marginTrend([]);
    expect(trend).toEqual([]);
  });
});