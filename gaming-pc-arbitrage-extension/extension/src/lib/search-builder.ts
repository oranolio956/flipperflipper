/**
 * Search Builder v3.6.0 - Apple-level Search Creation
 * Platform-aware search URL generation with visual builder
 */

export interface SearchFilter {
  id: string;
  type: 'price' | 'keyword' | 'location' | 'category' | 'condition' | 'custom';
  operator: 'equals' | 'contains' | 'between' | 'greater' | 'less' | 'not';
  value: any;
  label?: string;
}

export interface SearchParameters {
  // Core parameters
  platform: 'facebook' | 'craigslist' | 'offerup';
  keywords: string[];
  
  // Price filters
  minPrice?: number;
  maxPrice?: number;
  
  // Location filters
  location?: {
    radius: number; // miles
    zip?: string;
    city?: string;
    coordinates?: { lat: number; lng: number };
  };
  
  // Category filters
  category?: {
    main: string;
    sub?: string;
  };
  
  // Condition filters
  condition?: ('new' | 'used' | 'like-new' | 'for-parts')[];
  
  // Platform-specific
  facebook?: {
    availability?: 'in-stock' | 'all';
    sortBy?: 'relevance' | 'date' | 'price-asc' | 'price-desc' | 'distance';
    daysSinceListed?: number;
    delivery?: 'local' | 'shipping' | 'both';
  };
  
  craigslist?: {
    hasImage?: boolean;
    postedToday?: boolean;
    searchTitlesOnly?: boolean;
    bundleDuplicates?: boolean;
    section?: 'sss' | 'cta' | 'sys' | 'sya'; // for sale, computers, systems, system parts
  };
  
  offerup?: {
    radius?: number; // specific radius for OfferUp
    priceNegotiable?: boolean;
    sellerType?: 'owner' | 'dealer' | 'all';
    itemCondition?: 'new' | 'reconditioned' | 'used-like-new' | 'used-good' | 'used-fair';
  };
  
  // Advanced filters
  filters: SearchFilter[];
  
  // Saved search metadata
  name?: string;
  enabled?: boolean;
  interval?: number; // minutes between scans
  notifications?: boolean;
}

export class SearchBuilder {
  private baseUrls = {
    facebook: 'https://www.facebook.com/marketplace/search',
    craigslist: 'https://[CITY].craigslist.org/search',
    offerup: 'https://offerup.com/search'
  };
  
  // Platform-specific gaming PC keywords
  private defaultKeywords = {
    gaming: ['gaming pc', 'gaming computer', 'gaming desktop', 'gaming rig'],
    components: ['rtx', 'gtx', 'radeon', 'ryzen', 'intel', 'nvidia', 'amd'],
    modifiers: ['custom', 'built', 'rgb', 'water cooled', 'high end']
  };
  
  // Category mappings
  private categories = {
    facebook: {
      'Electronics': '1010524969306430',
      'Computers': '112704118786086',
      'Video Games': '139973559740962'
    },
    craigslist: {
      'computers': 'sya',
      'computer parts': 'syp',
      'electronics': 'ela',
      'video gaming': 'vga'
    },
    offerup: {
      'Electronics': 'electronics',
      'Computer Equipment': 'computer-equipment',
      'Video Games': 'video-games'
    }
  };
  
  /**
   * Build search URL from parameters
   */
  buildUrl(params: SearchParameters): string {
    switch (params.platform) {
      case 'facebook':
        return this.buildFacebookUrl(params);
      case 'craigslist':
        return this.buildCraigslistUrl(params);
      case 'offerup':
        return this.buildOfferUpUrl(params);
      default:
        throw new Error(`Unknown platform: ${params.platform}`);
    }
  }
  
