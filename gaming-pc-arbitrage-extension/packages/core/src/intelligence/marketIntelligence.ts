/**
 * Market Intelligence System
 * Automated market analysis and report generation
 */

import { db } from '../../../extension/lib/db';
import { Listing, Deal, ComponentPriceTier } from '../types';
import { componentPriceTiers } from '../data/pricing-tiers';
import * as ss from 'simple-statistics';

export interface MarketReport {
  id: string;
  type: 'daily' | 'weekly' | 'monthly' | 'custom';
  period: {
    start: Date;
    end: Date;
  };
  metrics: MarketMetrics;
  trends: MarketTrends;
  insights: MarketInsight[];
  recommendations: string[];
  componentAnalysis: ComponentMarketAnalysis;
  dealAnalysis: DealAnalysis;
  forecastAnalysis?: ForecastAnalysis;
  generatedAt: Date;
}

export interface MarketMetrics {
  // Volume metrics
  totalListings: number;
  newListings: number;
  soldListings: number;
  
  // Price metrics
  avgPrice: number;
  medianPrice: number;
  priceRange: { min: number; max: number };
  priceDistribution: PriceSegment[];
  
  // Performance metrics
  avgDaysToSell: number;
  sellThroughRate: number;
  
  // Component metrics
  gpuListingsPercent: number;
  avgGpuPrice: number;
  topComponents: ComponentCount[];
}

export interface MarketTrends {
  priceChange: TrendData;
  volumeChange: TrendData;
  demandIndicators: DemandIndicator[];
  seasonalFactors: SeasonalFactor[];
}

export interface TrendData {
  current: number;
  previous: number;
  change: number;
  changePercent: number;
  direction: 'up' | 'down' | 'stable';
  significance: 'high' | 'medium' | 'low';
}

export interface DemandIndicator {
  component: string;
  demandScore: number; // 0-100
  trend: 'increasing' | 'decreasing' | 'stable';
  priceImpact: number; // percentage
}

export interface SeasonalFactor {
  name: string;
  impact: number; // -1 to 1
  description: string;
}

export interface MarketInsight {
  type: 'opportunity' | 'warning' | 'trend' | 'anomaly';
  severity: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  actionItems: string[];
  affectedComponents?: string[];
}

export interface ComponentMarketAnalysis {
  cpuMarket: ComponentMarketData;
  gpuMarket: ComponentMarketData;
  trends: ComponentTrend[];
  priceMovers: PriceMover[];
}

export interface ComponentMarketData {
  avgPrice: number;
  medianPrice: number;
  volume: number;
  topModels: ModelData[];
  priceHistory: PricePoint[];
}

export interface ComponentTrend {
  component: string;
  trend: 'hot' | 'cooling' | 'stable';
  priceDirection: 'up' | 'down' | 'stable';
  volumeChange: number;
  recommendation: string;
}

export interface PriceMover {
  component: string;
  previousPrice: number;
  currentPrice: number;
  changePercent: number;
  reason?: string;
}

export interface DealAnalysis {
  totalDeals: number;
  successRate: number;
  avgROI: number;
  avgTimeToClose: number;
  topPerformers: DealPerformance[];
  missedOpportunities: MissedOpportunity[];
}

export interface DealPerformance {
  dealId: string;
  title: string;
  buyPrice: number;
  sellPrice: number;
  roi: number;
  daysToSell: number;
}

export interface MissedOpportunity {
  listingId: string;
  title: string;
  price: number;
  estimatedROI: number;
  reason: string;
}

export interface ForecastAnalysis {
  priceForecasts: ComponentForecast[];
  volumeForecasts: VolumeForecast[];
  recommendedActions: string[];
  confidence: number;
}

export interface ComponentForecast {
  component: string;
  currentPrice: number;
  forecast7Day: number;
  forecast30Day: number;
  confidence: number;
  factors: string[];
}

export interface VolumeForecast {
  platform: string;
  currentVolume: number;
  forecast7Day: number;
  trend: string;
}

export interface PriceSegment {
  range: string;
  count: number;
  percentage: number;
}

export interface ComponentCount {
  name: string;
  count: number;
  avgPrice: number;
}

export interface ModelData {
  model: string;
  count: number;
  avgPrice: number;
  trend: 'up' | 'down' | 'stable';
}

export interface PricePoint {
  date: Date;
  price: number;
  volume: number;
}

export class MarketIntelligence {
  private listings: Map<string, Listing[]> = new Map();
  private deals: Map<string, Deal[]> = new Map();
  private reports: Map<string, MarketReport> = new Map();
  private readonly STORAGE_KEY = 'marketReports';

