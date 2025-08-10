/**
 * FMV (Fair Market Value) Calculator
 * Calculates the fair market value of a PC based on its components
 */

import Decimal from 'decimal.js';
import { 
  Listing, 
  RAMComponent, 
  StorageComponent, 
  MotherboardComponent, 
  PSUComponent, 
  CaseComponent, 
  CoolerComponent,
  ListingComponents 
} from '../types';

// Component condition type
type ComponentCondition = 'new' | 'excellent' | 'good' | 'fair' | 'poor';
import { ALL_PRICING_TIERS, findPriceTier } from '../data/pricing-tiers';
import { Settings } from '../settings/schema';

export interface FMVResult {
  total: number;
  componentBreakdown: ComponentValue[];
  confidence: number;
  adjustments: Adjustment[];
  methodology: string;
}

export interface ComponentValue {
  type: string;
  name: string;
  condition: ComponentCondition;
  baseValue: number;
  adjustedValue: number;
  confidence: number;
}

export interface Adjustment {
  reason: string;
  factor: number;
  impact: number;
}

export class FMVCalculator {
  private settings: Settings;
  
  constructor(settings: Settings) {
    this.settings = settings;
  }
  
  /**
   * Calculate the FMV for a listing
   */
  async calculate(listing: Listing): Promise<FMVResult> {
    const componentValues: ComponentValue[] = [];
    const adjustments: Adjustment[] = [];
    
    // Calculate base component values
    if (listing.components?.cpu) {
      const cpuValue = this.calculateComponentValue(
        'CPU',
        listing.components.cpu.model,
        'good' as ComponentCondition
      );
      componentValues.push(cpuValue);
    }
    
    if (listing.components?.gpu) {
      const gpuValue = this.calculateComponentValue(
        'GPU',
        listing.components.gpu.model,
        'good' as ComponentCondition
      );
      
      // Apply mining risk adjustment for GPUs
      // Check for mining risk based on GPU model
      const gpuModel = listing.components?.gpu?.model.toLowerCase() || '';
      const isMiningGpu = gpuModel.includes('3060') || gpuModel.includes('3070') || 
                         gpuModel.includes('3080') || gpuModel.includes('3090');
      
      if (isMiningGpu) {
        const miningAdjustment = this.applyMiningAdjustment(gpuValue);
        adjustments.push(miningAdjustment);
        gpuValue.adjustedValue *= miningAdjustment.factor;
      }
      
      componentValues.push(gpuValue);
    }
    
    // RAM - sum all modules
    if (listing.components?.ram && listing.components.ram.length > 0) {
      for (const ram of listing.components.ram) {
        const ramValue = this.calculateRAMValue(ram);
        componentValues.push(ramValue);
      }
    }
    
    // Storage - sum all drives
    if (listing.components?.storage && listing.components.storage.length > 0) {
      for (const storage of listing.components.storage) {
        const storageValue = this.calculateStorageValue(storage);
        componentValues.push(storageValue);
      }
    }
    
    // Motherboard
    if (listing.components?.motherboard) {
      const moboValue = this.calculateMotherboardValue(listing.components.motherboard);
      componentValues.push(moboValue);
    }
    
    // PSU
    if (listing.components?.psu) {
      const psuValue = this.calculatePSUValue(listing.components.psu);
      componentValues.push(psuValue);
    }
    
    // Case
    if (listing.components?.case) {
      const caseValue = this.calculateCaseValue(listing.components.case);
      componentValues.push(caseValue);
    }
    
    // Cooling
    if (listing.components?.cooling) {
      const coolingValue = this.calculateCoolingValue(listing.components.cooling);
      componentValues.push(coolingValue);
    }
    
    // Calculate subtotal
    const subtotal = new Decimal(
      componentValues.reduce((sum, cv) => sum + cv.adjustedValue, 0)
    );
    
    // Apply global adjustments
    
    // Age adjustment
    if (typeof listing.condition === 'object' && listing.condition.ageEstimate) {
      const ageAdjustment = this.calculateAgeAdjustment(listing.condition.ageEstimate);
      adjustments.push(ageAdjustment);
    }
    
    // Condition adjustment
    const overall = typeof listing.condition === 'object' ? listing.condition.overall : 3;
    const conditionAdjustment = this.calculateConditionAdjustment(overall || 3);
    adjustments.push(conditionAdjustment);
    
    // Completeness adjustment
    const completenessAdjustment = this.calculateCompletenessAdjustment(listing.components);
    adjustments.push(completenessAdjustment);
    
    // Market demand adjustment
    const demandAdjustment = this.calculateDemandAdjustment(listing.components);
    adjustments.push(demandAdjustment);
    
    // Apply all adjustments
    let finalValue = subtotal;
    for (const adj of adjustments) {
      finalValue = finalValue.mul(adj.factor);
    }
    
    // Calculate confidence score
    const confidence = this.calculateConfidence(componentValues, listing);
    
    return {
      total: finalValue.toNumber(),
      componentBreakdown: componentValues,
      confidence,
      adjustments,
      methodology: 'Component sum with condition, age, and market adjustments',
    };
  }
  
