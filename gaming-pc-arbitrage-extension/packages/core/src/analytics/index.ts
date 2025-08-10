/**
 * Advanced Analytics
 * Local computation of business metrics
 */

import type { Deal } from '../types';

export interface CohortMetrics {
  month: string;
  acquired: number;
  sold: number;
  avgMarginPct: number;
  avgTurnTime: number;
}

export interface SeasonalityFactors {
  weekday: number[]; // 0-6 multipliers
  month: number[];   // 0-11 multipliers
}

export interface ElasticityResult {
  slope: number;
  intercept: number;
  r2: number;
}

export interface DemandScore {
  component: string;
  score: number;
  velocity: number;
  avgMargin: number;
}

export interface MarginTrend {
  date: string;
  marginPct: number;
  dealCount: number;
}

/**
 * Analyze deals by acquisition month cohorts
 */
export function cohortsByMonth(deals: Deal[]): CohortMetrics[] {
  const cohorts = new Map<string, Deal[]>();
  
  // Group by acquisition month
  for (const deal of deals) {
    const date = new Date(deal.metadata.createdAt);
    const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    
    if (!cohorts.has(monthKey)) {
      cohorts.set(monthKey, []);
    }
    cohorts.get(monthKey)!.push(deal);
  }
  
  // Calculate metrics per cohort
  const results: CohortMetrics[] = [];
  
  for (const [month, cohortDeals] of cohorts) {
    const acquired = cohortDeals.length;
    const sold = cohortDeals.filter(d => d.stage === 'sold').length;
    
    const margins = cohortDeals
      .filter(d => d.stage === 'sold' && d.salePrice && d.purchasePrice)
      .map(d => ((d.salePrice! - d.purchasePrice!) / d.purchasePrice!) * 100);
    
    const avgMarginPct = margins.length > 0 
      ? margins.reduce((a, b) => a + b, 0) / margins.length * 100
      : 0;
    
    const turnTimes = cohortDeals
      .filter(d => d.stage === 'sold' && d.soldAt)
      .map(d => {
        const start = new Date(d.metadata.createdAt);
        const end = new Date(d.soldAt!);
        return (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
      });
    
    const avgTurnTime = turnTimes.length > 0
      ? turnTimes.reduce((a, b) => a + b, 0) / turnTimes.length
      : 0;
    
    results.push({
      month,
      acquired,
      sold,
      avgMarginPct,
      avgTurnTime,
    });
  }
  
  return results.sort((a, b) => a.month.localeCompare(b.month));
}

/**
 * Calculate seasonality factors by weekday and month
 */
export function seasonalityFactors(deals: Deal[]): SeasonalityFactors {
  const soldDeals = deals.filter(d => d.stage === 'sold' && d.soldAt);
  
  // Count sales by weekday and month
  const weekdayCounts = new Array(7).fill(0);
  const monthCounts = new Array(12).fill(0);
  const weekdayRevenue = new Array(7).fill(0);
  const monthRevenue = new Array(12).fill(0);
  
  for (const deal of soldDeals) {
    const date = new Date(deal.soldAt!);
    const weekday = date.getDay();
    const month = date.getMonth();
    const revenue = deal.salePrice || deal.listing?.price || deal.askingPrice;
    
    weekdayCounts[weekday]++;
    monthCounts[month]++;
    weekdayRevenue[weekday] += revenue;
    monthRevenue[month] += revenue;
  }
  
  // Calculate average revenue per day
  const avgWeekdayRevenue = weekdayRevenue.reduce((a, b) => a + b, 0) / 7;
  const avgMonthRevenue = monthRevenue.reduce((a, b) => a + b, 0) / 12;
  
  // Calculate multipliers (1.0 = average)
  const weekdayFactors = weekdayRevenue.map(rev => 
    avgWeekdayRevenue > 0 ? rev / avgWeekdayRevenue : 1
  );
  
  const monthFactors = monthRevenue.map(rev => 
    avgMonthRevenue > 0 ? rev / avgMonthRevenue : 1
  );
  
  return {
    weekday: weekdayFactors,
    month: monthFactors,
  };
}

/**
 * Calculate price elasticity (discount % vs days to sell)
 */
export function priceElasticity(deals: Deal[]): ElasticityResult {
  const dataPoints = deals
    .filter(d => d.stage === 'sold' && (d.soldAt || d.soldDate) && d.salePrice)
    .map(d => {
      const discount = ((d.listing?.price || d.askingPrice) - d.salePrice!) / (d.listing?.price || d.askingPrice);
      const daysToSell = Math.ceil(
        (new Date(d.soldAt!).getTime() - new Date(d.metadata.createdAt).getTime()) / 
        (1000 * 60 * 60 * 24)
      );
      return { x: discount, y: daysToSell };
    });
  
  if (dataPoints.length < 3) {
    return { slope: 0, intercept: 0, r2: 0 };
  }
  
  // Simple linear regression
  const n = dataPoints.length;
  const sumX = dataPoints.reduce((sum, p) => sum + p.x, 0);
  const sumY = dataPoints.reduce((sum, p) => sum + p.y, 0);
  const sumXY = dataPoints.reduce((sum, p) => sum + p.x * p.y, 0);
  const sumX2 = dataPoints.reduce((sum, p) => sum + p.x * p.x, 0);
  
  const meanX = sumX / n;
  const meanY = sumY / n;
  
  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  const intercept = meanY - slope * meanX;
  
  // Calculate R²
  const yPred = dataPoints.map(p => slope * p.x + intercept);
  const ssRes = dataPoints.reduce((sum, p, i) => sum + Math.pow(p.y - yPred[i], 2), 0);
  const ssTot = dataPoints.reduce((sum, p) => sum + Math.pow(p.y - meanY, 2), 0);
  const r2 = ssTot > 0 ? 1 - (ssRes / ssTot) : 0;
  
  return { slope, intercept, r2 };
}

/**
 * Score component demand by velocity × margin
 */
export function demandScoreByComponent(deals: Deal[]): DemandScore[] {
  const componentStats = new Map<string, {
    count: number;
    totalMargin: number;
    totalDays: number;
  }>();
  
  for (const deal of deals.filter(d => d.stage === 'sold')) {
    const components = [];
    
    if (deal.listing?.components?.cpu) {
      components.push(`CPU: ${deal.listing.components.cpu.model}`);
    }
    if (deal.listing?.components?.gpu) {
      components.push(`GPU: ${deal.listing.components.gpu.model}`);
    }
    
    const margin = deal.salePrice && deal.purchasePrice 
      ? ((deal.salePrice - deal.purchasePrice) / deal.purchasePrice) * 100 
      : 0;
          const soldDate = deal.soldAt || deal.soldDate;
      const days = soldDate
        ? Math.ceil((new Date(soldDate).getTime() - new Date(deal.metadata.createdAt).getTime()) / (1000 * 60 * 60 * 24))
        : 30;
    
    for (const comp of components) {
      if (!componentStats.has(comp)) {
        componentStats.set(comp, { count: 0, totalMargin: 0, totalDays: 0 });
      }
      
      const stats = componentStats.get(comp)!;
      stats.count++;
      stats.totalMargin += margin;
      stats.totalDays += days;
    }
  }
  
  // Calculate scores
  const scores: DemandScore[] = [];
  
  for (const [component, stats] of componentStats) {
    const avgMargin = stats.totalMargin / stats.count;
    const velocity = stats.count / (stats.totalDays / 30); // Sales per month
    const score = velocity * avgMargin * 100; // Normalized score
    
    scores.push({
      component,
      score,
      velocity,
      avgMargin,
    });
  }
  
  return scores.sort((a, b) => b.score - a.score);
}

/**
 * Calculate margin trend over time
 */
export function marginTrend(deals: Deal[], windowDays = 30): MarginTrend[] {
  const soldDeals = deals
    .filter(d => d.stage === 'sold' && (d.soldAt || d.soldDate))
    .sort((a, b) => new Date(a.soldAt!).getTime() - new Date(b.soldAt!).getTime());
  
  if (soldDeals.length === 0) return [];
  
  const results: MarginTrend[] = [];
  const startDate = new Date(soldDeals[0].soldAt!);
  const endDate = new Date(soldDeals[soldDeals.length - 1].soldAt!);
  
  // Calculate rolling average
  const current = new Date(startDate);
  current.setDate(current.getDate() + windowDays);
  
  while (current <= endDate) {
    const windowStart = new Date(current);
    windowStart.setDate(windowStart.getDate() - windowDays);
    
    const windowDeals = soldDeals.filter(d => {
      const dealDate = new Date(d.soldAt!);
      return dealDate >= windowStart && dealDate <= current;
    });
    
    if (windowDeals.length > 0) {
      const avgMargin = windowDeals.reduce((sum, d) => {
        const roi = d.salePrice && d.purchasePrice 
          ? ((d.salePrice - d.purchasePrice) / d.purchasePrice) * 100 
          : 0;
        return sum + roi;
      }, 0) / windowDeals.length;
      
      results.push({
        date: current.toISOString().split('T')[0],
        marginPct: avgMargin * 100,
        dealCount: windowDeals.length,
      });
    }
    
    current.setDate(current.getDate() + 7); // Weekly intervals
  }
  
  return results;
}