/**
 * Advanced Analytics
 * Cohort analysis, predictive models, and business intelligence
 */

import type { Deal } from '../types';
import type { InventoryItem } from '../inventory/inventoryManager';
import { calculateROI } from '../calculators/roi-calculator';

export interface CohortAnalysis {
  cohortId: string;
  period: { start: Date; end: Date };
  metrics: {
    deals: number;
    revenue: number;
    profit: number;
    avgROI: number;
    avgHoldTime: number;
    successRate: number;
  };
  retention: {
    day1: number;
    day7: number;
    day30: number;
  };
  segments: Record<string, CohortMetrics>;
}

export interface CohortMetrics {
  count: number;
  revenue: number;
  avgValue: number;
  performance: number; // vs baseline
}

export interface PredictiveInsight {
  type: 'demand' | 'price' | 'risk' | 'opportunity';
  confidence: number;
  prediction: any;
  factors: Array<{ factor: string; weight: number }>;
  recommendation: string;
}

export interface SeasonalPattern {
  component: string;
  pattern: 'rising' | 'falling' | 'stable' | 'cyclical';
  peakMonths: number[];
  troughMonths: number[];
  volatility: number;
  forecast: Array<{ month: number; value: number }>;
}

export interface MarketIntelligence {
  trends: Array<{
    component: string;
    direction: 'up' | 'down' | 'stable';
    momentum: number;
    timeframe: string;
  }>;
  opportunities: Array<{
    type: string;
    description: string;
    potentialROI: number;
    confidence: number;
  }>;
  risks: Array<{
    type: string;
    severity: 'high' | 'medium' | 'low';
    probability: number;
    mitigation: string;
  }>;
}

/**
 * Perform cohort analysis
 */
export function analyzeCohorts(
  deals: Deal[],
  cohortBy: 'acquisition_month' | 'category' | 'source' | 'value_range'
): CohortAnalysis[] {
  const cohorts = groupIntoCohorts(deals, cohortBy);
  const analyses: CohortAnalysis[] = [];
  
  for (const [cohortId, cohortDeals] of cohorts.entries()) {
    const metrics = calculateCohortMetrics(cohortDeals);
    const retention = calculateRetention(cohortDeals);
    const segments = segmentCohort(cohortDeals);
    
    analyses.push({
      cohortId,
      period: getCohortPeriod(cohortDeals),
      metrics,
      retention,
      segments,
    });
  }
  
  return analyses.sort((a, b) => b.metrics.profit - a.metrics.profit);
}

/**
 * Generate predictive insights
 */
export function generatePredictiveInsights(
  historicalData: {
    deals: Deal[];
    inventory: InventoryItem[];
    marketPrices: Array<{ date: Date; component: string; price: number }>;
  }
): PredictiveInsight[] {
  const insights: PredictiveInsight[] = [];
  
  // Demand prediction
  const demandInsight = predictDemand(historicalData);
  if (demandInsight) insights.push(demandInsight);
  
  // Price prediction
  const priceInsights = predictPrices(historicalData);
  insights.push(...priceInsights);
  
  // Risk prediction
  const riskInsight = predictRisks(historicalData);
  if (riskInsight) insights.push(riskInsight);
  
  // Opportunity detection
  const opportunities = detectOpportunities(historicalData);
  insights.push(...opportunities);
  
  return insights.sort((a, b) => b.confidence - a.confidence);
}

/**
 * Analyze seasonal patterns
 */
export function analyzeSeasonalPatterns(
  salesData: Array<{ date: Date; component: string; volume: number; price: number }>
): SeasonalPattern[] {
  const patterns: SeasonalPattern[] = [];
  const componentGroups = groupBy(salesData, 'component');
  
  for (const [component, data] of Object.entries(componentGroups)) {
    const monthlyData = aggregateByMonth(data);
    const pattern = detectPattern(monthlyData);
    const peaks = findPeaks(monthlyData);
    const troughs = findTroughs(monthlyData);
    const volatility = calculateVolatility(monthlyData);
    const forecast = forecastNextYear(monthlyData, pattern);
    
    patterns.push({
      component,
      pattern,
      peakMonths: peaks,
      troughMonths: troughs,
      volatility,
      forecast,
    });
  }
  
  return patterns;
}

/**
 * Generate market intelligence
 */
