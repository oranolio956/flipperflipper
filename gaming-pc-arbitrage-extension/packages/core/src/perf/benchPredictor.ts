/**
 * Benchmark Score Predictor
 * Estimate synthetic benchmark scores from components
 */

import { findGPU } from '../data/gpuHierarchy';

export interface BenchmarkScore {
  overall: number; // 0-1000
  gaming: number;
  productivity: number;
  breakdown: {
    cpu: number;
    gpu: number;
    ram: number;
    storage: number;
  };
  confidence: 'high' | 'medium' | 'low';
}

// CPU benchmark weights (simplified)
const CPU_SCORES: Record<string, { single: number; multi: number }> = {
  // Intel 12th gen
  'i9-12900': { single: 95, multi: 90 },
  'i7-12700': { single: 90, multi: 85 },
  'i5-12600': { single: 85, multi: 70 },
  'i5-12400': { single: 75, multi: 60 },
  'i3-12100': { single: 70, multi: 45 },
  
  // Intel 11th gen
  'i9-11900': { single: 92, multi: 80 },
  'i7-11700': { single: 85, multi: 75 },
  'i5-11600': { single: 80, multi: 65 },
  'i5-11400': { single: 72, multi: 55 },
  
  // Intel 10th gen
  'i9-10900': { single: 88, multi: 85 },
  'i7-10700': { single: 82, multi: 75 },
  'i5-10600': { single: 75, multi: 60 },
  'i5-10400': { single: 68, multi: 50 },
  
  // AMD Ryzen 5000
  'ryzen 9 5950': { single: 90, multi: 95 },
  'ryzen 9 5900': { single: 88, multi: 90 },
  'ryzen 7 5800': { single: 86, multi: 80 },
  'ryzen 5 5600': { single: 84, multi: 65 },
  
  // AMD Ryzen 3000
  'ryzen 9 3950': { single: 80, multi: 92 },
  'ryzen 9 3900': { single: 78, multi: 88 },
  'ryzen 7 3700': { single: 75, multi: 75 },
  'ryzen 5 3600': { single: 72, multi: 60 },
};

/**
 * Predict benchmark score from components
 */
