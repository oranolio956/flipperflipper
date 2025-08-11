// ListingParser v3.5.0 - Extract structured data from listings
class ListingParser {
  constructor() {
    this.patterns = {
      gpu: /\b(RTX|GTX|RX|Arc)\s*\d{4}\w*/gi,
      cpu: /\b(i[357]|Ryzen\s*[357]|Xeon)\s*\d{4}\w*/gi,
      ram: /\b\d{1,3}\s*GB\s*(RAM|Memory|DDR)/gi,
      storage: /\b\d+\s*(GB|TB)\s*(SSD|HDD|NVMe)/gi,
      price: /\$\s*\d+\.?\d*/g
    };
  }
  
  parse(listing) {
    const text = `${listing.title} ${listing.description}`.toLowerCase();
    
    return {
      ...listing,
      specs: this.extractSpecs(text),
      condition: this.assessCondition(text),
      analysis: this.analyzeDeal(listing)
    };
  }
  
  extractSpecs(text) {
    return {
      gpu: this.extract(text, this.patterns.gpu),
      cpu: this.extract(text, this.patterns.cpu),
      ram: this.extract(text, this.patterns.ram),
      storage: this.extract(text, this.patterns.storage)
    };
  }
  
  extract(text, pattern) {
    const matches = text.match(pattern);
    return matches ? matches[0] : null;
  }
  
  assessCondition(text) {
    const conditions = {
      'like new': 0.95,
      'excellent': 0.90,
      'very good': 0.85,
      'good': 0.80,
      'fair': 0.70,
      'parts': 0.50
    };
    
    for (const [term, score] of Object.entries(conditions)) {
      if (text.includes(term)) {
        return { term, score };
      }
    }
    
    return { term: 'unknown', score: 0.75 };
  }
  
  analyzeDeal(listing) {
    const specs = this.extractSpecs(`${listing.title} ${listing.description}`);
    const fmv = this.calculateFMV(specs);
    const profit = fmv - listing.price;
    const roi = (profit / listing.price) * 100;
    
    return {
      fmv,
      profit,
      roi,
      rating: this.rateDeal(roi)
    };
  }
  
  calculateFMV(specs) {
    // Simplified FMV calculation
    let value = 400; // Base value
    
    if (specs.gpu) {
      if (specs.gpu.includes('3080')) value += 500;
      else if (specs.gpu.includes('3070')) value += 400;
      else if (specs.gpu.includes('3060')) value += 300;
    }
    
    if (specs.cpu) {
      if (specs.cpu.includes('i7')) value += 200;
      else if (specs.cpu.includes('i5')) value += 150;
    }
    
    return value;
  }
  
  rateDeal(roi) {
    if (roi >= 50) return 'excellent';
    if (roi >= 30) return 'good';
    if (roi >= 20) return 'fair';
    return 'poor';
  }
}

window.listingParser = new ListingParser();
