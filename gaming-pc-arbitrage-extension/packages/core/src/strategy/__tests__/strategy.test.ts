/**
 * Tests for Strategy Modules
 */

import { describe, it, expect } from 'vitest';
import { calculateUpgradePath, findBestUpgrade } from '../upgradePath';
import { calculatePartOutValue } from '../partOut';
import { calculateQuickFlip, suggestFlipVsHold } from '../quickFlip';

describe('Upgrade Path', () => {
  it('should calculate RAM upgrade path', () => {
    const currentSpecs = {
      cpu: 'Intel i5-10400',
      gpu: 'RTX 3060',
      ram: 8,
      storage: [{ type: 'ssd', capacity: 256 }],
    };
    
    const path = calculateUpgradePath(
      currentSpecs,
      800, // current value
      { minRam: 16 }
    );
    
    expect(path.upgrades).toHaveLength(1);
    expect(path.upgrades[0].component).toBe('ram');
    expect(path.upgrades[0].to).toBe('16GB');
    expect(path.totalCost).toBeLessThan(50);
    expect(path.expectedProfit).toBeGreaterThan(0);
  });

  it('should calculate GPU tier upgrade', () => {
    const currentSpecs = {
      gpu: 'GTX 1660', // C-tier
      ram: 16,
    };
    
    const path = calculateUpgradePath(
      currentSpecs,
      600,
      { minGpuTier: 'A' }
    );
    
    expect(path.upgrades.some(u => u.component === 'gpu')).toBe(true);
    const gpuUpgrade = path.upgrades.find(u => u.component === 'gpu');
    expect(gpuUpgrade?.to).toContain('A-Tier');
  });

  it('should use parts bin prices when available', () => {
    const currentSpecs = { ram: 8 };
    const partsBinPrices = { 'RAM 16GB': 25 };
    
    const path = calculateUpgradePath(
      currentSpecs,
      500,
      { minRam: 16 },
      partsBinPrices
    );
    
    expect(path.upgrades[0].cost).toBe(25);
  });

  it('should find best upgrade for budget', () => {
    const currentSpecs = {
      ram: 8,
      storage: [{ type: 'hdd', capacity: 1000 }],
    };
    
    const best = findBestUpgrade(currentSpecs, 50);
    
    expect(best).toBeTruthy();
    expect(best?.cost).toBeLessThanOrEqual(50);
    expect(best?.roi).toBeGreaterThan(0);
  });
});

describe('Part-Out Value', () => {
  it('should calculate part-out value for complete system', () => {
    const components = {
      cpu: { model: 'Intel i7-10700K', brand: 'Intel' },
      gpu: { model: 'RTX 3070', brand: 'NVIDIA' },
      ram: [{ capacity: 16, speed: 3200 }],
      storage: [
        { type: 'ssd', capacity: 512 },
        { type: 'hdd', capacity: 2000 },
      ],
      motherboard: { chipset: 'Z490' },
      psu: { wattage: 750, rating: 'Gold' },
    };
    
    const analysis = calculatePartOutValue(components, 1200);
    
    expect(analysis.components).toHaveLength(6);
    expect(analysis.totalValue).toBeGreaterThan(800);
    expect(analysis.components.find(c => c.category === 'gpu')?.marketDemand).toBe('high');
  });

  it('should recommend part-out when significantly more valuable', () => {
    const components = {
      gpu: { model: 'RTX 4090', brand: 'NVIDIA' }, // High value GPU
      cpu: { model: 'Intel i5-10400', brand: 'Intel' },
      ram: [{ capacity: 16 }],
    };
    
    const analysis = calculatePartOutValue(components, 1000); // Low whole system value
    
    expect(analysis.recommendation).toBe('part-out');
    expect(analysis.reasons.some(r => r.includes('higher'))).toBe(true);
  });

  it('should factor in platform fees', () => {
    const components = {
      gpu: { model: 'RTX 3060', brand: 'NVIDIA' },
    };
    
    const ebayAnalysis = calculatePartOutValue(components, 500, undefined, 'ebay');
    const fbAnalysis = calculatePartOutValue(components, 500, undefined, 'facebook');
    
    expect(ebayAnalysis.totalCost).toBeGreaterThan(fbAnalysis.totalCost);
  });

  it('should estimate time to sell', () => {
    const components = {
      gpu: { model: 'RTX 3080', brand: 'NVIDIA' },
      psu: { wattage: 500 }, // Low demand
    };
    
    const analysis = calculatePartOutValue(components, 800);
    
    const gpu = analysis.components.find(c => c.category === 'gpu');
    const psu = analysis.components.find(c => c.category === 'psu');
    
    expect(gpu?.listingTime).toBeLessThan(psu?.listingTime || 100);
  });
});