export function predictBenchmarkScore(components: {
  cpu?: string;
  gpu?: string;
  ram?: { capacity: number; speed?: number };
  storage?: Array<{ type: string; capacity: number }>;
}): BenchmarkScore {
  let cpuScore = 50; // Default
  let gpuScore = 50;
  let ramScore = 50;
  let storageScore = 50;
  let confidence: BenchmarkScore['confidence'] = 'low';
  
  // CPU scoring
  if (components.cpu) {
    const cpuLower = components.cpu.toLowerCase();
    const cpuData = Object.entries(CPU_SCORES).find(([model]) => 
      cpuLower.includes(model.toLowerCase())
    );
    
    if (cpuData) {
      cpuScore = (cpuData[1].single + cpuData[1].multi) / 2;
      confidence = 'high';
    } else {
      // Fallback heuristics
      if (cpuLower.includes('i9') || cpuLower.includes('ryzen 9')) cpuScore = 85;
      else if (cpuLower.includes('i7') || cpuLower.includes('ryzen 7')) cpuScore = 75;
      else if (cpuLower.includes('i5') || cpuLower.includes('ryzen 5')) cpuScore = 65;
      else if (cpuLower.includes('i3') || cpuLower.includes('ryzen 3')) cpuScore = 50;
      confidence = 'medium';
    }
  }
  
  // GPU scoring
  if (components.gpu) {
    const gpuInfo = findGPU(components.gpu);
    if (gpuInfo) {
      gpuScore = gpuInfo.perfIndex;
      if (confidence === 'high') confidence = 'high';
      else confidence = 'medium';
    } else {
      // Fallback
      const gpuLower = components.gpu.toLowerCase();
      if (gpuLower.includes('4090')) gpuScore = 100;
      else if (gpuLower.includes('4080')) gpuScore = 85;
      else if (gpuLower.includes('4070')) gpuScore = 70;
      else if (gpuLower.includes('3080')) gpuScore = 68;
      else if (gpuLower.includes('3070')) gpuScore = 58;
      else if (gpuLower.includes('3060')) gpuScore = 45;
      else gpuScore = 30;
    }
  }
  
  // RAM scoring
  if (components.ram) {
    const capacity = components.ram.capacity;
    const speed = components.ram.speed || 2666;
    
    // Capacity score
    if (capacity >= 64) ramScore = 95;
    else if (capacity >= 32) ramScore = 85;
    else if (capacity >= 16) ramScore = 70;
    else if (capacity >= 8) ramScore = 50;
    else ramScore = 30;
    
    // Speed bonus
    if (speed >= 4000) ramScore += 10;
    else if (speed >= 3600) ramScore += 7;
    else if (speed >= 3200) ramScore += 5;
    
    ramScore = Math.min(100, ramScore);
  }
  
  // Storage scoring
  if (components.storage && components.storage.length > 0) {
    const hasSSD = components.storage.some(s => s.type === 'ssd');
    const hasNVMe = components.storage.some(s => 
      s.type === 'nvme' || (s.type === 'ssd' && components.storage!.length > 1)
    );
    const totalCapacity = components.storage.reduce((sum, s) => sum + s.capacity, 0);
    
    if (hasNVMe) storageScore = 90;
    else if (hasSSD) storageScore = 70;
    else storageScore = 40;
    
    // Capacity bonus
    if (totalCapacity >= 2000) storageScore += 5;
    if (totalCapacity >= 4000) storageScore += 5;
    
    storageScore = Math.min(100, storageScore);
  }
  
  // Calculate overall scores
  const gamingScore = Math.round(
    gpuScore * 0.6 +    // GPU most important for gaming
    cpuScore * 0.25 +   
    ramScore * 0.1 +
    storageScore * 0.05
  );
  
  const productivityScore = Math.round(
    cpuScore * 0.4 +    // CPU most important for productivity
    ramScore * 0.3 +
    storageScore * 0.2 +
    gpuScore * 0.1
  );
  
  const overallScore = Math.round(
    gpuScore * 0.35 +
    cpuScore * 0.35 +
    ramScore * 0.15 +
    storageScore * 0.15
  );
  
  return {
    overall: overallScore * 10, // Scale to 0-1000
    gaming: gamingScore * 10,
    productivity: productivityScore * 10,
    breakdown: {
      cpu: cpuScore,
      gpu: gpuScore,
      ram: ramScore,
      storage: storageScore,
    },
    confidence,
  };
}

/**
 * Get performance tier from score
 */
export function getPerformanceTier(score: number): {
  tier: 'Enthusiast' | 'High-End' | 'Mid-Range' | 'Entry' | 'Budget';
  description: string;
} {
  if (score >= 850) {
    return {
      tier: 'Enthusiast',
      description: '4K gaming, content creation powerhouse',
    };
  } else if (score >= 700) {
    return {
      tier: 'High-End',
      description: '1440p high FPS gaming, professional work',
    };
  } else if (score >= 500) {
    return {
      tier: 'Mid-Range',
      description: '1080p gaming, general productivity',
    };
  } else if (score >= 300) {
    return {
      tier: 'Entry',
      description: 'Esports titles, office work',
    };
  } else {
    return {
      tier: 'Budget',
      description: 'Basic computing, light gaming',
    };
  }
}

/**
 * Compare to common benchmarks
 */
export function compareToBenchmarks(score: number): {
  fps1080p: { low: number; high: number };
  fps1440p: { low: number; high: number };
  renderTime: number; // Relative to baseline
} {
  // Simplified FPS estimates based on score
  const fps1080p = {
    low: Math.round(score * 0.15),  // ~150 FPS at score 1000
    high: Math.round(score * 0.08),  // ~80 FPS at score 1000 (demanding games)
  };
  
  const fps1440p = {
    low: Math.round(score * 0.1),   // ~100 FPS at score 1000
    high: Math.round(score * 0.05),  // ~50 FPS at score 1000
  };
  
  // Render time (inverse relationship)
  const renderTime = Math.round(10000 / score); // Lower is better
  
  return {
    fps1080p,
    fps1440p,
    renderTime,
  };
}