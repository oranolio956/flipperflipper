/**
 * Tests for Watches Module
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { 
  recordPrice, 
  getPriceHistory, 
  getSparklineData,
  addSavedSearch,
  getSavedSearches,
  updateSavedSearch,
  deleteSavedSearch,
  getSearchesDue,
  type PriceHistory,
  type SavedSearch,
} from '../watches';
import { db } from '../db';

// Mock database
vi.mock('../db', () => ({
  db: {
    priceHistory: {
      add: vi.fn(),
      where: vi.fn(() => ({
        equals: vi.fn(() => ({
          sortBy: vi.fn(() => Promise.resolve([])),
          and: vi.fn(() => ({
            sortBy: vi.fn(() => Promise.resolve([])),
          })),
        })),
      })),
      bulkDelete: vi.fn(),
    },
    savedSearches: {
      add: vi.fn(() => Promise.resolve(1)),
      toArray: vi.fn(() => Promise.resolve([])),
      where: vi.fn(() => ({
        equals: vi.fn(() => ({
          first: vi.fn(),
          delete: vi.fn(),
          and: vi.fn(() => ({
            toArray: vi.fn(() => Promise.resolve([])),
          })),
        })),
      })),
      update: vi.fn(),
    },
    savedSearchRuns: {
      add: vi.fn(),
      where: vi.fn(() => ({
        equals: vi.fn(() => ({
          delete: vi.fn(),
        })),
      })),
    },
  },
}));

describe('Price History', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should record price', async () => {
    await recordPrice('listing123', 500);
    
    expect(db.priceHistory.add).toHaveBeenCalledWith(
      expect.objectContaining({
        listingId: 'listing123',
        price: 500,
        timestamp: expect.any(Date),
      })
    );
  });

  it('should get price history', async () => {
    const mockHistory: PriceHistory[] = [
      { id: '1', listingId: 'listing123', price: 500, timestamp: new Date() },
      { id: '2', listingId: 'listing123', price: 480, timestamp: new Date() },
    ];
    
    vi.mocked(db.priceHistory.where).mockReturnValue({
      equals: vi.fn(() => ({
        and: vi.fn(() => ({
          sortBy: vi.fn(() => Promise.resolve(mockHistory)),
        })),
      })),
    } as any);
    
    const history = await getPriceHistory('listing123');
    
    expect(history).toEqual(mockHistory);
  });

  it('should generate sparkline data', () => {
    const history: PriceHistory[] = [
      { id: '1', listingId: 'listing123', price: 500, timestamp: new Date() },
      { id: '2', listingId: 'listing123', price: 480, timestamp: new Date() },
      { id: '3', listingId: 'listing123', price: 450, timestamp: new Date() },
    ];
    
    const sparkline = getSparklineData(history);
    
    expect(sparkline).toMatch(/^\d+,\d+\s+\d+,\d+\s+\d+,\d+$/);
  });
});

describe('Saved Searches', () => {
  it('should add saved search', async () => {
    const search = {
      name: 'Test Search',
      url: 'https://example.com/search',
      cadenceMin: 60,
      enabled: true,
      filters: {},
    };
    
    const result = await addSavedSearch(search);
    
    expect(result).toMatchObject({
      ...search,
      id: expect.any(String),
      createdAt: expect.any(Date),
      _id: 1,
    });
  });

  it('should get searches due', async () => {
    const searches: SavedSearch[] = [
      {
        id: '1',
        name: 'Old Search',
        url: 'https://example.com',
        cadenceMin: 60,
        enabled: true,
        filters: {},
        createdAt: new Date(),
        lastRunAt: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
      },
      {
        id: '2',
        name: 'Recent Search',
        url: 'https://example.com',
        cadenceMin: 60,
        enabled: true,
        filters: {},
        createdAt: new Date(),
        lastRunAt: new Date(Date.now() - 30 * 60 * 1000), // 30 min ago
      },
    ];
    
    vi.mocked(db.savedSearches.where).mockReturnValue({
      equals: vi.fn(() => ({
        and: vi.fn(() => ({
          toArray: vi.fn(() => Promise.resolve(searches)),
        })),
      })),
    } as any);
    
    const due = await getSearchesDue();
    
    expect(due).toHaveLength(1);
    expect(due[0].name).toBe('Old Search');
  });
});

describe('Sparkline Generation', () => {
  it('should handle empty history', () => {
    expect(getSparklineData([])).toBe('');
  });
  
  it('should handle single point', () => {
    const history: PriceHistory[] = [
      { id: '1', listingId: 'listing123', price: 500, timestamp: new Date() },
    ];
    
    expect(getSparklineData(history)).toBe('');
  });
  
  it('should normalize prices correctly', () => {
    const history: PriceHistory[] = [
      { id: '1', listingId: 'listing123', price: 100, timestamp: new Date() },
      { id: '2', listingId: 'listing123', price: 200, timestamp: new Date() },
      { id: '3', listingId: 'listing123', price: 150, timestamp: new Date() },
    ];
    
    const sparkline = getSparklineData(history);
    const points = sparkline.split(' ');
    
    expect(points).toHaveLength(3);
    
    // First point should be at x=0, y=100 (lowest price)
    expect(points[0]).toBe('0,100');
    
    // Last point should be at x=100
    expect(points[2]).toMatch(/^100,/);
  });
});