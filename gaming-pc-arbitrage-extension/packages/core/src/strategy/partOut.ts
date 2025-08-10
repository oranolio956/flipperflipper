/**
 * Part-Out Value Calculator
 * Calculate value of selling individual components
 */

import { findGPU } from '../data/gpuHierarchy';
import type { CompStats } from '../comps';

export interface PartOutComponent {
  name: string;
  category: string;
  estimatedValue: number;
  confidenceLevel: 'high' | 'medium' | 'low';
  marketDemand: 'high' | 'medium' | 'low';
  listingTime: number; // estimated days to sell
}

export interface PartOutAnalysis {
  components: PartOutComponent[];
  totalValue: number;
  totalCost: number; // time, fees, shipping
  netValue: number;
  timeEstimate: number; // total days
  recommendation: 'part-out' | 'sell-whole' | 'borderline';
  reasons: string[];
}

// Marketplace fees by platform
const PLATFORM_FEES = {
  ebay: 0.125, // 12.5% + payment processing
  facebook: 0.05, // 5% or $40 min
  mercari: 0.10, // 10%
  offerup: 0.099, // 9.9%
};

// Shipping cost estimates
const SHIPPING_COSTS = {
  cpu: 10,
  gpu: 15,
  motherboard: 15,
  ram: 8,
  storage: 8,
  psu: 20,
  case: 30,
  cooler: 12,
};

// Time estimates to sell (days)
const LISTING_TIME = {
  cpu: { high: 7, medium: 14, low: 30 },
  gpu: { high: 5, medium: 10, low: 21 },
  ram: { high: 10, medium: 20, low: 45 },
  storage: { high: 7, medium: 14, low: 30 },
  psu: { high: 14, medium: 30, low: 60 },
  case: { high: 21, medium: 45, low: 90 },
};

/**
 * Calculate part-out value
 */
export function calculatePartOutValue(
  components: {
    cpu?: { model: string; brand: string };
    gpu?: { model: string; brand: string };
    ram?: Array<{ capacity: number; speed?: number; brand?: string }>;
    storage?: Array<{ type: string; capacity: number; brand?: string }>;
    motherboard?: { model?: string; chipset?: string };
    psu?: { wattage?: number; rating?: string };
    case?: { model?: string; size?: string };
    cooler?: { type?: string; model?: string };
  },
  wholeSystemValue: number,
  compStats?: Record<string, CompStats>,
  platform: keyof typeof PLATFORM_FEES = 'ebay'
): PartOutAnalysis {
  const parts: PartOutComponent[] = [];
  let totalTime = 0;
  let maxTime = 0;
  
  // CPU
  if (components.cpu) {
    const value = estimateCpuValue(components.cpu, compStats?.cpu);
    const demand = getCpuDemand(components.cpu.model);
    const time = LISTING_TIME.cpu[demand];
    
    parts.push({
      name: components.cpu.model,
      category: 'cpu',
      estimatedValue: value,
      confidenceLevel: compStats?.cpu ? 'high' : 'medium',
      marketDemand: demand,
      listingTime: time,
    });
    
    maxTime = Math.max(maxTime, time);
  }
  
  // GPU
  if (components.gpu) {
    const gpuInfo = findGPU(components.gpu.model);
    const value = gpuInfo ? 
      (gpuInfo.resaleRange.min + gpuInfo.resaleRange.max) / 2 :
      estimateGpuValue(components.gpu, compStats?.gpu);
    const demand = getGpuDemand(components.gpu.model);
    const time = LISTING_TIME.gpu[demand];
    
    parts.push({
      name: components.gpu.model,
      category: 'gpu',
      estimatedValue: value,
      confidenceLevel: gpuInfo ? 'high' : compStats?.gpu ? 'medium' : 'low',
      marketDemand: demand,
      listingTime: time,
    });
    
    maxTime = Math.max(maxTime, time);
  }
  
  // RAM
  if (components.ram && components.ram.length > 0) {
    const totalRam = components.ram.reduce((sum, r) => sum + r.capacity, 0);
    const value = estimateRamValue(totalRam, components.ram[0].speed);
    const demand = totalRam >= 16 ? 'high' : 'medium';
    const time = LISTING_TIME.ram[demand];
    
    parts.push({
      name: `${totalRam}GB DDR${components.ram[0].speed ? '4' : '3'} RAM`,
      category: 'ram',
      estimatedValue: value,
      confidenceLevel: 'high',
      marketDemand: demand,
      listingTime: time,
    });
    
    maxTime = Math.max(maxTime, time);
  }
  
  // Storage
  if (components.storage && components.storage.length > 0) {
    components.storage.forEach(drive => {
      const value = estimateStorageValue(drive.type, drive.capacity);
      const demand = drive.type === 'ssd' ? 'high' : 'low';
      const time = LISTING_TIME.storage[demand];
      
      parts.push({
        name: `${drive.capacity}GB ${drive.type.toUpperCase()}`,
        category: 'storage',
        estimatedValue: value,
        confidenceLevel: 'high',
        marketDemand: demand,
        listingTime: time,
      });
      
      maxTime = Math.max(maxTime, time);
    });
  }
  
  // Motherboard
  if (components.motherboard) {
    const value = estimateMotherboardValue(components.motherboard);
    parts.push({
      name: components.motherboard.model || `${components.motherboard.chipset} Motherboard`,
      category: 'motherboard',
      estimatedValue: value,
      confidenceLevel: 'low',
      marketDemand: 'medium',
      listingTime: 30,
    });
    maxTime = Math.max(maxTime, 30);
  }
  
  // PSU
  if (components.psu) {
    const value = estimatePsuValue(components.psu);
    const demand = components.psu.wattage && components.psu.wattage >= 750 ? 'medium' : 'low';
    const time = LISTING_TIME.psu[demand];
    
    parts.push({
      name: `${components.psu.wattage}W PSU`,
      category: 'psu',
      estimatedValue: value,
      confidenceLevel: 'medium',
      marketDemand: demand,
      listingTime: time,
    });
    
    maxTime = Math.max(maxTime, time);
  }
  
  // Calculate totals
  const totalValue = parts.reduce((sum, p) => sum + p.estimatedValue, 0);
  
  // Calculate costs
  const fees = totalValue * PLATFORM_FEES[platform];
  const shipping = parts.reduce((sum, p) => sum + (SHIPPING_COSTS[p.category] || 10), 0);
  const laborCost = parts.length * 5; // $5 per listing effort
  const totalCost = fees + shipping + laborCost;
  
  const netValue = totalValue - totalCost;
  
  // Make recommendation
  let recommendation: PartOutAnalysis['recommendation'] = 'borderline';
  const reasons: string[] = [];
  
  const partOutRatio = netValue / wholeSystemValue;
  
  if (partOutRatio > 1.3) {
    recommendation = 'part-out';
    reasons.push(`Part-out value ${Math.round((partOutRatio - 1) * 100)}% higher`);
  } else if (partOutRatio < 0.9) {
    recommendation = 'sell-whole';
    reasons.push('Better value selling complete system');
  }
  
  // Time consideration
  if (maxTime > 30) {
    reasons.push(`Long selling time (${maxTime} days)`);
    if (recommendation === 'part-out') {
      recommendation = 'borderline';
    }
  }
  
  // High-value GPU consideration
  const gpu = parts.find(p => p.category === 'gpu');
  if (gpu && gpu.estimatedValue > wholeSystemValue * 0.6) {
    reasons.push('GPU represents majority of value');
    if (recommendation !== 'part-out') {
      recommendation = 'borderline';
    }
  }
  
  return {
    components: parts,
    totalValue,
    totalCost,
    netValue,
    timeEstimate: maxTime,
    recommendation,
    reasons,
  };
}

