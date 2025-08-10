/**
 * Main Parser Engine
 * Implements parsing strategies for different platforms
 */

import { Platform, Listing, CPUComponent, GPUComponent, RAMComponent, StorageComponent } from '../types';
import { ComponentDetector } from './component-detector';
import { FacebookParser } from './facebook-parser';
import { CraigslistParser } from './craigslist-parser';
import { OfferUpParser } from './offerup-parser';

export interface ParsedListing {
  url: string;
  platform: Platform;
  title: string;
  description: string;
  price: number;
  images: string[];
  location: {
    city: string;
    state: string;
    distance?: number;
  };
  seller: {
    name: string;
    profileUrl?: string;
    memberSince?: string;
    responseRate?: number;
  };
  rawHtml?: string;
}

export interface ParserStrategy {
  platform: Platform;
  canParse(url: string): boolean;
  parse(document: Document): ParsedListing;
  extractSellerInfo(document: Document): Listing['seller'];
  extractImages(document: Document): Listing['images'];
}

export class ListingParser {
  private strategies: Map<Platform, ParserStrategy>;
  private componentDetector: ComponentDetector;
  
  constructor() {
    this.strategies = new Map([
      ['facebook', new FacebookParser()],
      ['craigslist', new CraigslistParser()],
      ['offerup', new OfferUpParser()],
    ]);
    
    this.componentDetector = new ComponentDetector();
  }
  
  /**
   * Main parsing method - detects platform and parses listing
   */
  async parseListing(url: string, document: Document): Promise<Listing | null> {
    try {
      // Detect platform from URL
      const platform = this.detectPlatform(url);
      if (!platform) {
        console.warn('Unknown platform for URL:', url);
        return null;
      }
      
      // Get appropriate parser strategy
      const parser = this.strategies.get(platform);
      if (!parser) {
        console.warn('No parser available for platform:', platform);
        return null;
      }
      
      // Parse basic listing data
      const parsed = parser.parse(document);
      
      // Extract seller info with platform-specific logic
      const seller = parser.extractSellerInfo(document);
      
      // Extract and process images
      const images = parser.extractImages(document);
      
      // Detect components from title and description
      const components = await this.componentDetector.detectAllComponents(
        parsed.title + ' ' + parsed.description
      );
      
      // Calculate condition score
      const condition = this.assessCondition(parsed.description, images.length);
      
      // Identify risks
      const risks = this.assessRisks(parsed, seller, components);
      
      // Generate unique ID
      const id = this.generateListingId(platform, url);
      
      // Construct full listing object
      const listing: Listing = {
        id,
        url,
        platform,
        externalId: this.extractExternalId(url, platform),
        title: parsed.title,
        description: parsed.description,
        price: parsed.price,
        currency: 'USD',
        location: parsed.location,
        seller,
        images,
        components,
        condition,
        analysis: {
          fmv: 0, // Will be calculated by FMV engine
          componentValue: 0,
          profitPotential: 0,
          roi: 0,
          margin: 0,
          dealScore: 0,
          confidence: 0,
        },
        risks,
        metadata: {
          createdAt: new Date(),
          updatedAt: new Date(),
          lastViewedAt: new Date(),
          viewCount: 1,
          priceHistory: [{ date: new Date(), price: parsed.price }],
          status: 'active',
          starred: false,
          hidden: false,
          notes: '',
          tags: [],
        },
      };
      
      return listing;
      
    } catch (error) {
      console.error('Error parsing listing:', error);
      return null;
    }
  }
  
  /**
   * Detect platform from URL
   */
  private detectPlatform(url: string): Platform | null {
    if (url.includes('facebook.com') || url.includes('fb.com')) {
      return 'facebook';
    }
    if (url.includes('craigslist.org')) {
      return 'craigslist';
    }
    if (url.includes('offerup.com')) {
      return 'offerup';
    }
    return null;
  }
  
  /**
   * Extract external ID from platform URL
   */
  private extractExternalId(url: string, platform: Platform): string | undefined {
    switch (platform) {
      case 'facebook':
        // Extract item ID from Facebook URL
        const fbMatch = url.match(/\/item\/(\d+)/);
        return fbMatch?.[1];
        
      case 'craigslist':
        // Extract post ID from Craigslist URL
        const clMatch = url.match(/\/(\d+)\.html/);
        return clMatch?.[1];
        
      case 'offerup':
        // Extract item ID from OfferUp URL
        const ouMatch = url.match(/\/item\/detail\/([a-zA-Z0-9-]+)/);
        return ouMatch?.[1];
        
      default:
        return undefined;
    }
  }
  