  constructor() {
    this.loadReports();
  }

  /**
   * Generate a market report for the specified period
   */
  async generateReport(
    type: MarketReport['type'] = 'weekly',
    customPeriod?: { start: Date; end: Date }
  ): Promise<MarketReport> {
    const period = this.getPeriod(type, customPeriod);
    
    // Load data for the period
    await this.loadDataForPeriod(period);

    // Generate report sections
    const metrics = this.calculateMetrics(period);
    const trends = this.analyzeTrends(period, metrics);
    const componentAnalysis = this.analyzeComponents(period);
    const dealAnalysis = this.analyzeDeals(period);
    const insights = this.generateInsights(metrics, trends, componentAnalysis);
    const recommendations = this.generateRecommendations(insights, trends);
    const forecastAnalysis = this.generateForecasts(trends, componentAnalysis);

    const report: MarketReport = {
      id: `report_${Date.now()}`,
      type,
      period,
      metrics,
      trends,
      insights,
      recommendations,
      componentAnalysis,
      dealAnalysis,
      forecastAnalysis,
      generatedAt: new Date()
    };

    this.reports.set(report.id, report);
    await this.saveReports();

    return report;
  }

  /**
   * Calculate market metrics
   */
  private calculateMetrics(period: { start: Date; end: Date }): MarketMetrics {
    const currentListings = this.getListingsForPeriod(period);
    const previousPeriod = this.getPreviousPeriod(period);
    const previousListings = this.getListingsForPeriod(previousPeriod);

    // Basic metrics
    const prices = currentListings.map(l => l.price).filter(p => p > 0);
    const avgPrice = prices.length > 0 ? ss.mean(prices) : 0;
    const medianPrice = prices.length > 0 ? ss.median(prices) : 0;

    // Price distribution
    const priceDistribution = this.calculatePriceDistribution(prices);

    // Component metrics
    const gpuListings = currentListings.filter(l => l.components?.gpu);
    const gpuPrices = gpuListings.map(l => l.price);
    
    // Days to sell (simplified - in production, track actual sale dates)
    const soldListings = currentListings.filter(l => l.status === 'sold');
    const avgDaysToSell = this.calculateAvgDaysToSell(soldListings);

    // Top components
    const topComponents = this.getTopComponents(currentListings);

    return {
      totalListings: currentListings.length,
      newListings: currentListings.length - previousListings.length,
      soldListings: soldListings.length,
      avgPrice,
      medianPrice,
      priceRange: {
        min: Math.min(...prices),
        max: Math.max(...prices)
      },
      priceDistribution,
      avgDaysToSell,
      sellThroughRate: currentListings.length > 0 
        ? (soldListings.length / currentListings.length) * 100 
        : 0,
      gpuListingsPercent: currentListings.length > 0
        ? (gpuListings.length / currentListings.length) * 100
        : 0,
      avgGpuPrice: gpuPrices.length > 0 ? ss.mean(gpuPrices) : 0,
      topComponents
    };
  }

  /**
   * Analyze market trends
   */
  private analyzeTrends(
    period: { start: Date; end: Date },
    currentMetrics: MarketMetrics
  ): MarketTrends {
    const previousPeriod = this.getPreviousPeriod(period);
    const previousMetrics = this.calculateMetrics(previousPeriod);

    // Price trends
    const priceChange = this.calculateTrendData(
      currentMetrics.avgPrice,
      previousMetrics.avgPrice,
      'price'
    );

    // Volume trends
    const volumeChange = this.calculateTrendData(
      currentMetrics.totalListings,
      previousMetrics.totalListings,
      'volume'
    );

    // Demand indicators
    const demandIndicators = this.calculateDemandIndicators(period);

    // Seasonal factors
    const seasonalFactors = this.identifySeasonalFactors(period);

    return {
      priceChange,
      volumeChange,
      demandIndicators,
      seasonalFactors
    };
  }

  /**
   * Analyze component market
   */
  private analyzeComponents(period: { start: Date; end: Date }): ComponentMarketAnalysis {
    const listings = this.getListingsForPeriod(period);
    
    // CPU Market
    const cpuListings = listings.filter(l => l.components?.cpu);
    const cpuMarket = this.analyzeComponentType(cpuListings, 'cpu');

    // GPU Market
    const gpuListings = listings.filter(l => l.components?.gpu);
    const gpuMarket = this.analyzeComponentType(gpuListings, 'gpu');

    // Component trends
    const trends = this.identifyComponentTrends(listings);

    // Price movers
    const priceMovers = this.identifyPriceMovers(period);

    return {
      cpuMarket,
      gpuMarket,
      trends,
      priceMovers
    };
  }