// Helper functions for component value estimation
function estimateCpuValue(cpu: any, compStats?: CompStats): number {
  if (compStats?.median) return compStats.median;
  
  // Basic heuristics
  const model = cpu.model.toLowerCase();
  if (model.includes('i9') || model.includes('ryzen 9')) return 250;
  if (model.includes('i7') || model.includes('ryzen 7')) return 150;
  if (model.includes('i5') || model.includes('ryzen 5')) return 80;
  return 50;
}

function estimateGpuValue(gpu: any, compStats?: CompStats): number {
  if (compStats?.median) return compStats.median;
  
  const model = gpu.model.toLowerCase();
  if (model.includes('4090')) return 1400;
  if (model.includes('4080')) return 1000;
  if (model.includes('4070')) return 550;
  if (model.includes('3080')) return 500;
  if (model.includes('3070')) return 350;
  if (model.includes('3060')) return 250;
  return 150;
}

function estimateRamValue(totalGb: number, speed?: number): number {
  const basePrice = totalGb * 2.5; // $2.50 per GB
  const speedMultiplier = speed && speed >= 3200 ? 1.2 : 1.0;
  return Math.round(basePrice * speedMultiplier);
}

function estimateStorageValue(type: string, capacityGb: number): number {
  if (type === 'ssd') {
    return Math.round(capacityGb * 0.06); // $0.06 per GB
  }
  return Math.round(capacityGb * 0.02); // $0.02 per GB for HDD
}

function estimateMotherboardValue(mobo: any): number {
  if (mobo.chipset?.includes('X570') || mobo.chipset?.includes('Z690')) return 120;
  if (mobo.chipset?.includes('B550') || mobo.chipset?.includes('B660')) return 80;
  return 50;
}

function estimatePsuValue(psu: any): number {
  const wattage = psu.wattage || 500;
  const base = wattage * 0.08; // $0.08 per watt
  const efficiencyMultiplier = psu.rating?.includes('Gold') ? 1.3 : 
                              psu.rating?.includes('Bronze') ? 1.1 : 1.0;
  return Math.round(base * efficiencyMultiplier);
}

function getCpuDemand(model: string): 'high' | 'medium' | 'low' {
  const m = model.toLowerCase();
  if (m.includes('i9') || m.includes('ryzen 9')) return 'high';
  if (m.includes('i7') || m.includes('ryzen 7')) return 'high';
  if (m.includes('i5') || m.includes('ryzen 5')) return 'medium';
  return 'low';
}

function getGpuDemand(model: string): 'high' | 'medium' | 'low' {
  const m = model.toLowerCase();
  if (m.includes('4090') || m.includes('4080') || m.includes('4070')) return 'high';
  if (m.includes('3080') || m.includes('3070') || m.includes('3060')) return 'high';
  if (m.includes('2070') || m.includes('2060')) return 'medium';
  return 'low';
}