/**
 * Market Comp Aggregator
 * Aggregate and analyze sold prices from multiple sources
 */

import { ComponentDetector } from '../parsers/component-detector';

export interface CompRecord {
  id: string;
  source: 'ebay' | 'fb' | 'cl' | 'csv';
  title: string;
  price: number;
  currency: string;
  timestamp: Date;
  location?: { city?: string; state?: string };
  cpu?: string;
  gpu?: string;
  ram?: number; // GB
  storage?: number; // GB
  condition?: 'new' | 'used' | 'refurbished' | 'parts';
  url?: string;
}

export interface CompStats {
  median: number;
  p25: number;
  p75: number;
  n: number;
  recencyDays: number;
}

/**
 * Extract component specs from title/description
 */
export function normalizeCompTitleToSpecs(
  title: string,
  description?: string
): Partial<CompRecord> {
  const detector = new ComponentDetector();
  const combined = `${title} ${description || ''}`;
  
  const components = detector.detectAll(combined);
  
  return {
    cpu: components.cpu?.model,
    gpu: components.gpu?.model,
    ram: components.ram?.[0]?.capacity,
    storage: components.storage?.reduce((sum, s) => sum + (s.capacity || 0), 0),
    condition: inferCondition(combined),
  };
}

/**
 * Merge comp records with deduplication
 */
export function mergeComps(
  existing: CompRecord[],
  incoming: CompRecord[],
  dedupeBy: 'url' | 'titlePriceTs' = 'url'
): CompRecord[] {
  const merged = [...existing];
  const existingKeys = new Set<string>();
  
  // Build deduplication keys for existing records
  existing.forEach(comp => {
    const key = dedupeBy === 'url' 
      ? comp.url 
      : `${comp.title}-${comp.price}-${comp.timestamp.getTime()}`;
    if (key) existingKeys.add(key);
  });
  
  // Add non-duplicate incoming records
  incoming.forEach(comp => {
    const key = dedupeBy === 'url'
      ? comp.url
      : `${comp.title}-${comp.price}-${comp.timestamp.getTime()}`;
    
    if (!key || !existingKeys.has(key)) {
      merged.push(comp);
      if (key) existingKeys.add(key);
    }
  });
  
  return merged;
}

/**
 * Compute statistics for matching comps
 */
export function computeCompStats(
  specQuery: Partial<Pick<CompRecord, 'cpu' | 'gpu' | 'ram' | 'storage'>>,
  records: CompRecord[]
): CompStats | null {
  // Filter to matching records
  const matches = records.filter(r => {
    if (specQuery.cpu && !r.cpu?.toLowerCase().includes(specQuery.cpu.toLowerCase())) {
      return false;
    }
    if (specQuery.gpu && !r.gpu?.toLowerCase().includes(specQuery.gpu.toLowerCase())) {
      return false;
    }
    if (specQuery.ram && r.ram && Math.abs(r.ram - specQuery.ram) > 4) {
      return false;
    }
    if (specQuery.storage && r.storage && Math.abs(r.storage - specQuery.storage) > 128) {
      return false;
    }
    return true;
  });
  
  if (matches.length === 0) return null;
  
  // Sort by price
  const prices = matches.map(m => m.price).sort((a, b) => a - b);
  
  // Calculate age
  const now = Date.now();
  const ages = matches.map(m => (now - m.timestamp.getTime()) / (1000 * 60 * 60 * 24));
  const avgAge = ages.reduce((sum, age) => sum + age, 0) / ages.length;
  
  return {
    median: percentile(prices, 0.5),
    p25: percentile(prices, 0.25),
    p75: percentile(prices, 0.75),
    n: matches.length,
    recencyDays: Math.round(avgAge),
  };
}

/**
 * Calculate percentile
 */
function percentile(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  const index = p * (sorted.length - 1);
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  const weight = index % 1;
  
  if (lower === upper) {
    return sorted[lower];
  }
  
  return sorted[lower] * (1 - weight) + sorted[upper] * weight;
}

/**
 * Infer condition from text
 */
function inferCondition(text: string): CompRecord['condition'] {
  const lower = text.toLowerCase();
  if (lower.includes('new in box') || lower.includes('sealed')) return 'new';
  if (lower.includes('refurbished') || lower.includes('refurb')) return 'refurbished';
  if (lower.includes('for parts') || lower.includes('not working')) return 'parts';
  return 'used';
}