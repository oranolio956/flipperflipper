/**
 * Photo OCR Extractor
 * Extract specs from PC photos using Tesseract.js
 */

export interface OCRResult {
  text: string;
  confidence: number;
  specs: ExtractedSpecs;
  regions: OCRRegion[];
}

export interface OCRRegion {
  text: string;
  bbox: { x: number; y: number; width: number; height: number };
  confidence: number;
}

export interface ExtractedSpecs {
  cpu?: string;
  gpu?: string;
  ram?: string;
  storage?: string[];
  motherboard?: string;
  psu?: string;
  case?: string;
  cooler?: string;
}

// Common spec patterns
const SPEC_PATTERNS = {
  cpu: [
    /(?:intel\s*)?(?:core\s*)?i[3579]-?\d{4,5}[a-z]*/gi,
    /ryzen\s*[3579]\s*\d{4}[a-z]*/gi,
    /xeon\s*[ew]-?\d{4}/gi,
  ],
  gpu: [
    /(?:rtx|gtx)\s*\d{4}(?:\s*ti)?(?:\s*super)?/gi,
    /radeon\s*rx\s*\d{4}(?:\s*xt)?/gi,
    /(?:rtx|gtx)\s*\d{2}[67]0(?:\s*ti)?/gi,
    /arc\s*a\d{3,4}/gi,
  ],
  ram: [
    /\d{1,3}\s*gb\s*(?:ddr[345])?(?:\s*ram)?/gi,
    /\d{4,5}\s*mhz/gi,
  ],
  storage: [
    /\d{3,4}\s*gb\s*(?:ssd|hdd|nvme)/gi,
    /\d{1,2}\s*tb\s*(?:ssd|hdd|nvme)/gi,
    /(?:samsung|crucial|western|wd|seagate)\s*\w+/gi,
  ],
  motherboard: [
    /(?:asus|msi|gigabyte|asrock)\s*[a-z]\d{3,4}/gi,
    /(?:x570|x470|b550|b450|z690|z590|b660)/gi,
  ],
  psu: [
    /\d{3,4}\s*w(?:att)?/gi,
    /(?:corsair|evga|seasonic)\s*\w+/gi,
    /80\+\s*(?:gold|silver|bronze|platinum)/gi,
  ],
  case: [
    /(?:nzxt|corsair|fractal|lian\s*li|phanteks)\s*[a-z0-9\s-]+/gi,
  ],
  cooler: [
    /(?:noctua|corsair|cooler\s*master|arctic)\s*[a-z0-9\s-]+/gi,
    /(?:aio|liquid|air)\s*cool(?:er|ing)?/gi,
  ],
};

/**
 * Extract specs from OCR text
 */
export function extractSpecsFromText(text: string): ExtractedSpecs {
  const specs: ExtractedSpecs = {};
  const normalizedText = normalizeText(text);
  
  // CPU
  for (const pattern of SPEC_PATTERNS.cpu) {
    const match = normalizedText.match(pattern);
    if (match) {
      specs.cpu = cleanSpec(match[0]);
      break;
    }
  }
  
  // GPU
  for (const pattern of SPEC_PATTERNS.gpu) {
    const match = normalizedText.match(pattern);
    if (match) {
      specs.gpu = cleanSpec(match[0]);
      break;
    }
  }
  
  // RAM
  const ramMatches: string[] = [];
  for (const pattern of SPEC_PATTERNS.ram) {
    const matches = normalizedText.match(pattern);
    if (matches) {
      ramMatches.push(...matches);
    }
  }
  if (ramMatches.length > 0) {
    specs.ram = combineRamSpecs(ramMatches);
  }
  
  // Storage
  const storageMatches: string[] = [];
  for (const pattern of SPEC_PATTERNS.storage) {
    const matches = normalizedText.match(pattern);
    if (matches) {
      storageMatches.push(...matches);
    }
  }
  if (storageMatches.length > 0) {
    specs.storage = storageMatches.map(s => cleanSpec(s));
  }
  
  // Motherboard
  for (const pattern of SPEC_PATTERNS.motherboard) {
    const match = normalizedText.match(pattern);
    if (match) {
      specs.motherboard = cleanSpec(match[0]);
      break;
    }
  }
  
  // PSU
  for (const pattern of SPEC_PATTERNS.psu) {
    const match = normalizedText.match(pattern);
    if (match) {
      specs.psu = cleanSpec(match[0]);
      break;
    }
  }
  
  // Case
  for (const pattern of SPEC_PATTERNS.case) {
    const match = normalizedText.match(pattern);
    if (match) {
      specs.case = cleanSpec(match[0]);
      break;
    }
  }
  
  // Cooler
  for (const pattern of SPEC_PATTERNS.cooler) {
    const match = normalizedText.match(pattern);
    if (match) {
      specs.cooler = cleanSpec(match[0]);
      break;
    }
  }
  
  return specs;
}