export function generateMarketIntelligence(
  data: {
    recentDeals: Deal[];
    marketPrices: Array<{ date: Date; component: string; price: number }>;
    competitorActivity?: Array<{ date: Date; type: string; impact: number }>;
  }
): MarketIntelligence {
  const trends = analyzeTrends(data.marketPrices);
  const opportunities = identifyOpportunities(data);
  const risks = assessRisks(data);
  
  return { trends, opportunities, risks };
}

/**
 * Calculate customer lifetime value
 */
export function calculateCustomerLifetimeValue(
  customerHistory: Array<{
    customerId: string;
    purchases: Array<{ date: Date; value: number; profit: number }>;
  }>
): Array<{
  customerId: string;
  ltv: number;
  avgOrderValue: number;
  frequency: number;
  recency: number;
  segment: 'vip' | 'regular' | 'occasional' | 'dormant';
}> {
  const now = new Date();
  
  return customerHistory.map(customer => {
    const totalValue = customer.purchases.reduce((sum, p) => sum + p.value, 0);
    const totalProfit = customer.purchases.reduce((sum, p) => sum + p.profit, 0);
    const avgOrderValue = totalValue / customer.purchases.length;
    
    // Calculate purchase frequency (purchases per month)
    const firstPurchase = Math.min(...customer.purchases.map(p => p.date.getTime()));
    const monthsActive = (now.getTime() - firstPurchase) / (1000 * 60 * 60 * 24 * 30);
    const frequency = customer.purchases.length / Math.max(1, monthsActive);
    
    // Calculate recency (days since last purchase)
    const lastPurchase = Math.max(...customer.purchases.map(p => p.date.getTime()));
    const recency = (now.getTime() - lastPurchase) / (1000 * 60 * 60 * 24);
    
    // Estimate future value
    const projectedMonths = 12;
    const churnProbability = calculateChurnProbability(recency, frequency);
    const ltv = totalProfit + (avgOrderValue * frequency * projectedMonths * (1 - churnProbability));
    
    // Segment customer
    let segment: 'vip' | 'regular' | 'occasional' | 'dormant' = 'occasional';
    if (recency > 90) segment = 'dormant';
    else if (frequency > 2 && avgOrderValue > 500) segment = 'vip';
    else if (frequency > 1) segment = 'regular';
    
    return {
      customerId: customer.customerId,
      ltv,
      avgOrderValue,
      frequency,
      recency,
      segment,
    };
  });
}

/**
 * Anomaly detection
 */
export function detectAnomalies(
  metrics: Array<{ date: Date; metric: string; value: number }>,
  sensitivity: number = 2 // standard deviations
): Array<{
  date: Date;
  metric: string;
  value: number;
  expectedRange: { min: number; max: number };
  severity: 'high' | 'medium' | 'low';
  type: 'spike' | 'drop' | 'unusual_pattern';
}> {
  const anomalies: any[] = [];
  const metricGroups = groupBy(metrics, 'metric');
  
  for (const [metricName, data] of Object.entries(metricGroups)) {
    const values = data.map(d => d.value);
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const stdDev = Math.sqrt(
      values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length
    );
    
    const threshold = stdDev * sensitivity;
    const expectedMin = mean - threshold;
    const expectedMax = mean + threshold;
    
    data.forEach(point => {
      if (point.value < expectedMin || point.value > expectedMax) {
        const deviation = Math.abs(point.value - mean) / stdDev;
        
        anomalies.push({
          date: point.date,
          metric: metricName,
          value: point.value,
          expectedRange: { min: expectedMin, max: expectedMax },
          severity: deviation > 3 ? 'high' : deviation > 2.5 ? 'medium' : 'low',
          type: point.value > expectedMax ? 'spike' : 'drop',
        });
      }
    });
  }
  
  return anomalies;
}

// Helper functions
function groupIntoCohorts(deals: Deal[], cohortBy: string): Map<string, Deal[]> {
  const cohorts = new Map<string, Deal[]>();
  
  deals.forEach(deal => {
    let cohortId: string;
    
    switch (cohortBy) {
      case 'acquisition_month':
        cohortId = deal.metadata.createdAt.toISOString().slice(0, 7);
        break;
      case 'category':
        cohortId = deal.category || 'uncategorized';
        break;
      case 'source':
        cohortId = deal.metadata.source;
        break;
      case 'value_range':
        const value = deal.purchasePrice || deal.askingPrice || 0;
        if (value < 500) cohortId = 'low';
        else if (value < 1000) cohortId = 'medium';
        else cohortId = 'high';
        break;
      default:
        cohortId = 'default';
    }
    
    const existing = cohorts.get(cohortId) || [];
    existing.push(deal);
    cohorts.set(cohortId, existing);
  });
  
  return cohorts;
}