  /**
   * Assess listing condition based on description and photos
   */
  private assessCondition(description: string, photoCount: number): Listing['condition'] {
    const descLower = description.toLowerCase();
    const issues: Listing['condition']['issues'] = [];
    const notes: string[] = [];
    
    // Check for condition keywords
    let overallScore = 3; // Default to "good"
    
    if (descLower.includes('like new') || descLower.includes('barely used')) {
      overallScore = 4;
      notes.push('Seller claims like-new condition');
    } else if (descLower.includes('excellent') || descLower.includes('mint')) {
      overallScore = 4;
    } else if (descLower.includes('fair') || descLower.includes('some wear')) {
      overallScore = 2;
    } else if (descLower.includes('poor') || descLower.includes('for parts')) {
      overallScore = 1;
      notes.push('May be suitable for parts only');
    }
    
    // Check for specific issues
    if (descLower.includes('crack') || descLower.includes('broken')) {
      issues.push({
        component: 'unknown',
        issue: 'Physical damage mentioned',
        severity: 'major',
      });
      overallScore = Math.min(overallScore, 2);
    }
    
    if (descLower.includes('not working') || descLower.includes("doesn't work")) {
      issues.push({
        component: 'unknown',
        issue: 'Non-functional component',
        severity: 'major',
      });
      overallScore = 1;
    }
    
    if (descLower.includes('overheating') || descLower.includes('thermal')) {
      issues.push({
        component: 'cooling',
        issue: 'Thermal issues mentioned',
        severity: 'moderate',
      });
    }
    
    // Estimate age
    let ageEstimate: number | undefined;
    const yearMatch = descLower.match(/bought.{0,20}(\d{4})|purchased.{0,20}(\d{4})|from.{0,20}(\d{4})/);
    if (yearMatch) {
      const year = parseInt(yearMatch[1] || yearMatch[2] || yearMatch[3]);
      ageEstimate = (new Date().getFullYear() - year) * 12;
    }
    
    // Estimate usage
    let usageType: 'light' | 'moderate' | 'heavy' = 'moderate';
    if (descLower.includes('mining') || descLower.includes('24/7')) {
      usageType = 'heavy';
      notes.push('Heavy usage indicated (mining/24-7)');
    } else if (descLower.includes('light use') || descLower.includes('rarely used')) {
      usageType = 'light';
    }
    
    // Adjust score based on photo count
    if (photoCount < 3) {
      notes.push('Limited photos provided');
      overallScore = Math.min(overallScore, 3);
    }
    
    return {
      overall: overallScore as 1 | 2 | 3 | 4 | 5,
      notes,
      issues,
      ageEstimate,
      usageType,
    };
  }
  
  /**
   * Assess risks based on listing data
   */
  private assessRisks(
    parsed: ParsedListing,
    seller: Listing['seller'],
    components: Listing['components']
  ): Listing['risks'] {
    const flags: Listing['risks']['flags'] = [];
    let score = 0;
    
    // Price risk - too good to be true?
    const hasHighValueGPU = components.gpu && 
      (components.gpu.model.includes('3070') || 
       components.gpu.model.includes('3080') || 
       components.gpu.model.includes('4070'));
    
    if (hasHighValueGPU && parsed.price < 400) {
      flags.push({
        type: 'price_anomaly',
        severity: 'high',
        description: 'Price unusually low for high-end GPU',
      });
      score += 3;
    }
    
    // Seller risk
    if (!seller.memberSince) {
      flags.push({
        type: 'new_seller',
        severity: 'medium',
        description: 'Cannot verify seller history',
      });
      score += 2;
    }
    
    // Description risk
    const descLower = parsed.description.toLowerCase();
    if (descLower.length < 50) {
      flags.push({
        type: 'minimal_description',
        severity: 'low',
        description: 'Very brief description provided',
      });
      score += 1;
    }
    
    if (descLower.includes('no returns') || descLower.includes('as is')) {
      flags.push({
        type: 'no_returns',
        severity: 'medium',
        description: 'Seller explicitly states no returns',
      });
      score += 2;
    }
    
    // Photo risk
    if (parsed.images.length < 3) {
      flags.push({
        type: 'limited_photos',
        severity: 'medium',
        description: 'Few photos provided',
      });
      score += 2;
    }
    
    // Stolen goods indicators
    const stolenIndicators: string[] = [];
    if (descLower.includes('cash only') && descLower.includes('quick sale')) {
      stolenIndicators.push('Urgency + cash only requirement');
    }
    if (!parsed.images.some(img => img.includes('serial') || img.includes('specs'))) {
      stolenIndicators.push('No serial number photos');
    }
    
    // Scam patterns
    const scamPatterns: string[] = [];
    if (descLower.includes('shipping only') || descLower.includes('mail only')) {
      scamPatterns.push('Shipping only (no local pickup)');
      score += 3;
    }
    if (parsed.images.length === 1 && !descLower.includes('more photos')) {
      scamPatterns.push('Single stock photo');
      score += 2;
    }
    
    // Technical risks
    const technicalIssues: string[] = [];
    if (components.gpu && descLower.includes('mining')) {
      technicalIssues.push('GPU used for mining');
      flags.push({
        type: 'mining_gpu',
        severity: 'high',
        description: 'GPU may have mining wear',
      });
      score += 2;
    }
    
    return {
      score: Math.min(score, 10), // Cap at 10
      flags,
      stolen: {
        probability: stolenIndicators.length > 0 ? stolenIndicators.length * 0.3 : 0,
        indicators: stolenIndicators,
      },
      scam: {
        probability: scamPatterns.length > 0 ? scamPatterns.length * 0.4 : 0,
        patterns: scamPatterns,
      },
      technical: {
        issues: technicalIssues,
        severity: technicalIssues.length > 2 ? 'high' : 
                 technicalIssues.length > 0 ? 'medium' : 'low',
      },
    };
  }
  
  /**
   * Generate unique listing ID
   */
  private generateListingId(platform: Platform, url: string): string {
    const timestamp = Date.now();
    const urlHash = this.simpleHash(url);
    return `${platform}-${urlHash}-${timestamp}`;
  }
  
  /**
   * Simple hash function for URL
   */
  private simpleHash(str: string): string {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(36);
  }
}