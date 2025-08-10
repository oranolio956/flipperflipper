/**
 * GPU Hierarchy
 * Comprehensive GPU tier list with performance data
 */

export interface GPUInfo {
  name: string;
  tier: 'S' | 'A' | 'B' | 'C' | 'D' | 'F';
  perfIndex: number; // 0-100 performance score
  vram: number; // GB
  generation: number;
  tdp: number; // Watts
  msrp?: number;
  resaleRange: {
    min: number;
    max: number;
  };
}

// GPU Database - ordered by performance
export const GPU_HIERARCHY: GPUInfo[] = [
  // S Tier - Flagship/Enthusiast
  {
    name: 'RTX 4090',
    tier: 'S',
    perfIndex: 100,
    vram: 24,
    generation: 40,
    tdp: 450,
    msrp: 1599,
    resaleRange: { min: 1400, max: 1800 },
  },
  {
    name: 'RTX 4080',
    tier: 'S',
    perfIndex: 85,
    vram: 16,
    generation: 40,
    tdp: 320,
    msrp: 1199,
    resaleRange: { min: 1000, max: 1300 },
  },
  {
    name: 'RX 7900 XTX',
    tier: 'S',
    perfIndex: 82,
    vram: 24,
    generation: 7,
    tdp: 355,
    msrp: 999,
    resaleRange: { min: 850, max: 1100 },
  },
  
  // A Tier - High-End
  {
    name: 'RTX 4070 Ti',
    tier: 'A',
    perfIndex: 75,
    vram: 12,
    generation: 40,
    tdp: 285,
    msrp: 799,
    resaleRange: { min: 700, max: 900 },
  },
  {
    name: 'RTX 3080 Ti',
    tier: 'A',
    perfIndex: 72,
    vram: 12,
    generation: 30,
    tdp: 350,
    msrp: 1199,
    resaleRange: { min: 600, max: 800 },
  },
  {
    name: 'RTX 3080',
    tier: 'A',
    perfIndex: 68,
    vram: 10,
    generation: 30,
    tdp: 320,
    msrp: 699,
    resaleRange: { min: 500, max: 700 },
  },
  {
    name: 'RX 6900 XT',
    tier: 'A',
    perfIndex: 67,
    vram: 16,
    generation: 6,
    tdp: 300,
    msrp: 999,
    resaleRange: { min: 500, max: 700 },
  },
  {
    name: 'RTX 4070',
    tier: 'A',
    perfIndex: 65,
    vram: 12,
    generation: 40,
    tdp: 200,
    msrp: 599,
    resaleRange: { min: 550, max: 700 },
  },
  
  // B Tier - Mid-High
  {
    name: 'RTX 3070 Ti',
    tier: 'B',
    perfIndex: 58,
    vram: 8,
    generation: 30,
    tdp: 290,
    msrp: 599,
    resaleRange: { min: 400, max: 550 },
  },
  {
    name: 'RTX 3070',
    tier: 'B',
    perfIndex: 55,
    vram: 8,
    generation: 30,
    tdp: 220,
    msrp: 499,
    resaleRange: { min: 350, max: 500 },
  },
  {
    name: 'RTX 4060 Ti',
    tier: 'B',
    perfIndex: 52,
    vram: 8,
    generation: 40,
    tdp: 160,
    msrp: 399,
    resaleRange: { min: 350, max: 450 },
  },
  {
    name: 'RX 6800',
    tier: 'B',
    perfIndex: 51,
    vram: 16,
    generation: 6,
    tdp: 250,
    msrp: 579,
    resaleRange: { min: 350, max: 500 },
  },
  {
    name: 'RTX 3060 Ti',
    tier: 'B',
    perfIndex: 48,
    vram: 8,
    generation: 30,
    tdp: 200,
    msrp: 399,
    resaleRange: { min: 300, max: 400 },
  },
  
  // C Tier - Mainstream
  {
    name: 'RTX 4060',
    tier: 'C',
    perfIndex: 42,
    vram: 8,
    generation: 40,
    tdp: 115,
    msrp: 299,
    resaleRange: { min: 250, max: 350 },
  },
  {
    name: 'RTX 3060',
    tier: 'C',
    perfIndex: 38,
    vram: 12,
    generation: 30,
    tdp: 170,
    msrp: 329,
    resaleRange: { min: 250, max: 350 },
  },
  {
    name: 'RX 6700 XT',
    tier: 'C',
    perfIndex: 40,
    vram: 12,
    generation: 6,
    tdp: 230,
    msrp: 479,
    resaleRange: { min: 300, max: 400 },
  },
  {
    name: 'RTX 2070 Super',
    tier: 'C',
    perfIndex: 36,
    vram: 8,
    generation: 20,
    tdp: 215,
    msrp: 499,
    resaleRange: { min: 250, max: 350 },
  },
  {
    name: 'RX 6600 XT',
    tier: 'C',
    perfIndex: 32,
    vram: 8,
    generation: 6,
    tdp: 160,
    msrp: 379,
    resaleRange: { min: 200, max: 300 },
  },
  
  // D Tier - Budget
  {
    name: 'RTX 3050',
    tier: 'D',
    perfIndex: 25,
    vram: 8,
    generation: 30,
    tdp: 130,
    msrp: 249,
    resaleRange: { min: 150, max: 250 },
  },
  {
    name: 'GTX 1660 Ti',
    tier: 'D',
    perfIndex: 22,
    vram: 6,
    generation: 16,
    tdp: 120,
    msrp: 279,
    resaleRange: { min: 150, max: 200 },
  },
  {
    name: 'GTX 1660 Super',
    tier: 'D',
    perfIndex: 20,
    vram: 6,
    generation: 16,
    tdp: 125,
    msrp: 229,
    resaleRange: { min: 130, max: 180 },
  },
  {
    name: 'RX 6600',
    tier: 'D',
    perfIndex: 24,
    vram: 8,
    generation: 6,
    tdp: 132,
    msrp: 329,
    resaleRange: { min: 180, max: 250 },
  },
  {
    name: 'GTX 1650 Super',
    tier: 'D',
    perfIndex: 15,
    vram: 4,
    generation: 16,
    tdp: 100,
    msrp: 159,
    resaleRange: { min: 100, max: 150 },
  },
  
  // F Tier - Entry Level
  {
    name: 'GTX 1650',
    tier: 'F',
    perfIndex: 12,
    vram: 4,
    generation: 16,
    tdp: 75,
    msrp: 149,
    resaleRange: { min: 80, max: 120 },
  },
  {
    name: 'GT 1030',
    tier: 'F',
    perfIndex: 5,
    vram: 2,
    generation: 10,
    tdp: 30,
    msrp: 79,
    resaleRange: { min: 40, max: 70 },
  },
  {
    name: 'RX 6500 XT',
    tier: 'F',
    perfIndex: 10,
    vram: 4,
    generation: 6,
    tdp: 107,
    msrp: 199,
    resaleRange: { min: 100, max: 150 },
  },
];

