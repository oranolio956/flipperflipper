/**
 * Listing Parser v3.5.0 - Apple-level Intelligence
 * Extracts maximum value from marketplace listings with ML-like pattern recognition
 */

export interface ParsedListing {
  // Core identifiers
  id: string;
  platform: 'facebook' | 'craigslist' | 'offerup';
  url: string;
  scrapedAt: string;
  
  // Basic info
  title: string;
  description: string;
  price: number;
  originalPrice?: number; // If price was reduced
  
  // Enhanced location data
  location: {
    text: string;
    distance?: number;
    unit?: 'mi' | 'km';
    city?: string;
    state?: string;
    zip?: string;
    coordinates?: { lat: number; lng: number };
  };
  
  // Seller info
  seller: {
    name?: string;
    id?: string;
    responseTime?: string;
    memberSince?: string;
    rating?: number;
    verified?: boolean;
  };
  
  // Listing metadata
  posted: string;
  updated?: string;
  views?: number;
  saves?: number;
  
  // Images with analysis
  images: Array<{
    url: string;
    isPrimary: boolean;
    caption?: string;
    ocrText?: string; // Text detected in image
  }>;
  
  // Extracted specifications
  specs: {
    // CPU
    cpu?: {
      brand: 'Intel' | 'AMD' | string;
      model: string;
      generation?: number;
      cores?: number;
      threads?: number;
    };
    
    // GPU
    gpu?: {
      brand: 'NVIDIA' | 'AMD' | string;
      model: string;
      vram?: number;
      quantity?: number;
    };
    
    // Memory
    ram?: {
      capacity: number; // GB
      type?: 'DDR3' | 'DDR4' | 'DDR5';
      speed?: number; // MHz
      sticks?: number;
    };
    
    // Storage
    storage?: Array<{
      type: 'SSD' | 'HDD' | 'NVMe' | 'M.2';
      capacity: number; // GB
      brand?: string;
    }>;
    
    // Other components
    motherboard?: string;
    psu?: {
      wattage: number;
      rating?: '80+' | '80+ Bronze' | '80+ Gold' | '80+ Platinum';
    };
    case?: string;
    cooling?: string;
    
    // Peripherals included
    peripherals?: string[];
  };
  
  // Condition assessment
  condition: {
    stated?: 'new' | 'like new' | 'good' | 'fair' | 'parts';
    age?: string; // "6 months old", "bought last year"
    issues?: string[];
    upgradable?: boolean;
  };
  
  // Intelligence scores
  scores: {
    titleQuality: number; // 0-100
    descriptionQuality: number; // 0-100
    specCompleteness: number; // 0-100
    priceConfidence: number; // 0-100
    legitimacy: number; // 0-100 (scam detection)
  };
  
  // Profit analysis
  analysis: {
    estimatedValue: number;
    profitPotential: number;
    roi: number; // percentage
    dealQuality: 'excellent' | 'good' | 'fair' | 'poor';
    risks: string[];
    opportunities: string[];
  };
  
  // Extracted keywords for search
  keywords: string[];
  
  // Flags
  flags: {
    isBundle: boolean;
    hasWarranty: boolean;
    isNegotiable: boolean;
    isUrgent: boolean;
    hasShipping: boolean;
    acceptsTrades: boolean;
  };
}