function calculateCohortMetrics(deals: Deal[]): CohortAnalysis['metrics'] {
  const completedDeals = deals.filter(d => d.stage === 'completed');
  
  const revenue = completedDeals.reduce((sum, d) => sum + (d.salePrice || 0), 0);
  const costs = completedDeals.reduce((sum, d) => sum + (d.purchasePrice || 0), 0);
  const profit = revenue - costs;
  
  const rois = completedDeals.map(d => calculateROI(d).percentage);
  const avgROI = rois.length > 0 ? rois.reduce((a, b) => a + b, 0) / rois.length : 0;
  
  const holdTimes = completedDeals.map(d => {
    const acquired = d.acquiredDate || d.metadata.createdAt;
    const sold = d.soldDate || new Date();
    return (sold.getTime() - acquired.getTime()) / (1000 * 60 * 60 * 24);
  });
  const avgHoldTime = holdTimes.length > 0 
    ? holdTimes.reduce((a, b) => a + b, 0) / holdTimes.length 
    : 0;
  
  const successRate = deals.length > 0 
    ? completedDeals.length / deals.length 
    : 0;
  
  return {
    deals: deals.length,
    revenue,
    profit,
    avgROI,
    avgHoldTime,
    successRate,
  };
}

function calculateRetention(deals: Deal[]): CohortAnalysis['retention'] {
  // Simplified retention calculation
  const totalDeals = deals.length;
  const activeDays = deals.map(d => {
    const created = d.metadata.createdAt;
    const lastUpdate = d.metadata.updatedAt;
    return (lastUpdate.getTime() - created.getTime()) / (1000 * 60 * 60 * 24);
  });
  
  const day1 = activeDays.filter(days => days >= 1).length / totalDeals;
  const day7 = activeDays.filter(days => days >= 7).length / totalDeals;
  const day30 = activeDays.filter(days => days >= 30).length / totalDeals;
  
  return { day1, day7, day30 };
}

function segmentCohort(deals: Deal[]): Record<string, CohortMetrics> {
  const segments: Record<string, CohortMetrics> = {};
  
  // Segment by profitability
  const profitable = deals.filter(d => {
    const roi = calculateROI(d);
    return roi.percentage > 20;
  });
  
  segments['high_profit'] = {
    count: profitable.length,
    revenue: profitable.reduce((sum, d) => sum + (d.salePrice || 0), 0),
    avgValue: profitable.length > 0 
      ? profitable.reduce((sum, d) => sum + (d.salePrice || 0), 0) / profitable.length 
      : 0,
    performance: 1.0,
  };
  
  return segments;
}

function getCohortPeriod(deals: Deal[]): { start: Date; end: Date } {
  const dates = deals.map(d => d.metadata.createdAt.getTime());
  return {
    start: new Date(Math.min(...dates)),
    end: new Date(Math.max(...dates)),
  };
}

function predictDemand(data: any): PredictiveInsight | null {
  // Simplified demand prediction
  const recentVolume = data.deals.filter((d: Deal) => {
    const age = (new Date().getTime() - d.metadata.createdAt.getTime()) / (1000 * 60 * 60 * 24);
    return age < 30;
  }).length;
  
  const historicalAvg = data.deals.length / 90; // Daily average
  const trend = recentVolume / 30 - historicalAvg;
  
  if (Math.abs(trend) > historicalAvg * 0.2) {
    return {
      type: 'demand',
      confidence: 0.75,
      prediction: {
        direction: trend > 0 ? 'increasing' : 'decreasing',
        magnitude: Math.abs(trend / historicalAvg),
        forecast: trend > 0 ? recentVolume * 1.1 : recentVolume * 0.9,
      },
      factors: [
        { factor: 'Recent volume', weight: 0.6 },
        { factor: 'Historical trend', weight: 0.4 },
      ],
      recommendation: trend > 0 
        ? 'Increase inventory to meet rising demand' 
        : 'Reduce acquisition pace due to falling demand',
    };
  }
  
  return null;
}

