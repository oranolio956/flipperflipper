/**
 * Geographic Arbitrage Module
 * Enables multi-region price comparison and arbitrage opportunities
 */

export interface Region {
  id: string;
  name: string;
  code: string; // e.g., 'US-CA', 'US-TX'
  type: 'state' | 'metro' | 'zip';
  coordinates?: {
    lat: number;
    lng: number;
  };
  population?: number;
  medianIncome?: number;
  costOfLivingIndex?: number;
}

export interface RegionPriceData {
  regionId: string;
  category: string;
  averagePrice: number;
  medianPrice: number;
  priceRange: {
    min: number;
    max: number;
    percentile25: number;
    percentile75: number;
  };
  volume: number; // Number of listings
  lastUpdated: Date;
  trend: 'rising' | 'stable' | 'falling';
  trendPercentage: number; // % change over period
}

export interface ArbitrageOpportunity {
  id: string;
  sourceRegion: Region;
  targetRegion: Region;
  category: string;
  priceDifference: number;
  percentageDifference: number;
  estimatedProfit: number;
  transportCost: number;
  risk: 'low' | 'medium' | 'high';
  confidence: number;
  reasons: string[];
  expiresAt: Date;
}

export interface TransportCostEstimate {
  method: 'driving' | 'shipping' | 'flying';
  distance: number; // miles
  duration: number; // hours
  cost: number;
  carbonFootprint?: number; // kg CO2
}

export interface RegionMarketHealth {
  region: Region;
  supplyDemandRatio: number;
  averageDaysOnMarket: number;
  priceVolatility: number;
  competitionLevel: 'low' | 'medium' | 'high';
  bestCategories: string[];
  worstCategories: string[];
}

export class GeographicArbitrageAnalyzer {
  private regions: Map<string, Region> = new Map();
  private priceData: Map<string, RegionPriceData[]> = new Map();
  private opportunities: Map<string, ArbitrageOpportunity> = new Map();
  private readonly API_KEY = process.env.GOOGLE_MAPS_API_KEY || '';
  
  constructor() {
    this.initializeRegions();
    this.loadHistoricalData();
  }

  /**
   * Initialize common regions
   */
  private initializeRegions(): void {
    const commonRegions: Region[] = [
      // Major Tech Hubs (usually higher prices)
      {
        id: 'sf_bay_area',
        name: 'San Francisco Bay Area',
        code: 'US-CA-SF',
        type: 'metro',
        coordinates: { lat: 37.7749, lng: -122.4194 },
        population: 7700000,
        medianIncome: 136000,
        costOfLivingIndex: 180
      },
      {
        id: 'seattle_metro',
        name: 'Seattle Metro',
        code: 'US-WA-SEA',
        type: 'metro',
        coordinates: { lat: 47.6062, lng: -122.3321 },
        population: 4000000,
        medianIncome: 102000,
        costOfLivingIndex: 140
      },
      {
        id: 'nyc_metro',
        name: 'New York City Metro',
        code: 'US-NY-NYC',
        type: 'metro',
        coordinates: { lat: 40.7128, lng: -74.0060 },
        population: 20000000,
        medianIncome: 89000,
        costOfLivingIndex: 170
      },
      
      // Mid-tier Cities (balanced prices)
      {
        id: 'austin_metro',
        name: 'Austin Metro',
        code: 'US-TX-AUS',
        type: 'metro',
        coordinates: { lat: 30.2672, lng: -97.7431 },
        population: 2300000,
        medianIncome: 80000,
        costOfLivingIndex: 115
      },
      {
        id: 'denver_metro',
        name: 'Denver Metro',
        code: 'US-CO-DEN',
        type: 'metro',
        coordinates: { lat: 39.7392, lng: -104.9903 },
        population: 3000000,
        medianIncome: 77000,
        costOfLivingIndex: 110
      },
      
      // Lower Cost Areas (usually lower prices)
      {
        id: 'phoenix_metro',
        name: 'Phoenix Metro',
        code: 'US-AZ-PHX',
        type: 'metro',
        coordinates: { lat: 33.4484, lng: -112.0740 },
        population: 5000000,
        medianIncome: 65000,
        costOfLivingIndex: 95
      },
      {
        id: 'houston_metro',
        name: 'Houston Metro',
        code: 'US-TX-HOU',
        type: 'metro',
        coordinates: { lat: 29.7604, lng: -95.3698 },
        population: 7100000,
        medianIncome: 63000,
        costOfLivingIndex: 90
      },
      {
        id: 'atlanta_metro',
        name: 'Atlanta Metro',
        code: 'US-GA-ATL',
        type: 'metro',
        coordinates: { lat: 33.7490, lng: -84.3880 },
        population: 6100000,
        medianIncome: 71000,
        costOfLivingIndex: 95
      }
    ];

    commonRegions.forEach(region => {
      this.regions.set(region.id, region);
    });
  }

