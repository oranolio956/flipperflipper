/**
 * Comps Module Tests
 */

import { describe, it, expect } from 'vitest';
import {
  normalizeCompTitleToSpecs,
  mergeComps,
  computeCompStats,
  type CompRecord,
} from './index';

describe('normalizeCompTitleToSpecs', () => {
  it('should extract CPU from title', () => {
    const specs = normalizeCompTitleToSpecs('Gaming PC i7-10700K RTX 3070');
    expect(specs.cpu).toBe('i7-10700K');
  });

  it('should extract GPU from title', () => {
    const specs = normalizeCompTitleToSpecs('Custom Build with RTX 3080 Ti');
    expect(specs.gpu).toBe('RTX 3080 Ti');
  });

  it('should extract RAM from description', () => {
    const specs = normalizeCompTitleToSpecs('Gaming Desktop', '32GB DDR4 RAM');
    expect(specs.ram).toBe(32);
  });

  it('should extract storage from combined text', () => {
    const specs = normalizeCompTitleToSpecs('PC Build', '1TB NVMe SSD + 2TB HDD');
    expect(specs.storage).toBe(3072); // 1TB + 2TB in GB
  });

  it('should infer condition', () => {
    expect(normalizeCompTitleToSpecs('New in Box Gaming PC').condition).toBe('new');
    expect(normalizeCompTitleToSpecs('Refurbished Desktop').condition).toBe('refurbished');
    expect(normalizeCompTitleToSpecs('For Parts PC').condition).toBe('parts');
    expect(normalizeCompTitleToSpecs('Used Gaming PC').condition).toBe('used');
  });
});

describe('mergeComps', () => {
  const existing: CompRecord[] = [
    {
      id: '1',
      source: 'ebay',
      title: 'PC 1',
      price: 1000,
      currency: 'USD',
      timestamp: new Date('2024-01-01'),
      url: 'http://example.com/1',
    },
  ];

  it('should merge without duplicates when using URL dedup', () => {
    const incoming: CompRecord[] = [
      {
        id: '2',
        source: 'ebay',
        title: 'PC 2',
        price: 1200,
        currency: 'USD',
        timestamp: new Date('2024-01-02'),
        url: 'http://example.com/2',
      },
      {
        id: '3',
        source: 'ebay',
        title: 'PC 1 Duplicate',
        price: 1000,
        currency: 'USD',
        timestamp: new Date('2024-01-01'),
        url: 'http://example.com/1', // Same URL as existing
      },
    ];

    const merged = mergeComps(existing, incoming, 'url');
    expect(merged).toHaveLength(2);
    expect(merged.map(c => c.id)).toEqual(['1', '2']);
  });

  it('should merge without duplicates when using title+price+ts dedup', () => {
    const incoming: CompRecord[] = [
      {
        id: '2',
        source: 'fb',
        title: 'PC 1', // Same title, price, timestamp
        price: 1000,
        currency: 'USD',
        timestamp: new Date('2024-01-01'),
      },
    ];

    const merged = mergeComps(existing, incoming, 'titlePriceTs');
    expect(merged).toHaveLength(1);
  });
});

describe('computeCompStats', () => {
  const records: CompRecord[] = [
    {
      id: '1',
      source: 'ebay',
      title: 'PC 1',
      price: 800,
      currency: 'USD',
      timestamp: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000), // 5 days ago
      cpu: 'i7-10700K',
      gpu: 'RTX 3070',
      ram: 16,
    },
    {
      id: '2',
      source: 'ebay',
      title: 'PC 2',
      price: 1000,
      currency: 'USD',
      timestamp: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000), // 10 days ago
      cpu: 'i7-10700K',
      gpu: 'RTX 3070',
      ram: 16,
    },
    {
      id: '3',
      source: 'fb',
      title: 'PC 3',
      price: 1200,
      currency: 'USD',
      timestamp: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000), // 15 days ago
      cpu: 'i7-10700K',
      gpu: 'RTX 3070',
      ram: 16,
    },
  ];

  it('should compute stats for matching records', () => {
    const stats = computeCompStats({ cpu: 'i7-10700K', gpu: 'RTX 3070' }, records);
    
    expect(stats).not.toBeNull();
    expect(stats!.n).toBe(3);
    expect(stats!.median).toBe(1000);
    expect(stats!.p25).toBe(900); // Interpolated
    expect(stats!.p75).toBe(1100); // Interpolated
    expect(stats!.recencyDays).toBe(10); // Average age
  });

  it('should filter by CPU', () => {
    const stats = computeCompStats({ cpu: 'i9' }, records);
    expect(stats).toBeNull(); // No matches
  });

  it('should filter by RAM within tolerance', () => {
    const stats = computeCompStats({ ram: 18 }, records);
    expect(stats!.n).toBe(3); // All within 4GB tolerance
  });

  it('should handle empty results', () => {
    const stats = computeCompStats({ gpu: 'RTX 4090' }, records);
    expect(stats).toBeNull();
  });
});

describe('pricing integrations', () => {
  it('should blend comp stats with base value', async () => {
    const { adjustValueWithComps } = await import('../pricing/integrations');
    
    const baseValue = {
      fmv: 1000,
      confidence: 0.7,
      source: 'tier estimate',
    };
    
    const compStats = {
      median: 1200,
      p25: 1100,
      p75: 1300,
      n: 10,
      recencyDays: 7,
    };
    
    const adjusted = adjustValueWithComps(baseValue, compStats, 0.7);
    
    expect(adjusted.fmv).toBe(1140); // 30% * 1000 + 70% * 1200
    expect(adjusted.confidence).toBeGreaterThan(baseValue.confidence);
    expect(adjusted.source).toContain('10 comps');
  });
});