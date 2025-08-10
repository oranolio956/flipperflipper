/**
 * Pricing Integrations
 * Connect comp stats to FMV calculations
 */

import { CompStats } from '../comps';
import { ComponentValue } from '../calculators/fmv-calculator';

/**
 * Adjust component value based on comp stats
 */
export function adjustValueWithComps(
  baseValue: ComponentValue,
  compStats: CompStats | null,
  blendFactor = 0.7
): ComponentValue {
  if (!compStats || compStats.n < 3) {
    // Not enough data, use base value
    return baseValue;
  }
  
  // Blend tier-based estimate with comp median
  const compValue = compStats.median;
  const blendedFmv = baseValue.fmv * (1 - blendFactor) + compValue * blendFactor;
  
  return {
    ...baseValue,
    fmv: Math.round(blendedFmv),
    confidence: Math.min(baseValue.confidence + 0.2, 0.95), // Boost confidence with comps
    source: `${baseValue.source} + ${compStats.n} comps`,
  };
}

/**
 * Calculate deal metrics with comp-adjusted FMV
 */
export function calculateDealMetricsWithComps(
  listingPrice: number,
  fmv: number,
  compStats: CompStats | null
): {
  discount: number;
  margin: number;
  dealScore: number;
  pricePosition: 'below_p25' | 'p25_median' | 'median_p75' | 'above_p75' | 'unknown';
} {
  const discount = (fmv - listingPrice) / fmv;
  const margin = discount; // Simplified - in reality would include costs
  
  let dealScore = margin * 100;
  let pricePosition: 'below_p25' | 'p25_median' | 'median_p75' | 'above_p75' | 'unknown' = 'unknown';
  
  if (compStats && compStats.n >= 3) {
    // Determine price position
    if (listingPrice < compStats.p25) {
      pricePosition = 'below_p25';
      dealScore += 20; // Boost score for great price
    } else if (listingPrice < compStats.median) {
      pricePosition = 'p25_median';
      dealScore += 10;
    } else if (listingPrice < compStats.p75) {
      pricePosition = 'median_p75';
      dealScore -= 5;
    } else {
      pricePosition = 'above_p75';
      dealScore -= 15; // Penalize high price
    }
    
    // Adjust for data recency
    if (compStats.recencyDays > 30) {
      dealScore -= 5; // Stale data penalty
    }
  }
  
  return {
    discount,
    margin,
    dealScore: Math.max(0, Math.min(100, dealScore)),
    pricePosition,
  };
}