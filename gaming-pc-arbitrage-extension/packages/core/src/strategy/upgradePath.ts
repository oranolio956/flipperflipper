/**
 * Upgrade Path Strategy
 * Calculate optimal component upgrades for profit
 */

import { ComponentValue } from '../calculators/fmv-calculator';
import { findGPU, type GPUInfo } from '../data/gpuHierarchy';

export interface UpgradeOption {
  component: 'cpu' | 'gpu' | 'ram' | 'storage';
  from: string;
  to: string;
  cost: number;
  valueIncrease: number;
  roi: number;
  timeEstimate: number; // hours
}

export interface UpgradePath {
  currentValue: number;
  targetValue: number;
  upgrades: UpgradeOption[];
  totalCost: number;
  totalTime: number;
  expectedProfit: number;
  profitMargin: number;
}

// Component upgrade costs (typical market prices)
const UPGRADE_COSTS = {
  ram: {
    '8GB': { '16GB': 40, '32GB': 120 },
    '16GB': { '32GB': 80, '64GB': 280 },
  },
  storage: {
    '256GB SSD': { '512GB SSD': 40, '1TB SSD': 80 },
    '512GB SSD': { '1TB SSD': 50, '2TB SSD': 120 },
    '1TB HDD': { '1TB SSD': 60, '2TB SSD': 120 },
  },
  gpu: {
    // Tier upgrades
    'C': { 'B': 150, 'A': 350 },
    'B': { 'A': 200, 'S': 500 },
    'A': { 'S': 400 },
  },
};

// Time estimates for upgrades (hours)
const UPGRADE_TIME = {
  ram: 0.5,
  storage: 1.0,
  gpu: 1.5,
  cpu: 2.0, // Includes motherboard compatibility check
};

/**
 * Calculate upgrade path to target specs
 */
export function calculateUpgradePath(
  currentSpecs: {
    cpu?: string;
    gpu?: string;
    ram?: number;
    storage?: Array<{ type: string; capacity: number }>;
  },
  currentValue: number,
  targetSpecs?: {
    minGpuTier?: string;
    minRam?: number;
    minSsdStorage?: number;
  },
  partsBinPrices?: Record<string, number>
): UpgradePath {
  const upgrades: UpgradeOption[] = [];
  
  // RAM upgrade
  if (targetSpecs?.minRam && currentSpecs.ram && currentSpecs.ram < targetSpecs.minRam) {
    const ramUpgrade = calculateRamUpgrade(
      currentSpecs.ram,
      targetSpecs.minRam,
      partsBinPrices
    );
    if (ramUpgrade) {
      upgrades.push(ramUpgrade);
    }
  }
  
  // Storage upgrade
  if (targetSpecs?.minSsdStorage && currentSpecs.storage) {
    const ssdUpgrade = calculateStorageUpgrade(
      currentSpecs.storage,
      targetSpecs.minSsdStorage,
      partsBinPrices
    );
    if (ssdUpgrade) {
      upgrades.push(ssdUpgrade);
    }
  }
  
  // GPU upgrade
  if (targetSpecs?.minGpuTier && currentSpecs.gpu) {
    const gpuUpgrade = calculateGpuUpgrade(
      currentSpecs.gpu,
      targetSpecs.minGpuTier,
      partsBinPrices
    );
    if (gpuUpgrade) {
      upgrades.push(gpuUpgrade);
    }
  }
  
  // Calculate totals
  const totalCost = upgrades.reduce((sum, u) => sum + u.cost, 0);
  const totalValueIncrease = upgrades.reduce((sum, u) => sum + u.valueIncrease, 0);
  const targetValue = currentValue + totalValueIncrease;
  const totalTime = upgrades.reduce((sum, u) => sum + u.timeEstimate, 0);
  const expectedProfit = totalValueIncrease - totalCost;
  const profitMargin = totalCost > 0 ? (expectedProfit / totalCost) * 100 : 0;
  
  return {
    currentValue,
    targetValue,
    upgrades,
    totalCost,
    totalTime,
    expectedProfit,
    profitMargin,
  };
}

/**
 * Calculate RAM upgrade
 */
function calculateRamUpgrade(
  currentRam: number,
  targetRam: number,
  partsBinPrices?: Record<string, number>
): UpgradeOption | null {
  const currentKey = `${currentRam}GB`;
  const targetKey = `${targetRam}GB`;
  
  // Check parts bin first
  if (partsBinPrices?.[`RAM ${targetKey}`]) {
    const cost = partsBinPrices[`RAM ${targetKey}`];
    const valueIncrease = (targetRam - currentRam) * 3; // ~$3 per GB value increase
    
    return {
      component: 'ram',
      from: currentKey,
      to: targetKey,
      cost,
      valueIncrease,
      roi: ((valueIncrease - cost) / cost) * 100,
      timeEstimate: UPGRADE_TIME.ram,
    };
  }
  
  // Market prices
  const upgradeCost = UPGRADE_COSTS.ram[currentKey]?.[targetKey];
  if (!upgradeCost) return null;
  
  const valueIncrease = (targetRam - currentRam) * 3;
  
  return {
    component: 'ram',
    from: currentKey,
    to: targetKey,
    cost: upgradeCost,
    valueIncrease,
    roi: ((valueIncrease - upgradeCost) / upgradeCost) * 100,
    timeEstimate: UPGRADE_TIME.ram,
  };
}

