/**
 * Tests for Parsing & Enrichment
 */

import { describe, it, expect } from 'vitest';
import { advancedParse } from '../advancedParser';
import { enrichSpecs } from '../../enrichment/dataEnricher';

describe('Advanced Parser', () => {
  it('should parse complex listing with all components', () => {
    const listing = `
      High-End Gaming PC - $1500
      
      Specs:
      - Intel Core i7-12700K (12th Gen)
      - NVIDIA RTX 3080 Ti 12GB
      - 32GB DDR4 3600MHz RAM
      - 1TB NVMe SSD + 2TB HDD
      - ASUS Z690-A Motherboard
      - 850W 80+ Gold PSU
      - NZXT H510 Case
      - Corsair H100i AIO Cooler
      
      Windows 11 Pro included
      Like new condition, barely used
      6 months warranty remaining
    `;
    
    const result = advancedParse(listing);
    
    expect(result.confidence).toBeGreaterThan(0.8);
    
    // Check parsed specs
    expect(result.specs.cpu?.model).toBe('I7-12700K');
    expect(result.specs.cpu?.brand).toBe('Intel');
    expect(result.specs.cpu?.metadata?.generation).toBe(12);
    
    expect(result.specs.gpu?.model).toBe('RTX 3080 TI');
    expect(result.specs.gpu?.metadata?.vram).toBe(12);
    
    expect(result.specs.ram?.model).toBe('32GB DDR4 3600MHz');
    expect(result.specs.storage).toHaveLength(2);
    expect(result.specs.motherboard?.model).toContain('Z690');
    expect(result.specs.psu?.metadata?.wattage).toBe(850);
    expect(result.specs.case?.brand).toContain('NZXT');
    
    expect(result.specs.os).toContain('Windows 11');
    expect(result.specs.condition).toBe('like-new');
    expect(result.specs.warranty?.months).toBe(6);
  });

  it('should handle alternative CPU formats', () => {
    const listings = [
      'Intel i5 12600K',
      'Core i5-12600K',
      'i512600k',
      'Intel Core i5 12600K',
    ];
    
    for (const text of listings) {
      const result = advancedParse(text);
      expect(result.specs.cpu?.model).toContain('I5-12600');
    }
  });

  it('should detect insights and anomalies', () => {
    const listing = 'Gaming PC with RTX 3080 and 8GB RAM for $500';
    
    const result = advancedParse(listing, {
      platform: 'facebook',
      marketContext: {
        avgPrice: 1500,
        priceRange: { min: 1200, max: 1800 },
        demandLevel: 'high',
      },
    });
    
    // Should have missing CPU insight
    expect(result.insights.some(i => i.type === 'missing-info' && i.field === 'cpu')).toBe(true);
    
    // Low RAM for high-end GPU
    expect(result.specs.ram?.model).toBe('8GB DDR4');
  });

  it('should extract peripherals and extras', () => {
    const listing = `
      Complete Gaming Setup
      PC + 27" 144Hz monitor + RGB mechanical keyboard + gaming mouse
    `;
    
    const result = advancedParse(listing);
    
    expect(result.specs.peripherals).toContain('monitor');
    expect(result.specs.peripherals).toContain('keyboard');
    expect(result.specs.peripherals).toContain('mouse');
  });

  it('should handle AMD systems', () => {
    const listing = 'Ryzen 7 5800X with Radeon RX 6800 XT';
    
    const result = advancedParse(listing);
    
    expect(result.specs.cpu?.model).toBe('RYZEN 7-5800X');
    expect(result.specs.cpu?.brand).toBe('AMD');
    expect(result.specs.gpu?.model).toBe('RX 6800 XT');
    expect(result.specs.gpu?.brand).toBe('AMD');
  });

  it('should provide suggestions for incomplete data', () => {
    const listing = 'i7 gaming computer';
    
    const result = advancedParse(listing);
    
    // Should suggest CPU brand
    const cpuSuggestion = result.suggestions.find(s => s.field === 'cpu.brand');
    expect(cpuSuggestion).toBeDefined();
    expect(cpuSuggestion?.suggestion).toBe('Intel');
  });
});