describe('Quick-Flip Strategy', () => {
  it('should calculate quick flip with high competition', () => {
    const marketConditions = {
      competition: { score: 80, reasons: [], tips: [] },
      comps: { 
        median: 1000, 
        p25: 900, 
        p75: 1100,
        count: 10,
        recency: 0.8,
      },
      similarListings: 15,
      averageDaysOnMarket: 10,
      priceRange: { min: 800, max: 1200 },
    };
    
    const analysis = calculateQuickFlip(700, 1000, marketConditions);
    
    expect(analysis.strategy).toBe('undercut');
    expect(analysis.suggestedPrice).toBeLessThan(1000);
    expect(analysis.risks).toContain('High competition requires aggressive pricing');
  });

  it('should suggest premium pricing in low competition', () => {
    const marketConditions = {
      competition: { score: 20, reasons: [], tips: [] },
      comps: { median: 1000, p25: 950, p75: 1050, count: 5, recency: 0.9 },
      similarListings: 2,
      averageDaysOnMarket: 5,
      priceRange: { min: 900, max: 1100 },
    };
    
    const analysis = calculateQuickFlip(700, 1000, marketConditions);
    
    expect(analysis.strategy).toBe('premium');
    expect(analysis.suggestedPrice).toBeGreaterThan(1000);
  });

  it('should enforce minimum margin', () => {
    const marketConditions = {
      competition: { score: 90, reasons: [], tips: [] },
      comps: { median: 800, p25: 750, p75: 850, count: 20, recency: 0.9 },
      similarListings: 25,
      averageDaysOnMarket: 15,
      priceRange: { min: 700, max: 900 },
    };
    
    const analysis = calculateQuickFlip(750, 800, marketConditions, 'high');
    
    // Should maintain 15% minimum margin
    expect(analysis.suggestedPrice).toBeGreaterThanOrEqual(750 * 1.15);
  });

  it('should suggest flip vs hold decision', () => {
    const quickFlipAnalysis = {
      suggestedPrice: 1000,
      profitMargin: 25,
      probability: 75,
      timeframe: '1-3 days' as const,
      strategy: 'match' as const,
      risks: [],
      actions: [],
    };
    
    const decision = suggestFlipVsHold(
      quickFlipAnalysis,
      'stable',
      2, // $2/day holding cost
      800 // purchase price
    );
    
    expect(decision.recommendation).toBe('flip-now');
    expect(decision.reasoning).toContain('High probability of quick sale with good margin');
  });

  it('should recommend holding in rising market with low margin', () => {
    const quickFlipAnalysis = {
      suggestedPrice: 900,
      profitMargin: 12,
      probability: 60,
      timeframe: '1 week' as const,
      strategy: 'match' as const,
      risks: [],
      actions: [],
    };
    
    const decision = suggestFlipVsHold(
      quickFlipAnalysis,
      'rising',
      2,
      800
    );
    
    expect(decision.recommendation).toBe('hold');
    expect(decision.reasoning.some(r => r.includes('Rising market'))).toBe(true);
  });

  it('should recommend urgent flip in falling market', () => {
    const quickFlipAnalysis = {
      suggestedPrice: 950,
      profitMargin: 18,
      probability: 65,
      timeframe: '1-3 days' as const,
      strategy: 'undercut' as const,
      risks: [],
      actions: [],
    };
    
    const decision = suggestFlipVsHold(
      quickFlipAnalysis,
      'falling',
      3,
      800
    );
    
    expect(decision.recommendation).toBe('flip-urgent');
    expect(decision.reasoning).toContain('Falling market - sell quickly to avoid losses');
  });
});