  /**
   * Calculate value for a generic component
   */
  private calculateComponentValue(
    type: string,
    model: string,
    condition: ComponentCondition
  ): ComponentValue {
    const baseValue = findPriceTier(type, model, condition) || 0;
    
    // If no exact match, try to estimate
    let confidence = 1.0;
    let estimatedValue = baseValue;
    
    if (baseValue === 0) {
      estimatedValue = this.estimateComponentValue(type, model, condition);
      confidence = 0.7; // Lower confidence for estimates
    }
    
    return {
      type,
      name: model,
      condition,
      baseValue: estimatedValue,
      adjustedValue: estimatedValue,
      confidence,
    };
  }
  
  /**
   * Estimate value when no exact pricing data exists
   */
  private estimateComponentValue(
    type: string,
    model: string,
    condition: ComponentCondition
  ): number {
    // Find similar components and average their values
    const similarComponents = ALL_PRICING_TIERS.filter(
      tier => tier.type === type
    );
    
    if (similarComponents.length === 0) {
      // Fallback values by type
      const fallbacks: Record<string, number> = {
        CPU: 100,
        GPU: 150,
        RAM: 30,
        Storage: 40,
        PSU: 50,
        Motherboard: 80,
        Case: 40,
      };
      return fallbacks[type] || 30;
    }
    
    // Average similar components
    const avgPrice = similarComponents.reduce(
      (sum, comp) => sum + comp.prices[condition],
      0
    ) / similarComponents.length;
    
    return Math.round(avgPrice);
  }
  
  /**
   * Calculate RAM value
   */
  private calculateRAMValue(ram: RAMComponent): ComponentValue {
    // Price based on capacity and speed
    let basePrice = 20; // Base for 8GB
    
    if (ram.size === 16) basePrice = 40;
    else if (ram.size === 32) basePrice = 80;
    else if (ram.size === 64) basePrice = 160;
    
    // Adjust for speed
    if (ram.speed >= 3600) basePrice *= 1.1;
    else if (ram.speed <= 2400) basePrice *= 0.9;
    
    // Adjust for DDR generation
    if (ram.type === 'DDR5') basePrice *= 1.5;
    else if (ram.type === 'DDR3') basePrice *= 0.6;
    
    return {
      type: 'RAM',
      name: `${ram.size}GB ${ram.type}-${ram.speed}`,
      condition: 'good' as ComponentCondition,
      baseValue: basePrice,
      adjustedValue: basePrice,
      confidence: 0.9,
    };
  }
  
  /**
   * Calculate storage value
   */
  private calculateStorageValue(storage: StorageComponent): ComponentValue {
    let basePrice = 20;
    
    // Price by capacity
    const pricePerGB = storage.type === 'NVMe' ? 0.08 :
                      storage.type === 'SATA SSD' ? 0.06 :
                      0.02; // HDD
    
    basePrice = storage.capacity * pricePerGB;
    
    // Cap at reasonable maximums
    if (storage.type === 'NVMe') basePrice = Math.min(basePrice, 150);
    else if (storage.type === 'SATA SSD') basePrice = Math.min(basePrice, 100);
    else basePrice = Math.min(basePrice, 60);
    
    // Adjust for health if provided
    if (storage.health && storage.health < 90) {
      basePrice *= storage.health / 100;
    }
    
    return {
      type: 'Storage',
      name: `${storage.capacity}GB ${storage.type}`,
      condition: 'good' as ComponentCondition,
      baseValue: basePrice,
      adjustedValue: basePrice,
      confidence: 0.9,
    };
  }
  
