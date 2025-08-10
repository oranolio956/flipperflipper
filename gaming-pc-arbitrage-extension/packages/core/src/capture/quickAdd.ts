/**
 * Quick-Add Module
 * Rapid data entry for listings and deals
 */

export interface QuickAddListing {
  title: string;
  price: number;
  url?: string;
  location?: string;
  specs: QuickAddSpecs;
  source: 'manual' | 'voice' | 'ocr' | 'paste';
  confidence: number;
}

export interface QuickAddSpecs {
  cpu?: string;
  gpu?: string;
  ram?: string;
  storage?: string;
  other?: string[];
}

export interface ParsedQuickAdd {
  listing: QuickAddListing;
  suggestions: Suggestion[];
  validation: ValidationResult;
}

export interface Suggestion {
  field: string;
  current: string;
  suggested: string;
  confidence: number;
  reason: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

// Quick parse patterns
const QUICK_PATTERNS = {
  price: /\$?(\d{1,4})/,
  cpu: /(i[3579]|ryzen [3579])[^,\s]*/i,
  gpu: /(rtx|gtx|rx|arc)\s*\d{3,4}[^,\s]*/i,
  ram: /(\d{1,3})\s*gb/i,
  storage: /(\d{3,4})\s*gb|(\d{1,2})\s*tb/i,
};

/**
 * Parse quick-add text input
 */
export function parseQuickAddText(input: string): ParsedQuickAdd {
  const lines = input.trim().split('\n');
  const listing: QuickAddListing = {
    title: '',
    price: 0,
    specs: {},
    source: 'manual',
    confidence: 0.5,
  };
  
  const suggestions: Suggestion[] = [];
  const errors: string[] = [];
  const warnings: string[] = [];
  
  // Try to extract from single line or multi-line
  if (lines.length === 1) {
    // Single line format: "Gaming PC i7 RTX 3070 16GB $800"
    parseSingleLine(lines[0], listing, suggestions);
  } else {
    // Multi-line format
    parseMultiLine(lines, listing, suggestions);
  }
  
  // Validate
  if (!listing.price || listing.price < 50 || listing.price > 10000) {
    errors.push('Invalid price (must be $50-$10,000)');
  }
  
  if (!listing.specs.cpu && !listing.specs.gpu) {
    warnings.push('Missing CPU or GPU information');
  }
  
  // Generate title if missing
  if (!listing.title) {
    listing.title = generateTitle(listing.specs, listing.price);
  }
  
  // Add suggestions
  if (listing.specs.cpu) {
    const cpuSuggestion = suggestCpuNormalization(listing.specs.cpu);
    if (cpuSuggestion) suggestions.push(cpuSuggestion);
  }
  
  if (listing.specs.gpu) {
    const gpuSuggestion = suggestGpuNormalization(listing.specs.gpu);
    if (gpuSuggestion) suggestions.push(gpuSuggestion);
  }
  
  return {
    listing,
    suggestions,
    validation: {
      isValid: errors.length === 0,
      errors,
      warnings,
    },
  };
}

/**
 * Parse single line input
 */
function parseSingleLine(
  line: string,
  listing: QuickAddListing,
  suggestions: Suggestion[]
): void {
  // Extract price
  const priceMatch = line.match(QUICK_PATTERNS.price);
  if (priceMatch) {
    listing.price = parseInt(priceMatch[1]);
  }
  
  // Extract specs
  const cpuMatch = line.match(QUICK_PATTERNS.cpu);
  if (cpuMatch) {
    listing.specs.cpu = cpuMatch[0].trim();
  }
  
  const gpuMatch = line.match(QUICK_PATTERNS.gpu);
  if (gpuMatch) {
    listing.specs.gpu = gpuMatch[0].trim();
  }
  
  const ramMatch = line.match(QUICK_PATTERNS.ram);
  if (ramMatch) {
    listing.specs.ram = ramMatch[0].trim();
  }
  
  const storageMatch = line.match(QUICK_PATTERNS.storage);
  if (storageMatch) {
    listing.specs.storage = storageMatch[0].trim();
  }
  
  // Use remaining text as title
  let title = line;
  [priceMatch, cpuMatch, gpuMatch, ramMatch, storageMatch].forEach(match => {
    if (match) {
      title = title.replace(match[0], '');
    }
  });
  
  listing.title = title.trim() || 'Gaming PC';
}

/**
 * Parse multi-line input
 */
function parseMultiLine(
  lines: string[],
  listing: QuickAddListing,
  suggestions: Suggestion[]
): void {
  for (const line of lines) {
    const lower = line.toLowerCase();
    
    // Title (first line or explicit)
    if (lines.indexOf(line) === 0 || lower.includes('title:')) {
      listing.title = line.replace(/title:/i, '').trim();
      continue;
    }
    
    // Price
    if (lower.includes('price:') || lower.includes('$')) {
      const priceMatch = line.match(/\$?(\d{1,4})/);
      if (priceMatch) {
        listing.price = parseInt(priceMatch[1]);
      }
      continue;
    }
    
    // Location
    if (lower.includes('location:') || lower.includes('zip:')) {
      listing.location = line.replace(/location:|zip:/i, '').trim();
      continue;
    }
    
    // URL
    if (lower.includes('http') || lower.includes('marketplace')) {
      listing.url = line.trim();
      continue;
    }
    
    // CPU
    if (lower.includes('cpu:') || QUICK_PATTERNS.cpu.test(line)) {
      listing.specs.cpu = line.replace(/cpu:/i, '').trim();
      continue;
    }
    
    // GPU
    if (lower.includes('gpu:') || lower.includes('graphics:') || QUICK_PATTERNS.gpu.test(line)) {
      listing.specs.gpu = line.replace(/gpu:|graphics:/i, '').trim();
      continue;
    }
    
    // RAM
    if (lower.includes('ram:') || lower.includes('memory:') || QUICK_PATTERNS.ram.test(line)) {
      listing.specs.ram = line.replace(/ram:|memory:/i, '').trim();
      continue;
    }
    
    // Storage
    if (lower.includes('storage:') || lower.includes('ssd:') || lower.includes('hdd:')) {
      listing.specs.storage = line.replace(/storage:|ssd:|hdd:/i, '').trim();
      continue;
    }
    
    // Other specs
    if (!listing.specs.other) listing.specs.other = [];
    listing.specs.other.push(line.trim());
  }
}

/**
 * Generate title from specs
 */
function generateTitle(specs: QuickAddSpecs, price: number): string {
  const parts: string[] = ['Gaming PC'];
  
  if (specs.cpu) {
    parts.push(specs.cpu.split(' ').slice(0, 2).join(' '));
  }
  
  if (specs.gpu) {
    parts.push(specs.gpu.split(' ').slice(0, 2).join(' '));
  }
  
  if (specs.ram) {
    parts.push(specs.ram);
  }
  
  if (price > 0) {
    parts.push(`$${price}`);
  }
  
  return parts.join(' - ');
}

/**
 * Suggest CPU normalization
 */
function suggestCpuNormalization(cpu: string): Suggestion | null {
  const lower = cpu.toLowerCase();
  
  // Intel normalization
  if (lower.includes('i3') || lower.includes('i5') || lower.includes('i7') || lower.includes('i9')) {
    const normalized = cpu.replace(/\s+/g, ' ')
      .replace(/intel\s*core\s*/i, '')
      .replace(/(\d{4,5})\s*([a-z])/i, '$1$2')
      .trim();
    
    if (normalized !== cpu) {
      return {
        field: 'cpu',
        current: cpu,
        suggested: `Intel Core ${normalized}`,
        confidence: 0.9,
        reason: 'Standardized Intel CPU format',
      };
    }
  }
  
  // AMD normalization
  if (lower.includes('ryzen')) {
    const normalized = cpu.replace(/\s+/g, ' ')
      .replace(/amd\s*/i, '')
      .trim();
    
    if (normalized !== cpu) {
      return {
        field: 'cpu',
        current: cpu,
        suggested: `AMD ${normalized}`,
        confidence: 0.9,
        reason: 'Standardized AMD CPU format',
      };
    }
  }
  
  return null;
}

/**
 * Suggest GPU normalization
 */
function suggestGpuNormalization(gpu: string): Suggestion | null {
  const lower = gpu.toLowerCase();
  
  // NVIDIA normalization
  if (lower.includes('rtx') || lower.includes('gtx')) {
    const normalized = gpu.toUpperCase()
      .replace(/NVIDIA|GEFORCE/gi, '')
      .replace(/\s+/g, ' ')
      .trim();
    
    if (normalized !== gpu) {
      return {
        field: 'gpu',
        current: gpu,
        suggested: normalized,
        confidence: 0.9,
        reason: 'Standardized NVIDIA GPU format',
      };
    }
  }
  
  // AMD normalization
  if (lower.includes('rx') || lower.includes('radeon')) {
    const normalized = gpu.replace(/amd\s*/i, '')
      .replace(/radeon\s*/i, '')
      .toUpperCase()
      .replace(/\s+/g, ' ')
      .trim();
    
    if (normalized !== gpu) {
      return {
        field: 'gpu',
        current: gpu,
        suggested: `RX ${normalized.replace('RX ', '')}`,
        confidence: 0.9,
        reason: 'Standardized AMD GPU format',
      };
    }
  }
  
  return null;
}

/**
 * Parse pasted content (e.g., from another listing)
 */
export function parsePastedContent(content: string): ParsedQuickAdd {
  // Try to detect format
  const lines = content.trim().split('\n');
  
  // Check if it looks like a Facebook listing
  if (content.includes('marketplace') || content.includes('·')) {
    return parseFacebookPaste(content);
  }
  
  // Check if it looks like specs list
  if (lines.length > 3 && lines.some(l => l.includes(':'))) {
    return parseSpecsList(lines);
  }
  
  // Fall back to general parsing
  return parseQuickAddText(content);
}

/**
 * Parse Facebook-style paste
 */
function parseFacebookPaste(content: string): ParsedQuickAdd {
  const listing: QuickAddListing = {
    title: '',
    price: 0,
    specs: {},
    source: 'paste',
    confidence: 0.7,
  };
  
  // Extract price (usually first $XXX)
  const priceMatch = content.match(/\$(\d{1,4})/);
  if (priceMatch) {
    listing.price = parseInt(priceMatch[1]);
  }
  
  // Extract title (usually first line)
  const lines = content.split('\n');
  if (lines.length > 0) {
    listing.title = lines[0].replace(/\$\d+/, '').trim();
  }
  
  // Extract specs from description
  const specsText = lines.slice(1).join(' ');
  const parsed = parseQuickAddText(specsText);
  listing.specs = parsed.listing.specs;
  
  return {
    listing,
    suggestions: parsed.suggestions,
    validation: parsed.validation,
  };
}

/**
 * Parse specs list format
 */
function parseSpecsList(lines: string[]): ParsedQuickAdd {
  const listing: QuickAddListing = {
    title: 'Gaming PC Build',
    price: 0,
    specs: {},
    source: 'paste',
    confidence: 0.8,
  };
  
  for (const line of lines) {
    if (line.includes(':')) {
      const [key, value] = line.split(':').map(s => s.trim());
      const keyLower = key.toLowerCase();
      
      if (keyLower.includes('cpu') || keyLower.includes('processor')) {
        listing.specs.cpu = value;
      } else if (keyLower.includes('gpu') || keyLower.includes('graphics')) {
        listing.specs.gpu = value;
      } else if (keyLower.includes('ram') || keyLower.includes('memory')) {
        listing.specs.ram = value;
      } else if (keyLower.includes('storage') || keyLower.includes('ssd') || keyLower.includes('hdd')) {
        listing.specs.storage = value;
      } else if (keyLower.includes('price')) {
        const priceMatch = value.match(/\$?(\d+)/);
        if (priceMatch) {
          listing.price = parseInt(priceMatch[1]);
        }
      }
    }
  }
  
  return parseQuickAddText(
    `${listing.title}\n${listing.price}\n${Object.values(listing.specs).join('\n')}`
  );
}