  /**
   * Analyze price differences between regions
   */
  async analyzeArbitrage(
    category: string = 'all',
    minPriceDifference: number = 100,
    maxDistance: number = 500 // miles
  ): Promise<ArbitrageOpportunity[]> {
    const opportunities: ArbitrageOpportunity[] = [];
    const regions = Array.from(this.regions.values());

    // Compare all region pairs
    for (let i = 0; i < regions.length; i++) {
      for (let j = i + 1; j < regions.length; j++) {
        const source = regions[i];
        const target = regions[j];

        // Get price data for both regions
        const sourcePrices = await this.getRegionPrices(source.id, category);
        const targetPrices = await this.getRegionPrices(target.id, category);

        if (!sourcePrices || !targetPrices) continue;

        // Calculate potential arbitrage
        const priceDiff = targetPrices.averagePrice - sourcePrices.averagePrice;
        const percentDiff = (priceDiff / sourcePrices.averagePrice) * 100;

        // Check if opportunity exists
        if (Math.abs(priceDiff) >= minPriceDifference) {
          const distance = this.calculateDistance(source, target);
          
          if (distance <= maxDistance || maxDistance === 0) {
            const transport = await this.estimateTransportCost(source, target, 'driving');
            const estimatedProfit = Math.abs(priceDiff) - transport.cost;

            if (estimatedProfit > 50) { // Minimum $50 profit
              const opportunity: ArbitrageOpportunity = {
                id: `arb_${source.id}_${target.id}_${Date.now()}`,
                sourceRegion: priceDiff > 0 ? source : target,
                targetRegion: priceDiff > 0 ? target : source,
                category,
                priceDifference: Math.abs(priceDiff),
                percentageDifference: Math.abs(percentDiff),
                estimatedProfit,
                transportCost: transport.cost,
                risk: this.assessRisk(percentDiff, distance),
                confidence: this.calculateConfidence(sourcePrices, targetPrices),
                reasons: this.generateReasons(source, target, priceDiff),
                expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days
              };

              opportunities.push(opportunity);
              this.opportunities.set(opportunity.id, opportunity);
            }
          }
        }
      }
    }

    // Sort by profit potential
    opportunities.sort((a, b) => b.estimatedProfit - a.estimatedProfit);

    return opportunities;
  }

  /**
   * Get price data for a region
   */
  async getRegionPrices(regionId: string, category: string): Promise<RegionPriceData | null> {
    const cacheKey = `${regionId}_${category}`;
    const cached = this.priceData.get(cacheKey);

    // Return cached data if fresh (less than 24 hours old)
    if (cached && cached.length > 0) {
      const latest = cached[cached.length - 1];
      if (Date.now() - latest.lastUpdated.getTime() < 24 * 60 * 60 * 1000) {
        return latest;
      }
    }

    // Fetch new data (in production, would query regional marketplaces)
    const priceData = await this.fetchRegionPrices(regionId, category);
    
    if (priceData) {
      const existing = this.priceData.get(cacheKey) || [];
      existing.push(priceData);
      this.priceData.set(cacheKey, existing);
    }

    return priceData;
  }

  /**
   * Fetch current prices for a region
   */
  private async fetchRegionPrices(regionId: string, category: string): Promise<RegionPriceData | null> {
    const region = this.regions.get(regionId);
    if (!region) return null;

    // Simulate price data based on cost of living index
    const basePrice = category === 'gpu' ? 800 : 
                     category === 'cpu' ? 400 :
                     category === 'full-system' ? 1200 : 1000;

    const adjustmentFactor = (region.costOfLivingIndex || 100) / 100;
    const averagePrice = basePrice * adjustmentFactor;

    // Add some variance based on supply/demand
    const variance = 0.15; // 15% variance
    const min = averagePrice * (1 - variance);
    const max = averagePrice * (1 + variance);

    return {
      regionId,
      category,
      averagePrice,
      medianPrice: averagePrice * 0.95,
      priceRange: {
        min,
        max,
        percentile25: averagePrice * 0.85,
        percentile75: averagePrice * 1.1
      },
      volume: Math.floor(Math.random() * 100) + 50,
      lastUpdated: new Date(),
      trend: Math.random() > 0.5 ? 'rising' : Math.random() > 0.5 ? 'stable' : 'falling',
      trendPercentage: (Math.random() - 0.5) * 10
    };
  }

