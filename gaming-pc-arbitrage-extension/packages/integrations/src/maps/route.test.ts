/**
 * Route Planning Tests
 */

import { describe, it, expect } from 'vitest';
import {
  haversineMiles,
  nearestNeighborRoute,
  googleMapsUrlForRoute,
  fuelCostEstimate,
} from './route';

describe('haversineMiles', () => {
  it('should calculate distance between two points', () => {
    // Denver to Boulder (~25 miles)
    const denver = { lat: 39.7392, lng: -104.9903 };
    const boulder = { lat: 40.0150, lng: -105.2705 };
    
    const distance = haversineMiles(denver, boulder);
    expect(distance).toBeCloseTo(24.2, 0);
  });
  
  it('should return 0 for same location', () => {
    const point = { lat: 40.0, lng: -105.0 };
    expect(haversineMiles(point, point)).toBe(0);
  });
  
  it('should handle cross-meridian distances', () => {
    // Tokyo to San Francisco (~5,130 miles)
    const tokyo = { lat: 35.6762, lng: 139.6503 };
    const sf = { lat: 37.7749, lng: -122.4194 };
    
    const distance = haversineMiles(tokyo, sf);
    expect(distance).toBeCloseTo(5130, -1);
  });
});

describe('nearestNeighborRoute', () => {
  const stops = [
    { id: '1', name: 'Stop 1', coord: { lat: 39.7392, lng: -104.9903 } }, // Denver
    { id: '2', name: 'Stop 2', coord: { lat: 39.7294, lng: -104.8319 } }, // Aurora
    { id: '3', name: 'Stop 3', coord: { lat: 40.0150, lng: -105.2705 } }, // Boulder
  ];
  
  it('should return empty route for no stops', () => {
    const result = nearestNeighborRoute([]);
    expect(result.order).toEqual([]);
    expect(result.milesTotal).toBe(0);
  });
  
  it('should handle single stop', () => {
    const result = nearestNeighborRoute([stops[0]]);
    expect(result.order).toEqual(['1']);
    expect(result.milesTotal).toBe(0);
  });
  
  it('should find optimal route for multiple stops', () => {
    const result = nearestNeighborRoute(stops);
    
    // Should visit nearby stops first
    expect(result.order).toHaveLength(3);
    expect(result.order).toContain('1');
    expect(result.order).toContain('2');
    expect(result.order).toContain('3');
    
    // Denver -> Aurora -> Boulder is more efficient than Denver -> Boulder -> Aurora
    expect(result.order[0]).toBe('1');
    expect(result.order[1]).toBe('2');
    expect(result.order[2]).toBe('3');
    
    expect(result.milesTotal).toBeGreaterThan(30);
    expect(result.milesTotal).toBeLessThan(50);
  });
  
  it('should respect custom start location', () => {
    const start = { lat: 39.7711, lng: -104.9227 }; // Northeast Denver
    const result = nearestNeighborRoute(stops, start);
    
    // Should start with Aurora (closest to start)
    expect(result.order[0]).toBe('2');
    expect(result.milesTotal).toBeGreaterThan(30);
  });
});

describe('googleMapsUrlForRoute', () => {
  it('should generate URL for single stop', () => {
    const stops = [{ coord: { lat: 39.7392, lng: -104.9903 } }];
    const url = googleMapsUrlForRoute(stops);
    
    expect(url).toBe('https://www.google.com/maps/dir/39.7392,-104.9903/');
  });
  
  it('should generate URL for multiple stops', () => {
    const stops = [
      { coord: { lat: 39.7392, lng: -104.9903 } },
      { coord: { lat: 40.0150, lng: -105.2705 } },
    ];
    const url = googleMapsUrlForRoute(stops);
    
    expect(url).toBe('https://www.google.com/maps/dir/39.7392,-104.9903/40.015,-105.2705/');
  });
  
  it('should include start location if provided', () => {
    const stops = [{ coord: { lat: 40.0150, lng: -105.2705 } }];
    const start = { lat: 39.7392, lng: -104.9903 };
    const url = googleMapsUrlForRoute(stops, start);
    
    expect(url).toBe('https://www.google.com/maps/dir/39.7392,-104.9903/40.015,-105.2705/');
  });
  
  it('should handle empty stops', () => {
    expect(googleMapsUrlForRoute([])).toBe('');
  });
});

describe('fuelCostEstimate', () => {
  it('should calculate fuel cost', () => {
    expect(fuelCostEstimate(100, 0.15)).toBe(15);
    expect(fuelCostEstimate(50.5, 0.20)).toBe(10.10);
    expect(fuelCostEstimate(0, 0.15)).toBe(0);
  });
  
  it('should round to 2 decimal places', () => {
    expect(fuelCostEstimate(33.333, 0.15)).toBe(5);
    expect(fuelCostEstimate(66.666, 0.15)).toBe(10);
  });
});