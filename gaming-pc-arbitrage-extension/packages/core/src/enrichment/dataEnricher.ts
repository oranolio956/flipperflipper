/**
 * Data Enricher
 * Enrich listings with external data sources
 */

import type { ParsedSpecs, ComponentSpec } from '../parsers/advancedParser';
import { findGPU } from '../data/gpuHierarchy';
import { predictBenchmarkScore } from '../perf/benchPredictor';
import { detectBottlenecks } from '../perf/bottleneck';

export interface EnrichmentResult {
  original: ParsedSpecs;
  enriched: EnrichedSpecs;
  sources: DataSource[];
  confidence: number;
}

export interface EnrichedSpecs extends ParsedSpecs {
  // Enhanced component data
  cpuEnhanced?: EnhancedComponent;
  gpuEnhanced?: EnhancedComponent;
  
  // Performance metrics
  performance?: {
    benchmarkScore: number;
    gamingScore: number;
    productivityScore: number;
    bottlenecks: string[];
  };
  
  // Market data
  market?: {
    averagePrice: number;
    priceRange: { min: number; max: number };
    availability: 'high' | 'medium' | 'low';
    demandScore: number;
  };
  
  // Value metrics
  value?: {
    estimatedValue: number;
    partOutValue: number;
    upgradeValue: number;
    depreciation: number; // % per year
  };
  
  // Compatibility
  compatibility?: {
    issues: string[];
    upgradePaths: string[];
    powerRequirements: number; // watts
  };
}

export interface EnhancedComponent extends ComponentSpec {
  fullName?: string;
  specifications?: Record<string, any>;
  benchmarks?: {
    score: number;
    source: string;
    percentile: number;
  };
  marketData?: {
    msrp: number;
    currentPrice: number;
    availability: string;
  };
  alternatives?: {
    model: string;
    priceDiff: number;
    performanceDiff: number;
  }[];
}

export interface DataSource {
  type: 'internal' | 'cache' | 'api' | 'computed';
  name: string;
  confidence: number;
  timestamp: Date;
}

// CPU Database (simplified)
const CPU_DATABASE: Record<string, any> = {
  'I7-12700K': {
    fullName: 'Intel Core i7-12700K',
    cores: 12,
    threads: 20,
    baseClock: 3.6,
    boostClock: 5.0,
    tdp: 125,
    socket: 'LGA1700',
    msrp: 409,
    benchmarkScore: 85,
  },
  'I5-12600K': {
    fullName: 'Intel Core i5-12600K',
    cores: 10,
    threads: 16,
    baseClock: 3.7,
    boostClock: 4.9,
    tdp: 125,
    socket: 'LGA1700',
    msrp: 289,
    benchmarkScore: 75,
  },
  'RYZEN 7 5800X': {
    fullName: 'AMD Ryzen 7 5800X',
    cores: 8,
    threads: 16,
    baseClock: 3.8,
    boostClock: 4.7,
    tdp: 105,
    socket: 'AM4',
    msrp: 449,
    benchmarkScore: 82,
  },
};

/**
 * Enrich parsed specs with additional data
 */
export async function enrichSpecs(
  specs: ParsedSpecs,
  options?: {
    includeMarketData?: boolean;
    includePerformance?: boolean;
    includeCompatibility?: boolean;
  }
): Promise<EnrichmentResult> {
  const enriched: EnrichedSpecs = { ...specs };
  const sources: DataSource[] = [];
  
  // Enrich CPU
  if (specs.cpu) {
    enriched.cpuEnhanced = await enrichCPU(specs.cpu);
    sources.push({
      type: 'internal',
      name: 'CPU Database',
      confidence: 0.95,
      timestamp: new Date(),
    });
  }
  
  // Enrich GPU
  if (specs.gpu) {
    enriched.gpuEnhanced = await enrichGPU(specs.gpu);
    sources.push({
      type: 'internal',
      name: 'GPU Hierarchy',
      confidence: 0.90,
      timestamp: new Date(),
    });
  }
  
  // Calculate performance
  if (options?.includePerformance) {
    enriched.performance = calculatePerformance(enriched);
    sources.push({
      type: 'computed',
      name: 'Performance Calculator',
      confidence: 0.85,
      timestamp: new Date(),
    });
  }
  
  // Add market data
  if (options?.includeMarketData) {
    enriched.market = await getMarketData(enriched);
    enriched.value = calculateValue(enriched);
    sources.push({
      type: 'cache',
      name: 'Market Cache',
      confidence: 0.80,
      timestamp: new Date(),
    });
  }
  
  // Check compatibility
  if (options?.includeCompatibility) {
    enriched.compatibility = checkCompatibility(enriched);
    sources.push({
      type: 'computed',
      name: 'Compatibility Checker',
      confidence: 0.90,
      timestamp: new Date(),
    });
  }
  
  // Calculate overall confidence
  const confidence = sources.reduce((sum, s) => sum + s.confidence, 0) / sources.length;
  
  return {
    original: specs,
    enriched,
    sources,
    confidence,
  };
}

