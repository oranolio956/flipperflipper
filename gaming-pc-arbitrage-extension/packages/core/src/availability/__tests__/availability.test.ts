/**
 * Tests for Availability Module
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  generateAvailabilityPing,
  markPingSent,
  isPingStale,
  calculateResponseTime,
  generateFollowUp,
  createBatchPingPlan,
  getPingStatusSummary,
  AVAILABILITY_TEMPLATES,
} from '../index';

describe('Availability Check', () => {
  let mockDate: Date;
  
  beforeEach(() => {
    mockDate = new Date('2024-01-01T12:00:00Z');
    vi.useFakeTimers();
    vi.setSystemTime(mockDate);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should generate availability ping', () => {
    const ping = generateAvailabilityPing('listing123', 'facebook', 'polite');
    
    expect(ping).toMatchObject({
      listingId: 'listing123',
      platform: 'facebook',
      variant: 'polite',
      status: 'draft',
      message: AVAILABILITY_TEMPLATES[0].template,
    });
    
    expect(ping.responseDeadline).toBeInstanceOf(Date);
    expect(ping.responseDeadline.getTime()).toBeGreaterThan(mockDate.getTime());
  });

  it('should use different templates for variants', () => {
    const polite = generateAvailabilityPing('l1', 'fb', 'polite');
    const urgent = generateAvailabilityPing('l2', 'fb', 'urgent');
    const casual = generateAvailabilityPing('l3', 'fb', 'casual');
    
    expect(polite.message).toContain('very interested');
    expect(urgent.message).toContain('NOW');
    expect(casual.message).toContain('still for sale');
    
    // Different deadlines
    expect(urgent.responseDeadline.getTime()).toBeLessThan(polite.responseDeadline.getTime());
    expect(casual.responseDeadline.getTime()).toBeGreaterThan(polite.responseDeadline.getTime());
  });

  it('should mark ping as sent', () => {
    const ping = generateAvailabilityPing('listing123', 'facebook');
    const sentPing = markPingSent(ping);
    
    expect(sentPing.status).toBe('sent');
    expect(sentPing.sentAt).toEqual(mockDate);
  });

  it('should detect stale pings', () => {
    const ping = generateAvailabilityPing('listing123', 'facebook', 'urgent');
    const sentPing = markPingSent(ping);
    
    expect(isPingStale(sentPing)).toBe(false);
    
    // Advance time past deadline
    vi.advanceTimersByTime(13 * 60 * 60 * 1000); // 13 hours
    
    expect(isPingStale(sentPing)).toBe(true);
  });

  it('should calculate response time', () => {
    const ping = generateAvailabilityPing('listing123', 'facebook');
    const sentPing = markPingSent(ping);
    
    // Response after 30 minutes
    const responseTime = new Date(mockDate.getTime() + 30 * 60 * 1000);
    const minutes = calculateResponseTime(sentPing, responseTime);
    
    expect(minutes).toBe(30);
  });

  it('should generate follow-up messages', () => {
    const ping = generateAvailabilityPing('listing123', 'facebook');
    const followUp = generateFollowUp(ping);
    
    expect(followUp).toMatch(/following up|didn't hear back|still/i);
  });

  it('should create batch ping plan', () => {
    const config = {
      listingIds: ['l1', 'l2', 'l3'],
      platform: 'facebook',
      variant: 'polite' as const,
      staggerMinutes: 5,
    };
    
    const pings = createBatchPingPlan(config);
    
    expect(pings).toHaveLength(3);
    
    // Check staggering
    const time1 = pings[0].sentAt!.getTime();
    const time2 = pings[1].sentAt!.getTime();
    const time3 = pings[2].sentAt!.getTime();
    
    expect(time2 - time1).toBe(5 * 60 * 1000);
    expect(time3 - time2).toBe(5 * 60 * 1000);
  });

  it('should calculate ping status summary', () => {
    const pings = [
      { ...generateAvailabilityPing('l1', 'fb'), status: 'draft' as const },
      { ...generateAvailabilityPing('l2', 'fb'), status: 'sent' as const },
      { ...generateAvailabilityPing('l3', 'fb'), status: 'responded' as const },
      { ...generateAvailabilityPing('l4', 'fb'), status: 'sent' as const },
    ];
    
    const summary = getPingStatusSummary(pings);
    
    expect(summary).toEqual({
      total: 4,
      draft: 1,
      sent: 2,
      responded: 1,
      stale: 0,
      responseRate: 33.33333333333333, // 1/3
    });
  });
});