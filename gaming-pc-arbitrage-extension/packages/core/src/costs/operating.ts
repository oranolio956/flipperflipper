/**
 * Operating Cost Factors
 * Calculate electricity, mining profitability, and warranty value
 */

import { findGPU } from '../data/gpuHierarchy';

export interface ElectricityCost {
  dailyCost: number;
  monthlyCost: number;
  yearlyCost: number;
  assumptions: {
    hoursPerDay: number;
    kwhRate: number;
    totalWattage: number;
  };
}

export interface MiningProfitability {
  dailyRevenue: number;
  dailyCost: number;
  dailyProfit: number;
  breakEvenDays: number;
  warnings: string[];
}

export interface WarrantyValue {
  estimatedValue: number;
  monthsRemaining: number;
  transferable: boolean;
  coverage: 'manufacturer' | 'extended' | 'none';
}

// Mining hashrates (simplified - real values vary by algorithm)
const GPU_HASHRATES = {
  'RTX 4090': { ethash: 120, power: 450 },
  'RTX 4080': { ethash: 100, power: 320 },
  'RTX 4070 Ti': { ethash: 80, power: 285 },
  'RTX 3090': { ethash: 120, power: 350 },
  'RTX 3080': { ethash: 100, power: 320 },
  'RTX 3070': { ethash: 60, power: 220 },
  'RTX 3060 Ti': { ethash: 60, power: 200 },
  'RTX 3060': { ethash: 48, power: 170 },
  'RX 6900 XT': { ethash: 64, power: 300 },
  'RX 6800': { ethash: 61, power: 250 },
  'RX 6700 XT': { ethash: 47, power: 230 },
};

/**
 * Calculate electricity cost
 */
export function electricityCostWattHours(
  systemWattage: number,
  hoursPerDay: number,
  kwhRate: number
): ElectricityCost {
  // Convert watts to kilowatts
  const kw = systemWattage / 1000;
  
  // Daily consumption
  const dailyKwh = kw * hoursPerDay;
  const dailyCost = dailyKwh * kwhRate;
  
  // Monthly (30 days)
  const monthlyCost = dailyCost * 30;
  
  // Yearly (365 days)
  const yearlyCost = dailyCost * 365;
  
  return {
    dailyCost,
    monthlyCost,
    yearlyCost,
    assumptions: {
      hoursPerDay,
      kwhRate,
      totalWattage: systemWattage,
    },
  };
}

/**
 * Estimate system wattage from components
 */
export function estimateSystemWattage(components: {
  cpu?: string;
  gpu?: string;
  ram?: number;
  storage?: Array<{ type: string }>;
}): number {
  let totalWattage = 50; // Base system (motherboard, fans, etc.)
  
  // CPU estimation
  if (components.cpu) {
    const cpuModel = components.cpu.toLowerCase();
    if (cpuModel.includes('i9') || cpuModel.includes('ryzen 9')) {
      totalWattage += 125;
    } else if (cpuModel.includes('i7') || cpuModel.includes('ryzen 7')) {
      totalWattage += 95;
    } else if (cpuModel.includes('i5') || cpuModel.includes('ryzen 5')) {
      totalWattage += 65;
    } else {
      totalWattage += 45;
    }
  }
  
  // GPU estimation
  if (components.gpu) {
    const gpuInfo = findGPU(components.gpu);
    if (gpuInfo) {
      totalWattage += gpuInfo.tdp;
    } else {
      // Fallback estimation
      const gpuModel = components.gpu.toLowerCase();
      if (gpuModel.includes('4090')) totalWattage += 450;
      else if (gpuModel.includes('4080')) totalWattage += 320;
      else if (gpuModel.includes('3080')) totalWattage += 320;
      else if (gpuModel.includes('3070')) totalWattage += 220;
      else if (gpuModel.includes('3060')) totalWattage += 170;
      else totalWattage += 150; // Default
    }
  }
  
  // RAM (minimal power)
  if (components.ram) {
    totalWattage += Math.ceil(components.ram / 8) * 3; // ~3W per 8GB
  }
  
  // Storage
  if (components.storage) {
    components.storage.forEach(drive => {
      totalWattage += drive.type === 'ssd' ? 5 : 10; // SSD vs HDD
    });
  }
  
  // Add 20% overhead for PSU efficiency loss
  return Math.ceil(totalWattage * 1.2);
}

/**
 * Calculate mining profitability
 */
