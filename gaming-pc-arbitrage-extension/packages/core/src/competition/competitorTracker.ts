/**
 * Enhanced Competitor Tracking System
 * Real-time monitoring and analysis of competitor activities
 */

import { Listing, Deal } from '../types';
import { db } from '../../extension/lib/db';

export interface Competitor {
  id: string;
  name: string;
  platform: string;
  profileUrl?: string;
  metrics: {
    totalListings: number;
    activeListings: number;
    avgPrice: number;
    avgResponseTime?: number;
    salesVolume?: number;
    priceChangeFrequency: number;
    lastSeen: Date;
  };
  listings: CompetitorListing[];
  priceHistory: PricePoint[];
  tags: string[];
  notes?: string;
  threatLevel: 'low' | 'medium' | 'high';
  createdAt: Date;
  updatedAt: Date;
}

export interface CompetitorListing {
  id: string;
  url: string;
  title: string;
  price: number;
  components?: any;
  listedAt: Date;
  soldAt?: Date;
  daysToSell?: number;
  priceChanges: PriceChange[];
}

export interface PriceChange {
  date: Date;
  oldPrice: number;
  newPrice: number;
  percentChange: number;
}

export interface PricePoint {
  date: Date;
  avgPrice: number;
  minPrice: number;
  maxPrice: number;
  listingCount: number;
}

export interface CompetitorInsight {
  type: 'pricing' | 'inventory' | 'strategy' | 'opportunity';
  severity: 'info' | 'warning' | 'alert';
  title: string;
  description: string;
  actionable: boolean;
  suggestedAction?: string;
  data?: any;
}

export class EnhancedCompetitorTracker {
  private competitors: Map<string, Competitor> = new Map();
  private monitoringInterval: number | null = null;
  private readonly UPDATE_INTERVAL = 30 * 60 * 1000; // 30 minutes

  /**
   * Initialize tracker and load saved data
   */
  async initialize(): Promise<void> {
    await this.loadCompetitors();
    this.startMonitoring();
  }

  /**
   * Add or update a competitor
   */
  async trackCompetitor(
    sellerId: string,
    sellerName: string,
    platform: string,
    listing?: Listing
  ): Promise<Competitor> {
    let competitor = this.competitors.get(sellerId);

    if (!competitor) {
      competitor = {
        id: sellerId,
        name: sellerName,
        platform,
        profileUrl: this.generateProfileUrl(platform, sellerId),
        metrics: {
          totalListings: 0,
          activeListings: 0,
          avgPrice: 0,
          priceChangeFrequency: 0,
          lastSeen: new Date()
        },
        listings: [],
        priceHistory: [],
        tags: [],
        threatLevel: 'low',
        createdAt: new Date(),
        updatedAt: new Date()
      };
    }

    // Update metrics
    competitor.metrics.lastSeen = new Date();
    competitor.updatedAt = new Date();

    if (listing) {
      await this.addListingToCompetitor(competitor, listing);
    }

    // Calculate threat level
    competitor.threatLevel = this.calculateThreatLevel(competitor);

    this.competitors.set(sellerId, competitor);
    await this.saveCompetitors();

    return competitor;
  }

  /**
   * Add listing to competitor's history
   */
  private async addListingToCompetitor(
    competitor: Competitor,
    listing: Listing
  ): Promise<void> {
    // Check if listing already exists
    const existingIndex = competitor.listings.findIndex(
      l => l.id === listing.id || l.url === listing.url
    );

    if (existingIndex >= 0) {
      // Update existing listing
      const existing = competitor.listings[existingIndex];
      
      // Track price changes
      if (existing.price !== listing.price) {
        existing.priceChanges.push({
          date: new Date(),
          oldPrice: existing.price,
          newPrice: listing.price,
          percentChange: ((listing.price - existing.price) / existing.price) * 100
        });
        existing.price = listing.price;
      }

      // Check if sold
      if (listing.status === 'sold' && !existing.soldAt) {
        existing.soldAt = new Date();
        existing.daysToSell = Math.floor(
          (existing.soldAt.getTime() - existing.listedAt.getTime()) / 
          (1000 * 60 * 60 * 24)
        );
      }
    } else {
      // Add new listing
      competitor.listings.push({
        id: listing.id,
        url: listing.url,
        title: listing.title,
        price: listing.price,
        components: listing.components,
        listedAt: listing.postedAt,
        priceChanges: []
      });
    }

    // Update metrics
    this.updateCompetitorMetrics(competitor);
  }