  /**
   * Build Facebook Marketplace URL
   */
  private buildFacebookUrl(params: SearchParameters): string {
    const url = new URL(this.baseUrls.facebook);
    
    // Keywords
    if (params.keywords.length > 0) {
      url.searchParams.set('query', params.keywords.join(' '));
    }
    
    // Price range
    if (params.minPrice !== undefined) {
      url.searchParams.set('minPrice', params.minPrice.toString());
    }
    if (params.maxPrice !== undefined) {
      url.searchParams.set('maxPrice', params.maxPrice.toString());
    }
    
    // Location
    if (params.location) {
      if (params.location.radius) {
        url.searchParams.set('radius', params.location.radius.toString());
      }
      if (params.location.coordinates) {
        url.searchParams.set('latitude', params.location.coordinates.lat.toString());
        url.searchParams.set('longitude', params.location.coordinates.lng.toString());
      }
    }
    
    // Category
    if (params.category?.main && this.categories.facebook[params.category.main]) {
      url.searchParams.set('categoryID', this.categories.facebook[params.category.main]);
    }
    
    // Condition
    if (params.condition && params.condition.length > 0) {
      const conditionMap = {
        'new': 'new',
        'used': 'used_good',
        'like-new': 'used_like_new',
        'for-parts': 'used_fair'
      };
      
      params.condition.forEach(cond => {
        if (conditionMap[cond]) {
          url.searchParams.append('itemCondition', conditionMap[cond]);
        }
      });
    }
    
    // Facebook-specific parameters
    if (params.facebook) {
      if (params.facebook.availability) {
        url.searchParams.set('availability', params.facebook.availability);
      }
      if (params.facebook.sortBy) {
        url.searchParams.set('sortBy', params.facebook.sortBy);
      }
      if (params.facebook.daysSinceListed) {
        url.searchParams.set('daysSinceListed', params.facebook.daysSinceListed.toString());
      }
      if (params.facebook.delivery) {
        url.searchParams.set('deliveryMethod', params.facebook.delivery);
      }
    }
    
    return url.toString();
  }
  
  /**
   * Build Craigslist URL
   */
  private buildCraigslistUrl(params: SearchParameters): string {
    // Default to SF if no location specified
    const city = params.location?.city?.toLowerCase().replace(/\s+/g, '') || 'sfbay';
    const baseUrl = this.baseUrls.craigslist.replace('[CITY]', city);
    
    // Section
    const section = params.craigslist?.section || 'sss'; // default to all for sale
    const url = new URL(`${baseUrl}/${section}`);
    
    // Keywords
    if (params.keywords.length > 0) {
      url.searchParams.set('query', params.keywords.join(' '));
    }
    
    // Price range
    if (params.minPrice !== undefined) {
      url.searchParams.set('min_price', params.minPrice.toString());
    }
    if (params.maxPrice !== undefined) {
      url.searchParams.set('max_price', params.maxPrice.toString());
    }
    
    // Location radius
    if (params.location?.radius) {
      url.searchParams.set('search_distance', params.location.radius.toString());
    }
    if (params.location?.zip) {
      url.searchParams.set('postal', params.location.zip);
    }
    
    // Craigslist-specific parameters
    if (params.craigslist) {
      if (params.craigslist.hasImage) {
        url.searchParams.set('hasPic', '1');
      }
      if (params.craigslist.postedToday) {
        url.searchParams.set('postedToday', '1');
      }
      if (params.craigslist.searchTitlesOnly) {
        url.searchParams.set('srchType', 'T');
      }
      if (params.craigslist.bundleDuplicates) {
        url.searchParams.set('bundleDuplicates', '1');
      }
    }
    
    return url.toString();
  }
  
  /**
   * Build OfferUp URL
   */
  private buildOfferUpUrl(params: SearchParameters): string {
    const url = new URL(this.baseUrls.offerup);
    
    // Keywords
    if (params.keywords.length > 0) {
      url.searchParams.set('q', params.keywords.join(' '));
    }
    
    // Price range
    if (params.minPrice !== undefined) {
      url.searchParams.set('price_min', params.minPrice.toString());
    }
    if (params.maxPrice !== undefined) {
      url.searchParams.set('price_max', params.maxPrice.toString());
    }
    
    // Location
    if (params.location?.radius || params.offerup?.radius) {
      const radius = params.offerup?.radius || params.location?.radius || 50;
      url.searchParams.set('radius', radius.toString());
    }
    
    // Category
    if (params.category?.main && this.categories.offerup[params.category.main]) {
      url.searchParams.set('cid', this.categories.offerup[params.category.main]);
    }
    
    // Condition
    if (params.offerup?.itemCondition) {
      url.searchParams.set('condition', params.offerup.itemCondition);
    }
    
    // OfferUp-specific parameters
    if (params.offerup) {
      if (params.offerup.priceNegotiable) {
        url.searchParams.set('price_negotiable', 'true');
      }
      if (params.offerup.sellerType && params.offerup.sellerType !== 'all') {
        url.searchParams.set('seller_type', params.offerup.sellerType);
      }
    }
    
    return url.toString();
  }
  