/**
 * Preprocess image for better OCR
 */
export function preprocessImage(imageData: ImageData): ImageData {
  const data = new Uint8ClampedArray(imageData.data);
  const width = imageData.width;
  const height = imageData.height;
  
  // Convert to grayscale
  for (let i = 0; i < data.length; i += 4) {
    const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
    data[i] = gray;
    data[i + 1] = gray;
    data[i + 2] = gray;
  }
  
  // Increase contrast
  const contrast = 1.5;
  for (let i = 0; i < data.length; i += 4) {
    data[i] = Math.min(255, Math.max(0, (data[i] - 128) * contrast + 128));
    data[i + 1] = data[i];
    data[i + 2] = data[i];
  }
  
  return new ImageData(data, width, height);
}

/**
 * Find spec regions in image
 */
export function findSpecRegions(regions: OCRRegion[]): Map<keyof ExtractedSpecs, OCRRegion[]> {
  const specRegions = new Map<keyof ExtractedSpecs, OCRRegion[]>();
  
  for (const region of regions) {
    const text = region.text.toLowerCase();
    
    // Check each spec type
    for (const [specType, patterns] of Object.entries(SPEC_PATTERNS)) {
      for (const pattern of patterns) {
        if (text.match(pattern)) {
          const existing = specRegions.get(specType as keyof ExtractedSpecs) || [];
          existing.push(region);
          specRegions.set(specType as keyof ExtractedSpecs, existing);
          break;
        }
      }
    }
  }
  
  return specRegions;
}

/**
 * Calculate OCR confidence
 */
export function calculateConfidence(
  regions: OCRRegion[],
  extractedSpecs: ExtractedSpecs
): number {
  if (regions.length === 0) return 0;
  
  // Average confidence of regions
  const avgConfidence = regions.reduce((sum, r) => sum + r.confidence, 0) / regions.length;
  
  // Bonus for finding key specs
  let specBonus = 0;
  if (extractedSpecs.cpu) specBonus += 0.15;
  if (extractedSpecs.gpu) specBonus += 0.15;
  if (extractedSpecs.ram) specBonus += 0.1;
  if (extractedSpecs.storage?.length) specBonus += 0.1;
  
  return Math.min(1, avgConfidence + specBonus);
}

// Helper functions
function normalizeText(text: string): string {
  return text
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .replace(/[^\w\s\d-+]/g, ' ')
    .trim();
}

function cleanSpec(spec: string): string {
  return spec
    .trim()
    .replace(/\s+/g, ' ')
    .replace(/^-+|-+$/g, '');
}

function combineRamSpecs(matches: string[]): string {
  // Look for capacity
  const capacityMatch = matches.find(m => /\d+\s*gb/i.test(m));
  const speedMatch = matches.find(m => /\d{4}\s*mhz/i.test(m));
  
  if (capacityMatch && speedMatch) {
    return `${capacityMatch} ${speedMatch}`;
  }
  
  return capacityMatch || matches[0];
}

/**
 * Mock OCR function for testing
 * In production, this would use Tesseract.js Worker
 */
export async function performOCR(imageData: ImageData): Promise<OCRResult> {
  // This is a mock - real implementation would use Tesseract.js
  const mockText = "Intel Core i7-12700K RTX 3080 32GB DDR4 3200MHz 1TB NVMe SSD";
  const mockRegions: OCRRegion[] = [
    {
      text: "Intel Core i7-12700K",
      bbox: { x: 10, y: 10, width: 200, height: 30 },
      confidence: 0.95,
    },
    {
      text: "RTX 3080",
      bbox: { x: 10, y: 50, width: 100, height: 30 },
      confidence: 0.92,
    },
  ];
  
  const specs = extractSpecsFromText(mockText);
  const confidence = calculateConfidence(mockRegions, specs);
  
  return {
    text: mockText,
    confidence,
    specs,
    regions: mockRegions,
  };
}