/**
 * Enrich CPU data
 */
async function enrichCPU(cpu: ComponentSpec): Promise<EnhancedComponent> {
  const enhanced: EnhancedComponent = { ...cpu };
  
  // Look up in database
  const dbEntry = CPU_DATABASE[cpu.model.toUpperCase().replace(/\s+/g, '')];
  
  if (dbEntry) {
    enhanced.fullName = dbEntry.fullName;
    enhanced.specifications = {
      cores: dbEntry.cores,
      threads: dbEntry.threads,
      baseClock: dbEntry.baseClock,
      boostClock: dbEntry.boostClock,
      tdp: dbEntry.tdp,
      socket: dbEntry.socket,
    };
    enhanced.benchmarks = {
      score: dbEntry.benchmarkScore,
      source: 'Internal DB',
      percentile: calculatePercentile(dbEntry.benchmarkScore, 'cpu'),
    };
    enhanced.marketData = {
      msrp: dbEntry.msrp,
      currentPrice: estimateCurrentPrice(dbEntry.msrp, cpu.model),
      availability: 'medium',
    };
  }
  
  // Find alternatives
  enhanced.alternatives = findAlternatives(cpu.model, 'cpu');
  
  return enhanced;
}

/**
 * Enrich GPU data
 */
async function enrichGPU(gpu: ComponentSpec): Promise<EnhancedComponent> {
  const enhanced: EnhancedComponent = { ...gpu };
  
  // Use GPU hierarchy
  const gpuInfo = findGPU(gpu.model);
  
  if (gpuInfo) {
    enhanced.fullName = gpu.model;
    enhanced.specifications = {
      tier: gpuInfo.tier,
      vram: gpuInfo.vram,
      tdp: gpuInfo.tdp,
      generation: gpuInfo.generation,
    };
    enhanced.benchmarks = {
      score: gpuInfo.perfIndex,
      source: 'GPU Hierarchy',
      percentile: calculatePercentile(gpuInfo.perfIndex, 'gpu'),
    };
    enhanced.marketData = {
      msrp: gpuInfo.msrp,
      currentPrice: (gpuInfo.resaleRange.min + gpuInfo.resaleRange.max) / 2,
      availability: gpuInfo.tier === 'S' ? 'low' : 'medium',
    };
  }
  
  enhanced.alternatives = findAlternatives(gpu.model, 'gpu');
  
  return enhanced;
}

/**
 * Calculate system performance
 */
function calculatePerformance(specs: EnrichedSpecs): EnrichedSpecs['performance'] {
  // Convert to format expected by benchmark predictor
  const components = {
    cpu: specs.cpu?.model,
    gpu: specs.gpu?.model,
    ram: specs.ram ? {
      capacity: parseInt(specs.ram.model),
      speed: specs.ram.metadata?.speed,
    } : undefined,
    storage: specs.storage?.map(s => ({
      type: s.metadata?.type || 'ssd',
      capacity: s.metadata?.capacity || 500,
    })),
  };
  
  const benchmarks = predictBenchmarkScore(components);
  
  // Detect bottlenecks
  const bottleneckAnalysis = detectBottlenecks({
    cpu: specs.cpu ? { model: specs.cpu.model } : undefined,
    gpu: specs.gpu ? { model: specs.gpu.model } : undefined,
    ram: specs.ram ? {
      capacity: parseInt(specs.ram.model),
      speed: specs.ram.metadata?.speed,
    } : undefined,
    storage: specs.storage?.map(s => ({
      type: s.metadata?.type || 'ssd',
      capacity: s.metadata?.capacity || 500,
    })),
  });
  
  return {
    benchmarkScore: benchmarks.overall,
    gamingScore: benchmarks.gaming,
    productivityScore: benchmarks.productivity,
    bottlenecks: bottleneckAnalysis.recommendations,
  };
}

/**
 * Get market data
 */
async function getMarketData(specs: EnrichedSpecs): Promise<EnrichedSpecs['market']> {
  // Simplified market data calculation
  let totalValue = 0;
  let componentCount = 0;
  
  if (specs.cpuEnhanced?.marketData) {
    totalValue += specs.cpuEnhanced.marketData.currentPrice;
    componentCount++;
  }
  
  if (specs.gpuEnhanced?.marketData) {
    totalValue += specs.gpuEnhanced.marketData.currentPrice;
    componentCount++;
  }
  
  // Add estimates for other components
  if (specs.ram) {
    const ramGB = parseInt(specs.ram.model);
    totalValue += ramGB * 3; // ~$3/GB
    componentCount++;
  }
  
  if (specs.storage) {
    specs.storage.forEach(s => {
      const capacity = s.metadata?.capacity || 500;
      const type = s.metadata?.type || 'ssd';
      totalValue += type === 'ssd' ? capacity * 0.08 : capacity * 0.03;
      componentCount++;
    });
  }
  
  // Add case, PSU, motherboard estimates
  totalValue += 150; // Conservative estimates
  
  return {
    averagePrice: totalValue,
    priceRange: {
      min: totalValue * 0.8,
      max: totalValue * 1.2,
    },
    availability: componentCount > 5 ? 'high' : 'medium',
    demandScore: calculateDemandScore(specs),
  };
}

