/**
 * Quick-Flip Strategy
 * Calculate same-day resale potential
 */

import type { CompStats } from '../comps';
import type { CompetitionScore } from '../competition/signals';

export interface QuickFlipAnalysis {
  suggestedPrice: number;
  profitMargin: number;
  probability: number; // 0-100%
  timeframe: 'same-day' | '1-3 days' | '1 week';
  strategy: 'undercut' | 'match' | 'premium';
  risks: string[];
  actions: string[];
}

export interface MarketConditions {
  competition: CompetitionScore;
  comps: CompStats;
  similarListings: number;
  averageDaysOnMarket: number;
  priceRange: { min: number; max: number };
}

/**
 * Calculate quick-flip potential
 */
export function calculateQuickFlip(
  purchasePrice: number,
  estimatedValue: number,
  marketConditions: MarketConditions,
  urgency: 'high' | 'medium' | 'low' = 'medium'
): QuickFlipAnalysis {
  const risks: string[] = [];
  const actions: string[] = [];
  
  // Base calculations
  const marketPrice = marketConditions.comps.median || estimatedValue;
  const competitionLevel = marketConditions.competition.score;
  
  // Determine strategy based on competition
  let strategy: QuickFlipAnalysis['strategy'] = 'match';
  let pricingMultiplier = 1.0;
  
  if (competitionLevel > 70) {
    // High competition - undercut
    strategy = 'undercut';
    pricingMultiplier = 0.92;
    risks.push('High competition requires aggressive pricing');
    actions.push('Price below market for quick sale');
  } else if (competitionLevel < 30) {
    // Low competition - premium possible
    strategy = 'premium';
    pricingMultiplier = 1.05;
    actions.push('Can price at premium due to low competition');
  } else {
    // Moderate competition - match market
    strategy = 'match';
    pricingMultiplier = 0.98;
    actions.push('Price competitively with market');
  }
  
  // Urgency adjustment
  if (urgency === 'high') {
    pricingMultiplier *= 0.95;
    actions.push('Additional discount for urgent sale');
  } else if (urgency === 'low') {
    pricingMultiplier *= 1.02;
  }
  
  // Calculate suggested price
  let suggestedPrice = Math.round(marketPrice * pricingMultiplier);
  
  // Ensure minimum margin
  const minAcceptablePrice = purchasePrice * 1.15; // 15% minimum margin
  if (suggestedPrice < minAcceptablePrice) {
    suggestedPrice = minAcceptablePrice;
    risks.push('Price adjusted up to maintain minimum margin');
  }
  
  // Calculate profit
  const profitMargin = ((suggestedPrice - purchasePrice) / purchasePrice) * 100;
  
  // Calculate probability of quick sale
  let probability = 50; // Base probability
  
  // Competition factor
  if (competitionLevel > 70) {
    probability -= 20;
  } else if (competitionLevel < 30) {
    probability += 20;
  }
  
  // Price factor
  const priceVsMedian = suggestedPrice / marketPrice;
  if (priceVsMedian < 0.9) {
    probability += 25; // Significant discount
  } else if (priceVsMedian < 0.95) {
    probability += 15; // Moderate discount
  } else if (priceVsMedian > 1.05) {
    probability -= 15; // Premium pricing
  }
  
  // Market velocity factor
  if (marketConditions.averageDaysOnMarket < 7) {
    probability += 15;
    actions.push('Fast-moving market category');
  } else if (marketConditions.averageDaysOnMarket > 21) {
    probability -= 15;
    risks.push('Slow-moving market category');
  }
  
  // Similar listings factor
  if (marketConditions.similarListings > 10) {
    probability -= 10;
    risks.push(`${marketConditions.similarListings} similar listings active`);
  } else if (marketConditions.similarListings < 3) {
    probability += 10;
    actions.push('Limited competition from similar listings');
  }
  
  // Determine timeframe
  let timeframe: QuickFlipAnalysis['timeframe'];
  if (probability > 70 && strategy === 'undercut') {
    timeframe = 'same-day';
  } else if (probability > 50) {
    timeframe = '1-3 days';
  } else {
    timeframe = '1 week';
  }
  
  // Additional recommendations
  if (profitMargin < 20) {
    risks.push('Low profit margin - consider holding for better market');
  }
  
  if (marketConditions.comps.priceRange) {
    const priceVolatility = (marketConditions.comps.p75 - marketConditions.comps.p25) / marketConditions.comps.median;
    if (priceVolatility > 0.3) {
      risks.push('High price volatility in market');
      actions.push('Monitor competitor pricing closely');
    }
  }
  
  // Photo quality recommendation
  actions.push('Use high-quality photos from multiple angles');
  
  // Listing optimization
  if (competitionLevel > 50) {
    actions.push('Post during peak viewing hours (6-9 PM)');
    actions.push('Boost listing for first 24 hours');
  }
  
  // Bundle opportunity
  if (profitMargin > 30) {
    actions.push('Consider bundling with accessories for higher value');
  }
  
  return {
    suggestedPrice,
    profitMargin,
    probability: Math.max(10, Math.min(90, probability)), // Clamp 10-90%
    timeframe,
    strategy,
    risks,
    actions,
  };
}