  /**
   * Calculate motherboard value
   */
  private calculateMotherboardValue(mobo: MotherboardComponent): ComponentValue {
    let basePrice = 80;
    
    // Adjust by chipset tier
    if (mobo.chipset.includes('X') || mobo.chipset.includes('Z')) {
      basePrice = 120; // High-end chipset
    } else if (mobo.chipset.includes('B')) {
      basePrice = 80; // Mid-range
    } else if (mobo.chipset.includes('H') || mobo.chipset.includes('A')) {
      basePrice = 60; // Entry-level
    }
    
    // Adjust by form factor
    if (mobo.formFactor === 'ITX') basePrice *= 1.2;
    else if (mobo.formFactor === 'mATX') basePrice *= 0.9;
    
    return {
      type: 'Motherboard',
      name: `${mobo.brand} ${mobo.model}`,
      condition: 'good' as ComponentCondition,
      baseValue: basePrice,
      adjustedValue: basePrice,
      confidence: 0.8,
    };
  }
  
  /**
   * Calculate PSU value
   */
  private calculatePSUValue(psu: PSUComponent): ComponentValue {
    // Base price by wattage
    let basePrice = 40 + (psu.wattage - 400) * 0.05;
    
    // Adjust for efficiency
    const efficiencyMultipliers: Record<string, number> = {
      '80+': 1.0,
      '80+ Bronze': 1.1,
      '80+ Silver': 1.2,
      '80+ Gold': 1.3,
      '80+ Platinum': 1.5,
      '80+ Titanium': 1.7,
    };
    
    basePrice *= efficiencyMultipliers[psu.efficiency] || 1.0;
    
    // Adjust for modularity
    if (psu.modular === 'full-modular') basePrice *= 1.2;
    else if (psu.modular === 'semi-modular') basePrice *= 1.1;
    
    return {
      type: 'PSU',
      name: `${psu.wattage}W ${psu.efficiency}`,
      condition: 'good' as ComponentCondition,
      baseValue: basePrice,
      adjustedValue: basePrice,
      confidence: 0.9,
    };
  }
  
  /**
   * Calculate case value
   */
  private calculateCaseValue(pcCase: CaseComponent): ComponentValue {
    let basePrice = 50;
    
    // Adjust by form factor
    if (pcCase.formFactor === 'Full Tower') basePrice = 70;
    else if (pcCase.formFactor === 'Mini Tower' || pcCase.formFactor === 'SFF') basePrice = 60;
    
    // Adjust for features
    if (pcCase.sidePanel === 'tempered glass') basePrice *= 1.3;
    else if (pcCase.sidePanel === 'windowed') basePrice *= 1.1;
    
    // Premium brands
    if (pcCase.brand && ['Lian Li', 'Fractal', 'NZXT'].includes(pcCase.brand)) {
      basePrice *= 1.2;
    }
    
    return {
      type: 'Case',
      name: pcCase.brand ? `${pcCase.brand} ${pcCase.formFactor}` : pcCase.formFactor,
      condition: 'good' as ComponentCondition,
      baseValue: basePrice,
      adjustedValue: basePrice,
      confidence: 0.8,
    };
  }
  
  /**
   * Calculate cooling value
   */
  private calculateCoolingValue(cooling: CoolerComponent): ComponentValue {
    let basePrice = 20;
    
    if (cooling.type === 'stock') {
      basePrice = 10;
    } else if (cooling.type === 'air') {
      basePrice = 40;
    } else if (cooling.type === 'aio') {
      basePrice = 60;
      if (cooling.size && cooling.size >= 280) basePrice = 80;
      if (cooling.size && cooling.size >= 360) basePrice = 100;
    } else if (cooling.type === 'custom-loop') {
      basePrice = 200; // Custom loops are expensive
    }
    
    return {
      type: 'Cooling',
      name: cooling.brand ? `${cooling.brand} ${cooling.type}` : cooling.type,
      condition: 'good' as ComponentCondition,
      baseValue: basePrice,
      adjustedValue: basePrice,
      confidence: 0.8,
    };
  }
  