/**
 * Calculate value metrics
 */
function calculateValue(specs: EnrichedSpecs): EnrichedSpecs['value'] {
  const marketValue = specs.market?.averagePrice || 0;
  
  // Part-out estimation
  let partOutValue = 0;
  if (specs.cpuEnhanced?.marketData) {
    partOutValue += specs.cpuEnhanced.marketData.currentPrice * 0.9;
  }
  if (specs.gpuEnhanced?.marketData) {
    partOutValue += specs.gpuEnhanced.marketData.currentPrice * 0.85;
  }
  
  // Upgrade value (if upgraded to next tier)
  const upgradeValue = marketValue * 1.3;
  
  // Depreciation based on component age
  const depreciation = 20; // 20% per year average
  
  return {
    estimatedValue: marketValue,
    partOutValue,
    upgradeValue,
    depreciation,
  };
}

/**
 * Check system compatibility
 */
function checkCompatibility(specs: EnrichedSpecs): EnrichedSpecs['compatibility'] {
  const issues: string[] = [];
  const upgradePaths: string[] = [];
  
  // Check CPU-Motherboard compatibility
  if (specs.cpuEnhanced?.specifications?.socket && specs.motherboard) {
    // Simplified check
    const socket = specs.cpuEnhanced.specifications.socket;
    if (socket === 'LGA1700' && !specs.motherboard.model.includes('Z690')) {
      issues.push('CPU may require newer motherboard chipset');
    }
  }
  
  // Calculate power requirements
  let powerRequired = 100; // Base system
  if (specs.cpuEnhanced?.specifications?.tdp) {
    powerRequired += specs.cpuEnhanced.specifications.tdp;
  }
  if (specs.gpuEnhanced?.specifications?.tdp) {
    powerRequired += specs.gpuEnhanced.specifications.tdp;
  }
  powerRequired *= 1.3; // 30% overhead
  
  // Check PSU adequacy
  if (specs.psu?.metadata?.wattage && specs.psu.metadata.wattage < powerRequired) {
    issues.push(`PSU may be insufficient (${specs.psu.metadata.wattage}W < ${Math.round(powerRequired)}W needed)`);
  }
  
  // Suggest upgrades
  if (specs.ram && parseInt(specs.ram.model) < 16) {
    upgradePaths.push('Upgrade to 16GB+ RAM for better performance');
  }
  
  if (!specs.storage?.some(s => s.metadata?.type === 'ssd' || s.metadata?.type === 'nvme')) {
    upgradePaths.push('Add SSD for significant performance improvement');
  }
  
  return {
    issues,
    upgradePaths,
    powerRequirements: Math.round(powerRequired),
  };
}

// Helper functions
function calculatePercentile(score: number, type: 'cpu' | 'gpu'): number {
  // Simplified percentile calculation
  if (type === 'cpu') {
    if (score >= 90) return 95;
    if (score >= 80) return 85;
    if (score >= 70) return 70;
    if (score >= 60) return 50;
    return 30;
  } else {
    if (score >= 90) return 98;
    if (score >= 70) return 90;
    if (score >= 50) return 75;
    if (score >= 30) return 50;
    return 25;
  }
}

function estimateCurrentPrice(msrp: number, model: string): number {
  // Simple depreciation model
  const ageMonths = estimateComponentAge(model);
  const monthlyDepreciation = 0.02; // 2% per month
  return Math.round(msrp * (1 - monthlyDepreciation * ageMonths));
}

function estimateComponentAge(model: string): number {
  // Estimate based on generation
  if (model.includes('12') || model.includes('5000')) return 12; // ~1 year
  if (model.includes('11') || model.includes('3000')) return 24; // ~2 years
  if (model.includes('10') || model.includes('2000')) return 36; // ~3 years
  return 24; // Default 2 years
}

function findAlternatives(model: string, type: 'cpu' | 'gpu'): EnhancedComponent['alternatives'] {
  // Simplified alternative finder
  const alternatives: EnhancedComponent['alternatives'] = [];
  
  if (type === 'cpu' && model.includes('i7')) {
    alternatives.push({
      model: 'i5 equivalent',
      priceDiff: -100,
      performanceDiff: -10,
    });
    alternatives.push({
      model: 'i9 upgrade',
      priceDiff: 200,
      performanceDiff: 15,
    });
  }
  
  return alternatives;
}

function calculateDemandScore(specs: EnrichedSpecs): number {
  let score = 50; // Base
  
  // High-demand components boost score
  if (specs.gpu?.model.includes('RTX 30') || specs.gpu?.model.includes('RTX 40')) {
    score += 20;
  }
  
  if (specs.cpu?.model.includes('i7') || specs.cpu?.model.includes('Ryzen 7')) {
    score += 10;
  }
  
  if (specs.ram && parseInt(specs.ram.model) >= 32) {
    score += 10;
  }
  
  return Math.min(100, score);
}