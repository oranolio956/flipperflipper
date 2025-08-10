/**
 * Advanced Parser
 * ML-enhanced parsing with context understanding
 */

export interface ParseContext {
  platform: 'facebook' | 'craigslist' | 'offerup' | 'ebay';
  listingAge?: number; // days
  sellerHistory?: {
    listingCount: number;
    avgResponseTime?: number;
    rating?: number;
  };
  marketContext?: {
    avgPrice: number;
    priceRange: { min: number; max: number };
    demandLevel: 'high' | 'medium' | 'low';
  };
}

export interface EnhancedParseResult {
  confidence: number;
  specs: ParsedSpecs;
  insights: ParseInsight[];
  suggestions: ParseSuggestion[];
  anomalies: Anomaly[];
}

export interface ParsedSpecs {
  // Core components
  cpu?: ComponentSpec;
  gpu?: ComponentSpec;
  ram?: ComponentSpec;
  storage?: ComponentSpec[];
  motherboard?: ComponentSpec;
  psu?: ComponentSpec;
  case?: ComponentSpec;
  cooler?: ComponentSpec;
  
  // Additional details
  os?: string;
  peripherals?: string[];
  condition?: 'new' | 'like-new' | 'good' | 'fair' | 'parts';
  warranty?: { months: number; transferable: boolean };
}

export interface ComponentSpec {
  model: string;
  brand?: string;
  confidence: number;
  alternates?: string[]; // Possible alternatives if unsure
  metadata?: Record<string, any>;
}

export interface ParseInsight {
  type: 'missing-info' | 'inconsistency' | 'opportunity' | 'warning';
  message: string;
  priority: 'high' | 'medium' | 'low';
  field?: string;
}

export interface ParseSuggestion {
  field: string;
  suggestion: string;
  reasoning: string;
  confidence: number;
}

export interface Anomaly {
  type: 'price' | 'spec' | 'description' | 'photo';
  severity: 'high' | 'medium' | 'low';
  description: string;
  expectedValue?: any;
  actualValue?: any;
}

// Enhanced patterns with context
const CONTEXTUAL_PATTERNS = {
  cpu: {
    intel: {
      pattern: /(?:intel\s*)?(?:core\s*)?i([3579])[- ]?(\d{4,5})([a-z]*)/gi,
      extractor: (match: RegExpMatchArray) => ({
        series: `i${match[1]}`,
        model: match[2],
        suffix: match[3] || '',
        generation: inferIntelGeneration(match[2]),
      }),
    },
    amd: {
      pattern: /(?:amd\s*)?ryzen\s*([3579])\s*(\d{4})([a-z]*)/gi,
      extractor: (match: RegExpMatchArray) => ({
        series: `Ryzen ${match[1]}`,
        model: match[2],
        suffix: match[3] || '',
        generation: inferAMDGeneration(match[2]),
      }),
    },
  },
  gpu: {
    nvidia: {
      pattern: /(?:nvidia\s*)?(?:geforce\s*)?(rtx|gtx)\s*(\d{4})(?:\s*(ti|super))?/gi,
      extractor: (match: RegExpMatchArray) => ({
        series: match[1].toUpperCase(),
        model: match[2],
        variant: match[3] || '',
        vram: estimateVRAM(match[1], match[2], match[3]),
      }),
    },
    amd: {
      pattern: /(?:amd\s*)?(?:radeon\s*)?rx\s*(\d{4})(?:\s*(xt|xtx))?/gi,
      extractor: (match: RegExpMatchArray) => ({
        series: 'RX',
        model: match[1],
        variant: match[2] || '',
        vram: estimateVRAM('RX', match[1], match[2]),
      }),
    },
  },
};

/**
 * Advanced parse with ML enhancement
 */