  /**
   * Mining adjustment for GPUs
   */
  private applyMiningAdjustment(gpuValue: ComponentValue): Adjustment {
    return {
      reason: 'GPU mining wear risk',
      factor: 0.8,
      impact: -gpuValue.baseValue * 0.2,
    };
  }
  
  /**
   * Age-based depreciation
   */
  private calculateAgeAdjustment(ageMonths: number): Adjustment {
    // Depreciation curve: lose 20% first year, then 10% per year
    let factor = 1.0;
    
    if (ageMonths <= 12) {
      factor = 1 - (0.20 * (ageMonths / 12));
    } else {
      factor = 0.8 - (0.10 * ((ageMonths - 12) / 12));
    }
    
    factor = Math.max(factor, 0.3); // Floor at 30% of original value
    
    return {
      reason: `Age depreciation (${ageMonths} months)`,
      factor,
      impact: -(1 - factor) * 100,
    };
  }
  
  /**
   * Overall condition adjustment
   */
  private calculateConditionAdjustment(condition: 1 | 2 | 3 | 4 | 5): Adjustment {
    const factors: Record<number, number> = {
      5: 1.0,  // Excellent
      4: 0.9,  // Good
      3: 0.75, // Fair
      2: 0.6,  // Poor
      1: 0.4,  // Parts only
    };
    
    return {
      reason: `Overall condition score: ${condition}/5`,
      factor: factors[condition],
      impact: -(1 - factors[condition]) * 100,
    };
  }
  
  /**
   * Completeness adjustment - full builds worth more than sum of parts
   */
  private calculateCompletenessAdjustment(components: ListingComponents | undefined): Adjustment {
    const hasCore = !!(components?.cpu && components?.gpu && components?.motherboard);
    const hasMemory = !!(components?.ram && components.ram.length > 0);
    const hasStorage = !!(components?.storage && components.storage.length > 0);
    const hasPower = !!components?.psu;
    const hasCase = !!components?.case;
    
    if (hasCore && hasMemory && hasStorage && hasPower && hasCase) {
      // Complete system bonus
      return {
        reason: 'Complete system bonus',
        factor: 1.1,
        impact: 10,
      };
    } else if (hasCore && hasMemory && hasStorage) {
      // Near-complete system
      return {
        reason: 'Near-complete system',
        factor: 1.05,
        impact: 5,
      };
    }
    
    // Incomplete system
    return {
      reason: 'Incomplete system',
      factor: 0.95,
      impact: -5,
    };
  }
  
  /**
   * Market demand adjustment based on component desirability
   */
  private calculateDemandAdjustment(components: ListingComponents | undefined): Adjustment {
    let demandScore = 1.0;
    
    // High-demand GPUs
    if (components?.gpu) {
      const highDemandGPUs = ['3060', '3070', '3080', '4060', '4070', '6700'];
      if (highDemandGPUs.some(model => components.gpu!.model.includes(model))) {
        demandScore *= 1.1;
      }
    }
    
    // Current gen CPUs
    if (components?.cpu) {
      if (components.cpu.generation && components.cpu.generation >= 12) {
        demandScore *= 1.05;
      }
    }
    
    // DDR5 systems
    if (components.ram?.some(r => r.type === 'DDR5')) {
      demandScore *= 1.05;
    }
    
    return {
      reason: 'Market demand adjustment',
      factor: demandScore,
      impact: (demandScore - 1) * 100,
    };
  }
  
  /**
   * Calculate confidence score for the FMV estimate
   */
  private calculateConfidence(componentValues: ComponentValue[], listing: Listing): number {
    let confidence = 0.5; // Base confidence
    
    // More components identified = higher confidence
    confidence += componentValues.length * 0.05;
    
    // Higher individual component confidence = higher overall
    const avgComponentConfidence = componentValues.reduce(
      (sum, cv) => sum + cv.confidence,
      0
    ) / componentValues.length;
    confidence += avgComponentConfidence * 0.3;
    
    // More photos = higher confidence
    if (listing.images.length >= 5) confidence += 0.1;
    else if (listing.images.length >= 3) confidence += 0.05;
    
    // Detailed description = higher confidence
    if (listing.description.length > 200) confidence += 0.05;
    
    return Math.min(confidence, 0.95); // Cap at 95%
  }
}