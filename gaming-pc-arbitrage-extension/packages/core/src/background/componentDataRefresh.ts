/**
 * Component Data Auto-Refresh Module
 * Automatically updates component pricing and availability data in the background
 */

import { ComponentPriceTier } from '../data/pricing-tiers';
import { ExtensionSettings } from '../types';

export interface RefreshConfig {
  enabled: boolean;
  intervals: {
    components: number; // minutes
    deals: number; // minutes
    competitors: number; // minutes
    market: number; // minutes
  };
  sources: DataSource[];
  lastRefresh: Record<string, Date>;
  nextRefresh: Record<string, Date>;
}

export interface DataSource {
  id: string;
  name: string;
  type: 'api' | 'scraper' | 'rss' | 'webhook';
  url: string;
  enabled: boolean;
  rateLimit?: {
    requests: number;
    period: number; // seconds
  };
  authentication?: {
    type: 'apiKey' | 'oauth' | 'basic';
    credentials: any;
  };
}

export interface RefreshResult {
  source: string;
  type: string;
  itemsUpdated: number;
  newItems: number;
  errors: string[];
  duration: number;
  timestamp: Date;
}

export interface ComponentUpdate {
  model: string;
  category: 'cpu' | 'gpu' | 'ram' | 'storage' | 'motherboard' | 'psu';
  msrp?: number;
  streetPrice?: number;
  availability: 'in-stock' | 'limited' | 'out-of-stock' | 'discontinued';
  lastSeen: Date;
  sources: string[];
  priceHistory: Array<{
    price: number;
    date: Date;
    source: string;
  }>;
}

export class ComponentDataRefreshManager {
  private config: RefreshConfig;
  private refreshIntervals: Map<string, NodeJS.Timeout> = new Map();
  private isRunning = false;
  private refreshQueue: Array<{ type: string; priority: number }> = [];
  private componentCache: Map<string, ComponentUpdate> = new Map();
  
  constructor() {
    this.config = this.getDefaultConfig();
    this.loadConfig();
  }