  /**
   * Update competitor metrics based on listings
   */
  private updateCompetitorMetrics(competitor: Competitor): void {
    const activeListings = competitor.listings.filter(l => !l.soldAt);
    const soldListings = competitor.listings.filter(l => l.soldAt);

    competitor.metrics.totalListings = competitor.listings.length;
    competitor.metrics.activeListings = activeListings.length;

    // Calculate average price
    if (activeListings.length > 0) {
      const totalPrice = activeListings.reduce((sum, l) => sum + l.price, 0);
      competitor.metrics.avgPrice = Math.round(totalPrice / activeListings.length);
    }

    // Calculate sales volume
    competitor.metrics.salesVolume = soldListings.length;

    // Calculate average response time (days to sell)
    if (soldListings.length > 0) {
      const totalDays = soldListings
        .filter(l => l.daysToSell !== undefined)
        .reduce((sum, l) => sum + l.daysToSell!, 0);
      competitor.metrics.avgResponseTime = 
        Math.round(totalDays / soldListings.length);
    }

    // Calculate price change frequency
    const totalPriceChanges = competitor.listings.reduce(
      (sum, l) => sum + l.priceChanges.length,
      0
    );
    competitor.metrics.priceChangeFrequency = 
      competitor.listings.length > 0 
        ? totalPriceChanges / competitor.listings.length
        : 0;

    // Update price history
    this.updatePriceHistory(competitor);
  }