/**
 * Calculate breakeven days
 */
export function calculateBreakevenDays(
  purchasePrice: number,
  holdingCostPerDay: number,
  expectedSalePrice: number
): number {
  const maxProfit = expectedSalePrice - purchasePrice;
  if (maxProfit <= 0) return Infinity;
  
  return Math.floor(maxProfit / holdingCostPerDay);
}

/**
 * Suggest flip vs hold decision
 */
export interface FlipVsHoldDecision {
  recommendation: 'flip-now' | 'hold' | 'flip-urgent';
  reasoning: string[];
  breakEvenDays: number;
  optimalHoldDays: number;
}

export function suggestFlipVsHold(
  quickFlipAnalysis: QuickFlipAnalysis,
  marketTrend: 'rising' | 'stable' | 'falling',
  holdingCostPerDay: number = 2,
  purchasePrice: number
): FlipVsHoldDecision {
  const reasoning: string[] = [];
  let recommendation: FlipVsHoldDecision['recommendation'] = 'flip-now';
  
  const breakEvenDays = calculateBreakevenDays(
    purchasePrice,
    holdingCostPerDay,
    quickFlipAnalysis.suggestedPrice
  );
  
  // High probability quick flip
  if (quickFlipAnalysis.probability > 70 && quickFlipAnalysis.profitMargin > 20) {
    recommendation = 'flip-now';
    reasoning.push('High probability of quick sale with good margin');
  }
  
  // Rising market
  else if (marketTrend === 'rising' && quickFlipAnalysis.profitMargin < 25) {
    recommendation = 'hold';
    reasoning.push('Rising market may yield better prices');
    reasoning.push(`Can hold up to ${breakEvenDays} days before losing money`);
  }
  
  // Falling market
  else if (marketTrend === 'falling') {
    recommendation = 'flip-urgent';
    reasoning.push('Falling market - sell quickly to avoid losses');
  }
  
  // Low margin
  else if (quickFlipAnalysis.profitMargin < 15) {
    recommendation = 'hold';
    reasoning.push('Margin too low for immediate flip');
  }
  
  // Calculate optimal hold days
  let optimalHoldDays = 0;
  if (recommendation === 'hold') {
    // Simple heuristic: hold for 1 week if margin < 20%, 2 weeks if < 15%
    if (quickFlipAnalysis.profitMargin < 15) {
      optimalHoldDays = 14;
    } else if (quickFlipAnalysis.profitMargin < 20) {
      optimalHoldDays = 7;
    } else {
      optimalHoldDays = 3;
    }
    
    // Don't exceed breakeven
    optimalHoldDays = Math.min(optimalHoldDays, Math.floor(breakEvenDays * 0.7));
  }
  
  return {
    recommendation,
    reasoning,
    breakEvenDays,
    optimalHoldDays,
  };
}