export function advancedParse(
  text: string,
  context?: ParseContext
): EnhancedParseResult {
  const specs: ParsedSpecs = {};
  const insights: ParseInsight[] = [];
  const suggestions: ParseSuggestion[] = [];
  const anomalies: Anomaly[] = [];
  
  // Extract components with confidence
  specs.cpu = extractCPU(text);
  specs.gpu = extractGPU(text);
  specs.ram = extractRAM(text);
  specs.storage = extractStorage(text);
  specs.motherboard = extractMotherboard(text);
  specs.psu = extractPSU(text);
  specs.case = extractCase(text);
  specs.cooler = extractCooler(text);
  
  // Extract additional details
  specs.os = extractOS(text);
  specs.peripherals = extractPeripherals(text);
  specs.condition = extractCondition(text);
  specs.warranty = extractWarranty(text);
  
  // Generate insights
  if (!specs.cpu) {
    insights.push({
      type: 'missing-info',
      message: 'CPU information not found',
      priority: 'high',
      field: 'cpu',
    });
  }
  
  if (!specs.gpu) {
    insights.push({
      type: 'missing-info',
      message: 'GPU information not found',
      priority: 'high',
      field: 'gpu',
    });
  }
  
  // Check for inconsistencies
  if (specs.cpu && specs.motherboard) {
    const compatible = checkCompatibility(specs.cpu, specs.motherboard);
    if (!compatible) {
      insights.push({
        type: 'inconsistency',
        message: 'CPU and motherboard may not be compatible',
        priority: 'high',
      });
    }
  }
  
  // Detect anomalies
  if (context?.marketContext) {
    const priceAnomaly = detectPriceAnomaly(specs, context.marketContext);
    if (priceAnomaly) {
      anomalies.push(priceAnomaly);
    }
  }
  
  // Generate suggestions
  if (specs.cpu && !specs.cpu.brand) {
    suggestions.push({
      field: 'cpu.brand',
      suggestion: inferCPUBrand(specs.cpu.model),
      reasoning: 'Inferred from model number',
      confidence: 0.9,
    });
  }
  
  // Calculate overall confidence
  const componentConfidences = [
    specs.cpu?.confidence || 0,
    specs.gpu?.confidence || 0,
    specs.ram?.confidence || 0,
  ].filter(c => c > 0);
  
  const confidence = componentConfidences.length > 0
    ? componentConfidences.reduce((a, b) => a + b, 0) / componentConfidences.length
    : 0.1;
  
  return {
    confidence,
    specs,
    insights,
    suggestions,
    anomalies,
  };
}

/**
 * Extract CPU with alternatives
 */
function extractCPU(text: string): ComponentSpec | undefined {
  const normalizedText = text.toLowerCase();
  
  // Try Intel patterns
  for (const [brand, config] of Object.entries(CONTEXTUAL_PATTERNS.cpu)) {
    const matches = Array.from(normalizedText.matchAll(config.pattern));
    if (matches.length > 0) {
      const bestMatch = matches[0];
      const extracted = config.extractor(bestMatch);
      
      return {
        model: `${extracted.series}-${extracted.model}${extracted.suffix}`.toUpperCase(),
        brand: brand === 'intel' ? 'Intel' : 'AMD',
        confidence: calculateMatchConfidence(bestMatch, text),
        metadata: extracted,
        alternates: matches.slice(1).map(m => {
          const alt = config.extractor(m);
          return `${alt.series}-${alt.model}${alt.suffix}`.toUpperCase();
        }),
      };
    }
  }
  
  return undefined;
}

/**
 * Extract GPU with VRAM estimation
 */
function extractGPU(text: string): ComponentSpec | undefined {
  const normalizedText = text.toLowerCase();
  
  for (const [brand, config] of Object.entries(CONTEXTUAL_PATTERNS.gpu)) {
    const matches = Array.from(normalizedText.matchAll(config.pattern));
    if (matches.length > 0) {
      const bestMatch = matches[0];
      const extracted = config.extractor(bestMatch);
      
      const model = `${extracted.series} ${extracted.model}${extracted.variant ? ' ' + extracted.variant.toUpperCase() : ''}`;
      
      return {
        model,
        brand: brand === 'nvidia' ? 'NVIDIA' : 'AMD',
        confidence: calculateMatchConfidence(bestMatch, text),
        metadata: extracted,
      };
    }
  }
  
  return undefined;
}

/**
 * Extract RAM with speed detection
 */