describe('Data Enricher', () => {
  it('should enrich specs with full data', async () => {
    const specs = {
      cpu: { model: 'I7-12700K', confidence: 0.9 },
      gpu: { model: 'RTX 3080', confidence: 0.9 },
      ram: { model: '32GB DDR4', confidence: 0.8, metadata: { speed: 3600 } },
      storage: [
        { model: '1TB SSD', confidence: 0.9, metadata: { type: 'ssd', capacity: 1000 } },
      ],
    };
    
    const result = await enrichSpecs(specs, {
      includeMarketData: true,
      includePerformance: true,
      includeCompatibility: true,
    });
    
    expect(result.confidence).toBeGreaterThan(0.8);
    
    // Check CPU enrichment
    expect(result.enriched.cpuEnhanced?.fullName).toBe('Intel Core i7-12700K');
    expect(result.enriched.cpuEnhanced?.specifications?.cores).toBe(12);
    expect(result.enriched.cpuEnhanced?.marketData?.msrp).toBe(409);
    
    // Check GPU enrichment
    expect(result.enriched.gpuEnhanced?.specifications?.tier).toBeDefined();
    expect(result.enriched.gpuEnhanced?.benchmarks?.score).toBeGreaterThan(70);
    
    // Check performance metrics
    expect(result.enriched.performance?.benchmarkScore).toBeGreaterThan(80);
    expect(result.enriched.performance?.gamingScore).toBeGreaterThan(85);
    
    // Check market data
    expect(result.enriched.market?.averagePrice).toBeGreaterThan(1000);
    expect(result.enriched.market?.demandScore).toBeGreaterThan(60);
    
    // Check value metrics
    expect(result.enriched.value?.estimatedValue).toBeGreaterThan(0);
    expect(result.enriched.value?.partOutValue).toBeGreaterThan(0);
    expect(result.enriched.value?.depreciation).toBe(20);
  });

  it('should detect compatibility issues', async () => {
    const specs = {
      cpu: { model: 'I7-12700K', confidence: 0.9 },
      motherboard: { model: 'B450M', confidence: 0.7 }, // Wrong chipset
      psu: { model: '450W', confidence: 0.8, metadata: { wattage: 450 } },
      gpu: { model: 'RTX 3080', confidence: 0.9 },
    };
    
    const result = await enrichSpecs(specs, {
      includeCompatibility: true,
    });
    
    const compatibility = result.enriched.compatibility;
    expect(compatibility?.issues).toHaveLength(1); // PSU insufficient
    expect(compatibility?.issues[0]).toContain('PSU may be insufficient');
    expect(compatibility?.powerRequirements).toBeGreaterThan(450);
  });

  it('should suggest upgrade paths', async () => {
    const specs = {
      cpu: { model: 'I5-10400', confidence: 0.9 },
      gpu: { model: 'GTX 1660', confidence: 0.9 },
      ram: { model: '8GB DDR4', confidence: 0.8 },
      storage: [
        { model: '500GB HDD', confidence: 0.9, metadata: { type: 'hdd', capacity: 500 } },
      ],
    };
    
    const result = await enrichSpecs(specs, {
      includeCompatibility: true,
    });
    
    const upgradePaths = result.enriched.compatibility?.upgradePaths || [];
    expect(upgradePaths).toContain('Upgrade to 16GB+ RAM for better performance');
    expect(upgradePaths).toContain('Add SSD for significant performance improvement');
  });

  it('should handle partial specs gracefully', async () => {
    const specs = {
      gpu: { model: 'RTX 3070', confidence: 0.9 },
    };
    
    const result = await enrichSpecs(specs, {
      includeMarketData: true,
      includePerformance: true,
    });
    
    expect(result.enriched.gpuEnhanced).toBeDefined();
    expect(result.enriched.market).toBeDefined();
    // Should still calculate partial performance
    expect(result.enriched.performance?.gamingScore).toBeGreaterThan(0);
  });

  it('should track data sources', async () => {
    const specs = {
      cpu: { model: 'I7-12700K', confidence: 0.9 },
      gpu: { model: 'RTX 3080', confidence: 0.9 },
    };
    
    const result = await enrichSpecs(specs, {
      includeMarketData: true,
      includePerformance: true,
    });
    
    expect(result.sources).toHaveLength(4); // CPU, GPU, Performance, Market
    expect(result.sources.some(s => s.name === 'CPU Database')).toBe(true);
    expect(result.sources.some(s => s.name === 'GPU Hierarchy')).toBe(true);
    expect(result.sources.every(s => s.confidence > 0.7)).toBe(true);
  });
});