  /**
   * Update competitor's price history
   */
  private updatePriceHistory(competitor: Competitor): void {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Check if we already have today's data
    const todayIndex = competitor.priceHistory.findIndex(
      p => p.date.getTime() === today.getTime()
    );

    const activeListings = competitor.listings.filter(l => !l.soldAt);
    
    if (activeListings.length === 0) return;

    const prices = activeListings.map(l => l.price);
    const pricePoint: PricePoint = {
      date: today,
      avgPrice: Math.round(prices.reduce((a, b) => a + b) / prices.length),
      minPrice: Math.min(...prices),
      maxPrice: Math.max(...prices),
      listingCount: prices.length
    };

    if (todayIndex >= 0) {
      competitor.priceHistory[todayIndex] = pricePoint;
    } else {
      competitor.priceHistory.push(pricePoint);
    }

    // Keep only last 90 days
    const ninetyDaysAgo = new Date();
    ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);
    competitor.priceHistory = competitor.priceHistory.filter(
      p => p.date >= ninetyDaysAgo
    );
  }

  /**
   * Calculate competitor threat level
   */
  private calculateThreatLevel(competitor: Competitor): 'low' | 'medium' | 'high' {
    let score = 0;

    // Volume factor
    if (competitor.metrics.activeListings > 10) score += 2;
    else if (competitor.metrics.activeListings > 5) score += 1;

    // Sales velocity factor
    if (competitor.metrics.avgResponseTime && competitor.metrics.avgResponseTime < 7) {
      score += 2;
    } else if (competitor.metrics.avgResponseTime && competitor.metrics.avgResponseTime < 14) {
      score += 1;
    }

    // Price competitiveness factor
    if (competitor.metrics.priceChangeFrequency > 2) score += 2;
    else if (competitor.metrics.priceChangeFrequency > 1) score += 1;

    // Activity factor
    const daysSinceLastSeen = 
      (new Date().getTime() - competitor.metrics.lastSeen.getTime()) / 
      (1000 * 60 * 60 * 24);
    if (daysSinceLastSeen < 1) score += 2;
    else if (daysSinceLastSeen < 7) score += 1;

    if (score >= 6) return 'high';
    if (score >= 3) return 'medium';
    return 'low';
  }

  /**
   * Get insights about competitors
   */
  async getCompetitorInsights(): Promise<CompetitorInsight[]> {
    const insights: CompetitorInsight[] = [];
    const competitors = Array.from(this.competitors.values());

    // Pricing insights
    const avgMarketPrice = this.calculateMarketAverage();
    competitors.forEach(competitor => {
      if (competitor.metrics.avgPrice < avgMarketPrice * 0.8) {
        insights.push({
          type: 'pricing',
          severity: 'alert',
          title: `${competitor.name} is undercutting market`,
          description: `Average price ${Math.round((1 - competitor.metrics.avgPrice / avgMarketPrice) * 100)}% below market`,
          actionable: true,
          suggestedAction: 'Consider adjusting your pricing strategy',
          data: { competitor, avgMarketPrice }
        });
      }
    });

    // Inventory insights
    const highVolumeCompetitors = competitors.filter(
      c => c.metrics.activeListings > 8
    );
    if (highVolumeCompetitors.length > 0) {
      insights.push({
        type: 'inventory',
        severity: 'warning',
        title: 'High-volume competitors detected',
        description: `${highVolumeCompetitors.length} competitors with 8+ active listings`,
        actionable: true,
        suggestedAction: 'Monitor their pricing and adjust strategy',
        data: { competitors: highVolumeCompetitors }
      });
    }

    // Strategy insights
    const aggressivePricers = competitors.filter(
      c => c.metrics.priceChangeFrequency > 2
    );
    if (aggressivePricers.length > 0) {
      insights.push({
        type: 'strategy',
        severity: 'warning',
        title: 'Aggressive pricing strategies detected',
        description: `${aggressivePricers.length} competitors frequently adjusting prices`,
        actionable: true,
        suggestedAction: 'Consider dynamic pricing or price matching',
        data: { competitors: aggressivePricers }
      });
    }

    // Opportunity insights
    const inactiveCompetitors = competitors.filter(c => {
      const daysSinceLastSeen = 
        (new Date().getTime() - c.metrics.lastSeen.getTime()) / 
        (1000 * 60 * 60 * 24);
      return daysSinceLastSeen > 14;
    });
    if (inactiveCompetitors.length > 0) {
      insights.push({
        type: 'opportunity',
        severity: 'info',
        title: 'Competitor activity decreased',
        description: `${inactiveCompetitors.length} competitors inactive for 14+ days`,
        actionable: true,
        suggestedAction: 'Good time to capture market share',
        data: { competitors: inactiveCompetitors }
      });
    }

    return insights;
  }

  /**
   * Get competitor statistics
   */
  getCompetitorStats(): {
    totalCompetitors: number;
    avgListingsPerCompetitor: number;
    marketShare: Map<string, number>;
    topCompetitors: Competitor[];
  } {
    const competitors = Array.from(this.competitors.values());
    const totalListings = competitors.reduce(
      (sum, c) => sum + c.metrics.activeListings,
      0
    );

    // Calculate market share
    const marketShare = new Map<string, number>();
    competitors.forEach(c => {
      const share = totalListings > 0 
        ? (c.metrics.activeListings / totalListings) * 100 
        : 0;
      marketShare.set(c.id, share);
    });

    return {
      totalCompetitors: competitors.length,
      avgListingsPerCompetitor: 
        competitors.length > 0 
          ? totalListings / competitors.length 
          : 0,
      marketShare,
      topCompetitors: competitors
        .sort((a, b) => b.metrics.activeListings - a.metrics.activeListings)
        .slice(0, 5)
    };
  }

  /**
   * Monitor competitor for specific behaviors
   */
  async watchCompetitor(
    competitorId: string,
    watchConfig: {
      priceDrops?: boolean;
      newListings?: boolean;
      soldItems?: boolean;
      priceThreshold?: number;
    }
  ): Promise<void> {
    const competitor = this.competitors.get(competitorId);
    if (!competitor) return;

    // Store watch configuration
    await chrome.storage.local.get('competitorWatches').then(result => {
      const watches = result.competitorWatches || {};
      watches[competitorId] = watchConfig;
      chrome.storage.local.set({ competitorWatches: watches });
    });
  }

  /**
   * Start automated monitoring
   */
  private startMonitoring(): void {
    if (this.monitoringInterval) return;

    this.monitoringInterval = window.setInterval(
      () => this.performMonitoringCycle(),
      this.UPDATE_INTERVAL
    );

    // Also run immediately
    this.performMonitoringCycle();
  }

  /**
   * Perform monitoring cycle
   */
  private async performMonitoringCycle(): Promise<void> {
    console.log('Running competitor monitoring cycle');

    // Get watch configurations
    const { competitorWatches = {} } = await chrome.storage.local.get('competitorWatches');

    // Check each watched competitor
    for (const [competitorId, config] of Object.entries(competitorWatches)) {
      const competitor = this.competitors.get(competitorId);
      if (!competitor) continue;

      // Simulate checking for updates (in production, would fetch real data)
      await this.checkCompetitorUpdates(competitor, config as any);
    }

    // Generate insights
    const insights = await this.getCompetitorInsights();
    
    // Notify about important insights
    const criticalInsights = insights.filter(i => i.severity === 'alert');
    if (criticalInsights.length > 0) {
      chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('icons/icon-48.png'),
        title: 'Competitor Alert',
        message: criticalInsights[0].title
      });
    }
  }

  /**
   * Check for competitor updates
   */
  private async checkCompetitorUpdates(
    competitor: Competitor,
    watchConfig: any
  ): Promise<void> {
    // This would fetch real data in production
    // For now, we'll simulate some changes

    if (watchConfig.priceDrops) {
      // Check for price drops
      competitor.listings.forEach(listing => {
        if (listing.priceChanges.length > 0) {
          const lastChange = listing.priceChanges[listing.priceChanges.length - 1];
          if (lastChange.percentChange < -10) {
            // Significant price drop detected
            chrome.notifications.create({
              type: 'basic',
              iconUrl: chrome.runtime.getURL('icons/icon-48.png'),
              title: 'Competitor Price Drop',
              message: `${competitor.name} dropped price by ${Math.abs(lastChange.percentChange).toFixed(0)}%`
            });
          }
        }
      });
    }
  }

  /**
   * Helper methods
   */
  private calculateMarketAverage(): number {
    const allPrices: number[] = [];
    this.competitors.forEach(c => {
      c.listings
        .filter(l => !l.soldAt)
        .forEach(l => allPrices.push(l.price));
    });
    
    return allPrices.length > 0
      ? allPrices.reduce((a, b) => a + b) / allPrices.length
      : 0;
  }

  private generateProfileUrl(platform: string, sellerId: string): string {
    switch (platform.toLowerCase()) {
      case 'facebook':
        return `https://www.facebook.com/marketplace/profile/${sellerId}`;
      case 'offerup':
        return `https://offerup.com/p/${sellerId}`;
      case 'craigslist':
        return `https://craigslist.org/contact/${sellerId}`;
      default:
        return '';
    }
  }

  /**
   * Persistence methods
   */
  private async loadCompetitors(): Promise<void> {
    const { competitors = {} } = await chrome.storage.local.get('competitors');
    Object.entries(competitors).forEach(([id, data]) => {
      this.competitors.set(id, this.deserializeCompetitor(data as any));
    });
  }

  private async saveCompetitors(): Promise<void> {
    const data: Record<string, any> = {};
    this.competitors.forEach((competitor, id) => {
      data[id] = this.serializeCompetitor(competitor);
    });
    await chrome.storage.local.set({ competitors: data });
  }

  private serializeCompetitor(competitor: Competitor): any {
    return {
      ...competitor,
      metrics: {
        ...competitor.metrics,
        lastSeen: competitor.metrics.lastSeen.toISOString()
      },
      priceHistory: competitor.priceHistory.map(p => ({
        ...p,
        date: p.date.toISOString()
      })),
      listings: competitor.listings.map(l => ({
        ...l,
        listedAt: l.listedAt.toISOString(),
        soldAt: l.soldAt?.toISOString(),
        priceChanges: l.priceChanges.map(pc => ({
          ...pc,
          date: pc.date.toISOString()
        }))
      })),
      createdAt: competitor.createdAt.toISOString(),
      updatedAt: competitor.updatedAt.toISOString()
    };
  }

  private deserializeCompetitor(data: any): Competitor {
    return {
      ...data,
      metrics: {
        ...data.metrics,
        lastSeen: new Date(data.metrics.lastSeen)
      },
      priceHistory: data.priceHistory.map((p: any) => ({
        ...p,
        date: new Date(p.date)
      })),
      listings: data.listings.map((l: any) => ({
        ...l,
        listedAt: new Date(l.listedAt),
        soldAt: l.soldAt ? new Date(l.soldAt) : undefined,
        priceChanges: l.priceChanges.map((pc: any) => ({
          ...pc,
          date: new Date(pc.date)
        }))
      })),
      createdAt: new Date(data.createdAt),
      updatedAt: new Date(data.updatedAt)
    };
  }

  /**
   * Get all competitors
   */
  getAllCompetitors(): Competitor[] {
    return Array.from(this.competitors.values());
  }

  /**
   * Get competitor by ID
   */
  getCompetitor(id: string): Competitor | undefined {
    return this.competitors.get(id);
  }

  /**
   * Search competitors
   */
  searchCompetitors(query: string): Competitor[] {
    const queryLower = query.toLowerCase();
    return Array.from(this.competitors.values()).filter(
      c => c.name.toLowerCase().includes(queryLower) ||
           c.platform.toLowerCase().includes(queryLower) ||
           c.tags.some(t => t.toLowerCase().includes(queryLower))
    );
  }

  /**
   * Stop monitoring
   */
  stopMonitoring(): void {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
  }
}

// Export singleton instance
export const competitorTracker = new EnhancedCompetitorTracker();