function extractRAM(text: string): ComponentSpec | undefined {
  const capacityMatch = text.match(/(\d{1,3})\s*gb\s*(?:of\s*)?(?:ddr(\d))?(?:\s*ram)?/i);
  const speedMatch = text.match(/(\d{4,5})\s*mhz/i);
  
  if (capacityMatch) {
    const capacity = parseInt(capacityMatch[1]);
    const ddrVersion = capacityMatch[2] || '4';
    const speed = speedMatch ? parseInt(speedMatch[1]) : null;
    
    return {
      model: `${capacity}GB DDR${ddrVersion}${speed ? ` ${speed}MHz` : ''}`,
      confidence: 0.85,
      metadata: {
        capacity,
        ddrVersion,
        speed,
      },
    };
  }
  
  return undefined;
}

/**
 * Extract storage devices
 */
function extractStorage(text: string): ComponentSpec[] {
  const storageSpecs: ComponentSpec[] = [];
  
  // SSD/NVMe patterns
  const ssdMatches = text.matchAll(/(\d+)\s*(gb|tb)\s*(ssd|nvme|m\.2)/gi);
  for (const match of ssdMatches) {
    const capacity = parseInt(match[1]);
    const unit = match[2].toUpperCase();
    const type = match[3].toUpperCase();
    
    storageSpecs.push({
      model: `${capacity}${unit} ${type}`,
      confidence: 0.9,
      metadata: {
        capacity: unit === 'TB' ? capacity * 1000 : capacity,
        type: type.includes('NVME') || type.includes('M.2') ? 'nvme' : 'ssd',
      },
    });
  }
  
  // HDD patterns
  const hddMatches = text.matchAll(/(\d+)\s*(gb|tb)\s*(hdd|hard\s*drive)/gi);
  for (const match of hddMatches) {
    const capacity = parseInt(match[1]);
    const unit = match[2].toUpperCase();
    
    storageSpecs.push({
      model: `${capacity}${unit} HDD`,
      confidence: 0.9,
      metadata: {
        capacity: unit === 'TB' ? capacity * 1000 : capacity,
        type: 'hdd',
      },
    });
  }
  
  return storageSpecs;
}

// Helper functions
function extractMotherboard(text: string): ComponentSpec | undefined {
  const patterns = [
    /(?:asus|msi|gigabyte|asrock)\s*([a-z]\d{3,4}[a-z0-9\s-]*)/i,
    /(x570|x470|b550|b450|z690|z590|b660|h610)[a-z0-9\s-]*/i,
  ];
  
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      return {
        model: match[0].trim(),
        confidence: 0.7,
      };
    }
  }
  
  return undefined;
}

function extractPSU(text: string): ComponentSpec | undefined {
  const wattageMatch = text.match(/(\d{3,4})\s*w(?:att)?/i);
  const certMatch = text.match(/80\+?\s*(bronze|silver|gold|platinum|titanium)/i);
  
  if (wattageMatch) {
    const wattage = parseInt(wattageMatch[1]);
    const certification = certMatch ? certMatch[1] : null;
    
    return {
      model: `${wattage}W${certification ? ` 80+ ${certification}` : ''}`,
      confidence: 0.8,
      metadata: {
        wattage,
        certification,
      },
    };
  }
  
  return undefined;
}

function extractCase(text: string): ComponentSpec | undefined {
  const patterns = [
    /(nzxt|corsair|fractal|lian\s*li|phanteks|thermaltake)\s*([a-z0-9\s-]+)/i,
  ];
  
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      return {
        model: match[0].trim(),
        brand: match[1],
        confidence: 0.7,
      };
    }
  }
  
  return undefined;
}

function extractCooler(text: string): ComponentSpec | undefined {
  const patterns = [
    /(noctua|corsair|cooler\s*master|arctic|be\s*quiet)\s*([a-z0-9\s-]+)/i,
    /(\d{3,4}mm\s*aio|liquid\s*cool(?:er|ing)|air\s*cool(?:er|ing))/i,
  ];
  
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      return {
        model: match[0].trim(),
        confidence: 0.6,
      };
    }
  }
  
  return undefined;
}

function extractOS(text: string): string | undefined {
  const patterns = [
    /windows\s*(\d{1,2})\s*(home|pro|enterprise)?/i,
    /ubuntu|linux|debian|fedora/i,
    /mac\s*os/i,
  ];
  
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      return match[0];
    }
  }
  
  return undefined;
}

