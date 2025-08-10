/**
 * Google Sheets Adapter Tests
 */

import { describe, it, expect } from 'vitest';
import {
  buildRowFromDeal,
  parseRowToDeal,
  diffLocalVsRemote,
  buildHeaderRow,
  DEFAULT_DEAL_MAPPING,
} from './sheetsAdapter';
import type { Deal } from '@/core';

const mockDeal: Deal = {
  id: 'deal-123',
  listingId: 'listing-456',
  stage: 'negotiating',
  listing: {
    id: 'listing-456',
    platform: 'facebook',
    externalId: 'fb-789',
    url: 'https://facebook.com/marketplace/item/789',
    title: 'Gaming PC RTX 3070',
    description: 'Great condition gaming PC',
    price: 1200,
    location: {
      city: 'Denver',
      state: 'CO',
      zipCode: '80202',
    },
    images: [],
    seller: {
      name: 'John Doe',
      id: 'seller-123',
    },
    components: {},
    metadata: {
      createdAt: new Date('2024-01-01'),
      lastSeen: new Date('2024-01-01'),
      priceHistory: [],
    },
  },
  metrics: {
    estimatedProfit: 350,
    roi: 0.29,
    dealScore: 85,
  },
  history: [],
  metadata: {
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01'),
  },
};

describe('buildRowFromDeal', () => {
  it('should build a row from a deal', () => {
    const row = buildRowFromDeal(mockDeal, DEFAULT_DEAL_MAPPING);
    
    expect(row).toEqual([
      'deal-123',
      'Gaming PC RTX 3070',
      'negotiating',
      '$1,200.00',
      '$350.00',
      '29%',
      'John Doe',
      'Denver',
      '1/1/2024',
      '',
    ]);
  });

  it('should handle missing nested values', () => {
    const dealWithMissing = {
      ...mockDeal,
      listing: {
        ...mockDeal.listing,
        seller: undefined,
      },
    };
    
    const row = buildRowFromDeal(dealWithMissing as any, DEFAULT_DEAL_MAPPING);
    expect(row[6]).toBe(''); // Seller name should be empty
  });
});

describe('parseRowToDeal', () => {
  it('should parse a row into a deal update', () => {
    const row = [
      'deal-123',
      'Updated Gaming PC',
      'contacted',
      '$1,100.00',
      '$400.00',
      '36%',
      'Jane Smith',
      'Boulder',
      '1/2/2024',
      'Great deal!',
    ];
    
    const update = parseRowToDeal(row, DEFAULT_DEAL_MAPPING);
    
    expect(update).toEqual({
      id: 'deal-123',
      listing: {
        title: 'Updated Gaming PC',
        price: 1100,
        seller: {
          name: 'Jane Smith',
        },
        location: {
          city: 'Boulder',
        },
      },
      stage: 'contacted',
      metrics: {
        estimatedProfit: 400,
        roi: 0.36,
      },
      metadata: {
        createdAt: new Date('1/2/2024'),
      },
      notes: 'Great deal!',
    });
  });

  it('should skip empty values', () => {
    const row = ['deal-123', '', 'contacted', '', '', '', '', '', '', ''];
    const update = parseRowToDeal(row, DEFAULT_DEAL_MAPPING);
    
    expect(update.id).toBe('deal-123');
    expect(update.stage).toBe('contacted');
    expect(update.listing?.title).toBeUndefined();
  });
});

describe('diffLocalVsRemote', () => {
  it('should identify items to create', () => {
    const localDeals = [mockDeal];
    const remoteRows: any[][] = [];
    
    const diff = diffLocalVsRemote(localDeals, remoteRows, DEFAULT_DEAL_MAPPING);
    
    expect(diff.toCreate).toHaveLength(1);
    expect(diff.toCreate[0].id).toBe('deal-123');
    expect(diff.toUpdate).toHaveLength(0);
    expect(diff.toDelete).toHaveLength(0);
  });

  it('should identify items to update', () => {
    const localDeals = [mockDeal];
    const remoteRows = [
      ['deal-123', 'Old Title', 'sourcing', '$1000', '$200', '20%', 'Old Seller', 'Denver', '12/1/2023', ''],
    ];
    
    const diff = diffLocalVsRemote(localDeals, remoteRows, DEFAULT_DEAL_MAPPING);
    
    expect(diff.toCreate).toHaveLength(0);
    expect(diff.toUpdate).toHaveLength(1);
    expect(diff.toUpdate[0].local.id).toBe('deal-123');
    expect(diff.toDelete).toHaveLength(0);
  });

  it('should identify items to delete', () => {
    const localDeals: Deal[] = [];
    const remoteRows = [
      ['deal-999', 'Deleted Deal', 'sourcing', '$1000', '$200', '20%', 'Seller', 'Denver', '12/1/2023', ''],
    ];
    
    const diff = diffLocalVsRemote(localDeals, remoteRows, DEFAULT_DEAL_MAPPING);
    
    expect(diff.toCreate).toHaveLength(0);
    expect(diff.toUpdate).toHaveLength(0);
    expect(diff.toDelete).toHaveLength(1);
    expect(diff.toDelete[0][0]).toBe('deal-999');
  });
});

describe('buildHeaderRow', () => {
  it('should build header row from mapping', () => {
    const headers = buildHeaderRow(DEFAULT_DEAL_MAPPING);
    
    expect(headers).toEqual([
      'Id',
      'Listing Title',
      'Stage',
      'Listing Price',
      'Metrics EstimatedProfit',
      'Metrics Roi',
      'Listing Seller Name',
      'Listing Location City',
      'Metadata CreatedAt',
      'Notes',
    ]);
  });
});