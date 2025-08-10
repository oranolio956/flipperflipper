/**
 * P&L Tests
 */

import { describe, it, expect } from 'vitest';
import { 
  computeDealPnL, 
  rollupPnL,
  generatePnLTimeSeries 
} from './pnl';
import type { Deal } from '../types';

const createDeal = (overrides: Partial<Deal> = {}): Deal => ({
  id: '123',
  listingId: 'listing-123',
  listing: {
    id: 'listing-123',
    title: 'Gaming PC',
    externalId: 'ext-123',
    platform: 'facebook',
    url: 'https://example.com',
    price: { amount: 1000, currency: 'USD', formatted: '$1,000' },
    seller: { id: 'seller-123', name: 'John Doe', profileUrl: '' },
    location: { city: 'SF', state: 'CA' },
    metadata: { createdAt: new Date(), updatedAt: new Date(), status: 'active' },
  },
  stage: 'sold',
  financials: {
    purchasePrice: 800,
    listingFees: 0,
    transportCost: 0,
    refurbCosts: [],
    totalInvestment: 800,
    estimatedResale: 1200,
    estimatedProfit: 400,
  },
  negotiation: {
    askingPrice: 1000,
    offers: [],
    walkAwayPrice: 700,
    targetPrice: 850,
  },
  communication: {
    messages: [],
    templates: [],
    sellerEngagement: 'medium',
  },
  logistics: {
    pickup: { confirmed: true, notes: '' },
    transport: { method: 'personal', cost: 0, distance: 10, time: 30 },
  },
  documentation: {
    receipts: [],
    photos: [],
    serialNumbers: [],
    testResults: [],
  },
  analytics: {
    daysInStage: {} as any,
    totalCycleDays: 7,
    profitMargin: 0.25,
    roi: 0.5,
    scorecard: { negotiation: 8, timing: 9, execution: 8, overall: 8 },
  },
  metadata: {
    createdAt: new Date(),
    updatedAt: new Date(),
    createdBy: 'user-123',
    tags: [],
    priority: 'medium',
    archived: false,
  },
  purchasePrice: 800,
  sellPrice: 1200,
  sellPlatform: 'facebook',
  soldAt: new Date(),
  ...overrides,
} as Deal);

describe('computeDealPnL', () => {
  it('should calculate P&L for Facebook sale', () => {
    const deal = createDeal({
      purchasePrice: 800,
      sellPrice: 1200,
      sellPlatform: 'facebook',
      logistics: {
        pickup: { confirmed: true, notes: '' },
        transport: { method: 'personal', cost: 0, distance: 20, time: 30 },
      },
    });
    
    const pnl = computeDealPnL(deal);
    
    expect(pnl.revenue).toBe(1200);
    expect(pnl.cogs).toBe(800);
    expect(pnl.fees).toBe(60); // 5% of 1200
    expect(pnl.mileage).toBeCloseTo(13.1); // 20 miles * 0.655
    expect(pnl.supplies).toBe(5); // Default
    expect(pnl.grossProfit).toBe(400);
    expect(pnl.marginPct).toBeGreaterThan(20);
    expect(pnl.roiPct).toBeGreaterThan(30);
  });

  it('should calculate different fees for eBay', () => {
    const deal = createDeal({
      sellPlatform: 'ebay',
      sellPrice: 1000,
    });
    
    const pnl = computeDealPnL(deal);
    
    expect(pnl.fees).toBe(100); // 10% of 1000
  });

  it('should handle losses', () => {
    const deal = createDeal({
      purchasePrice: 1000,
      sellPrice: 800,
    });
    
    const pnl = computeDealPnL(deal);
    
    expect(pnl.netProfit).toBeLessThan(0);
    expect(pnl.marginPct).toBeLessThan(0);
    expect(pnl.taxes).toBe(0); // No tax on losses
  });
});

describe('rollupPnL', () => {
  it('should aggregate multiple deals', () => {
    const deals = [
      createDeal({ purchasePrice: 500, sellPrice: 700, stage: 'sold' }),
      createDeal({ purchasePrice: 800, sellPrice: 1200, stage: 'sold' }),
      createDeal({ purchasePrice: 600, sellPrice: 900, stage: 'sold' }),
    ];
    
    const summary = rollupPnL(deals);
    
    expect(summary.dealCount).toBe(3);
    expect(summary.totalRevenue).toBe(2800);
    expect(summary.totalCogs).toBe(1900);
    expect(summary.avgDealSize).toBeCloseTo(933.33);
  });

  it('should filter by date range', () => {
    const now = new Date();
    const oldDate = new Date(now.getTime() - 60 * 24 * 60 * 60 * 1000); // 60 days ago
    
    const deals = [
      createDeal({ soldAt: now, stage: 'sold' }),
      createDeal({ soldAt: oldDate, stage: 'sold' }),
    ];
    
    const range = {
      start: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000),
      end: now,
    };
    
    const summary = rollupPnL(deals, range);
    
    expect(summary.dealCount).toBe(1); // Only recent deal
  });

  it('should only include sold deals', () => {
    const deals = [
      createDeal({ stage: 'sold' }),
      createDeal({ stage: 'acquired' }),
      createDeal({ stage: 'listed' }),
    ];
    
    const summary = rollupPnL(deals);
    
    expect(summary.dealCount).toBe(1);
  });
});

describe('generatePnLTimeSeries', () => {
  it('should group by month', () => {
    const deals = [
      createDeal({ 
        soldAt: new Date('2024-01-15'), 
        stage: 'sold',
        sellPrice: 1000,
      }),
      createDeal({ 
        soldAt: new Date('2024-01-20'), 
        stage: 'sold',
        sellPrice: 1200,
      }),
      createDeal({ 
        soldAt: new Date('2024-02-10'), 
        stage: 'sold',
        sellPrice: 1100,
      }),
    ];
    
    const series = generatePnLTimeSeries(deals, 'monthly');
    
    expect(series).toHaveLength(2);
    expect(series[0].date).toBe('2024-01');
    expect(series[0].dealCount).toBe(2);
    expect(series[0].revenue).toBe(2200);
    expect(series[1].date).toBe('2024-02');
    expect(series[1].dealCount).toBe(1);
  });

  it('should handle empty deals', () => {
    const series = generatePnLTimeSeries([]);
    expect(series).toHaveLength(0);
  });
});