  /**
   * Calculate distance between regions
   */
  private calculateDistance(region1: Region, region2: Region): number {
    if (!region1.coordinates || !region2.coordinates) return Infinity;

    const R = 3959; // Earth radius in miles
    const lat1Rad = region1.coordinates.lat * Math.PI / 180;
    const lat2Rad = region2.coordinates.lat * Math.PI / 180;
    const deltaLat = (region2.coordinates.lat - region1.coordinates.lat) * Math.PI / 180;
    const deltaLng = (region2.coordinates.lng - region1.coordinates.lng) * Math.PI / 180;

    const a = Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) +
              Math.cos(lat1Rad) * Math.cos(lat2Rad) *
              Math.sin(deltaLng / 2) * Math.sin(deltaLng / 2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    
    return R * c;
  }

  /**
   * Estimate transport cost between regions
   */
  async estimateTransportCost(
    source: Region,
    target: Region,
    method: TransportCostEstimate['method'] = 'driving'
  ): Promise<TransportCostEstimate> {
    const distance = this.calculateDistance(source, target);

    switch (method) {
      case 'driving':
        // Assume $0.65 per mile (gas + wear)
        const drivingCost = distance * 0.65;
        const drivingTime = distance / 60; // 60 mph average
        
        return {
          method: 'driving',
          distance,
          duration: drivingTime,
          cost: drivingCost,
          carbonFootprint: distance * 0.404 // kg CO2 per mile
        };

      case 'shipping':
        // Base rate + per mile
        const shippingBase = 50;
        const shippingPerMile = 0.25;
        const shippingCost = shippingBase + (distance * shippingPerMile);
        
        return {
          method: 'shipping',
          distance,
          duration: 72, // 3 days average
          cost: shippingCost,
          carbonFootprint: distance * 0.1 // More efficient than driving
        };

      case 'flying':
        // Only for high-value items
        const flightCost = 200 + (distance * 0.15);
        const flightTime = 4 + (distance / 500); // Base time + flight
        
        return {
          method: 'flying',
          distance,
          duration: flightTime,
          cost: flightCost,
          carbonFootprint: distance * 0.9 // High carbon cost
        };

      default:
        return this.estimateTransportCost(source, target, 'driving');
    }
  }

  /**
   * Assess risk level of arbitrage opportunity
   */
  private assessRisk(
    priceDifferencePercent: number,
    distance: number
  ): ArbitrageOpportunity['risk'] {
    let riskScore = 0;

    // Price volatility risk
    if (Math.abs(priceDifferencePercent) < 10) riskScore += 2;
    else if (Math.abs(priceDifferencePercent) < 20) riskScore += 1;

    // Distance risk
    if (distance > 300) riskScore += 2;
    else if (distance > 150) riskScore += 1;

    // Time risk (prices may change during transport)
    if (distance > 500) riskScore += 1;

    if (riskScore >= 4) return 'high';
    if (riskScore >= 2) return 'medium';
    return 'low';
  }

  /**
   * Calculate confidence in arbitrage opportunity
   */
  private calculateConfidence(
    sourcePrices: RegionPriceData,
    targetPrices: RegionPriceData
  ): number {
    let confidence = 0.5;

    // Volume factor
    if (sourcePrices.volume > 50 && targetPrices.volume > 50) {
      confidence += 0.2;
    }

    // Trend alignment
    if (sourcePrices.trend === 'stable' && targetPrices.trend === 'stable') {
      confidence += 0.15;
    }

    // Recent data
    const sourceAge = Date.now() - sourcePrices.lastUpdated.getTime();
    const targetAge = Date.now() - targetPrices.lastUpdated.getTime();
    
    if (sourceAge < 3600000 && targetAge < 3600000) { // Less than 1 hour old
      confidence += 0.15;
    }

    return Math.min(confidence, 0.95);
  }

