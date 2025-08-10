/**
 * A/B Testing Tests
 */

import { describe, it, expect, vi } from 'vitest';
import {
  recordImpression,
  recordOutcome,
  twoProportionZTest,
  pickVariant,
  maybePromoteWinner,
  type Experiment,
} from './index';

const createExperiment = (overrides: Partial<Experiment> = {}): Experiment => ({
  id: 'test-exp',
  name: 'Test Experiment',
  description: 'Testing',
  variants: [
    { id: 'a', impressions: 0, successes: 0, conversionRate: 0 },
    { id: 'b', impressions: 0, successes: 0, conversionRate: 0 },
  ],
  createdAt: new Date(),
  updatedAt: new Date(),
  ...overrides,
});

describe('recordImpression', () => {
  it('should increment impression count', () => {
    const exp = createExperiment();
    const updated = recordImpression(exp, 'a');
    
    expect(updated.variants[0].impressions).toBe(1);
    expect(updated.variants[1].impressions).toBe(0);
  });

  it('should update conversion rate', () => {
    const exp = createExperiment({
      variants: [
        { id: 'a', impressions: 10, successes: 5, conversionRate: 0.5 },
        { id: 'b', impressions: 0, successes: 0, conversionRate: 0 },
      ],
    });
    
    const updated = recordImpression(exp, 'a');
    expect(updated.variants[0].conversionRate).toBeCloseTo(5/11);
  });

  it('should throw for invalid variant', () => {
    const exp = createExperiment();
    expect(() => recordImpression(exp, 'invalid')).toThrow();
  });
});

describe('recordOutcome', () => {
  it('should increment success count', () => {
    const exp = createExperiment({
      variants: [
        { id: 'a', impressions: 1, successes: 0, conversionRate: 0 },
        { id: 'b', impressions: 0, successes: 0, conversionRate: 0 },
      ],
    });
    
    const updated = recordOutcome(exp, 'a', true);
    expect(updated.variants[0].successes).toBe(1);
    expect(updated.variants[0].conversionRate).toBe(1);
  });

  it('should not increment for failure', () => {
    const exp = createExperiment({
      variants: [
        { id: 'a', impressions: 1, successes: 0, conversionRate: 0 },
        { id: 'b', impressions: 0, successes: 0, conversionRate: 0 },
      ],
    });
    
    const updated = recordOutcome(exp, 'a', false);
    expect(updated.variants[0].successes).toBe(0);
    expect(updated.variants[0].conversionRate).toBe(0);
  });
});

describe('twoProportionZTest', () => {
  it('should calculate z-test correctly', () => {
    // 50/100 vs 30/100 conversion rates
    const result = twoProportionZTest(
      { s: 50, n: 100 },
      { s: 30, n: 100 }
    );
    
    expect(result.z).toBeGreaterThan(2.8);
    expect(result.p).toBeLessThan(0.01); // Significant
  });

  it('should handle no difference', () => {
    const result = twoProportionZTest(
      { s: 50, n: 100 },
      { s: 50, n: 100 }
    );
    
    expect(result.z).toBe(0);
    expect(result.p).toBe(1);
  });

  it('should handle zero samples', () => {
    const result = twoProportionZTest(
      { s: 0, n: 0 },
      { s: 0, n: 100 }
    );
    
    expect(result.z).toBe(0);
    expect(result.p).toBe(1);
  });
});

describe('pickVariant', () => {
  it('should use promoted variant if set', () => {
    const exp = createExperiment({ promotedId: 'b' });
    const picked = pickVariant(exp);
    expect(picked).toBe('b');
  });

  it('should pick best variant when exploiting', () => {
    vi.spyOn(Math, 'random').mockReturnValue(0.5); // Exploit
    
    const exp = createExperiment({
      variants: [
        { id: 'a', impressions: 100, successes: 20, conversionRate: 0.2 },
        { id: 'b', impressions: 100, successes: 30, conversionRate: 0.3 },
      ],
    });
    
    const picked = pickVariant(exp, 'epsilonGreedy', 0.1);
    expect(picked).toBe('b');
    
    vi.restoreAllMocks();
  });

  it('should explore randomly with epsilon probability', () => {
    vi.spyOn(Math, 'random')
      .mockReturnValueOnce(0.05) // Explore
      .mockReturnValueOnce(0.8); // Pick second variant
    
    const exp = createExperiment();
    const picked = pickVariant(exp, 'epsilonGreedy', 0.1);
    expect(picked).toBe('b');
    
    vi.restoreAllMocks();
  });

  it('should use UCB1 strategy', () => {
    const exp = createExperiment({
      variants: [
        { id: 'a', impressions: 100, successes: 20, conversionRate: 0.2 },
        { id: 'b', impressions: 10, successes: 3, conversionRate: 0.3 },
      ],
    });
    
    // UCB1 should favor exploration of variant with fewer impressions
    const picked = pickVariant(exp, 'ucb1');
    expect(picked).toBe('b');
  });
});

describe('maybePromoteWinner', () => {
  it('should not promote without enough trials', () => {
    const exp = createExperiment({
      variants: [
        { id: 'a', impressions: 30, successes: 20, conversionRate: 0.67 },
        { id: 'b', impressions: 30, successes: 10, conversionRate: 0.33 },
      ],
    });
    
    const updated = maybePromoteWinner(exp, 0.05, 50);
    expect(updated.promotedId).toBeUndefined();
  });

  it('should promote significant winner', () => {
    const exp = createExperiment({
      variants: [
        { id: 'a', impressions: 100, successes: 60, conversionRate: 0.6 },
        { id: 'b', impressions: 100, successes: 40, conversionRate: 0.4 },
      ],
    });
    
    const updated = maybePromoteWinner(exp, 0.05, 50);
    expect(updated.promotedId).toBe('a');
  });

  it('should not promote if not significant', () => {
    const exp = createExperiment({
      variants: [
        { id: 'a', impressions: 100, successes: 52, conversionRate: 0.52 },
        { id: 'b', impressions: 100, successes: 48, conversionRate: 0.48 },
      ],
    });
    
    const updated = maybePromoteWinner(exp, 0.05, 50);
    expect(updated.promotedId).toBeUndefined();
  });

  it('should keep existing promotion', () => {
    const exp = createExperiment({ promotedId: 'a' });
    const updated = maybePromoteWinner(exp);
    expect(updated.promotedId).toBe('a');
  });
});