export class ListingParser {
  // Component patterns with confidence scores
  private patterns = {
    cpu: {
      intel: [
        { regex: /i[3579]-?\d{4,5}[a-z]?/gi, confidence: 0.95 },
        { regex: /core\s*i[3579]/gi, confidence: 0.85 },
        { regex: /intel.*?gen/gi, confidence: 0.7 }
      ],
      amd: [
        { regex: /ryzen\s*[3579]\s*\d{4}[a-z]?/gi, confidence: 0.95 },
        { regex: /ryzen.*?[3579]00/gi, confidence: 0.85 },
        { regex: /amd.*?series/gi, confidence: 0.7 }
      ]
    },
    gpu: {
      nvidia: [
        { regex: /rtx\s*[234]0[6789]0(\s*ti)?/gi, confidence: 0.95 },
        { regex: /gtx\s*1[06][5678]0(\s*ti)?/gi, confidence: 0.95 },
        { regex: /nvidia.*?gb/gi, confidence: 0.8 }
      ],
      amd: [
        { regex: /rx\s*[567][0-9]00(\s*xt)?/gi, confidence: 0.95 },
        { regex: /radeon.*?[567]00/gi, confidence: 0.85 }
      ]
    },
    ram: {
      capacity: [
        { regex: /(\d{1,2})\s*gb\s*(ram|memory|ddr)/gi, confidence: 0.9 },
        { regex: /(\d{1,2})\s*gigabyte/gi, confidence: 0.7 }
      ],
      type: [
        { regex: /ddr[345]/gi, confidence: 0.95 },
        { regex: /(\d{4,5})\s*mhz/gi, confidence: 0.85 }
      ]
    },
    storage: {
      ssd: [
        { regex: /(\d{3,4})\s*gb\s*ssd/gi, confidence: 0.95 },
        { regex: /(\d+)\s*tb\s*ssd/gi, confidence: 0.95 },
        { regex: /nvme|m\.2/gi, confidence: 0.9 }
      ],
      hdd: [
        { regex: /(\d+)\s*[gt]b\s*hdd/gi, confidence: 0.9 },
        { regex: /(\d+)\s*[gt]b\s*hard/gi, confidence: 0.85 }
      ]
    }
  };
  
  // Price analysis thresholds
  private marketPrices = {
    cpu: {
      'i9-13900K': 500, 'i7-13700K': 350, 'i5-13600K': 250,
      'Ryzen 9 7900X': 450, 'Ryzen 7 7700X': 300, 'Ryzen 5 7600X': 200
    },
    gpu: {
      'RTX 4090': 1500, 'RTX 4080': 1000, 'RTX 4070 Ti': 700,
      'RTX 3080': 500, 'RTX 3070': 350, 'RTX 3060': 250,
      'RX 7900 XTX': 900, 'RX 6800 XT': 450, 'RX 6700 XT': 300
    }
  };
  
  /**
   * Parse a raw listing into structured data
   */
  parse(rawListing: any, html?: string): ParsedListing {
    const text = `${rawListing.title} ${rawListing.description || ''}`.toLowerCase();
    
    const parsed: ParsedListing = {
      id: rawListing.id,
      platform: rawListing.platform,
      url: rawListing.url,
      scrapedAt: rawListing.foundAt || new Date().toISOString(),
      
      title: this.cleanTitle(rawListing.title),
      description: rawListing.description || this.extractDescription(html),
      price: this.parsePrice(rawListing.price),
      
      location: this.parseLocation(rawListing.location, html),
      seller: this.parseSeller(html),
      
      posted: rawListing.foundAt,
      images: this.parseImages(rawListing.images || [], html),
      
      specs: this.extractSpecs(text, html),
      condition: this.assessCondition(text),
      
      scores: this.calculateScores(rawListing, text),
      analysis: {} as any, // Will be filled after specs extraction
      
      keywords: this.extractKeywords(text),
      flags: this.extractFlags(text)
    };
    
    // Calculate analysis after we have specs
    parsed.analysis = this.analyzeProfit(parsed);
    
    return parsed;
  }
  
  private cleanTitle(title: string): string {
    // Remove common spam patterns
    return title
      .replace(/[🔥💯⭐️✨🎮💻]/g, '')
      .replace(/\s+/g, ' ')
      .replace(/!{2,}/g, '!')
      .trim();
  }
  
  private parsePrice(price: any): number {
    if (typeof price === 'number') return price;
    
    const cleaned = String(price).replace(/[^0-9.]/g, '');
    return parseFloat(cleaned) || 0;
  }
  
