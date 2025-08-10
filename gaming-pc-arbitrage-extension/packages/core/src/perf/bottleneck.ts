/**
 * Bottleneck Detector
 * Identify system performance bottlenecks
 */

export interface Bottleneck {
  component: 'cpu' | 'gpu' | 'ram' | 'storage';
  severity: 'severe' | 'moderate' | 'mild' | 'none';
  impact: number; // 0-100% performance impact
  reason: string;
  upgrade: string;
}

export interface BottleneckAnalysis {
  primary: Bottleneck | null;
  secondary: Bottleneck | null;
  balanced: boolean;
  recommendations: string[];
}

// CPU-GPU balance ratios (simplified)
const BALANCE_RATIOS = {
  // GPU tier -> minimum CPU tier for balance
  'S': { minCpuTier: 'high', examples: ['i7/i9', 'Ryzen 7/9'] },
  'A': { minCpuTier: 'mid-high', examples: ['i5/i7', 'Ryzen 5/7'] },
  'B': { minCpuTier: 'mid', examples: ['i5', 'Ryzen 5'] },
  'C': { minCpuTier: 'mid-low', examples: ['i3/i5', 'Ryzen 3/5'] },
  'D': { minCpuTier: 'low', examples: ['i3', 'Ryzen 3'] },
};

// Minimum RAM for GPU tiers
const MIN_RAM_BY_GPU = {
  'S': 32,
  'A': 16,
  'B': 16,
  'C': 8,
  'D': 8,
  'F': 8,
};

/**
 * Detect bottlenecks in system configuration
 */
export function detectBottlenecks(components: {
  cpu?: { model: string; cores?: number; threads?: number };
  gpu?: { model: string; tier?: string; vram?: number };
  ram?: { capacity: number; speed?: number; channels?: number };
  storage?: Array<{ type: string; capacity: number }>;
}): BottleneckAnalysis {
  const bottlenecks: Bottleneck[] = [];
  const recommendations: string[] = [];
  
  // Get component tiers
  const cpuTier = getCpuTier(components.cpu);
  const gpuTier = components.gpu?.tier || getGpuTier(components.gpu?.model);
  
  // Check CPU-GPU balance
  if (cpuTier && gpuTier) {
    const cpuBottleneck = checkCpuGpuBalance(cpuTier, gpuTier);
    if (cpuBottleneck) {
      bottlenecks.push(cpuBottleneck);
    }
  }
  
  // Check RAM bottleneck
  if (components.ram) {
    const ramBottleneck = checkRamBottleneck(
      components.ram,
      gpuTier,
      cpuTier
    );
    if (ramBottleneck) {
      bottlenecks.push(ramBottleneck);
    }
  }
  
  // Check storage bottleneck
  if (components.storage) {
    const storageBottleneck = checkStorageBottleneck(components.storage);
    if (storageBottleneck) {
      bottlenecks.push(storageBottleneck);
    }
  }
  
  // Check GPU VRAM bottleneck
  if (components.gpu?.vram) {
    const vramBottleneck = checkVramBottleneck(components.gpu.vram, gpuTier);
    if (vramBottleneck) {
      bottlenecks.push(vramBottleneck);
    }
  }
  
  // Sort by severity
  bottlenecks.sort((a, b) => {
    const severityOrder = { severe: 3, moderate: 2, mild: 1, none: 0 };
    return severityOrder[b.severity] - severityOrder[a.severity];
  });
  
  // Generate recommendations
  if (bottlenecks.length === 0) {
    recommendations.push('System appears well-balanced');
  } else {
    bottlenecks.forEach(b => {
      if (b.severity !== 'none') {
        recommendations.push(b.upgrade);
      }
    });
  }
  
  return {
    primary: bottlenecks[0] || null,
    secondary: bottlenecks[1] || null,
    balanced: bottlenecks.filter(b => b.severity !== 'none').length === 0,
    recommendations,
  };
}

/**
 * Check CPU-GPU balance
 */
function checkCpuGpuBalance(
  cpuTier: string,
  gpuTier: string
): Bottleneck | null {
  const cpuScore = getCpuScore(cpuTier);
  const gpuScore = getGpuScore(gpuTier);
  
  const ratio = cpuScore / gpuScore;
  
  if (ratio < 0.5) {
    // CPU is much weaker
    return {
      component: 'cpu',
      severity: ratio < 0.3 ? 'severe' : 'moderate',
      impact: Math.round((1 - ratio) * 50), // Up to 50% impact
      reason: `CPU (${cpuTier}) is too weak for GPU (${gpuTier} tier)`,
      upgrade: `Upgrade to ${BALANCE_RATIOS[gpuTier as keyof typeof BALANCE_RATIOS]?.examples.join(' or ')} CPU`,
    };
  } else if (ratio > 2.0) {
    // GPU is much weaker
    return {
      component: 'gpu',
      severity: ratio > 3.0 ? 'severe' : 'moderate',
      impact: Math.round((ratio - 1) * 20), // Up to 40% impact
      reason: `GPU (${gpuTier} tier) is limiting CPU (${cpuTier}) performance`,
      upgrade: 'Consider GPU upgrade for better gaming performance',
    };
  }
  
  return null;
}