  /**
   * Generate reasons for arbitrage opportunity
   */
  private generateReasons(
    source: Region,
    target: Region,
    priceDifference: number
  ): string[] {
    const reasons: string[] = [];

    // Income disparity
    if (source.medianIncome && target.medianIncome) {
      const incomeDiff = target.medianIncome - source.medianIncome;
      if (priceDifference > 0 && incomeDiff > 20000) {
        reasons.push(`${target.name} has ${((incomeDiff / source.medianIncome) * 100).toFixed(0)}% higher median income`);
      }
    }

    // Cost of living
    if (source.costOfLivingIndex && target.costOfLivingIndex) {
      const colDiff = target.costOfLivingIndex - source.costOfLivingIndex;
      if (Math.abs(colDiff) > 20) {
        reasons.push(`${Math.abs(colDiff)}% cost of living difference between regions`);
      }
    }

    // Tech hub premium
    const techHubs = ['sf_bay_area', 'seattle_metro', 'austin_metro'];
    if (techHubs.includes(target.id) && !techHubs.includes(source.id)) {
      reasons.push(`${target.name} is a major tech hub with higher demand`);
    }

    // Population density
    if (source.population && target.population) {
      if (target.population > source.population * 1.5) {
        reasons.push(`${target.name} has larger market with more buyers`);
      }
    }

    return reasons;
  }

  /**
   * Get market health analysis for a region
   */
  async analyzeRegionHealth(regionId: string): Promise<RegionMarketHealth | null> {
    const region = this.regions.get(regionId);
    if (!region) return null;

    // Get price data for all categories
    const categories = ['gpu', 'cpu', 'full-system', 'peripherals'];
    const categoryAnalysis: Array<{ category: string; health: number }> = [];

    for (const category of categories) {
      const priceData = await this.getRegionPrices(regionId, category);
      if (priceData) {
        // Calculate health score based on volume and trend
        let healthScore = 50;
        
        if (priceData.volume > 75) healthScore += 20;
        else if (priceData.volume > 50) healthScore += 10;
        
        if (priceData.trend === 'rising') healthScore += 15;
        else if (priceData.trend === 'falling') healthScore -= 15;
        
        categoryAnalysis.push({ category, health: healthScore });
      }
    }

    // Sort by health score
    categoryAnalysis.sort((a, b) => b.health - a.health);

    // Calculate overall metrics
    const avgVolume = categoryAnalysis.reduce((sum, cat) => sum + cat.health, 0) / categoryAnalysis.length;
    
    return {
      region,
      supplyDemandRatio: Math.random() * 2 + 0.5, // Mock data
      averageDaysOnMarket: Math.floor(Math.random() * 14) + 7,
      priceVolatility: Math.random() * 0.3,
      competitionLevel: avgVolume > 70 ? 'high' : avgVolume > 50 ? 'medium' : 'low',
      bestCategories: categoryAnalysis.slice(0, 2).map(c => c.category),
      worstCategories: categoryAnalysis.slice(-2).map(c => c.category)
    };
  }

  /**
   * Find best regions for a specific category
   */
  async findBestRegions(
    category: string,
    criteria: 'lowest_price' | 'highest_volume' | 'best_trend' = 'lowest_price'
  ): Promise<Array<{ region: Region; score: number; data: RegionPriceData }>> {
    const results: Array<{ region: Region; score: number; data: RegionPriceData }> = [];

    for (const region of this.regions.values()) {
      const priceData = await this.getRegionPrices(region.id, category);
      if (!priceData) continue;

      let score = 0;
      
      switch (criteria) {
        case 'lowest_price':
          score = 1000 - priceData.averagePrice; // Lower price = higher score
          break;
        
        case 'highest_volume':
          score = priceData.volume;
          break;
        
        case 'best_trend':
          score = priceData.trend === 'rising' ? 100 :
                 priceData.trend === 'stable' ? 50 : 0;
          score += priceData.trendPercentage;
          break;
      }

      results.push({ region, score, data: priceData });
    }

    // Sort by score (descending)
    results.sort((a, b) => b.score - a.score);

    return results;
  }