  private parseLocation(location: any, html?: string): ParsedListing['location'] {
    const result: ParsedListing['location'] = {
      text: location || 'Unknown'
    };
    
    // Extract distance
    const distanceMatch = String(location).match(/(\d+)\s*(mi|km|miles?|kilometers?)/i);
    if (distanceMatch) {
      result.distance = parseInt(distanceMatch[1]);
      result.unit = distanceMatch[2].toLowerCase().startsWith('k') ? 'km' : 'mi';
    }
    
    // Try to extract city/state from various formats
    const cityStateMatch = String(location).match(/([A-Za-z\s]+),\s*([A-Z]{2})/);
    if (cityStateMatch) {
      result.city = cityStateMatch[1].trim();
      result.state = cityStateMatch[2];
    }
    
    return result;
  }
  
  private parseSeller(html?: string): ParsedListing['seller'] {
    // Would parse from HTML if available
    return {};
  }
  
  private parseImages(images: any[], html?: string): ParsedListing['images'] {
    if (!Array.isArray(images)) return [];
    
    return images.map((img, index) => ({
      url: typeof img === 'string' ? img : img.url,
      isPrimary: index === 0,
      caption: typeof img === 'object' ? img.caption : undefined
    }));
  }
  
  private extractDescription(html?: string): string {
    if (!html) return '';
    
    // Remove HTML tags and clean up
    return html
      .replace(/<[^>]*>/g, ' ')
      .replace(/\s+/g, ' ')
      .substring(0, 5000)
      .trim();
  }
  
  private extractSpecs(text: string, html?: string): ParsedListing['specs'] {
    const specs: ParsedListing['specs'] = {};
    
    // Extract CPU
    specs.cpu = this.extractCPU(text);
    
    // Extract GPU
    specs.gpu = this.extractGPU(text);
    
    // Extract RAM
    specs.ram = this.extractRAM(text);
    
    // Extract Storage
    specs.storage = this.extractStorage(text);
    
    // Extract PSU
    specs.psu = this.extractPSU(text);
    
    // Extract other components
    specs.motherboard = this.extractMotherboard(text);
    specs.case = this.extractCase(text);
    specs.cooling = this.extractCooling(text);
    
    return specs;
  }
  
  private extractCPU(text: string): ParsedListing['specs']['cpu'] | undefined {
    let bestMatch: any = null;
    let highestConfidence = 0;
    
    // Check Intel patterns
    for (const pattern of this.patterns.cpu.intel) {
      const matches = text.match(pattern.regex);
      if (matches && pattern.confidence > highestConfidence) {
        highestConfidence = pattern.confidence;
        bestMatch = {
          brand: 'Intel',
          model: matches[0],
          generation: this.extractIntelGeneration(matches[0])
        };
      }
    }
    
    // Check AMD patterns
    for (const pattern of this.patterns.cpu.amd) {
      const matches = text.match(pattern.regex);
      if (matches && pattern.confidence > highestConfidence) {
        highestConfidence = pattern.confidence;
        bestMatch = {
          brand: 'AMD',
          model: matches[0],
          generation: this.extractAMDGeneration(matches[0])
        };
      }
    }
    
    if (bestMatch) {
      // Extract core count if mentioned
      const coreMatch = text.match(/(\d+)\s*cores?/i);
      if (coreMatch) {
        bestMatch.cores = parseInt(coreMatch[1]);
      }
      
      return bestMatch;
    }
    
    return undefined;
  }
  
