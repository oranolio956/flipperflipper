// SearchBuilder v3.5.0 - Multi-platform search URL builder
class SearchBuilder {
  constructor() {
    this.platforms = {
      facebook: {
        name: 'Facebook Marketplace',
        baseUrl: 'https://www.facebook.com/marketplace/search',
        params: {
          query: 'query',
          minPrice: 'minPrice',
          maxPrice: 'maxPrice',
          radius: 'radius',
          sort: 'sortBy'
        }
      },
      craigslist: {
        name: 'Craigslist',
        baseUrl: 'https://craigslist.org/search/sss',
        params: {
          query: 'query',
          minPrice: 'min_price',
          maxPrice: 'max_price',
          radius: 'search_distance'
        }
      },
      offerup: {
        name: 'OfferUp',
        baseUrl: 'https://offerup.com/search',
        params: {
          query: 'q',
          minPrice: 'price_min',
          maxPrice: 'price_max'
        }
      }
    };
  }
  
  buildSearchUrl(platform, keywords, filters = {}) {
    const config = this.platforms[platform];
    if (!config) throw new Error(`Unknown platform: ${platform}`);
    
    const params = new URLSearchParams();
    
    // Add keywords
    if (keywords.length > 0) {
      params.set(config.params.query, keywords.join(' '));
    }
    
    // Add filters
    Object.entries(filters).forEach(([key, value]) => {
      if (config.params[key] && value !== undefined) {
        params.set(config.params[key], value);
      }
    });
    
    return `${config.baseUrl}?${params.toString()}`;
  }
  
  suggestKeywords(category) {
    const suggestions = {
      gaming: ['gaming pc', 'gaming computer', 'rgb pc', 'custom pc'],
      gpu: ['rtx 3080', 'rtx 3070', 'rtx 3090', 'rx 6800'],
      cpu: ['i7', 'i9', 'ryzen 7', 'ryzen 9']
    };
    
    return suggestions[category] || [];
  }
}

window.searchBuilder = new SearchBuilder();