  /**
   * Analyze deals performance
   */
  private analyzeDeals(period: { start: Date; end: Date }): DealAnalysis {
    const deals = this.getDealsForPeriod(period);
    const completedDeals = deals.filter(d => d.status === 'completed');

    // Calculate metrics
    const rois = completedDeals.map(d => d.profit);
    const avgROI = rois.length > 0 ? ss.mean(rois) : 0;
    
    const closeTimes = completedDeals
      .filter(d => d.purchasedAt && d.soldAt)
      .map(d => (d.soldAt!.getTime() - d.purchasedAt!.getTime()) / (1000 * 60 * 60 * 24));
    
    const avgTimeToClose = closeTimes.length > 0 ? ss.mean(closeTimes) : 0;

    // Top performers
    const topPerformers = completedDeals
      .sort((a, b) => b.profit - a.profit)
      .slice(0, 5)
      .map(d => ({
        dealId: d.id,
        title: d.listing.title,
        buyPrice: d.purchasePrice,
        sellPrice: d.sellPrice || 0,
        roi: d.profit,
        daysToSell: d.soldAt && d.purchasedAt
          ? Math.round((d.soldAt.getTime() - d.purchasedAt.getTime()) / (1000 * 60 * 60 * 24))
          : 0
      }));

    // Missed opportunities (simplified)
    const missedOpportunities = this.identifyMissedOpportunities(period);

    return {
      totalDeals: deals.length,
      successRate: deals.length > 0 
        ? (completedDeals.length / deals.length) * 100 
        : 0,
      avgROI,
      avgTimeToClose,
      topPerformers,
      missedOpportunities
    };
  }

  /**
   * Generate market insights
   */
  private generateInsights(
    metrics: MarketMetrics,
    trends: MarketTrends,
    componentAnalysis: ComponentMarketAnalysis
  ): MarketInsight[] {
    const insights: MarketInsight[] = [];

    // Price movement insights
    if (trends.priceChange.changePercent > 10) {
      insights.push({
        type: 'warning',
        severity: 'high',
        title: 'Significant Price Increase Detected',
        description: `Average prices have increased by ${trends.priceChange.changePercent.toFixed(1)}%. This may impact buying opportunities.`,
        actionItems: [
          'Focus on underpriced listings',
          'Adjust offer strategies',
          'Monitor specific component prices'
        ]
      });
    }

    // GPU market insights
    if (metrics.gpuListingsPercent > 70) {
      insights.push({
        type: 'opportunity',
        severity: 'medium',
        title: 'High GPU System Availability',
        description: `${metrics.gpuListingsPercent.toFixed(1)}% of listings include GPUs, indicating good selection.`,
        actionItems: [
          'Prioritize high-end GPU systems',
          'Compare GPU prices across listings',
          'Look for bundle deals'
        ],
        affectedComponents: ['GPU']
      });
    }

    // Demand insights
    const hotComponents = trends.demandIndicators
      .filter(d => d.demandScore > 80)
      .map(d => d.component);
    
    if (hotComponents.length > 0) {
      insights.push({
        type: 'trend',
        severity: 'high',
        title: 'High Demand Components Identified',
        description: `Components with exceptional demand: ${hotComponents.join(', ')}`,
        actionItems: [
          'Prioritize systems with these components',
          'Quick action required on related listings',
          'Consider higher offers for competitive advantage'
        ],
        affectedComponents: hotComponents
      });
    }

    // Seasonal insights
    const significantSeasonalFactors = trends.seasonalFactors
      .filter(f => Math.abs(f.impact) > 0.3);
    
    if (significantSeasonalFactors.length > 0) {
      insights.push({
        type: 'trend',
        severity: 'medium',
        title: 'Seasonal Market Factors Active',
        description: significantSeasonalFactors.map(f => f.description).join('. '),
        actionItems: [
          'Adjust pricing expectations',
          'Plan inventory accordingly',
          'Monitor competitor activity'
        ]
      });
    }

    // Component price movement
    const majorPriceMovers = componentAnalysis.priceMovers
      .filter(m => Math.abs(m.changePercent) > 15);
    
    if (majorPriceMovers.length > 0) {
      insights.push({
        type: 'anomaly',
        severity: 'high',
        title: 'Significant Component Price Changes',
        description: `Major price movements detected in: ${majorPriceMovers.map(m => m.component).join(', ')}`,
        actionItems: [
          'Review pricing strategies',
          'Update valuation models',
          'Investigate market causes'
        ],
        affectedComponents: majorPriceMovers.map(m => m.component)
      });
    }

    return insights;
  }