  /**
   * Generate smart keyword suggestions
   */
  suggestKeywords(base: string, platform: 'facebook' | 'craigslist' | 'offerup'): string[] {
    const suggestions = new Set<string>();
    
    // Add base keyword
    suggestions.add(base.toLowerCase());
    
    // Add gaming variants
    if (base.toLowerCase().includes('pc') || base.toLowerCase().includes('computer')) {
      this.defaultKeywords.gaming.forEach(kw => suggestions.add(kw));
    }
    
    // Add component keywords if relevant
    const hasComponent = this.defaultKeywords.components.some(comp => 
      base.toLowerCase().includes(comp)
    );
    
    if (hasComponent) {
      this.defaultKeywords.components.forEach(comp => {
        suggestions.add(`${base} ${comp}`);
        suggestions.add(`${comp} ${base}`);
      });
    }
    
    // Platform-specific additions
    if (platform === 'facebook') {
      suggestions.add(`${base} local`);
      suggestions.add(`${base} pickup`);
    } else if (platform === 'craigslist') {
      suggestions.add(`${base} cash`);
      suggestions.add(`${base} firm`);
    } else if (platform === 'offerup') {
      suggestions.add(`${base} obo`);
      suggestions.add(`${base} negotiable`);
    }
    
    return Array.from(suggestions).slice(0, 10);
  }
  
  /**
   * Validate search parameters
   */
  validateParameters(params: SearchParameters): { valid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    // Must have at least one keyword
    if (!params.keywords || params.keywords.length === 0) {
      errors.push('At least one keyword is required');
    }
    
    // Price validation
    if (params.minPrice !== undefined && params.maxPrice !== undefined) {
      if (params.minPrice > params.maxPrice) {
        errors.push('Minimum price cannot be greater than maximum price');
      }
    }
    
    // Location validation
    if (params.location) {
      if (params.location.radius && (params.location.radius < 1 || params.location.radius > 500)) {
        errors.push('Search radius must be between 1 and 500 miles');
      }
    }
    
    // Platform-specific validation
    if (params.platform === 'facebook' && params.facebook?.daysSinceListed) {
      if (params.facebook.daysSinceListed < 1 || params.facebook.daysSinceListed > 30) {
        errors.push('Days since listed must be between 1 and 30');
      }
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
  
  /**
   * Create default search for gaming PCs
   */
  createDefaultSearch(platform: 'facebook' | 'craigslist' | 'offerup'): SearchParameters {
    return {
      platform,
      keywords: ['gaming pc', 'gaming computer'],
      minPrice: 200,
      maxPrice: 2000,
      location: {
        radius: 25
      },
      condition: ['used', 'like-new'],
      filters: [],
      enabled: true,
      interval: 30,
      notifications: true,
      
      // Platform defaults
      facebook: platform === 'facebook' ? {
        sortBy: 'date',
        daysSinceListed: 7,
        delivery: 'local'
      } : undefined,
      
      craigslist: platform === 'craigslist' ? {
        hasImage: true,
        section: 'sya',
        searchTitlesOnly: false
      } : undefined,
      
      offerup: platform === 'offerup' ? {
        radius: 25,
        priceNegotiable: true,
        sellerType: 'owner'
      } : undefined
    };
  }
  
  /**
   * Export search as shareable config
   */
  exportSearch(params: SearchParameters): string {
    const config = {
      version: '1.0',
      created: new Date().toISOString(),
      search: params
    };
    
    return btoa(JSON.stringify(config));
  }
  
  /**
   * Import search from config string
   */
  importSearch(configString: string): SearchParameters | null {
    try {
      const config = JSON.parse(atob(configString));
      if (config.version === '1.0' && config.search) {
        return config.search;
      }
    } catch (e) {
      console.error('Failed to import search config:', e);
    }
    
    return null;
  }
}

// Export singleton
export const searchBuilder = new SearchBuilder();