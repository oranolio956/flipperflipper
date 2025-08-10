/**
 * OCR Service Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the OCR worker patterns
const mockOCRPatterns = {
  extractCPU: (text: string) => {
    const patterns = [
      /i[357]-?\d{4,5}[A-Z]*/gi,
      /Ryzen\s+[357]\s+\d{4}[A-Z]*/gi,
    ];
    
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) return match[0];
    }
    return undefined;
  },
  
  extractGPU: (text: string) => {
    const patterns = [
      /RTX\s*\d{4}\s*(Ti|SUPER)?/gi,
      /GTX\s*\d{4}\s*(Ti|SUPER)?/gi,
      /RX\s*\d{4}\s*(XT)?/gi,
    ];
    
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) return match[0];
    }
    return undefined;
  },
  
  extractRAM: (text: string) => {
    const patterns = [
      /\d{1,2}\s*GB\s*(?:DDR[345]|RAM)/gi,
    ];
    
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) return match[0];
    }
    return undefined;
  },
  
  extractStorage: (text: string) => {
    const patterns = [
      /\d+\s*(?:GB|TB)\s*(?:SSD|HDD|NVMe|M\.2)/gi,
    ];
    
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) return match[0];
    }
    return undefined;
  },
  
  extractPSU: (text: string) => {
    const patterns = [
      /\d{3,4}\s*W(?:att)?/gi,
    ];
    
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) return match[0];
    }
    return undefined;
  },
};

describe('OCR Pattern Extraction', () => {
  it('should extract Intel CPU models', () => {
    const text = 'Gaming PC with Intel Core i7-10700K processor';
    expect(mockOCRPatterns.extractCPU(text)).toBe('i7-10700K');
  });

  it('should extract AMD CPU models', () => {
    const text = 'Built with AMD Ryzen 7 5800X';
    expect(mockOCRPatterns.extractCPU(text)).toBe('Ryzen 7 5800X');
  });

  it('should extract NVIDIA GPU models', () => {
    const text = 'Graphics: NVIDIA GeForce RTX 3080 Ti';
    expect(mockOCRPatterns.extractGPU(text)).toBe('RTX 3080 Ti');
  });

  it('should extract AMD GPU models', () => {
    const text = 'AMD Radeon RX 6700 XT installed';
    expect(mockOCRPatterns.extractGPU(text)).toBe('RX 6700 XT');
  });

  it('should extract RAM specifications', () => {
    const text = '32GB DDR4 RAM at 3600MHz';
    expect(mockOCRPatterns.extractRAM(text)).toBe('32GB DDR4');
  });

  it('should extract storage specifications', () => {
    const text = '1TB NVMe SSD for fast loading';
    expect(mockOCRPatterns.extractStorage(text)).toBe('1TB NVMe');
  });

  it('should extract PSU specifications', () => {
    const text = 'Powered by 750W Gold certified PSU';
    expect(mockOCRPatterns.extractPSU(text)).toBe('750W');
  });
});

describe('OCR Full Text Processing', () => {
  it('should extract all specs from a complete listing', () => {
    const text = `
      High-End Gaming Build
      
      CPU: Intel Core i9-12900K
      GPU: NVIDIA RTX 3090 Ti
      RAM: 64GB DDR5 RAM
      Storage: 2TB NVMe SSD
      PSU: 1000W Platinum
      
      Runs all games at 4K max settings!
    `;
    
    expect(mockOCRPatterns.extractCPU(text)).toBe('i9-12900K');
    expect(mockOCRPatterns.extractGPU(text)).toBe('RTX 3090 Ti');
    expect(mockOCRPatterns.extractRAM(text)).toBe('64GB DDR5');
    expect(mockOCRPatterns.extractStorage(text)).toBe('2TB NVMe');
    expect(mockOCRPatterns.extractPSU(text)).toBe('1000W');
  });

  it('should handle messy OCR output', () => {
    const text = `
      GA M I NG  PC
      
      lntel Core i5-11400F
      NVlDlA RTX3060 12GB
      16 GB DDR4 Memory
      512GB SSD Storage
      650 Watt PSU
    `;
    
    // Even with OCR errors, patterns should still match
    expect(mockOCRPatterns.extractCPU(text)).toBe('i5-11400F');
    expect(mockOCRPatterns.extractGPU(text)).toBe('RTX3060');
    expect(mockOCRPatterns.extractRAM(text)).toBe('16 GB DDR4');
    expect(mockOCRPatterns.extractStorage(text)).toBe('512GB SSD');
    expect(mockOCRPatterns.extractPSU(text)).toBe('650 Watt');
  });

  it('should return undefined for missing components', () => {
    const text = 'Gaming PC for sale, great condition!';
    
    expect(mockOCRPatterns.extractCPU(text)).toBeUndefined();
    expect(mockOCRPatterns.extractGPU(text)).toBeUndefined();
    expect(mockOCRPatterns.extractRAM(text)).toBeUndefined();
    expect(mockOCRPatterns.extractStorage(text)).toBeUndefined();
    expect(mockOCRPatterns.extractPSU(text)).toBeUndefined();
  });
});