  /**
   * Generate recommendations
   */
  private generateRecommendations(
    insights: MarketInsight[],
    trends: MarketTrends
  ): string[] {
    const recommendations: string[] = [];

    // Price-based recommendations
    if (trends.priceChange.direction === 'up' && trends.priceChange.changePercent > 5) {
      recommendations.push('Consider increasing offer amounts by 5-10% to remain competitive');
      recommendations.push('Focus on quick decision-making as prices are rising');
    } else if (trends.priceChange.direction === 'down') {
      recommendations.push('Market prices declining - negotiate more aggressively');
      recommendations.push('Wait 24-48 hours before making offers on new listings');
    }

    // Volume-based recommendations
    if (trends.volumeChange.changePercent > 20) {
      recommendations.push('High listing volume detected - more selection available');
      recommendations.push('Use bulk scanning to efficiently process opportunities');
    }

    // Component-specific recommendations
    const highDemandComponents = trends.demandIndicators
      .filter(d => d.demandScore > 75)
      .sort((a, b) => b.demandScore - a.demandScore)
      .slice(0, 3);
    
    if (highDemandComponents.length > 0) {
      recommendations.push(
        `Priority components: ${highDemandComponents.map(c => c.component).join(', ')}`
      );
    }

    // Seasonal recommendations
    const currentMonth = new Date().getMonth();
    if (currentMonth === 10 || currentMonth === 11) { // November, December
      recommendations.push('Holiday season approaching - expect increased competition');
      recommendations.push('Stock up on popular configurations for gift season');
    } else if (currentMonth === 7 || currentMonth === 8) { // August, September
      recommendations.push('Back-to-school season - focus on budget and mid-range systems');
    }

    // Risk-based recommendations
    if (insights.some(i => i.type === 'warning' && i.severity === 'high')) {
      recommendations.push('High-risk market conditions - emphasize due diligence');
      recommendations.push('Diversify component focus to reduce exposure');
    }

    return recommendations;
  }

  /**
   * Generate forecasts
   */
  private generateForecasts(
    trends: MarketTrends,
    componentAnalysis: ComponentMarketAnalysis
  ): ForecastAnalysis {
    // Component price forecasts
    const priceForecasts = this.forecastComponentPrices(
      componentAnalysis,
      trends
    );

    // Volume forecasts
    const volumeForecasts = this.forecastVolumes(trends);

    // Recommended actions based on forecasts
    const recommendedActions = this.getRecommendedActions(
      priceForecasts,
      volumeForecasts
    );

    // Calculate overall confidence
    const confidence = this.calculateForecastConfidence(trends);

    return {
      priceForecasts,
      volumeForecasts,
      recommendedActions,
      confidence
    };
  }

  /**
   * Helper methods
   */
  private getPeriod(
    type: MarketReport['type'],
    customPeriod?: { start: Date; end: Date }
  ): { start: Date; end: Date } {
    if (customPeriod) return customPeriod;

    const end = new Date();
    const start = new Date();

    switch (type) {
      case 'daily':
        start.setDate(end.getDate() - 1);
        break;
      case 'weekly':
        start.setDate(end.getDate() - 7);
        break;
      case 'monthly':
        start.setMonth(end.getMonth() - 1);
        break;
    }

    return { start, end };
  }

  private getPreviousPeriod(period: { start: Date; end: Date }): { start: Date; end: Date } {
    const duration = period.end.getTime() - period.start.getTime();
    return {
      start: new Date(period.start.getTime() - duration),
      end: new Date(period.start)
    };
  }

  private async loadDataForPeriod(period: { start: Date; end: Date }): Promise<void> {
    // Load listings from database
    const listings = await db.listings
      .where('postedAt')
      .between(period.start, period.end)
      .toArray();
    
    this.listings.set(this.periodKey(period), listings);

    // Load deals
    const deals = await db.deals
      .where('createdAt')
      .between(period.start, period.end)
      .toArray();
    
    this.deals.set(this.periodKey(period), deals);
  }

  private getListingsForPeriod(period: { start: Date; end: Date }): Listing[] {
    return this.listings.get(this.periodKey(period)) || [];
  }

  private getDealsForPeriod(period: { start: Date; end: Date }): Deal[] {
    return this.deals.get(this.periodKey(period)) || [];
  }

  private periodKey(period: { start: Date; end: Date }): string {
    return `${period.start.toISOString()}_${period.end.toISOString()}`;
  }