/**
 * Check RAM bottleneck
 */
function checkRamBottleneck(
  ram: { capacity: number; speed?: number; channels?: number },
  gpuTier?: string,
  cpuTier?: string
): Bottleneck | null {
  const capacity = ram.capacity;
  const speed = ram.speed || 2666;
  const channels = ram.channels || 1;
  
  // Check capacity
  const minRam = gpuTier ? MIN_RAM_BY_GPU[gpuTier as keyof typeof MIN_RAM_BY_GPU] || 8 : 8;
  
  if (capacity < minRam) {
    return {
      component: 'ram',
      severity: capacity < minRam / 2 ? 'severe' : 'moderate',
      impact: Math.round((1 - capacity / minRam) * 30),
      reason: `${capacity}GB RAM insufficient for ${gpuTier || 'this'} tier GPU`,
      upgrade: `Upgrade to at least ${minRam}GB RAM`,
    };
  }
  
  // Check speed for high-end systems
  if ((gpuTier === 'S' || gpuTier === 'A') && speed < 3200) {
    return {
      component: 'ram',
      severity: 'mild',
      impact: 5,
      reason: `RAM speed (${speed}MHz) suboptimal for high-end system`,
      upgrade: 'Consider 3200MHz+ RAM for better performance',
    };
  }
  
  // Check single channel
  if (channels === 1 && capacity >= 8) {
    return {
      component: 'ram',
      severity: 'moderate',
      impact: 15,
      reason: 'Single channel RAM limiting bandwidth',
      upgrade: 'Use dual channel RAM configuration',
    };
  }
  
  return null;
}

/**
 * Check storage bottleneck
 */
function checkStorageBottleneck(
  storage: Array<{ type: string; capacity: number }>
): Bottleneck | null {
  const hasSSD = storage.some(s => s.type === 'ssd' || s.type === 'nvme');
  const hasNVMe = storage.some(s => s.type === 'nvme');
  const totalCapacity = storage.reduce((sum, s) => sum + s.capacity, 0);
  
  if (!hasSSD) {
    return {
      component: 'storage',
      severity: 'severe',
      impact: 25,
      reason: 'No SSD detected - significant performance impact',
      upgrade: 'Add SSD for OS and applications',
    };
  }
  
  if (!hasNVMe && totalCapacity < 500) {
    return {
      component: 'storage',
      severity: 'mild',
      impact: 5,
      reason: 'Limited SSD capacity may affect load times',
      upgrade: 'Consider NVMe SSD for faster performance',
    };
  }
  
  return null;
}

/**
 * Check VRAM bottleneck
 */
function checkVramBottleneck(vram: number, gpuTier?: string): Bottleneck | null {
  // Check for modern gaming requirements
  if (vram < 6) {
    return {
      component: 'gpu',
      severity: vram < 4 ? 'severe' : 'moderate',
      impact: Math.round((6 - vram) * 10),
      reason: `${vram}GB VRAM limits texture quality and resolution`,
      upgrade: 'GPU with 8GB+ VRAM recommended for modern gaming',
    };
  }
  
  // High-tier GPU with low VRAM is suspicious
  if ((gpuTier === 'S' || gpuTier === 'A') && vram < 10) {
    return {
      component: 'gpu',
      severity: 'mild',
      impact: 5,
      reason: 'VRAM may limit 4K gaming potential',
      upgrade: 'Consider 12GB+ VRAM for 4K gaming',
    };
  }
  
  return null;
}

// Helper functions
function getCpuTier(cpu?: { model: string }): string | null {
  if (!cpu) return null;
  
  const model = cpu.model.toLowerCase();
  if (model.includes('i9') || model.includes('ryzen 9')) return 'high';
  if (model.includes('i7') || model.includes('ryzen 7')) return 'mid-high';
  if (model.includes('i5') || model.includes('ryzen 5')) return 'mid';
  if (model.includes('i3') || model.includes('ryzen 3')) return 'low';
  return 'low';
}

function getGpuTier(model?: string): string | null {
  if (!model) return null;
  
  const m = model.toLowerCase();
  if (m.includes('4090') || m.includes('4080')) return 'S';
  if (m.includes('4070') || m.includes('3080')) return 'A';
  if (m.includes('3070') || m.includes('3060 ti')) return 'B';
  if (m.includes('3060') || m.includes('2070')) return 'C';
  if (m.includes('1660') || m.includes('2060')) return 'D';
  return 'F';
}

function getCpuScore(tier: string): number {
  const scores: Record<string, number> = {
    'high': 90,
    'mid-high': 75,
    'mid': 60,
    'mid-low': 45,
    'low': 30,
  };
  return scores[tier] || 30;
}

function getGpuScore(tier: string): number {
  const scores: Record<string, number> = {
    'S': 100,
    'A': 80,
    'B': 60,
    'C': 40,
    'D': 25,
    'F': 15,
  };
  return scores[tier] || 15;
}