/**
 * Calculate storage upgrade
 */
function calculateStorageUpgrade(
  currentStorage: Array<{ type: string; capacity: number }>,
  targetSsd: number,
  partsBinPrices?: Record<string, number>
): UpgradeOption | null {
  // Find current SSD
  const currentSsd = currentStorage.find(s => s.type === 'ssd');
  const currentCapacity = currentSsd?.capacity || 0;
  
  if (currentCapacity >= targetSsd) return null;
  
  const targetKey = `${targetSsd}GB SSD`;
  
  // Check parts bin
  if (partsBinPrices?.[targetKey]) {
    const cost = partsBinPrices[targetKey];
    const valueIncrease = (targetSsd - currentCapacity) * 0.08; // ~$0.08 per GB
    
    return {
      component: 'storage',
      from: currentSsd ? `${currentCapacity}GB SSD` : 'HDD',
      to: targetKey,
      cost,
      valueIncrease,
      roi: ((valueIncrease - cost) / cost) * 100,
      timeEstimate: UPGRADE_TIME.storage,
    };
  }
  
  // Market price estimate
  const cost = targetSsd <= 512 ? 50 : targetSsd <= 1024 ? 80 : 150;
  const valueIncrease = (targetSsd - currentCapacity) * 0.08;
  
  return {
    component: 'storage',
    from: currentSsd ? `${currentCapacity}GB SSD` : 'HDD',
    to: targetKey,
    cost,
    valueIncrease,
    roi: ((valueIncrease - cost) / cost) * 100,
    timeEstimate: UPGRADE_TIME.storage,
  };
}

/**
 * Calculate GPU upgrade
 */
function calculateGpuUpgrade(
  currentGpu: string,
  targetTier: string,
  partsBinPrices?: Record<string, number>
): UpgradeOption | null {
  const currentGpuInfo = findGPU(currentGpu);
  if (!currentGpuInfo) return null;
  
  // Check if already meets target
  const tierOrder = ['F', 'D', 'C', 'B', 'A', 'S'];
  const currentTierIndex = tierOrder.indexOf(currentGpuInfo.tier);
  const targetTierIndex = tierOrder.indexOf(targetTier);
  
  if (currentTierIndex >= targetTierIndex) return null;
  
  // Estimate upgrade cost
  const tierDiff = targetTierIndex - currentTierIndex;
  const baseCost = tierDiff * 200; // Rough estimate
  
  // Value increase based on performance jump
  const perfIncrease = (targetTierIndex - currentTierIndex) * 20; // ~20 points per tier
  const valueIncrease = perfIncrease * 10; // ~$10 per performance point
  
  return {
    component: 'gpu',
    from: currentGpu,
    to: `${targetTier}-Tier GPU`,
    cost: baseCost,
    valueIncrease,
    roi: ((valueIncrease - baseCost) / baseCost) * 100,
    timeEstimate: UPGRADE_TIME.gpu,
  };
}

/**
 * Find best upgrade for budget
 */
export function findBestUpgrade(
  currentSpecs: any,
  budget: number,
  partsBinPrices?: Record<string, number>
): UpgradeOption | null {
  const allUpgrades: UpgradeOption[] = [];
  
  // Try different RAM upgrades
  if (currentSpecs.ram === 8) {
    const ram16 = calculateRamUpgrade(8, 16, partsBinPrices);
    if (ram16 && ram16.cost <= budget) allUpgrades.push(ram16);
    
    const ram32 = calculateRamUpgrade(8, 32, partsBinPrices);
    if (ram32 && ram32.cost <= budget) allUpgrades.push(ram32);
  }
  
  // Try storage upgrades
  if (currentSpecs.storage) {
    const ssd512 = calculateStorageUpgrade(currentSpecs.storage, 512, partsBinPrices);
    if (ssd512 && ssd512.cost <= budget) allUpgrades.push(ssd512);
    
    const ssd1tb = calculateStorageUpgrade(currentSpecs.storage, 1024, partsBinPrices);
    if (ssd1tb && ssd1tb.cost <= budget) allUpgrades.push(ssd1tb);
  }
  
  // Sort by ROI
  allUpgrades.sort((a, b) => b.roi - a.roi);
  
  return allUpgrades[0] || null;
}