function predictPrices(data: any): PredictiveInsight[] {
  // Price prediction for top components
  const insights: PredictiveInsight[] = [];
  const components = ['gpu', 'cpu'];
  
  components.forEach(component => {
    const prices = data.marketPrices
      .filter((p: any) => p.component === component)
      .sort((a: any, b: any) => a.date.getTime() - b.date.getTime());
    
    if (prices.length > 10) {
      const recentPrices = prices.slice(-10);
      const trend = calculateTrend(recentPrices.map((p: any) => p.price));
      
      insights.push({
        type: 'price',
        confidence: 0.7,
        prediction: {
          component,
          direction: trend > 0 ? 'up' : 'down',
          magnitude: Math.abs(trend),
          forecast: recentPrices[recentPrices.length - 1].price * (1 + trend),
        },
        factors: [
          { factor: 'Historical prices', weight: 0.7 },
          { factor: 'Market trend', weight: 0.3 },
        ],
        recommendation: trend > 0 
          ? `Consider selling ${component} inventory - prices rising`
          : `Good time to acquire ${component} - prices falling`,
      });
    }
  });
  
  return insights;
}

function predictRisks(data: any): PredictiveInsight | null {
  // Risk prediction based on patterns
  const recentDeals = data.deals.filter((d: Deal) => {
    const age = (new Date().getTime() - d.metadata.createdAt.getTime()) / (1000 * 60 * 60 * 24);
    return age < 30;
  });
  
  const failureRate = recentDeals.filter((d: Deal) => d.stage === 'cancelled').length / recentDeals.length;
  
  if (failureRate > 0.3) {
    return {
      type: 'risk',
      confidence: 0.8,
      prediction: {
        riskLevel: 'high',
        failureRate,
        categories: ['negotiation_failure', 'quality_issues'],
      },
      factors: [
        { factor: 'Recent failure rate', weight: 0.8 },
        { factor: 'Deal complexity', weight: 0.2 },
      ],
      recommendation: 'Review qualification criteria and improve initial screening',
    };
  }
  
  return null;
}

function detectOpportunities(data: any): PredictiveInsight[] {
  const opportunities: PredictiveInsight[] = [];
  
  // Bundle opportunity
  const gpuCount = data.inventory.filter((i: InventoryItem) => i.category === 'gpu').length;
  const cpuCount = data.inventory.filter((i: InventoryItem) => i.category === 'cpu').length;
  
  if (gpuCount > 3 && cpuCount > 3) {
    opportunities.push({
      type: 'opportunity',
      confidence: 0.85,
      prediction: {
        type: 'bundle',
        potential: gpuCount + cpuCount,
        estimatedProfit: (gpuCount + cpuCount) * 50, // $50 extra per bundle
      },
      factors: [
        { factor: 'Inventory levels', weight: 0.6 },
        { factor: 'Market demand', weight: 0.4 },
      ],
      recommendation: 'Create component bundles to increase average order value',
    });
  }
  
  return opportunities;
}

function groupBy<T>(array: T[], key: keyof T): Record<string, T[]> {
  return array.reduce((groups, item) => {
    const value = String(item[key]);
    (groups[value] = groups[value] || []).push(item);
    return groups;
  }, {} as Record<string, T[]>);
}

function aggregateByMonth(data: any[]): Array<{ month: number; value: number }> {
  const monthly: Record<number, { sum: number; count: number }> = {};
  
  data.forEach(item => {
    const month = item.date.getMonth();
    if (!monthly[month]) monthly[month] = { sum: 0, count: 0 };
    monthly[month].sum += item.volume * item.price;
    monthly[month].count += item.volume;
  });
  
  return Object.entries(monthly).map(([month, data]) => ({
    month: parseInt(month),
    value: data.sum / data.count,
  }));
}

function detectPattern(monthlyData: Array<{ month: number; value: number }>): SeasonalPattern['pattern'] {
  if (monthlyData.length < 3) return 'stable';
  
  const values = monthlyData.map(d => d.value);
  const trend = calculateTrend(values);
  const variance = calculateVariance(values);
  
  if (Math.abs(trend) < 0.05) return 'stable';
  if (variance > 0.3) return 'cyclical';
  return trend > 0 ? 'rising' : 'falling';
}

function findPeaks(data: Array<{ month: number; value: number }>): number[] {
  const peaks: number[] = [];
  for (let i = 1; i < data.length - 1; i++) {
    if (data[i].value > data[i - 1].value && data[i].value > data[i + 1].value) {
      peaks.push(data[i].month);
    }
  }
  return peaks;
}

