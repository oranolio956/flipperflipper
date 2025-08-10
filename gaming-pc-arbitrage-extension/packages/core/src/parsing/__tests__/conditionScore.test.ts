/**
 * Tests for Condition Score
 */

import { describe, it, expect } from 'vitest';
import { 
  calculateConditionScore, 
  getConditionColor,
  getConditionDescription,
} from '../conditionScore';

describe('Condition Score', () => {
  it('should identify new items', () => {
    const texts = [
      'Brand new in box, never opened',
      'BNIB sealed gaming PC',
      'Factory sealed, unopened',
    ];
    
    texts.forEach(text => {
      const result = calculateConditionScore(text);
      expect(result.grade).toBe('new');
      expect(result.score).toBeGreaterThanOrEqual(95);
      expect(result.factors.positive).toContain('States "new"');
    });
  });

  it('should identify excellent condition', () => {
    const text = 'Excellent condition, adult owned, smoke-free home';
    const result = calculateConditionScore(text);
    
    expect(result.grade).toBe('excellent');
    expect(result.factors.positive).toContain('States "excellent"');
    expect(result.factors.positive).toContain('smoke-free');
  });

  it('should penalize negative indicators', () => {
    const text = 'Good condition but used for crypto mining 24/7';
    const result = calculateConditionScore(text);
    
    expect(result.factors.negative).toContain('mining');
    expect(result.factors.negative).toContain('24/7');
    expect(result.score).toBeLessThan(70);
  });

  it('should factor in age', () => {
    const newText = 'Like new, only 2 months old';
    const oldText = 'Good condition, 5 years old';
    
    const newResult = calculateConditionScore(newText);
    const oldResult = calculateConditionScore(oldText);
    
    expect(newResult.score).toBeGreaterThan(oldResult.score);
    expect(newResult.factors.positive).toContain('Only 2 months old');
    expect(oldResult.factors.negative).toContain('5 years old');
  });

  it('should handle usage patterns', () => {
    const lightUse = 'Excellent condition, used as spare PC';
    const heavyUse = 'Good condition, daily driver for work';
    
    const lightResult = calculateConditionScore(lightUse);
    const heavyResult = calculateConditionScore(heavyUse);
    
    expect(lightResult.factors.positive).toContain('Light use (spare/backup)');
    expect(heavyResult.factors.negative).toContain('Daily use');
  });

  it('should calculate confidence based on indicators', () => {
    const detailed = 'Like new, smoke-free, pet-free, original box, barely used, adult owned';
    const simple = 'Good condition';
    
    const detailedResult = calculateConditionScore(detailed);
    const simpleResult = calculateConditionScore(simple);
    
    expect(detailedResult.confidence).toBeGreaterThan(simpleResult.confidence);
  });

  it('should provide correct colors', () => {
    expect(getConditionColor('new')).toBe('#10b981');
    expect(getConditionColor('poor')).toBe('#ef4444');
  });

  it('should provide descriptions', () => {
    expect(getConditionDescription('new')).toContain('Brand new');
    expect(getConditionDescription('fair')).toContain('wear');
  });
});