/**
 * Find GPU by name (fuzzy match)
 */
export function findGPU(name: string): GPUInfo | null {
  const normalized = name.toLowerCase().replace(/[^a-z0-9]/g, '');
  
  for (const gpu of GPU_HIERARCHY) {
    const gpuNorm = gpu.name.toLowerCase().replace(/[^a-z0-9]/g, '');
    if (gpuNorm.includes(normalized) || normalized.includes(gpuNorm)) {
      return gpu;
    }
  }
  
  // Try partial matches
  const tokens = normalized.match(/\d+/g);
  if (tokens) {
    for (const gpu of GPU_HIERARCHY) {
      const gpuTokens = gpu.name.toLowerCase().match(/\d+/g);
      if (gpuTokens && tokens.some(t => gpuTokens.includes(t))) {
        return gpu;
      }
    }
  }
  
  return null;
}

/**
 * Get GPUs by tier
 */
export function getGPUsByTier(tier: GPUInfo['tier']): GPUInfo[] {
  return GPU_HIERARCHY.filter(gpu => gpu.tier === tier);
}

/**
 * Compare two GPUs
 */
export function compareGPUs(gpu1: string, gpu2: string): {
  gpu1: GPUInfo | null;
  gpu2: GPUInfo | null;
  performanceDiff: number;
  recommendation: string;
} {
  const g1 = findGPU(gpu1);
  const g2 = findGPU(gpu2);
  
  if (!g1 || !g2) {
    return {
      gpu1: g1,
      gpu2: g2,
      performanceDiff: 0,
      recommendation: 'Unable to compare - GPU not found',
    };
  }
  
  const diff = ((g1.perfIndex - g2.perfIndex) / g2.perfIndex) * 100;
  
  let recommendation = '';
  if (Math.abs(diff) < 5) {
    recommendation = 'Similar performance';
  } else if (diff > 0) {
    recommendation = `${g1.name} is ${Math.round(diff)}% faster`;
  } else {
    recommendation = `${g2.name} is ${Math.round(-diff)}% faster`;
  }
  
  return {
    gpu1: g1,
    gpu2: g2,
    performanceDiff: diff,
    recommendation,
  };
}

/**
 * Get value proposition score
 */
export function getValueScore(gpu: GPUInfo, price: number): number {
  const midpoint = (gpu.resaleRange.min + gpu.resaleRange.max) / 2;
  const discount = (midpoint - price) / midpoint;
  
  // Factor in performance per dollar
  const perfPerDollar = gpu.perfIndex / price;
  const avgPerfPerDollar = 0.1; // Rough average
  
  const valueScore = (discount * 50) + ((perfPerDollar / avgPerfPerDollar) * 50);
  
  return Math.max(0, Math.min(100, valueScore));
}