  private calculatePriceDistribution(prices: number[]): PriceSegment[] {
    const segments = [
      { range: '$0-$300', min: 0, max: 300 },
      { range: '$300-$600', min: 300, max: 600 },
      { range: '$600-$1000', min: 600, max: 1000 },
      { range: '$1000-$1500', min: 1000, max: 1500 },
      { range: '$1500-$2500', min: 1500, max: 2500 },
      { range: '$2500+', min: 2500, max: Infinity }
    ];

    return segments.map(segment => {
      const count = prices.filter(p => p >= segment.min && p < segment.max).length;
      return {
        range: segment.range,
        count,
        percentage: prices.length > 0 ? (count / prices.length) * 100 : 0
      };
    });
  }

  private calculateAvgDaysToSell(soldListings: Listing[]): number {
    // Simplified - in production, track actual sale completion
    return 7; // Default estimate
  }

  private getTopComponents(listings: Listing[]): ComponentCount[] {
    const componentCounts = new Map<string, { count: number; totalPrice: number }>();

    listings.forEach(listing => {
      if (listing.components?.cpu) {
        const key = listing.components.cpu.model;
        const current = componentCounts.get(key) || { count: 0, totalPrice: 0 };
        current.count++;
        current.totalPrice += listing.price;
        componentCounts.set(key, current);
      }
      
      if (listing.components?.gpu) {
        const key = listing.components.gpu.model;
        const current = componentCounts.get(key) || { count: 0, totalPrice: 0 };
        current.count++;
        current.totalPrice += listing.price;
        componentCounts.set(key, current);
      }
    });

    return Array.from(componentCounts.entries())
      .map(([name, data]) => ({
        name,
        count: data.count,
        avgPrice: data.totalPrice / data.count
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  }

  private calculateTrendData(
    current: number,
    previous: number,
    type: 'price' | 'volume'
  ): TrendData {
    const change = current - previous;
    const changePercent = previous > 0 ? (change / previous) * 100 : 0;
    
    let direction: 'up' | 'down' | 'stable';
    if (changePercent > 2) direction = 'up';
    else if (changePercent < -2) direction = 'down';
    else direction = 'stable';

    let significance: 'high' | 'medium' | 'low';
    if (Math.abs(changePercent) > 20) significance = 'high';
    else if (Math.abs(changePercent) > 10) significance = 'medium';
    else significance = 'low';

    return {
      current,
      previous,
      change,
      changePercent,
      direction,
      significance
    };
  }

  private calculateDemandIndicators(period: { start: Date; end: Date }): DemandIndicator[] {
    const listings = this.getListingsForPeriod(period);
    const indicators: DemandIndicator[] = [];

    // Analyze each component type
    const componentTypes = ['RTX 4090', 'RTX 4080', 'RTX 4070', 'RTX 3080', 'RTX 3070'];
    
    componentTypes.forEach(component => {
      const componentListings = listings.filter(l => 
        l.components?.gpu?.model.includes(component)
      );
      
      if (componentListings.length > 0) {
        // Calculate demand score based on multiple factors
        const avgDaysListed = 5; // Simplified
        const priceVariance = componentListings.length > 1
          ? ss.variance(componentListings.map(l => l.price))
          : 0;
        
        // Lower days + higher price variance = higher demand
        const demandScore = Math.min(100, 
          (100 - avgDaysListed * 10) + (Math.sqrt(priceVariance) / 100)
        );

        indicators.push({
          component,
          demandScore,
          trend: demandScore > 70 ? 'increasing' : demandScore < 30 ? 'decreasing' : 'stable',
          priceImpact: demandScore > 70 ? 5 : 0
        });
      }
    });

    return indicators;
  }

  private identifySeasonalFactors(period: { start: Date; end: Date }): SeasonalFactor[] {
    const factors: SeasonalFactor[] = [];
    const month = period.start.getMonth();

    // Holiday season
    if (month === 10 || month === 11) {
      factors.push({
        name: 'Holiday Shopping',
        impact: 0.3,
        description: 'Increased demand due to holiday gift shopping'
      });
    }

    // Tax season
    if (month === 3 || month === 4) {
      factors.push({
        name: 'Tax Refunds',
        impact: 0.2,
        description: 'Higher purchasing power from tax refunds'
      });
    }

    // Back to school
    if (month === 7 || month === 8) {
      factors.push({
        name: 'Back to School',
        impact: 0.15,
        description: 'Student demand for gaming/productivity systems'
      });
    }

    // New GPU releases (example pattern)
    if (month === 8 || month === 9) {
      factors.push({
        name: 'New Hardware Releases',
        impact: -0.2,
        description: 'Previous gen prices dropping due to new releases'
      });
    }

    return factors;
  }

  private analyzeComponentType(
    listings: Listing[],
    type: 'cpu' | 'gpu'
  ): ComponentMarketData {
    const prices = listings.map(l => l.price);
    const avgPrice = prices.length > 0 ? ss.mean(prices) : 0;
    const medianPrice = prices.length > 0 ? ss.median(prices) : 0;

    // Get top models
    const modelCounts = new Map<string, number[]>();
    listings.forEach(l => {
      const model = type === 'cpu' 
        ? l.components?.cpu?.model 
        : l.components?.gpu?.model;
      
      if (model) {
        const prices = modelCounts.get(model) || [];
        prices.push(l.price);
        modelCounts.set(model, prices);
      }
    });

    const topModels = Array.from(modelCounts.entries())
      .map(([model, prices]) => ({
        model,
        count: prices.length,
        avgPrice: ss.mean(prices),
        trend: 'stable' as const // Simplified
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    // Price history (simplified - last 7 days)
    const priceHistory: PricePoint[] = [];
    for (let i = 6; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      priceHistory.push({
        date,
        price: avgPrice * (1 + (Math.random() - 0.5) * 0.1), // Simulated variation
        volume: listings.length
      });
    }

    return {
      avgPrice,
      medianPrice,
      volume: listings.length,
      topModels,
      priceHistory
    };
  }

  private identifyComponentTrends(listings: Listing[]): ComponentTrend[] {
    // Simplified trend identification
    const trends: ComponentTrend[] = [];

    const gpuModels = ['RTX 4090', 'RTX 4080', 'RTX 4070', 'RTX 3080'];
    
    gpuModels.forEach(model => {
      const modelListings = listings.filter(l => 
        l.components?.gpu?.model.includes(model)
      );
      
      if (modelListings.length > 5) {
        const volumeChange = Math.random() * 40 - 20; // Simulated
        
        trends.push({
          component: model,
          trend: volumeChange > 10 ? 'hot' : volumeChange < -10 ? 'cooling' : 'stable',
          priceDirection: volumeChange > 10 ? 'up' : 'stable',
          volumeChange,
          recommendation: volumeChange > 10 
            ? `High demand for ${model} - act quickly on listings`
            : `Stable market for ${model} - normal pricing applies`
        });
      }
    });

    return trends;
  }

  private identifyPriceMovers(period: { start: Date; end: Date }): PriceMover[] {
    // Simplified - compare with previous period
    const movers: PriceMover[] = [];
    
    const components = [
      { component: 'RTX 4090', previous: 1500, current: 1600 },
      { component: 'RTX 4080', previous: 1200, current: 1150 },
      { component: 'Intel i9-13900K', previous: 550, current: 520 }
    ];

    components.forEach(comp => {
      const changePercent = ((comp.current - comp.previous) / comp.previous) * 100;
      
      if (Math.abs(changePercent) > 5) {
        movers.push({
          component: comp.component,
          previousPrice: comp.previous,
          currentPrice: comp.current,
          changePercent,
          reason: changePercent > 0 
            ? 'Increased demand' 
            : 'New inventory flooding market'
        });
      }
    });

    return movers;
  }

  private identifyMissedOpportunities(
    period: { start: Date; end: Date }
  ): MissedOpportunity[] {
    // Simplified - identify listings that would have been profitable
    const opportunities: MissedOpportunity[] = [];
    const listings = this.getListingsForPeriod(period);

    listings
      .filter(l => l.components?.gpu && l.price < 500)
      .slice(0, 5)
      .forEach(l => {
        opportunities.push({
          listingId: l.id,
          title: l.title,
          price: l.price,
          estimatedROI: Math.round(l.price * 0.3), // 30% estimated
          reason: 'Below market price for GPU system'
        });
      });

    return opportunities;
  }

  private forecastComponentPrices(
    componentAnalysis: ComponentMarketAnalysis,
    trends: MarketTrends
  ): ComponentForecast[] {
    const forecasts: ComponentForecast[] = [];

    // Simplified forecasting
    componentAnalysis.priceMovers.forEach(mover => {
      const trendMultiplier = mover.changePercent > 0 ? 1.05 : 0.95;
      
      forecasts.push({
        component: mover.component,
        currentPrice: mover.currentPrice,
        forecast7Day: Math.round(mover.currentPrice * trendMultiplier),
        forecast30Day: Math.round(mover.currentPrice * Math.pow(trendMultiplier, 4)),
        confidence: 0.7,
        factors: [
          trends.priceChange.direction === 'up' ? 'Overall market uptrend' : 'Market stabilization',
          'Historical price patterns',
          'Component availability'
        ]
      });
    });

    return forecasts;
  }

  private forecastVolumes(trends: MarketTrends): VolumeForecast[] {
    // Simplified volume forecasting
    const platforms = ['facebook', 'craigslist', 'offerup'];
    
    return platforms.map(platform => ({
      platform,
      currentVolume: 100, // Baseline
      forecast7Day: Math.round(100 * (1 + trends.volumeChange.changePercent / 100)),
      trend: trends.volumeChange.direction
    }));
  }

  private getRecommendedActions(
    priceForecasts: ComponentForecast[],
    volumeForecasts: VolumeForecast[]
  ): string[] {
    const actions: string[] = [];

    // Price-based actions
    const risingComponents = priceForecasts.filter(f => f.forecast7Day > f.currentPrice);
    if (risingComponents.length > 0) {
      actions.push(
        `Buy now: ${risingComponents.map(c => c.component).join(', ')} prices expected to rise`
      );
    }

    // Volume-based actions
    const highVolumePlatforms = volumeForecasts.filter(v => v.forecast7Day > v.currentVolume * 1.1);
    if (highVolumePlatforms.length > 0) {
      actions.push(
        `Increase scanning on: ${highVolumePlatforms.map(p => p.platform).join(', ')}`
      );
    }

    // General actions
    actions.push('Update pricing models with latest market data');
    actions.push('Review and adjust automated offer thresholds');

    return actions;
  }

  private calculateForecastConfidence(trends: MarketTrends): number {
    // Base confidence
    let confidence = 0.6;

    // Adjust based on trend stability
    if (trends.priceChange.direction === 'stable') confidence += 0.1;
    if (trends.volumeChange.significance === 'low') confidence += 0.1;

    // Adjust based on seasonal factors
    if (trends.seasonalFactors.length > 0) confidence += 0.1;

    return Math.min(0.9, confidence);
  }

  /**
   * Export report to various formats
   */
  async exportReport(reportId: string, format: 'pdf' | 'html' | 'json' = 'html'): Promise<string> {
    const report = this.reports.get(reportId);
    if (!report) throw new Error('Report not found');

    switch (format) {
      case 'json':
        return JSON.stringify(report, null, 2);
      
      case 'html':
        return this.generateHTMLReport(report);
      
      case 'pdf':
        // In production, use a PDF library
        return this.generateHTMLReport(report);
      
      default:
        throw new Error('Unsupported format');
    }
  }

  /**
   * Generate HTML report
   */
  private generateHTMLReport(report: MarketReport): string {
    return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Market Intelligence Report - ${report.generatedAt.toLocaleDateString()}</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; color: #333; }
    h1, h2, h3 { color: #2196f3; }
    .metric { display: inline-block; margin: 10px 20px; }
    .metric-value { font-size: 24px; font-weight: bold; }
    .metric-label { font-size: 14px; color: #666; }
    .trend-up { color: #4caf50; }
    .trend-down { color: #f44336; }
    .insight { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
    .insight-high { border-left: 4px solid #f44336; }
    .insight-medium { border-left: 4px solid #ff9800; }
    .insight-low { border-left: 4px solid #4caf50; }
    table { border-collapse: collapse; width: 100%; margin: 20px 0; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f5f5f5; }
    .chart { margin: 20px 0; }
    .recommendation { background: #e3f2fd; padding: 10px; margin: 5px 0; border-radius: 3px; }
  </style>
</head>
<body>
  <h1>Market Intelligence Report</h1>
  <p>Period: ${report.period.start.toLocaleDateString()} - ${report.period.end.toLocaleDateString()}</p>
  
  <h2>Executive Summary</h2>
  <div class="metrics">
    <div class="metric">
      <div class="metric-value">$${report.metrics.avgPrice.toFixed(0)}</div>
      <div class="metric-label">Average Price</div>
    </div>
    <div class="metric">
      <div class="metric-value ${report.trends.priceChange.direction === 'up' ? 'trend-up' : 'trend-down'}">
        ${report.trends.priceChange.changePercent > 0 ? '+' : ''}${report.trends.priceChange.changePercent.toFixed(1)}%
      </div>
      <div class="metric-label">Price Change</div>
    </div>
    <div class="metric">
      <div class="metric-value">${report.metrics.totalListings}</div>
      <div class="metric-label">Total Listings</div>
    </div>
    <div class="metric">
      <div class="metric-value">${report.dealAnalysis.avgROI.toFixed(0)}</div>
      <div class="metric-label">Avg ROI</div>
    </div>
  </div>

  <h2>Key Insights</h2>
  ${report.insights.map(insight => `
    <div class="insight insight-${insight.severity}">
      <h3>${insight.title}</h3>
      <p>${insight.description}</p>
      <ul>
        ${insight.actionItems.map(item => `<li>${item}</li>`).join('')}
      </ul>
    </div>
  `).join('')}

  <h2>Market Trends</h2>
  <h3>Price Distribution</h3>
  <table>
    <tr>
      <th>Price Range</th>
      <th>Count</th>
      <th>Percentage</th>
    </tr>
    ${report.metrics.priceDistribution.map(segment => `
      <tr>
        <td>${segment.range}</td>
        <td>${segment.count}</td>
        <td>${segment.percentage.toFixed(1)}%</td>
      </tr>
    `).join('')}
  </table>

  <h3>Top Components</h3>
  <table>
    <tr>
      <th>Component</th>
      <th>Count</th>
      <th>Avg Price</th>
    </tr>
    ${report.metrics.topComponents.slice(0, 10).map(comp => `
      <tr>
        <td>${comp.name}</td>
        <td>${comp.count}</td>
        <td>$${comp.avgPrice.toFixed(0)}</td>
      </tr>
    `).join('')}
  </table>

  <h2>Recommendations</h2>
  ${report.recommendations.map(rec => `
    <div class="recommendation">${rec}</div>
  `).join('')}

  <h2>Forecast</h2>
  ${report.forecastAnalysis ? `
    <p>Forecast Confidence: ${(report.forecastAnalysis.confidence * 100).toFixed(0)}%</p>
    <h3>Component Price Forecasts</h3>
    <table>
      <tr>
        <th>Component</th>
        <th>Current</th>
        <th>7-Day Forecast</th>
        <th>30-Day Forecast</th>
      </tr>
      ${report.forecastAnalysis.priceForecasts.map(forecast => `
        <tr>
          <td>${forecast.component}</td>
          <td>$${forecast.currentPrice}</td>
          <td>$${forecast.forecast7Day}</td>
          <td>$${forecast.forecast30Day}</td>
        </tr>
      `).join('')}
    </table>
  ` : ''}

  <p style="margin-top: 40px; font-size: 12px; color: #666;">
    Generated on ${report.generatedAt.toLocaleString()} by Gaming PC Arbitrage Extension
  </p>
</body>
</html>
    `;
  }

  /**
   * Schedule automated reports
   */
  async scheduleReport(
    frequency: 'daily' | 'weekly' | 'monthly',
    deliveryMethod: 'email' | 'notification' | 'download'
  ): Promise<void> {
    // Store schedule in chrome.storage
    const schedule = {
      frequency,
      deliveryMethod,
      nextRun: this.getNextRunDate(frequency),
      enabled: true
    };

    await chrome.storage.local.set({ reportSchedule: schedule });

    // Set up alarm for next run
    chrome.alarms.create('marketReport', {
      when: schedule.nextRun.getTime()
    });
  }

  private getNextRunDate(frequency: 'daily' | 'weekly' | 'monthly'): Date {
    const next = new Date();
    
    switch (frequency) {
      case 'daily':
        next.setDate(next.getDate() + 1);
        next.setHours(8, 0, 0, 0); // 8 AM
        break;
      case 'weekly':
        next.setDate(next.getDate() + (7 - next.getDay() + 1) % 7); // Next Monday
        next.setHours(8, 0, 0, 0);
        break;
      case 'monthly':
        next.setMonth(next.getMonth() + 1);
        next.setDate(1);
        next.setHours(8, 0, 0, 0);
        break;
    }

    return next;
  }

  /**
   * Get all reports
   */
  getAllReports(): MarketReport[] {
    return Array.from(this.reports.values())
      .sort((a, b) => b.generatedAt.getTime() - a.generatedAt.getTime());
  }

  /**
   * Get report by ID
   */
  getReport(reportId: string): MarketReport | undefined {
    return this.reports.get(reportId);
  }

  /**
   * Persistence
   */
  private async loadReports(): Promise<void> {
    const { [this.STORAGE_KEY]: saved } = await chrome.storage.local.get(this.STORAGE_KEY);
    if (saved) {
      Object.entries(saved).forEach(([id, data]: [string, any]) => {
        this.reports.set(id, {
          ...data,
          period: {
            start: new Date(data.period.start),
            end: new Date(data.period.end)
          },
          generatedAt: new Date(data.generatedAt)
        });
      });
    }
  }

  private async saveReports(): Promise<void> {
    const data: Record<string, any> = {};
    this.reports.forEach((report, id) => {
      data[id] = {
        ...report,
        period: {
          start: report.period.start.toISOString(),
          end: report.period.end.toISOString()
        },
        generatedAt: report.generatedAt.toISOString()
      };
    });
    await chrome.storage.local.set({ [this.STORAGE_KEY]: data });
  }
}

// Export singleton instance
export const marketIntelligence = new MarketIntelligence();