  private extractGPU(text: string): ParsedListing['specs']['gpu'] | undefined {
    let bestMatch: any = null;
    let highestConfidence = 0;
    
    // Check NVIDIA patterns
    for (const pattern of this.patterns.gpu.nvidia) {
      const matches = text.match(pattern.regex);
      if (matches && pattern.confidence > highestConfidence) {
        highestConfidence = pattern.confidence;
        bestMatch = {
          brand: 'NVIDIA',
          model: matches[0].toUpperCase()
        };
      }
    }
    
    // Check AMD patterns
    for (const pattern of this.patterns.gpu.amd) {
      const matches = text.match(pattern.regex);
      if (matches && pattern.confidence > highestConfidence) {
        highestConfidence = pattern.confidence;
        bestMatch = {
          brand: 'AMD',
          model: matches[0].toUpperCase()
        };
      }
    }
    
    if (bestMatch) {
      // Extract VRAM if mentioned
      const vramMatch = text.match(/(\d+)\s*gb\s*(vram|memory|gddr)/i);
      if (vramMatch) {
        bestMatch.vram = parseInt(vramMatch[1]);
      }
      
      // Check for multiple GPUs
      if (text.match(/dual|two|2x|sli|crossfire/i)) {
        bestMatch.quantity = 2;
      }
      
      return bestMatch;
    }
    
    return undefined;
  }
  
  private extractRAM(text: string): ParsedListing['specs']['ram'] | undefined {
    const capacityMatch = text.match(/(\d{1,3})\s*gb\s*(ram|memory|ddr)/i);
    if (!capacityMatch) return undefined;
    
    const ram: ParsedListing['specs']['ram'] = {
      capacity: parseInt(capacityMatch[1])
    };
    
    // Extract type
    const typeMatch = text.match(/ddr([345])/i);
    if (typeMatch) {
      ram.type = `DDR${typeMatch[1]}` as any;
    }
    
    // Extract speed
    const speedMatch = text.match(/(\d{4,5})\s*mhz/i);
    if (speedMatch) {
      ram.speed = parseInt(speedMatch[1]);
    }
    
    // Extract stick count
    const stickMatch = text.match(/(\d+)x(\d+)gb/i);
    if (stickMatch) {
      ram.sticks = parseInt(stickMatch[1]);
    }
    
    return ram;
  }
  
  private extractStorage(text: string): ParsedListing['specs']['storage'] | undefined {
    const storage: ParsedListing['specs']['storage'] = [];
    
    // Extract SSDs
    const ssdMatches = text.matchAll(/(\d+)\s*(gb|tb)\s*(ssd|nvme|m\.2)/gi);
    for (const match of ssdMatches) {
      const capacity = parseInt(match[1]) * (match[2].toLowerCase() === 'tb' ? 1000 : 1);
      storage.push({
        type: match[3].toLowerCase().includes('nvme') ? 'NVMe' : 
              match[3].toLowerCase().includes('m.2') ? 'M.2' : 'SSD',
        capacity
      });
    }
    
    // Extract HDDs
    const hddMatches = text.matchAll(/(\d+)\s*(gb|tb)\s*(hdd|hard\s*drive)/gi);
    for (const match of hddMatches) {
      const capacity = parseInt(match[1]) * (match[2].toLowerCase() === 'tb' ? 1000 : 1);
      storage.push({
        type: 'HDD',
        capacity
      });
    }
    
    return storage.length > 0 ? storage : undefined;
  }
  
  private extractPSU(text: string): ParsedListing['specs']['psu'] | undefined {
    const wattageMatch = text.match(/(\d{3,4})\s*w(att)?/i);
    if (!wattageMatch) return undefined;
    
    const psu: ParsedListing['specs']['psu'] = {
      wattage: parseInt(wattageMatch[1])
    };
    
    // Extract efficiency rating
    if (text.match(/80\+\s*platinum/i)) {
      psu.rating = '80+ Platinum';
    } else if (text.match(/80\+\s*gold/i)) {
      psu.rating = '80+ Gold';
    } else if (text.match(/80\+\s*bronze/i)) {
      psu.rating = '80+ Bronze';
    } else if (text.match(/80\+/i)) {
      psu.rating = '80+';
    }
    
    return psu;
  }
  
