/**
 * A/B Testing Module
 * Statistical testing for negotiation templates
 */

export interface VariantStats {
  id: string;
  impressions: number;
  successes: number;
  conversionRate: number;
}

export interface Experiment {
  id: string;
  name: string;
  description: string;
  variants: VariantStats[];
  promotedId?: string;
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Record an impression for a variant
 */
export function recordImpression(
  exp: Experiment, 
  variantId: string
): Experiment {
  const variant = exp.variants.find(v => v.id === variantId);
  if (!variant) {
    throw new Error(`Variant ${variantId} not found`);
  }
  
  const updatedVariants = exp.variants.map(v => {
    if (v.id === variantId) {
      const impressions = v.impressions + 1;
      return {
        ...v,
        impressions,
        conversionRate: v.successes / impressions,
      };
    }
    return v;
  });
  
  return {
    ...exp,
    variants: updatedVariants,
    updatedAt: new Date(),
  };
}

/**
 * Record an outcome (success or failure) for a variant
 */
export function recordOutcome(
  exp: Experiment,
  variantId: string,
  success: boolean
): Experiment {
  const variant = exp.variants.find(v => v.id === variantId);
  if (!variant) {
    throw new Error(`Variant ${variantId} not found`);
  }
  
  const updatedVariants = exp.variants.map(v => {
    if (v.id === variantId) {
      const successes = success ? v.successes + 1 : v.successes;
      return {
        ...v,
        successes,
        conversionRate: v.impressions > 0 ? successes / v.impressions : 0,
      };
    }
    return v;
  });
  
  return {
    ...exp,
    variants: updatedVariants,
    updatedAt: new Date(),
  };
}

/**
 * Two-proportion z-test for comparing conversion rates
 */
export function twoProportionZTest(
  a: { s: number; n: number },
  b: { s: number; n: number }
): { z: number; p: number } {
  if (a.n === 0 || b.n === 0) {
    return { z: 0, p: 1 };
  }
  
  const p1 = a.s / a.n;
  const p2 = b.s / b.n;
  const p = (a.s + b.s) / (a.n + b.n);
  
  const se = Math.sqrt(p * (1 - p) * (1/a.n + 1/b.n));
  if (se === 0) {
    return { z: 0, p: 1 };
  }
  
  const z = (p1 - p2) / se;
  
  // Calculate p-value (two-tailed)
  const p_value = 2 * (1 - normalCDF(Math.abs(z)));
  
  return { z, p: p_value };
}

/**
 * Select a variant using the specified strategy
 */
export function pickVariant(
  exp: Experiment,
  strategy: 'epsilonGreedy' | 'ucb1' = 'epsilonGreedy',
  epsilon = 0.1
): string {
  // If experiment has a promoted variant, always use it
  if (exp.promotedId) {
    return exp.promotedId;
  }
  
  if (exp.variants.length === 0) {
    throw new Error('No variants in experiment');
  }
  
  if (strategy === 'epsilonGreedy') {
    // Epsilon-greedy: explore with probability epsilon
    if (Math.random() < epsilon) {
      // Random exploration
      const idx = Math.floor(Math.random() * exp.variants.length);
      return exp.variants[idx].id;
    } else {
      // Exploit: choose best performing
      const best = exp.variants.reduce((a, b) => 
        a.conversionRate > b.conversionRate ? a : b
      );
      return best.id;
    }
  } else if (strategy === 'ucb1') {
    // Upper Confidence Bound
    const totalImpressions = exp.variants.reduce((sum, v) => sum + v.impressions, 0);
    if (totalImpressions === 0) {
      // No data yet, pick randomly
      const idx = Math.floor(Math.random() * exp.variants.length);
      return exp.variants[idx].id;
    }
    
    let bestScore = -Infinity;
    let bestVariant = exp.variants[0];
    
    for (const variant of exp.variants) {
      if (variant.impressions === 0) {
        // Always try untested variants first
        return variant.id;
      }
      
      const avgReward = variant.conversionRate;
      const confidence = Math.sqrt(2 * Math.log(totalImpressions) / variant.impressions);
      const score = avgReward + confidence;
      
      if (score > bestScore) {
        bestScore = score;
        bestVariant = variant;
      }
    }
    
    return bestVariant.id;
  }
  
  // Default to first variant
  return exp.variants[0].id;
}

/**
 * Check if we can promote a winner
 */
export function maybePromoteWinner(
  exp: Experiment,
  alpha = 0.05,
  minTrials = 50
): Experiment {
  if (exp.promotedId) {
    // Already promoted
    return exp;
  }
  
  if (exp.variants.length < 2) {
    // Need at least 2 variants
    return exp;
  }
  
  // Sort by conversion rate
  const sorted = [...exp.variants].sort((a, b) => b.conversionRate - a.conversionRate);
  const best = sorted[0];
  const secondBest = sorted[1];
  
  // Check minimum trials
  if (best.impressions < minTrials || secondBest.impressions < minTrials) {
    return exp;
  }
  
  // Run significance test
  const { p } = twoProportionZTest(
    { s: best.successes, n: best.impressions },
    { s: secondBest.successes, n: secondBest.impressions }
  );
  
  // Check if significant
  if (p < alpha) {
    return {
      ...exp,
      promotedId: best.id,
      updatedAt: new Date(),
    };
  }
  
  return exp;
}

/**
 * Get experiment statistics
 */
export function getExperimentStats(exp: Experiment) {
  const totalImpressions = exp.variants.reduce((sum, v) => sum + v.impressions, 0);
  const totalSuccesses = exp.variants.reduce((sum, v) => sum + v.successes, 0);
  const overallConversion = totalImpressions > 0 ? totalSuccesses / totalImpressions : 0;
  
  // Calculate confidence intervals
  const variantsWithCI = exp.variants.map(v => {
    const ci = wilsonConfidenceInterval(v.successes, v.impressions);
    return { ...v, ci };
  });
  
  return {
    totalImpressions,
    totalSuccesses,
    overallConversion,
    variants: variantsWithCI,
    isSignificant: false,
    winner: null as VariantStats | null,
  };
}

/**
 * Normal CDF approximation
 */
function normalCDF(z: number): number {
  const b1 = 0.319381530;
  const b2 = -0.356563782;
  const b3 = 1.781477937;
  const b4 = -1.821255978;
  const b5 = 1.330274429;
  const p = 0.2316419;
  const c = 0.39894228;
  
  if (z >= 0) {
    const t = 1 / (1 + p * z);
    return 1 - c * Math.exp(-z * z / 2) * t *
      (t * (t * (t * (t * b5 + b4) + b3) + b2) + b1);
  } else {
    return 1 - normalCDF(-z);
  }
}

/**
 * Wilson confidence interval for binomial proportion
 */
function wilsonConfidenceInterval(
  successes: number,
  trials: number,
  confidence = 0.95
): { lower: number; upper: number } {
  if (trials === 0) {
    return { lower: 0, upper: 0 };
  }
  
  const z = 1.96; // 95% confidence
  const p = successes / trials;
  const n = trials;
  
  const denominator = 1 + z * z / n;
  const centre = (p + z * z / (2 * n)) / denominator;
  const spread = z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator;
  
  return {
    lower: Math.max(0, centre - spread),
    upper: Math.min(1, centre + spread),
  };
}