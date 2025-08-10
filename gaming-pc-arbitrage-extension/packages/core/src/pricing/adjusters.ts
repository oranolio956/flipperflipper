/**
 * Pricing Adjusters
 * Seasonal, regional, and brand-based FMV adjustments
 */

export interface SeasonalMultiplier {
  month: number; // 1-12
  multiplier: number; // e.g., 1.1 = 10% increase
  reason: string;
}

export interface RegionalMultiplier {
  state: string;
  multiplier: number;
  notes?: string;
}

export interface BrandPremium {
  brand: string;
  category: 'cpu' | 'gpu' | 'case' | 'psu' | 'motherboard';
  premium: number; // percentage, e.g., 5 = 5% premium
}

// Default seasonal multipliers
export const DEFAULT_SEASONAL_MULTIPLIERS: SeasonalMultiplier[] = [
  { month: 1, multiplier: 0.95, reason: 'Post-holiday slowdown' },
  { month: 2, multiplier: 0.97, reason: 'Winter slowdown' },
  { month: 3, multiplier: 1.0, reason: 'Spring neutral' },
  { month: 4, multiplier: 1.02, reason: 'Tax refund season' },
  { month: 5, multiplier: 1.0, reason: 'Spring neutral' },
  { month: 6, multiplier: 0.98, reason: 'Summer begins' },
  { month: 7, multiplier: 0.96, reason: 'Summer vacation' },
  { month: 8, multiplier: 1.05, reason: 'Back-to-school' },
  { month: 9, multiplier: 1.08, reason: 'Fall semester' },
  { month: 10, multiplier: 1.03, reason: 'Pre-holiday buildup' },
  { month: 11, multiplier: 1.12, reason: 'Black Friday/Cyber Monday' },
  { month: 12, multiplier: 1.15, reason: 'Holiday peak' },
];

// Default regional multipliers
export const DEFAULT_REGIONAL_MULTIPLIERS: RegionalMultiplier[] = [
  // High-cost areas
  { state: 'CA', multiplier: 1.15, notes: 'High cost of living, tech hub' },
  { state: 'NY', multiplier: 1.12, notes: 'High cost of living' },
  { state: 'WA', multiplier: 1.10, notes: 'Tech hub' },
  { state: 'MA', multiplier: 1.08, notes: 'High education density' },
  
  // Medium-cost areas
  { state: 'TX', multiplier: 1.0, notes: 'Baseline' },
  { state: 'FL', multiplier: 1.0, notes: 'Baseline' },
  { state: 'CO', multiplier: 1.02, notes: 'Growing tech scene' },
  { state: 'GA', multiplier: 0.98, notes: 'Lower cost of living' },
  
  // Low-cost areas
  { state: 'OH', multiplier: 0.92, notes: 'Lower demand' },
  { state: 'MI', multiplier: 0.90, notes: 'Lower demand' },
  { state: 'WV', multiplier: 0.88, notes: 'Rural, lower demand' },
  { state: 'MS', multiplier: 0.85, notes: 'Lowest cost of living' },
];

// Default brand premiums
export const DEFAULT_BRAND_PREMIUMS: BrandPremium[] = [
  // CPUs
  { brand: 'Intel Core i9', category: 'cpu', premium: 5 },
  { brand: 'AMD Ryzen 9', category: 'cpu', premium: 3 },
  { brand: 'Intel Core i7', category: 'cpu', premium: 2 },
  { brand: 'AMD Ryzen 7', category: 'cpu', premium: 1 },
  
  // GPUs
  { brand: 'NVIDIA RTX', category: 'gpu', premium: 8 },
  { brand: 'ASUS ROG', category: 'gpu', premium: 5 },
  { brand: 'EVGA', category: 'gpu', premium: 4 },
  { brand: 'MSI Gaming', category: 'gpu', premium: 3 },
  { brand: 'Gigabyte AORUS', category: 'gpu', premium: 3 },
  
  // Cases
  { brand: 'Lian Li', category: 'case', premium: 10 },
  { brand: 'Corsair', category: 'case', premium: 5 },
  { brand: 'NZXT', category: 'case', premium: 4 },
  { brand: 'Fractal Design', category: 'case', premium: 3 },
  
  // PSUs
  { brand: 'Seasonic', category: 'psu', premium: 7 },
  { brand: 'Corsair', category: 'psu', premium: 5 },
  { brand: 'EVGA', category: 'psu', premium: 4 },
  
  // Motherboards
  { brand: 'ASUS ROG', category: 'motherboard', premium: 6 },
  { brand: 'MSI MEG', category: 'motherboard', premium: 5 },
  { brand: 'Gigabyte AORUS', category: 'motherboard', premium: 4 },
];