function findTroughs(data: Array<{ month: number; value: number }>): number[] {
  const troughs: number[] = [];
  for (let i = 1; i < data.length - 1; i++) {
    if (data[i].value < data[i - 1].value && data[i].value < data[i + 1].value) {
      troughs.push(data[i].month);
    }
  }
  return troughs;
}

function calculateVolatility(data: Array<{ month: number; value: number }>): number {
  const values = data.map(d => d.value);
  return calculateVariance(values);
}

function calculateVariance(values: number[]): number {
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const squaredDiffs = values.map(v => Math.pow(v - mean, 2));
  return Math.sqrt(squaredDiffs.reduce((a, b) => a + b, 0) / values.length) / mean;
}

function calculateTrend(values: number[]): number {
  if (values.length < 2) return 0;
  const firstHalf = values.slice(0, Math.floor(values.length / 2));
  const secondHalf = values.slice(Math.floor(values.length / 2));
  const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
  const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
  return (secondAvg - firstAvg) / firstAvg;
}

function forecastNextYear(
  monthlyData: Array<{ month: number; value: number }>,
  pattern: SeasonalPattern['pattern']
): Array<{ month: number; value: number }> {
  const forecast: Array<{ month: number; value: number }> = [];
  const avgValue = monthlyData.reduce((sum, d) => sum + d.value, 0) / monthlyData.length;
  
  for (let month = 0; month < 12; month++) {
    const historicalMonth = monthlyData.find(d => d.month === month);
    const baseValue = historicalMonth?.value || avgValue;
    
    let adjustedValue = baseValue;
    if (pattern === 'rising') adjustedValue *= 1.1;
    else if (pattern === 'falling') adjustedValue *= 0.9;
    else if (pattern === 'cyclical') {
      const seasonalFactor = 1 + 0.2 * Math.sin((month - 3) * Math.PI / 6);
      adjustedValue *= seasonalFactor;
    }
    
    forecast.push({ month, value: adjustedValue });
  }
  
  return forecast;
}

function analyzeTrends(prices: Array<{ date: Date; component: string; price: number }>): MarketIntelligence['trends'] {
  const trends: MarketIntelligence['trends'] = [];
  const components = new Set(prices.map(p => p.component));
  
  components.forEach(component => {
    const componentPrices = prices
      .filter(p => p.component === component)
      .sort((a, b) => a.date.getTime() - b.date.getTime());
    
    if (componentPrices.length > 5) {
      const recentPrices = componentPrices.slice(-5).map(p => p.price);
      const trend = calculateTrend(recentPrices);
      
      trends.push({
        component,
        direction: trend > 0.05 ? 'up' : trend < -0.05 ? 'down' : 'stable',
        momentum: Math.abs(trend),
        timeframe: '30 days',
      });
    }
  });
  
  return trends;
}

function identifyOpportunities(data: any): MarketIntelligence['opportunities'] {
  const opportunities: MarketIntelligence['opportunities'] = [];
  
  // Price arbitrage
  const priceVariance = calculatePriceVariance(data.marketPrices);
  if (priceVariance > 0.2) {
    opportunities.push({
      type: 'arbitrage',
      description: 'High price variance detected - arbitrage opportunity',
      potentialROI: priceVariance * 100,
      confidence: 0.8,
    });
  }
  
  return opportunities;
}

function assessRisks(data: any): MarketIntelligence['risks'] {
  const risks: MarketIntelligence['risks'] = [];
  
  // Inventory risk
  if (data.recentDeals.length < 5) {
    risks.push({
      type: 'liquidity',
      severity: 'medium',
      probability: 0.6,
      mitigation: 'Increase marketing efforts to maintain deal flow',
    });
  }
  
  return risks;
}

function calculatePriceVariance(prices: any[]): number {
  if (prices.length < 2) return 0;
  const values = prices.map(p => p.price);
  return calculateVariance(values);
}

function calculateChurnProbability(recency: number, frequency: number): number {
  // Simple churn model
  const recencyScore = Math.min(1, recency / 180); // 180 days = high churn risk
  const frequencyScore = 1 - Math.min(1, frequency / 2); // 2 purchases/month = low churn
  return (recencyScore + frequencyScore) / 2;
}