  /**
   * Get arbitrage route recommendations
   */
  async getArbitrageRoutes(
    startRegionId: string,
    budget: number = 5000,
    maxStops: number = 3
  ): Promise<Array<{
    route: Region[];
    totalProfit: number;
    totalDistance: number;
    items: Array<{ category: string; buyPrice: number; sellPrice: number }>;
  }>> {
    const routes: any[] = [];
    const startRegion = this.regions.get(startRegionId);
    if (!startRegion) return routes;

    // Find profitable multi-stop routes
    const opportunities = await this.analyzeArbitrage('all', 50, 0);
    
    // Group by source region
    const opportunitiesBySource = new Map<string, ArbitrageOpportunity[]>();
    opportunities.forEach(opp => {
      const existing = opportunitiesBySource.get(opp.sourceRegion.id) || [];
      existing.push(opp);
      opportunitiesBySource.set(opp.sourceRegion.id, existing);
    });

    // Build routes
    // This is a simplified version - in production would use proper route optimization
    const visited = new Set<string>([startRegionId]);
    const currentRoute: Region[] = [startRegion];
    let currentBudget = budget;
    let totalProfit = 0;
    let totalDistance = 0;
    const items: any[] = [];

    // Greedy approach: always go to the most profitable next destination
    let currentRegionId = startRegionId;
    
    for (let stop = 0; stop < maxStops; stop++) {
      const nextOpportunities = opportunitiesBySource.get(currentRegionId) || [];
      
      // Filter by budget and unvisited
      const viable = nextOpportunities.filter(opp => 
        !visited.has(opp.targetRegion.id) &&
        opp.sourceRegion.id === currentRegionId
      );

      if (viable.length === 0) break;

      // Pick best opportunity
      const best = viable.reduce((a, b) => 
        a.estimatedProfit > b.estimatedProfit ? a : b
      );

      // Check if we can afford it
      const buyPrice = best.priceDifference / (1 + best.percentageDifference / 100);
      if (buyPrice > currentBudget) continue;

      // Execute trade
      currentRoute.push(best.targetRegion);
      visited.add(best.targetRegion.id);
      totalDistance += this.calculateDistance(
        this.regions.get(currentRegionId)!,
        best.targetRegion
      );
      totalProfit += best.estimatedProfit;
      currentBudget -= buyPrice;
      currentBudget += buyPrice + best.priceDifference;
      
      items.push({
        category: best.category,
        buyPrice,
        sellPrice: buyPrice + best.priceDifference
      });

      currentRegionId = best.targetRegion.id;
    }

    if (currentRoute.length > 1) {
      routes.push({
        route: currentRoute,
        totalProfit,
        totalDistance,
        items
      });
    }

    return routes;
  }

  /**
   * Save opportunity alert
   */
  async createAlert(
    opportunityId: string,
    threshold: number = 100
  ): Promise<void> {
    const opportunity = this.opportunities.get(opportunityId);
    if (!opportunity) return;

    await chrome.storage.local.set({
      [`alert_${opportunityId}`]: {
        opportunity,
        threshold,
        createdAt: new Date(),
        triggered: false
      }
    });

    // Set up monitoring
    this.monitorOpportunity(opportunityId, threshold);
  }

  /**
   * Monitor opportunity for changes
   */
  private async monitorOpportunity(
    opportunityId: string,
    threshold: number
  ): Promise<void> {
    const checkInterval = setInterval(async () => {
      const opportunity = this.opportunities.get(opportunityId);
      if (!opportunity || opportunity.expiresAt < new Date()) {
        clearInterval(checkInterval);
        return;
      }

      // Re-calculate current profit
      const sourcePrices = await this.getRegionPrices(
        opportunity.sourceRegion.id,
        opportunity.category
      );
      const targetPrices = await this.getRegionPrices(
        opportunity.targetRegion.id,
        opportunity.category
      );

      if (!sourcePrices || !targetPrices) return;

      const currentProfit = Math.abs(
        targetPrices.averagePrice - sourcePrices.averagePrice
      ) - opportunity.transportCost;

      // Check if still meets threshold
      if (currentProfit >= threshold) {
        // Send notification
        chrome.notifications.create({
          type: 'basic',
          iconUrl: chrome.runtime.getURL('icons/icon-48.png'),
          title: 'Arbitrage Opportunity Active!',
          message: `${opportunity.sourceRegion.name} → ${opportunity.targetRegion.name}: $${currentProfit.toFixed(0)} profit`
        });

        // Mark as triggered
        const { [`alert_${opportunityId}`]: alert } = await chrome.storage.local.get(`alert_${opportunityId}`);
        if (alert) {
          alert.triggered = true;
          await chrome.storage.local.set({ [`alert_${opportunityId}`]: alert });
        }

        clearInterval(checkInterval);
      }
    }, 3600000); // Check every hour
  }

  /**
   * Load historical data
   */
  private async loadHistoricalData(): Promise<void> {
    const { geographicPriceHistory } = await chrome.storage.local.get('geographicPriceHistory');
    if (geographicPriceHistory) {
      Object.entries(geographicPriceHistory).forEach(([key, data]) => {
        this.priceData.set(key, data as RegionPriceData[]);
      });
    }
  }

  /**
   * Get all regions
   */
  getAllRegions(): Region[] {
    return Array.from(this.regions.values());
  }

  /**
   * Add custom region
   */
  addRegion(region: Region): void {
    this.regions.set(region.id, region);
  }
}

// Export singleton instance
export const geographicArbitrageAnalyzer = new GeographicArbitrageAnalyzer();