/**
 * Apply seasonal adjustment
 */
export function seasonalAdjust(
  baseValue: number,
  date: Date = new Date(),
  multipliers: SeasonalMultiplier[] = DEFAULT_SEASONAL_MULTIPLIERS
): {
  adjustedValue: number;
  multiplier: number;
  reason: string;
} {
  const month = date.getMonth() + 1; // 1-12
  const seasonal = multipliers.find(m => m.month === month);
  
  if (!seasonal) {
    return {
      adjustedValue: baseValue,
      multiplier: 1.0,
      reason: 'No seasonal adjustment',
    };
  }
  
  return {
    adjustedValue: Math.round(baseValue * seasonal.multiplier),
    multiplier: seasonal.multiplier,
    reason: seasonal.reason,
  };
}

/**
 * Apply regional adjustment
 */
export function regionalAdjust(
  baseValue: number,
  state: string,
  multipliers: RegionalMultiplier[] = DEFAULT_REGIONAL_MULTIPLIERS
): {
  adjustedValue: number;
  multiplier: number;
  notes?: string;
} {
  const regional = multipliers.find(m => m.state === state.toUpperCase());
  
  if (!regional) {
    // Default for unlisted states
    return {
      adjustedValue: baseValue,
      multiplier: 0.95,
      notes: 'Unlisted state, conservative estimate',
    };
  }
  
  return {
    adjustedValue: Math.round(baseValue * regional.multiplier),
    multiplier: regional.multiplier,
    notes: regional.notes,
  };
}

/**
 * Apply brand premium
 */
export function brandPremium(
  baseValue: number,
  brand: string,
  category: BrandPremium['category'],
  premiums: BrandPremium[] = DEFAULT_BRAND_PREMIUMS
): {
  adjustedValue: number;
  premium: number;
  applied: boolean;
} {
  // Find matching premium
  const premium = premiums.find(p => 
    p.category === category && 
    brand.toLowerCase().includes(p.brand.toLowerCase())
  );
  
  if (!premium) {
    return {
      adjustedValue: baseValue,
      premium: 0,
      applied: false,
    };
  }
  
  const multiplier = 1 + (premium.premium / 100);
  
  return {
    adjustedValue: Math.round(baseValue * multiplier),
    premium: premium.premium,
    applied: true,
  };
}

/**
 * Apply all adjustments
 */
export interface AdjustmentResult {
  originalValue: number;
  adjustedValue: number;
  adjustments: {
    seasonal: {
      multiplier: number;
      reason: string;
      delta: number;
    };
    regional: {
      multiplier: number;
      notes?: string;
      delta: number;
    };
    brand: {
      premium: number;
      applied: boolean;
      delta: number;
    };
  };
  totalMultiplier: number;
  totalDelta: number;
}

export function applyAllAdjustments(
  baseValue: number,
  options: {
    date?: Date;
    state?: string;
    brand?: string;
    category?: BrandPremium['category'];
    seasonalMultipliers?: SeasonalMultiplier[];
    regionalMultipliers?: RegionalMultiplier[];
    brandPremiums?: BrandPremium[];
  }
): AdjustmentResult {
  let currentValue = baseValue;
  
  // Apply seasonal
  const seasonal = seasonalAdjust(
    currentValue, 
    options.date, 
    options.seasonalMultipliers
  );
  const seasonalDelta = seasonal.adjustedValue - currentValue;
  currentValue = seasonal.adjustedValue;
  
  // Apply regional
  const regional = options.state ? regionalAdjust(
    currentValue,
    options.state,
    options.regionalMultipliers
  ) : { adjustedValue: currentValue, multiplier: 1.0 };
  const regionalDelta = regional.adjustedValue - currentValue;
  currentValue = regional.adjustedValue;
  
  // Apply brand
  const brand = options.brand && options.category ? brandPremium(
    currentValue,
    options.brand,
    options.category,
    options.brandPremiums
  ) : { adjustedValue: currentValue, premium: 0, applied: false };
  const brandDelta = brand.adjustedValue - currentValue;
  currentValue = brand.adjustedValue;
  
  return {
    originalValue: baseValue,
    adjustedValue: currentValue,
    adjustments: {
      seasonal: {
        multiplier: seasonal.multiplier,
        reason: seasonal.reason,
        delta: seasonalDelta,
      },
      regional: {
        multiplier: regional.multiplier,
        notes: regional.notes,
        delta: regionalDelta,
      },
      brand: {
        premium: brand.premium,
        applied: brand.applied,
        delta: brandDelta,
      },
    },
    totalMultiplier: currentValue / baseValue,
    totalDelta: currentValue - baseValue,
  };
}