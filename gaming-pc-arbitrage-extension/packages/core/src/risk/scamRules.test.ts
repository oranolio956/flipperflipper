/**
 * Scam Rules Tests
 */

import { describe, it, expect } from 'vitest';
import { calculateScamRisk } from './scamRules';
import type { Listing } from '../types';

const createListing = (overrides: Partial<Listing> = {}): Listing => ({
  id: '123',
  externalId: 'ext-123',
  platform: 'facebook',
  url: 'https://example.com',
  title: 'Gaming PC for sale',
  description: 'Great condition gaming PC',
  price: {
    amount: 1000,
    currency: 'USD',
    formatted: '$1,000',
  },
  seller: {
    id: 'seller-123',
    name: 'John Doe',
    profileUrl: 'https://example.com/seller',
    memberSince: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000), // 1 year ago
  },
  location: {
    city: 'San Francisco',
    state: 'CA',
    coordinates: { lat: 37.7749, lng: -122.4194 },
  },
  images: [
    { url: 'https://example.com/1.jpg', width: 800, height: 600 },
    { url: 'https://example.com/2.jpg', width: 800, height: 600 },
    { url: 'https://example.com/3.jpg', width: 800, height: 600 },
  ],
  metadata: {
    createdAt: new Date(),
    updatedAt: new Date(),
    status: 'active',
  },
  ...overrides,
});

describe('calculateScamRisk', () => {
  it('should return low risk for normal listing', () => {
    const listing = createListing();
    const result = calculateScamRisk(listing);
    
    expect(result.score).toBe(0);
    expect(result.recommendation).toBe('safe');
    expect(result.reasons).toHaveLength(0);
  });

  it('should detect price anomaly', () => {
    const listing = createListing({ 
      price: { amount: 200, currency: 'USD', formatted: '$200' } 
    });
    
    const comps = {
      median: 1000,
      p25: 800,
      p75: 1200,
      n: 10,
      recencyDays: 5,
    };
    
    const result = calculateScamRisk(listing, comps);
    
    expect(result.score).toBeGreaterThan(30);
    expect(result.reasons.some(r => r.reason.includes('below market'))).toBe(true);
  });

  it('should detect stock photos', () => {
    const listing = createListing({
      images: [
        { url: 'https://example.com/stock-photo.jpg', width: 800, height: 600 },
      ],
    });
    
    const result = calculateScamRisk(listing);
    
    expect(result.score).toBeGreaterThan(20);
    expect(result.reasons.some(r => r.reason.includes('Stock photos'))).toBe(true);
  });

  it('should detect shipping only red flag', () => {
    const listing = createListing({
      description: 'Great PC, shipping only, no local pickup',
    });
    
    const result = calculateScamRisk(listing);
    
    expect(result.score).toBeGreaterThan(20);
    expect(result.reasons.some(r => r.reason.includes('Shipping only'))).toBe(true);
  });

  it('should detect urgent payment requests', () => {
    const listing = createListing({
      description: 'Must sell today! Zelle only for quick payment',
    });
    
    const result = calculateScamRisk(listing);
    
    expect(result.score).toBeGreaterThan(30);
    expect(result.reasons.some(r => r.reason.includes('Urgent payment'))).toBe(true);
  });

  it('should detect removed serial', () => {
    const listing = createListing({
      description: 'Works great, serial removed for privacy',
    });
    
    const result = calculateScamRisk(listing);
    
    expect(result.score).toBeGreaterThan(25);
    expect(result.reasons.some(r => r.reason.includes('Serial number removed'))).toBe(true);
  });

  it('should detect new seller with high value', () => {
    const listing = createListing({
      price: { amount: 2000, currency: 'USD', formatted: '$2,000' },
      seller: {
        id: 'new-seller',
        name: 'New User',
        profileUrl: 'https://example.com/new',
        memberSince: new Date(), // Just joined
      },
    });
    
    const result = calculateScamRisk(listing);
    
    expect(result.score).toBeGreaterThan(15);
    expect(result.reasons.some(r => r.reason.includes('New seller'))).toBe(true);
  });

  it('should detect spam patterns', () => {
    const listing = createListing({
      description: 'Great deal!!! $$$ Text me at 555-123-4567',
    });
    
    const result = calculateScamRisk(listing);
    
    expect(result.score).toBeGreaterThan(10);
    expect(result.reasons.some(r => r.reason.includes('Spam patterns'))).toBe(true);
  });

  it('should accumulate multiple risks', () => {
    const listing = createListing({
      price: { amount: 200, currency: 'USD', formatted: '$200' },
      description: 'Urgent sale! Shipping only, Zelle only',
      images: [{ url: 'https://example.com/stock.jpg', width: 800, height: 600 }],
    });
    
    const comps = {
      median: 1000,
      p25: 800,
      p75: 1200,
      n: 10,
      recencyDays: 5,
    };
    
    const result = calculateScamRisk(listing, comps);
    
    expect(result.score).toBeGreaterThan(60);
    expect(result.recommendation).toBe('avoid');
    expect(result.reasons.length).toBeGreaterThan(3);
  });

  it('should provide mitigations for each risk', () => {
    const listing = createListing({
      description: 'Shipping only available',
    });
    
    const result = calculateScamRisk(listing);
    
    const shippingRisk = result.reasons.find(r => r.reason.includes('Shipping only'));
    expect(shippingRisk?.mitigation).toBeTruthy();
    expect(shippingRisk?.mitigation).toContain('local');
  });
});