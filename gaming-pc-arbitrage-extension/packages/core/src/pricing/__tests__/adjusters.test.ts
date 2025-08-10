/**
 * Tests for Pricing Adjusters
 */

import { describe, it, expect } from 'vitest';
import {
  seasonalAdjust,
  regionalAdjust,
  brandPremium,
  applyAllAdjustments,
  DEFAULT_SEASONAL_MULTIPLIERS,
  DEFAULT_REGIONAL_MULTIPLIERS,
  DEFAULT_BRAND_PREMIUMS,
} from '../adjusters';

describe('Pricing Adjusters', () => {
  describe('Seasonal Adjustment', () => {
    it('should apply holiday peak adjustment in December', () => {
      const date = new Date('2024-12-15');
      const result = seasonalAdjust(1000, date);
      
      expect(result.multiplier).toBe(1.15);
      expect(result.adjustedValue).toBe(1150);
      expect(result.reason).toBe('Holiday peak');
    });

    it('should apply post-holiday slowdown in January', () => {
      const date = new Date('2024-01-15');
      const result = seasonalAdjust(1000, date);
      
      expect(result.multiplier).toBe(0.95);
      expect(result.adjustedValue).toBe(950);
      expect(result.reason).toBe('Post-holiday slowdown');
    });

    it('should apply back-to-school boost in August', () => {
      const date = new Date('2024-08-15');
      const result = seasonalAdjust(1000, date);
      
      expect(result.multiplier).toBe(1.05);
      expect(result.adjustedValue).toBe(1050);
    });
  });

  describe('Regional Adjustment', () => {
    it('should apply tech hub premium for California', () => {
      const result = regionalAdjust(1000, 'CA');
      
      expect(result.multiplier).toBe(1.15);
      expect(result.adjustedValue).toBe(1150);
      expect(result.notes).toContain('tech hub');
    });

    it('should apply lower multiplier for rural states', () => {
      const result = regionalAdjust(1000, 'WV');
      
      expect(result.multiplier).toBe(0.88);
      expect(result.adjustedValue).toBe(880);
    });

    it('should handle unlisted states conservatively', () => {
      const result = regionalAdjust(1000, 'XX');
      
      expect(result.multiplier).toBe(0.95);
      expect(result.notes).toContain('Unlisted state');
    });

    it('should handle case insensitive state codes', () => {
      const result1 = regionalAdjust(1000, 'ca');
      const result2 = regionalAdjust(1000, 'CA');
      
      expect(result1.adjustedValue).toBe(result2.adjustedValue);
    });
  });

  describe('Brand Premium', () => {
    it('should apply NVIDIA RTX premium', () => {
      const result = brandPremium(1000, 'NVIDIA RTX 4090', 'gpu');
      
      expect(result.premium).toBe(8);
      expect(result.adjustedValue).toBe(1080);
      expect(result.applied).toBe(true);
    });

    it('should apply Lian Li case premium', () => {
      const result = brandPremium(200, 'Lian Li O11 Dynamic', 'case');
      
      expect(result.premium).toBe(10);
      expect(result.adjustedValue).toBe(220);
    });

    it('should handle unrecognized brands', () => {
      const result = brandPremium(1000, 'Generic Brand', 'gpu');
      
      expect(result.premium).toBe(0);
      expect(result.adjustedValue).toBe(1000);
      expect(result.applied).toBe(false);
    });

    it('should be case insensitive', () => {
      const result = brandPremium(1000, 'nvidia rtx', 'gpu');
      
      expect(result.premium).toBe(8);
      expect(result.applied).toBe(true);
    });
  });

  describe('Combined Adjustments', () => {
    it('should apply all adjustments sequentially', () => {
      const result = applyAllAdjustments(1000, {
        date: new Date('2024-12-15'), // Holiday peak
        state: 'CA', // Tech hub
        brand: 'NVIDIA RTX',
        category: 'gpu',
      });
      
      // Base 1000 * 1.15 (seasonal) = 1150
      // 1150 * 1.15 (CA) = 1323
      // 1323 * 1.08 (NVIDIA) = 1429
      expect(result.adjustedValue).toBe(1429);
      expect(result.totalMultiplier).toBeCloseTo(1.429, 2);
      
      expect(result.adjustments.seasonal.multiplier).toBe(1.15);
      expect(result.adjustments.regional.multiplier).toBe(1.15);
      expect(result.adjustments.brand.premium).toBe(8);
    });

    it('should handle partial adjustments', () => {
      const result = applyAllAdjustments(1000, {
        date: new Date('2024-06-15'), // Summer
        state: 'TX', // Baseline
      });
      
      expect(result.adjustedValue).toBe(980); // 1000 * 0.98
      expect(result.adjustments.brand.applied).toBe(false);
    });

    it('should calculate correct deltas', () => {
      const result = applyAllAdjustments(1000, {
        date: new Date('2024-11-15'), // Black Friday
        state: 'NY',
      });
      
      expect(result.adjustments.seasonal.delta).toBe(120); // 1000 * 0.12
      expect(result.totalDelta).toBe(result.adjustedValue - 1000);
    });
  });

  describe('Custom Multipliers', () => {
    it('should use custom seasonal multipliers', () => {
      const customMultipliers = [
        { month: 6, multiplier: 1.5, reason: 'Custom summer boost' },
      ];
      
      const result = seasonalAdjust(1000, new Date('2024-06-15'), customMultipliers);
      
      expect(result.multiplier).toBe(1.5);
      expect(result.reason).toBe('Custom summer boost');
    });

    it('should use custom regional multipliers', () => {
      const customMultipliers = [
        { state: 'AK', multiplier: 1.3, notes: 'Remote premium' },
      ];
      
      const result = regionalAdjust(1000, 'AK', customMultipliers);
      
      expect(result.multiplier).toBe(1.3);
      expect(result.notes).toBe('Remote premium');
    });

    it('should use custom brand premiums', () => {
      const customPremiums = [
        { brand: 'Custom GPU', category: 'gpu' as const, premium: 15 },
      ];
      
      const result = brandPremium(1000, 'Custom GPU RTX', 'gpu', customPremiums);
      
      expect(result.premium).toBe(15);
      expect(result.adjustedValue).toBe(1150);
    });
  });
});