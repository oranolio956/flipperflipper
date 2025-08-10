/**
 * Photo Spec Extractor
 * Uses OCR to extract PC specifications from images
 */

import { ComponentDetector } from '../../parsers/component-detector';
import type { ExtractedSpecs, OCRResult } from '../../types';

export interface OCRResult {
  text: string;
  confidence: number;
  regions: OCRRegion[];
  metadata: {
    processingTime: number;
    imageSize: { width: number; height: number };
    language: string;
  };
}

export interface OCRRegion {
  text: string;
  confidence: number;
  boundingBox: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export interface ExtractedSpecs {
  cpu?: string;
  gpu?: string;
  ram?: string;
  storage?: string[];
  motherboard?: string;
  psu?: string;
  confidence: number;
  rawText: string;
}

// Common patterns in spec sheets
const SPEC_PATTERNS = {
  cpu: /(?:cpu|processor):\s*(.+?)(?:\n|$)/i,
  gpu: /(?:gpu|graphics|video card):\s*(.+?)(?:\n|$)/i,
  ram: /(?:ram|memory):\s*(\d+\s*gb)/i,
  storage: /(?:storage|ssd|hdd):\s*(.+?)(?:\n|$)/i,
  motherboard: /(?:motherboard|mobo):\s*(.+?)(?:\n|$)/i,
  psu: /(?:psu|power supply):\s*(\d+w)/i,
};

export class PhotoExtractor {
  private componentDetector: ComponentDetector;

  constructor() {
    this.componentDetector = new ComponentDetector();
  }

  /**
   * Extract specs from OCR text
   */
  extractSpecsFromText(ocrText: string): ExtractedSpecs {
    const specs: ExtractedSpecs = {
      confidence: 0,
      rawText: ocrText,
    };

    // Try pattern matching first
    for (const [component, pattern] of Object.entries(SPEC_PATTERNS)) {
      const match = ocrText.match(pattern);
      if (match) {
        switch (component) {
          case 'cpu':
            specs.cpu = match[1].trim();
            break;
          case 'gpu':
            specs.gpu = match[1].trim();
            break;
          case 'ram':
            specs.ram = match[1].trim();
            break;
          case 'storage':
            specs.storage = [match[1].trim()];
            break;
          case 'motherboard':
            specs.motherboard = match[1].trim();
            break;
          case 'psu':
            specs.psu = match[1].trim();
            break;
        }
      }
    }

    // Fall back to component detector
    const detected = this.componentDetector.detectAll(ocrText);
    
    if (!specs.cpu && detected.cpu) {
      specs.cpu = detected.cpu.model;
    }
    if (!specs.gpu && detected.gpu) {
      specs.gpu = detected.gpu.model;
    }
    if (!specs.ram && detected.ram && detected.ram.length > 0) {
      specs.ram = `${detected.ram[0].capacity}GB`;
    }
    if (!specs.storage && detected.storage && detected.storage.length > 0) {
      specs.storage = detected.storage.map(s => `${s.capacity}GB ${s.type}`);
    }

    // Calculate confidence based on how many specs we found
    const foundCount = [
      specs.cpu,
      specs.gpu,
      specs.ram,
      specs.storage && specs.storage.length > 0,
      specs.motherboard,
      specs.psu,
    ].filter(Boolean).length;

    specs.confidence = foundCount / 6;

    return specs;
  }

  /**
   * Preprocess image for better OCR results
   */
  preprocessImage(imageData: ImageData): ImageData {
    const data = new Uint8ClampedArray(imageData.data);
    
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
    
    return new ImageData(data, imageData.width, imageData.height);
  }

  /**
   * Find regions likely to contain spec information
   */
  findSpecRegions(ocrResult: OCRResult): OCRRegion[] {
    const specKeywords = [
      'cpu', 'processor', 'gpu', 'graphics', 'ram', 'memory',
      'storage', 'ssd', 'hdd', 'motherboard', 'psu', 'power'
    ];
    
    return ocrResult.regions.filter(region => {
      const lowerText = region.text.toLowerCase();
      return specKeywords.some(keyword => lowerText.includes(keyword));
    });
  }

  /**
   * Calculate overall confidence score
   */
  calculateConfidence(ocrResult: OCRResult, extractedSpecs: ExtractedSpecs): number {
    const ocrConfidence = ocrResult.confidence;
    const specConfidence = extractedSpecs.confidence;
    const textLength = ocrResult.text.length;
    
    // Penalize very short or very long texts
    const lengthPenalty = textLength < 50 ? 0.5 : textLength > 5000 ? 0.8 : 1.0;
    
    return ocrConfidence * specConfidence * lengthPenalty;
  }

  /**
   * Clean and normalize storage strings
   */
  private normalizeStorage(storageStrings: string[]): string[] {
    return storageStrings.map(str => {
      // Extract capacity
      const capacityMatch = str.match(/(\d+)\s*(gb|tb)/i);
      if (!capacityMatch) return str;
      
      const capacity = parseInt(capacityMatch[1]);
      const unit = capacityMatch[2].toUpperCase();
      const capacityGB = unit === 'TB' ? capacity * 1000 : capacity;
      
      // Detect type
      let type = 'HDD';
      if (str.toLowerCase().includes('ssd') || str.toLowerCase().includes('solid')) {
        type = 'SSD';
      } else if (str.toLowerCase().includes('nvme') || str.toLowerCase().includes('m.2')) {
        type = 'NVMe';
      }
      
      return `${capacityGB}GB ${type}`;
    });
  }
}

/**
 * Mock OCR function - in production, this would use Tesseract.js or similar
 */
export async function performOCR(imageData: ImageData): Promise<OCRResult> {
  // This is a placeholder - actual implementation would use Tesseract.js
  return {
    text: 'CPU: Intel Core i7-10700K\nGPU: NVIDIA RTX 3070\nRAM: 32GB DDR4\nStorage: 1TB NVMe SSD',
    confidence: 0.95,
    regions: [],
    metadata: {
      processingTime: 1500,
      imageSize: { width: imageData.width, height: imageData.height },
      language: 'en',
    },
  };
}

// Export the class as default and named export
export default PhotoExtractor;
export { PhotoExtractor as photoExtractor };