  /**
   * Initialize background refresh
   */
  async initialize(): Promise<void> {
    await this.loadConfig();
    await this.loadComponentCache();
    
    if (this.config.enabled) {
      this.start();
    }

    // Listen for manual refresh requests
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.type === 'REFRESH_DATA') {
        this.refreshData(request.dataType, request.priority || 1)
          .then(result => sendResponse(result))
          .catch(error => sendResponse({ error: error.message }));
        return true; // Keep channel open for async response
      }
    });
  }

  /**
   * Start auto-refresh
   */
  start(): void {
    if (this.isRunning) return;
    
    this.isRunning = true;
    
    // Set up refresh intervals
    Object.entries(this.config.intervals).forEach(([type, intervalMinutes]) => {
      if (intervalMinutes > 0) {
        // Initial refresh
        this.scheduleRefresh(type, 0);
        
        // Recurring refresh
        const interval = setInterval(() => {
          this.scheduleRefresh(type, 2);
        }, intervalMinutes * 60 * 1000);
        
        this.refreshIntervals.set(type, interval);
      }
    });

    console.log('Component data auto-refresh started');
  }

  /**
   * Stop auto-refresh
   */
  stop(): void {
    this.isRunning = false;
    
    // Clear all intervals
    this.refreshIntervals.forEach(interval => clearInterval(interval));
    this.refreshIntervals.clear();
    
    console.log('Component data auto-refresh stopped');
  }

  /**
   * Schedule a refresh task
   */
  private scheduleRefresh(type: string, priority: number): void {
    // Check if already in queue
    const existing = this.refreshQueue.find(item => item.type === type);
    if (existing) {
      existing.priority = Math.max(existing.priority, priority);
      return;
    }

    this.refreshQueue.push({ type, priority });
    this.refreshQueue.sort((a, b) => b.priority - a.priority);
    
    // Process queue
    this.processRefreshQueue();
  }

  /**
   * Process refresh queue
   */
  private async processRefreshQueue(): Promise<void> {
    if (this.refreshQueue.length === 0) return;
    
    const task = this.refreshQueue.shift();
    if (!task) return;

    try {
      await this.refreshData(task.type, task.priority);
    } catch (error) {
      console.error(`Refresh failed for ${task.type}:`, error);
    }

    // Process next item
    if (this.refreshQueue.length > 0) {
      setTimeout(() => this.processRefreshQueue(), 1000);
    }
  }

  /**
   * Refresh specific data type
   */
  async refreshData(type: string, priority: number): Promise<RefreshResult> {
    const startTime = Date.now();
    const results: RefreshResult = {
      source: 'auto-refresh',
      type,
      itemsUpdated: 0,
      newItems: 0,
      errors: [],
      duration: 0,
      timestamp: new Date()
    };

    try {
      switch (type) {
        case 'components':
          await this.refreshComponentData(results);
          break;
        
        case 'deals':
          await this.refreshDealData(results);
          break;
        
        case 'competitors':
          await this.refreshCompetitorData(results);
          break;
        
        case 'market':
          await this.refreshMarketData(results);
          break;
        
        default:
          throw new Error(`Unknown refresh type: ${type}`);
      }

      // Update last refresh time
      this.config.lastRefresh[type] = new Date();
      this.config.nextRefresh[type] = new Date(
        Date.now() + (this.config.intervals[type as keyof typeof this.config.intervals] || 60) * 60 * 1000
      );
      
      await this.saveConfig();
    } catch (error) {
      results.errors.push(error instanceof Error ? error.message : 'Unknown error');
    }

    results.duration = Date.now() - startTime;
    
    // Store result
    await this.storeRefreshResult(results);
    
    // Notify UI if needed
    if (priority > 1) {
      chrome.runtime.sendMessage({
        type: 'REFRESH_COMPLETE',
        data: results
      });
    }

    return results;
  }

  /**
   * Refresh component pricing data
   */
  private async refreshComponentData(results: RefreshResult): Promise<void> {
    const sources = this.config.sources.filter(s => s.enabled);
    
    for (const source of sources) {
      try {
        const updates = await this.fetchComponentUpdates(source);
        
        for (const update of updates) {
          const existing = this.componentCache.get(update.model);
          
          if (existing) {
            // Update existing
            existing.streetPrice = update.streetPrice || existing.streetPrice;
            existing.availability = update.availability;
            existing.lastSeen = new Date();
            existing.sources = Array.from(new Set([...existing.sources, source.id]));
            
            // Add to price history
            if (update.streetPrice) {
              existing.priceHistory.push({
                price: update.streetPrice,
                date: new Date(),
                source: source.id
              });
              
              // Keep only last 30 days
              const cutoff = new Date();
              cutoff.setDate(cutoff.getDate() - 30);
              existing.priceHistory = existing.priceHistory.filter(p => p.date > cutoff);
            }
            
            results.itemsUpdated++;
          } else {
            // New component
            this.componentCache.set(update.model, update);
            results.newItems++;
          }
        }
      } catch (error) {
        results.errors.push(`${source.name}: ${error}`);
      }
    }

    // Save updated cache
    await this.saveComponentCache();
  }

  /**
   * Fetch component updates from a source
   */
  private async fetchComponentUpdates(source: DataSource): Promise<ComponentUpdate[]> {
    // Apply rate limiting
    await this.applyRateLimit(source);

    switch (source.type) {
      case 'api':
        return this.fetchFromAPI(source);
      
      case 'scraper':
        return this.fetchFromScraper(source);
      
      case 'rss':
        return this.fetchFromRSS(source);
      
      case 'webhook':
        // Webhooks are passive, data comes to us
        return [];
      
      default:
        throw new Error(`Unknown source type: ${source.type}`);
    }
  }

  /**
   * Fetch from API source
   */
  private async fetchFromAPI(source: DataSource): Promise<ComponentUpdate[]> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json'
    };

    // Add authentication
    if (source.authentication) {
      switch (source.authentication.type) {
        case 'apiKey':
          headers['X-API-Key'] = source.authentication.credentials.key;
          break;
        case 'basic':
          headers['Authorization'] = `Basic ${btoa(`${source.authentication.credentials.username}:${source.authentication.credentials.password}`)}`;
          break;
      }
    }

    const response = await fetch(source.url, { headers });
    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    const data = await response.json();
    
    // Parse API response (mock implementation)
    return this.parseAPIResponse(data, source.id);
  }

  /**
   * Parse API response into component updates
   */
  private parseAPIResponse(data: any, sourceId: string): ComponentUpdate[] {
    const updates: ComponentUpdate[] = [];
    
    // Mock parser - in production would handle various API formats
    if (Array.isArray(data)) {
      data.forEach(item => {
        updates.push({
          model: item.model || item.name,
          category: this.detectCategory(item.model || item.name),
          msrp: item.msrp,
          streetPrice: item.price || item.streetPrice,
          availability: this.parseAvailability(item.stock || item.availability),
          lastSeen: new Date(),
          sources: [sourceId],
          priceHistory: []
        });
      });
    }

    return updates;
  }

  /**
   * Detect component category from model name
   */
  private detectCategory(model: string): ComponentUpdate['category'] {
    const modelLower = model.toLowerCase();
    
    if (modelLower.includes('rtx') || modelLower.includes('gtx') || modelLower.includes('radeon')) {
      return 'gpu';
    } else if (modelLower.includes('ryzen') || modelLower.includes('intel') || modelLower.includes('i5') || modelLower.includes('i7') || modelLower.includes('i9')) {
      return 'cpu';
    } else if (modelLower.includes('ddr') || modelLower.includes('memory')) {
      return 'ram';
    } else if (modelLower.includes('ssd') || modelLower.includes('nvme') || modelLower.includes('hdd')) {
      return 'storage';
    } else if (modelLower.includes('psu') || modelLower.includes('power')) {
      return 'psu';
    } else if (modelLower.includes('motherboard') || modelLower.includes('mobo')) {
      return 'motherboard';
    }
    
    return 'gpu'; // Default
  }

  /**
   * Parse availability status
   */
  private parseAvailability(value: any): ComponentUpdate['availability'] {
    if (typeof value === 'boolean') {
      return value ? 'in-stock' : 'out-of-stock';
    }
    
    if (typeof value === 'number') {
      if (value > 10) return 'in-stock';
      if (value > 0) return 'limited';
      return 'out-of-stock';
    }
    
    const strValue = String(value).toLowerCase();
    if (strValue.includes('stock') || strValue.includes('available')) return 'in-stock';
    if (strValue.includes('limited') || strValue.includes('low')) return 'limited';
    if (strValue.includes('out') || strValue.includes('unavailable')) return 'out-of-stock';
    if (strValue.includes('discontinued')) return 'discontinued';
    
    return 'out-of-stock';
  }

  /**
   * Fetch from web scraper
   */
  private async fetchFromScraper(source: DataSource): Promise<ComponentUpdate[]> {
    // In production, would use Puppeteer or similar
    // For now, return mock data
    return [
      {
        model: 'RTX 4070 Ti',
        category: 'gpu',
        streetPrice: 799,
        availability: 'in-stock',
        lastSeen: new Date(),
        sources: [source.id],
        priceHistory: []
      }
    ];
  }

  /**
   * Fetch from RSS feed
   */
  private async fetchFromRSS(source: DataSource): Promise<ComponentUpdate[]> {
    const response = await fetch(source.url);
    const text = await response.text();
    
    // Parse RSS (simplified)
    const parser = new DOMParser();
    const doc = parser.parseFromString(text, 'text/xml');
    const items = doc.querySelectorAll('item');
    
    const updates: ComponentUpdate[] = [];
    
    items.forEach(item => {
      const title = item.querySelector('title')?.textContent || '';
      const description = item.querySelector('description')?.textContent || '';
      
      // Extract component info from RSS item
      const componentInfo = this.extractComponentFromText(title + ' ' + description);
      if (componentInfo) {
        updates.push({
          ...componentInfo,
          lastSeen: new Date(),
          sources: [source.id],
          priceHistory: []
        });
      }
    });

    return updates;
  }

  /**
   * Extract component information from text
   */
  private extractComponentFromText(text: string): Partial<ComponentUpdate> | null {
    // Price extraction
    const priceMatch = text.match(/\$(\d+(?:,\d{3})*(?:\.\d{2})?)/);
    const price = priceMatch ? parseFloat(priceMatch[1].replace(',', '')) : undefined;
    
    // Model extraction (simplified)
    const modelPatterns = [
      /RTX\s*\d{4}\s*(?:Ti|SUPER)?/i,
      /GTX\s*\d{4}\s*(?:Ti|SUPER)?/i,
      /RX\s*\d{4}\s*(?:XT)?/i,
      /(?:i[359]|Ryzen\s*[357])\s*\d{4}[A-Z]*/i
    ];
    
    let model: string | undefined;
    for (const pattern of modelPatterns) {
      const match = text.match(pattern);
      if (match) {
        model = match[0];
        break;
      }
    }
    
    if (!model) return null;
    
    return {
      model,
      category: this.detectCategory(model),
      streetPrice: price,
      availability: 'in-stock' // Default assumption for RSS
    };
  }

  /**
   * Refresh deal data
   */
  private async refreshDealData(results: RefreshResult): Promise<void> {
    // Get active deals
    const { deals = [] } = await chrome.storage.local.get('deals');
    
    for (const deal of deals) {
      if (deal.status === 'active' || deal.status === 'in-progress') {
        try {
          // Update listing price if URL is available
          if (deal.listing.url) {
            const currentPrice = await this.fetchCurrentPrice(deal.listing.url);
            if (currentPrice && currentPrice !== deal.listing.price) {
              deal.listing.price = currentPrice;
              deal.listing.lastUpdated = new Date();
              results.itemsUpdated++;
              
              // Notify if price dropped significantly
              if (currentPrice < deal.listing.price * 0.9) {
                chrome.notifications.create({
                  type: 'basic',
                  iconUrl: chrome.runtime.getURL('icons/icon-48.png'),
                  title: 'Price Drop Alert!',
                  message: `${deal.listing.title} dropped to $${currentPrice}`
                });
              }
            }
          }
        } catch (error) {
          results.errors.push(`Deal ${deal.id}: ${error}`);
        }
      }
    }
    
    // Save updated deals
    await chrome.storage.local.set({ deals });
  }

  /**
   * Fetch current price from listing URL
   */
  private async fetchCurrentPrice(url: string): Promise<number | null> {
    // In production, would use platform-specific scrapers
    // For now, return mock data
    return Math.random() > 0.5 ? Math.floor(Math.random() * 200) + 800 : null;
  }

  /**
   * Refresh competitor data
   */
  private async refreshCompetitorData(results: RefreshResult): Promise<void> {
    // This would integrate with the competitor tracker module
    results.itemsUpdated = 0;
  }

  /**
   * Refresh market data
   */
  private async refreshMarketData(results: RefreshResult): Promise<void> {
    // Update market trends, indices, etc.
    results.itemsUpdated = 0;
  }

  /**
   * Apply rate limiting
   */
  private async applyRateLimit(source: DataSource): Promise<void> {
    if (!source.rateLimit) return;
    
    const key = `rateLimit_${source.id}`;
    const { [key]: history = [] } = await chrome.storage.local.get(key);
    
    const now = Date.now();
    const periodStart = now - (source.rateLimit.period * 1000);
    
    // Filter requests within the period
    const recentRequests = history.filter((timestamp: number) => timestamp > periodStart);
    
    if (recentRequests.length >= source.rateLimit.requests) {
      // Calculate wait time
      const oldestRequest = Math.min(...recentRequests);
      const waitTime = oldestRequest + (source.rateLimit.period * 1000) - now;
      
      if (waitTime > 0) {
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }
    
    // Record this request
    recentRequests.push(now);
    await chrome.storage.local.set({ [key]: recentRequests });
  }

  /**
   * Get component price trends
   */
  async getComponentTrends(
    model: string,
    days: number = 30
  ): Promise<{
    current: number;
    average: number;
    min: number;
    max: number;
    trend: 'rising' | 'stable' | 'falling';
    history: Array<{ date: Date; price: number }>;
  } | null> {
    const component = this.componentCache.get(model);
    if (!component || !component.streetPrice) return null;
    
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);
    
    const relevantHistory = component.priceHistory.filter(p => p.date > cutoff);
    
    if (relevantHistory.length === 0) {
      return {
        current: component.streetPrice,
        average: component.streetPrice,
        min: component.streetPrice,
        max: component.streetPrice,
        trend: 'stable',
        history: []
      };
    }
    
    const prices = relevantHistory.map(p => p.price);
    const average = prices.reduce((a, b) => a + b, 0) / prices.length;
    
    // Determine trend
    const recentPrices = prices.slice(-5);
    const olderPrices = prices.slice(0, 5);
    const recentAvg = recentPrices.reduce((a, b) => a + b, 0) / recentPrices.length;
    const olderAvg = olderPrices.reduce((a, b) => a + b, 0) / olderPrices.length;
    
    let trend: 'rising' | 'stable' | 'falling';
    if (recentAvg > olderAvg * 1.05) trend = 'rising';
    else if (recentAvg < olderAvg * 0.95) trend = 'falling';
    else trend = 'stable';
    
    return {
      current: component.streetPrice,
      average,
      min: Math.min(...prices),
      max: Math.max(...prices),
      trend,
      history: relevantHistory.map(p => ({ date: p.date, price: p.price }))
    };
  }

  /**
   * Configuration management
   */
  private getDefaultConfig(): RefreshConfig {
    return {
      enabled: true,
      intervals: {
        components: 360, // 6 hours
        deals: 60, // 1 hour
        competitors: 120, // 2 hours
        market: 720 // 12 hours
      },
      sources: [
        {
          id: 'pcpartpicker',
          name: 'PCPartPicker API',
          type: 'api',
          url: 'https://api.pcpartpicker.com/v1/products',
          enabled: false, // Requires API key
          rateLimit: { requests: 100, period: 3600 }
        },
        {
          id: 'newegg',
          name: 'Newegg RSS',
          type: 'rss',
          url: 'https://www.newegg.com/rss',
          enabled: true
        }
      ],
      lastRefresh: {},
      nextRefresh: {}
    };
  }

  private async loadConfig(): Promise<void> {
    const { componentRefreshConfig } = await chrome.storage.local.get('componentRefreshConfig');
    if (componentRefreshConfig) {
      this.config = { ...this.config, ...componentRefreshConfig };
    }
  }

  private async saveConfig(): Promise<void> {
    await chrome.storage.local.set({ componentRefreshConfig: this.config });
  }

  private async loadComponentCache(): Promise<void> {
    const { componentCache } = await chrome.storage.local.get('componentCache');
    if (componentCache) {
      this.componentCache = new Map(Object.entries(componentCache));
    }
  }

  private async saveComponentCache(): Promise<void> {
    const cacheObject = Object.fromEntries(this.componentCache);
    await chrome.storage.local.set({ componentCache: cacheObject });
  }

  private async storeRefreshResult(result: RefreshResult): Promise<void> {
    const { refreshHistory = [] } = await chrome.storage.local.get('refreshHistory');
    refreshHistory.push(result);
    
    // Keep only last 100 results
    if (refreshHistory.length > 100) {
      refreshHistory.splice(0, refreshHistory.length - 100);
    }
    
    await chrome.storage.local.set({ refreshHistory });
  }

  /**
   * Get configuration
   */
  getConfig(): RefreshConfig {
    return { ...this.config };
  }

  /**
   * Update configuration
   */
  async updateConfig(updates: Partial<RefreshConfig>): Promise<void> {
    this.config = { ...this.config, ...updates };
    await this.saveConfig();
    
    // Restart if running
    if (this.isRunning) {
      this.stop();
      this.start();
    }
  }

  /**
   * Get refresh status
   */
  getStatus(): {
    isRunning: boolean;
    queueLength: number;
    lastRefresh: Record<string, Date>;
    nextRefresh: Record<string, Date>;
  } {
    return {
      isRunning: this.isRunning,
      queueLength: this.refreshQueue.length,
      lastRefresh: this.config.lastRefresh,
      nextRefresh: this.config.nextRefresh
    };
  }
}

// Export singleton instance
export const componentDataRefreshManager = new ComponentDataRefreshManager();