  private extractMotherboard(text: string): string | undefined {
    // Look for common motherboard patterns
    const patterns = [
      /\b[A-Z]\d{3}[A-Z]?\s*[A-Z]+/g, // B550M, X570, etc.
      /\b(asus|msi|gigabyte|asrock)\s*\w+/gi
    ];
    
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) return match[0];
    }
    
    return undefined;
  }
  
  private extractCase(text: string): string | undefined {
    const caseMatch = text.match(/(corsair|nzxt|fractal|cooler\s*master|lian\s*li)\s*\w+/i);
    return caseMatch ? caseMatch[0] : undefined;
  }
  
  private extractCooling(text: string): string | undefined {
    if (text.match(/liquid|water|aio/i)) {
      const sizeMatch = text.match(/(\d{3})mm/);
      return sizeMatch ? `${sizeMatch[1]}mm AIO` : 'Liquid Cooling';
    }
    
    if (text.match(/stock\s*cool/i)) {
      return 'Stock Cooler';
    }
    
    const coolerMatch = text.match(/(noctua|corsair|cooler\s*master)\s*\w+/i);
    return coolerMatch ? coolerMatch[0] : undefined;
  }
  
  private extractIntelGeneration(model: string): number | undefined {
    const match = model.match(/i[3579]-?(\d{1,2})/);
    if (match) {
      const num = parseInt(match[1]);
      return num < 20 ? num : Math.floor(num / 100);
    }
    return undefined;
  }
  
  private extractAMDGeneration(model: string): number | undefined {
    const match = model.match(/(\d)0{2,3}/);
    return match ? parseInt(match[1]) : undefined;
  }
  
  private assessCondition(text: string): ParsedListing['condition'] {
    const condition: ParsedListing['condition'] = {};
    
    // Check stated condition
    if (text.match(/new\s*in\s*box|nib|bnib|sealed/i)) {
      condition.stated = 'new';
    } else if (text.match(/like\s*new|barely\s*used|mint/i)) {
      condition.stated = 'like new';
    } else if (text.match(/good\s*condition|well\s*maintained/i)) {
      condition.stated = 'good';
    } else if (text.match(/fair|some\s*wear/i)) {
      condition.stated = 'fair';
    } else if (text.match(/parts|broken|not\s*working/i)) {
      condition.stated = 'parts';
    }
    
    // Extract age
    const ageMatch = text.match(/(\d+)\s*(month|year)s?\s*old/i);
    if (ageMatch) {
      condition.age = ageMatch[0];
    } else if (text.match(/bought\s*last\s*(month|year)/i)) {
      condition.age = 'Less than 1 year old';
    }
    
    // Check for issues
    const issues = [];
    if (text.match(/no\s*gpu|gpu\s*not\s*included/i)) issues.push('No GPU');
    if (text.match(/no\s*storage|drive\s*not\s*included/i)) issues.push('No storage');
    if (text.match(/cosmetic|scratch|dent/i)) issues.push('Cosmetic damage');
    
    if (issues.length > 0) {
      condition.issues = issues;
    }
    
    // Check if upgradable
    condition.upgradable = text.match(/upgrad|expand|room\s*for/i) !== null;
    
    return condition;
  }
  
  private calculateScores(listing: any, text: string): ParsedListing['scores'] {
    return {
      titleQuality: this.scoreTitleQuality(listing.title),
      descriptionQuality: this.scoreDescriptionQuality(text),
      specCompleteness: this.scoreSpecCompleteness(text),
      priceConfidence: this.scorePriceConfidence(listing.price, text),
      legitimacy: this.scoreLegitimacy(listing, text)
    };
  }
  
  private scoreTitleQuality(title: string): number {
    let score = 100;
    
    // Deduct for ALL CAPS
    if (title === title.toUpperCase()) score -= 20;
    
    // Deduct for excessive punctuation
    const punctCount = (title.match(/[!?]/g) || []).length;
    score -= Math.min(punctCount * 5, 20);
    
    // Deduct for spam words
    if (title.match(/urgent|asap|must\s*go/i)) score -= 15;
    
    // Deduct for emojis
    if (title.match(/[🔥💯⭐️✨🎮💻]/)) score -= 10;
    
    return Math.max(score, 0);
  }
  
  private scoreDescriptionQuality(text: string): number {
    let score = 50; // Base score
    
    // Add points for length
    if (text.length > 500) score += 20;
    if (text.length > 1000) score += 10;
    
    // Add for technical details
    if (text.match(/specs|specifications/i)) score += 10;
    if (text.match(/benchmark|fps|performance/i)) score += 10;
    
    return Math.min(score, 100);
  }
  
  private scoreSpecCompleteness(text: string): number {
    let found = 0;
    const total = 6;
    
    if (this.extractCPU(text)) found++;
    if (this.extractGPU(text)) found++;
    if (this.extractRAM(text)) found++;
    if (this.extractStorage(text)) found++;
    if (this.extractPSU(text)) found++;
    if (this.extractMotherboard(text)) found++;
    
    return Math.round((found / total) * 100);
  }
  
  private scorePriceConfidence(price: any, text: string): number {
    let score = 80; // Base score
    
    // Higher confidence if price is mentioned in text
    if (text.match(/\$\d+/)) score += 10;
    
    // Lower confidence for round numbers (often placeholders)
    if (price % 100 === 0) score -= 10;
    
    // Lower confidence for very low prices
    if (price < 100) score -= 20;
    
    // Check for "or best offer"
    if (text.match(/obo|best\s*offer|negotiable/i)) score -= 5;
    
    return Math.max(score, 0);
  }
  
  private scoreLegitimacy(listing: any, text: string): number {
    let score = 100;
    
    // Red flags
    if (text.match(/western\s*union|money\s*gram|wire\s*transfer/i)) score -= 50;
    if (text.match(/shipping\s*only|no\s*local/i)) score -= 20;
    if (!listing.images || listing.images.length === 0) score -= 30;
    if (text.length < 50) score -= 20;
    
    // Price too good to be true
    const specs = this.extractSpecs(text, '');
    if (specs.gpu?.model && listing.price < 200) score -= 40;
    
    return Math.max(score, 0);
  }
  
  private extractKeywords(text: string): string[] {
    const keywords = new Set<string>();
    
    // Add component models
    const cpu = this.extractCPU(text);
    if (cpu) keywords.add(cpu.model.toLowerCase());
    
    const gpu = this.extractGPU(text);
    if (gpu) keywords.add(gpu.model.toLowerCase());
    
    // Add common search terms
    const terms = text.match(/\b(gaming|rgb|custom|built|water\s*cooled|overclocked)\b/gi);
    if (terms) {
      terms.forEach(term => keywords.add(term.toLowerCase()));
    }
    
    return Array.from(keywords);
  }
  
  private extractFlags(text: string): ParsedListing['flags'] {
    return {
      isBundle: text.match(/bundle|package|includes|comes\s*with/i) !== null,
      hasWarranty: text.match(/warranty|guaranteed/i) !== null,
      isNegotiable: text.match(/obo|negotiable|best\s*offer/i) !== null,
      isUrgent: text.match(/urgent|asap|must\s*go|moving/i) !== null,
      hasShipping: text.match(/ship|deliver/i) !== null,
      acceptsTrades: text.match(/trade|swap|exchange/i) !== null
    };
  }
  
  private analyzeProfit(listing: ParsedListing): ParsedListing['analysis'] {
    // Calculate estimated value based on components
    let estimatedValue = 0;
    const risks: string[] = [];
    const opportunities: string[] = [];
    
    // CPU value
    if (listing.specs.cpu) {
      const cpuValue = this.estimateComponentValue('cpu', listing.specs.cpu);
      estimatedValue += cpuValue;
      
      if (listing.specs.cpu.generation && listing.specs.cpu.generation >= 12) {
        opportunities.push('Current generation CPU');
      }
    } else {
      risks.push('CPU not specified');
    }
    
    // GPU value
    if (listing.specs.gpu) {
      const gpuValue = this.estimateComponentValue('gpu', listing.specs.gpu);
      estimatedValue += gpuValue * (listing.specs.gpu.quantity || 1);
      
      if (listing.specs.gpu.model.includes('RTX')) {
        opportunities.push('RTX card with DLSS support');
      }
    } else {
      risks.push('GPU not specified');
      estimatedValue += 200; // Assume basic GPU
    }
    
    // Other components (rough estimates)
    estimatedValue += (listing.specs.ram?.capacity || 16) * 3; // $3/GB RAM
    estimatedValue += 150; // Motherboard
    estimatedValue += 80; // Case
    estimatedValue += (listing.specs.psu?.wattage || 500) * 0.1; // PSU
    
    if (listing.specs.storage) {
      listing.specs.storage.forEach(drive => {
        estimatedValue += drive.type === 'SSD' || drive.type === 'NVMe' 
          ? drive.capacity * 0.08 
          : drive.capacity * 0.02;
      });
    }
    
    // Adjust for condition
    const conditionMultiplier = {
      'new': 1.0,
      'like new': 0.9,
      'good': 0.8,
      'fair': 0.65,
      'parts': 0.4
    }[listing.condition.stated || 'good'] || 0.75;
    
    estimatedValue *= conditionMultiplier;
    
    // Calculate profit metrics
    const profitPotential = estimatedValue - listing.price;
    const roi = (profitPotential / listing.price) * 100;
    
    // Determine deal quality
    let dealQuality: ParsedListing['analysis']['dealQuality'] = 'poor';
    if (roi > 50 && listing.scores.legitimacy > 70) {
      dealQuality = 'excellent';
    } else if (roi > 30 && listing.scores.legitimacy > 60) {
      dealQuality = 'good';
    } else if (roi > 15) {
      dealQuality = 'fair';
    }
    
    // Add more risks/opportunities
    if (listing.scores.legitimacy < 50) {
      risks.push('Possible scam - verify carefully');
    }
    
    if (listing.flags.isBundle) {
      opportunities.push('Bundle deal - potential extra value');
    }
    
    if (listing.flags.isUrgent) {
      opportunities.push('Seller motivated - negotiate');
    }
    
    if (listing.condition.issues?.length) {
      risks.push(...listing.condition.issues);
    }
    
    return {
      estimatedValue: Math.round(estimatedValue),
      profitPotential: Math.round(profitPotential),
      roi: Math.round(roi),
      dealQuality,
      risks,
      opportunities
    };
  }
  
  private estimateComponentValue(type: 'cpu' | 'gpu', component: any): number {
    // Use market prices if we have them
    const prices = type === 'cpu' ? this.marketPrices.cpu : this.marketPrices.gpu;
    
    for (const [model, price] of Object.entries(prices)) {
      if (component.model.toUpperCase().includes(model)) {
        return price * 0.6; // Used price is ~60% of new
      }
    }
    
    // Fallback estimates
    if (type === 'cpu') {
      if (component.brand === 'Intel' && component.model.includes('i9')) return 300;
      if (component.brand === 'Intel' && component.model.includes('i7')) return 200;
      if (component.brand === 'Intel' && component.model.includes('i5')) return 150;
      if (component.brand === 'AMD' && component.model.includes('9')) return 250;
      if (component.brand === 'AMD' && component.model.includes('7')) return 180;
      if (component.brand === 'AMD' && component.model.includes('5')) return 120;
    }
    
    if (type === 'gpu') {
      if (component.model.includes('4090')) return 1200;
      if (component.model.includes('4080')) return 800;
      if (component.model.includes('4070')) return 500;
      if (component.model.includes('3080')) return 400;
      if (component.model.includes('3070')) return 300;
      if (component.model.includes('3060')) return 200;
    }
    
    return 100; // Default fallback
  }
}

// Export singleton instance
export const listingParser = new ListingParser();