export function miningProfitability(
  gpu: string,
  electricityRate: number,
  miningRevenue: {
    algorithm: 'ethash' | 'kawpow' | 'autolykos';
    revenuePerMhPerDay: number; // USD per MH/s per day
  }
): MiningProfitability {
  const warnings: string[] = [];
  
  // Find GPU hashrate
  const gpuData = Object.entries(GPU_HASHRATES).find(([model]) => 
    gpu.toLowerCase().includes(model.toLowerCase())
  );
  
  if (!gpuData) {
    warnings.push('GPU mining data not available');
    return {
      dailyRevenue: 0,
      dailyCost: 0,
      dailyProfit: 0,
      breakEvenDays: Infinity,
      warnings,
    };
  }
  
  const [model, data] = gpuData;
  const hashrate = data.ethash; // MH/s
  const powerDraw = data.power; // Watts
  
  // Calculate revenue
  const dailyRevenue = hashrate * miningRevenue.revenuePerMhPerDay;
  
  // Calculate electricity cost
  const electricityCost = electricityCostWattHours(powerDraw, 24, electricityRate);
  const dailyCost = electricityCost.dailyCost;
  
  // Calculate profit
  const dailyProfit = dailyRevenue - dailyCost;
  
  // Warnings
  if (dailyProfit < 0) {
    warnings.push('Mining is not profitable at current rates');
  }
  
  if (dailyProfit < 1) {
    warnings.push('Very low profitability - consider market volatility');
  }
  
  // Mining difficulty and market warnings
  warnings.push('Mining profitability varies with difficulty and coin prices');
  warnings.push('Consider wear on components from 24/7 operation');
  
  // Break-even calculation (simplified - assumes GPU price)
  const gpuPrice = estimateGpuPrice(gpu);
  const breakEvenDays = dailyProfit > 0 ? Math.ceil(gpuPrice / dailyProfit) : Infinity;
  
  return {
    dailyRevenue,
    dailyCost,
    dailyProfit,
    breakEvenDays,
    warnings,
  };
}

/**
 * Calculate warranty value
 */
export function warrantyValue(
  monthsRemaining: number,
  brand: string,
  category: 'cpu' | 'gpu' | 'psu' | 'motherboard' | 'ram',
  originalPrice?: number
): WarrantyValue {
  // Base warranty value as percentage of original price
  const warrantyPercentages = {
    cpu: 0.08, // 8% of value per year
    gpu: 0.12, // 12% - higher failure rate
    psu: 0.06, // 6% - reliable
    motherboard: 0.08,
    ram: 0.04, // 4% - very reliable
  };
  
  const basePercentage = warrantyPercentages[category] || 0.08;
  const monthlyValue = basePercentage / 12;
  
  // Brand premium multipliers
  const brandMultipliers: Record<string, number> = {
    'evga': 1.3, // Known for excellent warranty
    'asus': 1.2,
    'msi': 1.1,
    'corsair': 1.2,
    'seasonic': 1.3,
    'intel': 1.0,
    'amd': 1.0,
  };
  
  const brandMultiplier = brandMultipliers[brand.toLowerCase()] || 1.0;
  
  // Estimate value
  let estimatedValue = 0;
  
  if (originalPrice) {
    estimatedValue = originalPrice * monthlyValue * monthsRemaining * brandMultiplier;
  } else {
    // Fallback estimation based on category
    const baseValues = {
      cpu: 20,
      gpu: 50,
      psu: 15,
      motherboard: 25,
      ram: 10,
    };
    estimatedValue = (baseValues[category] || 20) * (monthsRemaining / 12) * brandMultiplier;
  }
  
  // Determine coverage type
  let coverage: WarrantyValue['coverage'] = 'manufacturer';
  if (monthsRemaining > 36) {
    coverage = 'extended';
  } else if (monthsRemaining === 0) {
    coverage = 'none';
  }
  
  // Most warranties are transferable
  const transferable = category !== 'extended' && brand.toLowerCase() !== 'dell';
  
  return {
    estimatedValue: Math.round(estimatedValue),
    monthsRemaining,
    transferable,
    coverage,
  };
}

/**
 * Calculate total cost of ownership
 */
export interface TotalCostOfOwnership {
  purchasePrice: number;
  electricityCost: ElectricityCost;
  maintenanceCost: number;
  opportunityCost: number;
  totalFirstYear: number;
  effectiveValue: number; // Purchase price minus costs plus benefits
}

export function calculateTCO(
  purchasePrice: number,
  systemWattage: number,
  usageHoursPerDay: number,
  electricityRate: number,
  expectedHoldingMonths: number,
  warrantyMonths: number = 0
): TotalCostOfOwnership {
  // Electricity costs
  const electricityCost = electricityCostWattHours(
    systemWattage,
    usageHoursPerDay,
    electricityRate
  );
  
  // Maintenance cost estimate ($5/month for cleaning, thermal paste, etc.)
  const maintenanceCost = 5 * expectedHoldingMonths;
  
  // Opportunity cost (could have invested the money at ~5% annually)
  const opportunityCost = purchasePrice * 0.05 * (expectedHoldingMonths / 12);
  
  // Total first year cost
  const totalFirstYear = purchasePrice + 
    electricityCost.yearlyCost + 
    (maintenanceCost * 12 / expectedHoldingMonths) +
    opportunityCost;
  
  // Effective value (considering warranty benefit)
  const warrantyBenefit = warrantyMonths > 0 ? warrantyValue(warrantyMonths, 'generic', 'gpu').estimatedValue : 0;
  const effectiveValue = purchasePrice - 
    (electricityCost.monthlyCost * expectedHoldingMonths) -
    maintenanceCost -
    opportunityCost +
    warrantyBenefit;
  
  return {
    purchasePrice,
    electricityCost,
    maintenanceCost,
    opportunityCost,
    totalFirstYear,
    effectiveValue,
  };
}

// Helper function
function estimateGpuPrice(gpu: string): number {
  const gpuInfo = findGPU(gpu);
  if (gpuInfo) {
    return (gpuInfo.resaleRange.min + gpuInfo.resaleRange.max) / 2;
  }
  
  // Fallback
  const model = gpu.toLowerCase();
  if (model.includes('4090')) return 1400;
  if (model.includes('4080')) return 1000;
  if (model.includes('3080')) return 500;
  if (model.includes('3070')) return 350;
  return 250;
}