function extractPeripherals(text: string): string[] {
  const peripherals: string[] = [];
  
  const patterns = {
    monitor: /(\d{2,3})["\s-]*(inch|hz|monitor|display)/i,
    keyboard: /(mechanical|rgb|wireless)\s*keyboard/i,
    mouse: /(gaming|wireless|rgb)\s*mouse/i,
  };
  
  for (const [type, pattern] of Object.entries(patterns)) {
    if (pattern.test(text)) {
      peripherals.push(type);
    }
  }
  
  return peripherals;
}

function extractCondition(text: string): ParsedSpecs['condition'] {
  const patterns = {
    'new': /brand\s*new|new\s*in\s*box|nib|bnib/i,
    'like-new': /like\s*new|barely\s*used|mint/i,
    'good': /good\s*condition|lightly\s*used/i,
    'fair': /fair\s*condition|used|works/i,
    'parts': /for\s*parts|not\s*working|broken/i,
  };
  
  for (const [condition, pattern] of Object.entries(patterns)) {
    if (pattern.test(text)) {
      return condition as ParsedSpecs['condition'];
    }
  }
  
  return 'good'; // Default
}

function extractWarranty(text: string): ParsedSpecs['warranty'] {
  const warrantyMatch = text.match(/(\d+)\s*(month|year)s?\s*warranty/i);
  
  if (warrantyMatch) {
    const amount = parseInt(warrantyMatch[1]);
    const unit = warrantyMatch[2].toLowerCase();
    const months = unit === 'year' ? amount * 12 : amount;
    
    return {
      months,
      transferable: text.includes('transferable') || !text.includes('non-transferable'),
    };
  }
  
  return undefined;
}

// Utility functions
function calculateMatchConfidence(match: RegExpMatchArray, fullText: string): number {
  // Base confidence
  let confidence = 0.7;
  
  // Boost if match is in a prominent position
  if (match.index! < fullText.length * 0.3) {
    confidence += 0.1;
  }
  
  // Boost if surrounded by spec-like context
  const surrounding = fullText.substring(
    Math.max(0, match.index! - 20),
    Math.min(fullText.length, match.index! + match[0].length + 20)
  );
  
  if (/specs|components|build|includes/i.test(surrounding)) {
    confidence += 0.1;
  }
  
  return Math.min(0.95, confidence);
}

function inferIntelGeneration(model: string): number {
  const firstDigit = parseInt(model[0]);
  if (model.length === 5) {
    return firstDigit + 1; // e.g., 12700 = 12th gen
  } else if (model.length === 4) {
    return firstDigit + 1; // e.g., 9700 = 9th gen
  }
  return 0;
}

function inferAMDGeneration(model: string): number {
  const firstDigit = parseInt(model[0]);
  return firstDigit; // e.g., 5800 = 5000 series
}

function estimateVRAM(series: string, model: string, variant?: string): number {
  // Simplified VRAM estimation
  const vramMap: Record<string, number> = {
    'RTX4090': 24,
    'RTX4080': 16,
    'RTX4070TI': 12,
    'RTX4070': 12,
    'RTX3090': 24,
    'RTX3080': 10,
    'RTX3070': 8,
    'RTX3060': 12,
    'RX6900': 16,
    'RX6800': 16,
    'RX6700': 12,
  };
  
  const key = `${series}${model}${variant || ''}`.replace(/\s/g, '').toUpperCase();
  return vramMap[key] || 8;
}

function inferCPUBrand(model: string): string {
  if (/i[3579]/.test(model)) return 'Intel';
  if (/ryzen/i.test(model)) return 'AMD';
  return 'Unknown';
}

function checkCompatibility(cpu: ComponentSpec, motherboard: ComponentSpec): boolean {
  // Simplified compatibility check
  const cpuSocket = cpu.metadata?.socket;
  const moboSocket = motherboard.metadata?.socket;
  
  if (cpuSocket && moboSocket) {
    return cpuSocket === moboSocket;
  }
  
  // Basic heuristics
  if (cpu.brand === 'Intel' && motherboard.model.includes('AM4')) return false;
  if (cpu.brand === 'AMD' && motherboard.model.includes('LGA')) return false;
  
  return true; // Assume compatible if unsure
}

function detectPriceAnomaly(
  specs: ParsedSpecs,
  marketContext: { avgPrice: number; priceRange: { min: number; max: number } }
): Anomaly | null {
  // This would use the parsed specs to estimate value
  // and compare with market context
  // Simplified for example
  
  return null;
}