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
import { ALL_PRICING_TIERS, findPriceTier, getPriceRange } from '../data/pricing-tiers';
import { Settings } from '../settings/schema';

export interface FMVResult {
  total: number;
  componentBreakdown: ComponentValue[];
  confidence: number;
  adjustments: Adjustment[];
  priceRange: {
    min: number;
    max: number;
  };
  marketInsights: string[];
}

export interface ComponentValue {
  type: string;
  name: string;
  condition: ComponentCondition;
  baseValue: number;
  adjustedValue: number;
  confidence: number;
  source: string;
}

export interface Adjustment {
  type: string;
  description: string;
  factor: number;
  impact: number;
}

export class FMVCalculator {
  private settings: Settings;

  constructor(settings: Settings) {
    this.settings = settings;
  }

  updateSettings(settings: Settings) {
    this.settings = settings;
  }

  /**
   * Calculate the fair market value of a listing
   */
  calculate(listing: Listing): FMVResult {
    const componentValues: ComponentValue[] = [];
    const adjustments: Adjustment[] = [];
    const marketInsights: string[] = [];
    
    // Determine overall condition
    const condition = this.determineCondition(listing);
    
    // Calculate base component values
    if (listing.components?.cpu) {
      const cpuValue = this.calculateComponentValue(
        'CPU',
        listing.components.cpu.model,
        condition
      );
      if (cpuValue) {
        componentValues.push(cpuValue);
        if (cpuValue.confidence < 0.8) {
          marketInsights.push(`CPU model "${listing.components.cpu.model}" not in database - using estimate`);
        }
      }
    }
    
    if (listing.components?.gpu) {
      const gpuValue = this.calculateComponentValue(
        'GPU',
        listing.components.gpu.model,
        condition
      );
      
      if (gpuValue) {
        // Apply mining risk adjustment for RTX 30 series
        const gpuModel = listing.components.gpu.model.toLowerCase();
        const isMiningRisk = gpuModel.includes('3060') || gpuModel.includes('3070') || 
                           gpuModel.includes('3080') || gpuModel.includes('3090');
        
        if (isMiningRisk) {
          const miningAdjustment = this.applyMiningAdjustment(gpuValue);
          adjustments.push(miningAdjustment);
          gpuValue.adjustedValue *= miningAdjustment.factor;
          marketInsights.push('GPU may have mining history - 15% reduction applied');
        }
        
        componentValues.push(gpuValue);
      }
    }
    
    // RAM - sum all modules
    if (listing.components?.ram && listing.components.ram.length > 0) {
      const totalCapacity = listing.components.ram.reduce((sum, r) => sum + (r.capacity || r.size || 0), 0);
      const speed = Math.max(...listing.components.ram.map(r => r.speed || 3200));
      const type = listing.components.ram[0].type || 'DDR4';
      
      const ramValue = this.calculateRAMValue({
        capacity: totalCapacity,
        speed,
        type,
        modules: listing.components.ram.length
      } as RAMComponent, condition);
      
      if (ramValue) {
        componentValues.push(ramValue);
      }
    }
    
    // Storage - sum all drives
    if (listing.components?.storage && listing.components.storage.length > 0) {
      for (const storage of listing.components.storage) {
        const storageValue = this.calculateStorageValue(storage, condition);
        if (storageValue) {
          componentValues.push(storageValue);
        }
      }
    }
    
    // Motherboard
    if (listing.components?.motherboard) {
      const moboValue = this.calculateMotherboardValue(listing.components.motherboard, condition);
      if (moboValue) {
        componentValues.push(moboValue);
      }
    }
    
    // PSU
    if (listing.components?.psu) {
      const psuValue = this.calculatePSUValue(listing.components.psu, condition);
      if (psuValue) {
        componentValues.push(psuValue);
      }
    }
    
    // Case
    if (listing.components?.case) {
      const caseValue = this.calculateCaseValue(listing.components.case, condition);
      if (caseValue) {
        componentValues.push(caseValue);
      }
    }
    
    // Cooling
    if (listing.components?.cooling || listing.components?.cooler) {
      const cooling = listing.components.cooling || listing.components.cooler;
      const coolingValue = this.calculateCoolingValue(cooling!, condition);
      if (coolingValue) {
        componentValues.push(coolingValue);
      }
    }
    
    // Apply global adjustments
    
    // Age adjustment
    if (typeof listing.condition === 'object' && listing.condition.ageEstimate) {
      const ageAdjustment = this.calculateAgeAdjustment(listing.condition.ageEstimate);
      adjustments.push(ageAdjustment);
    }
    
    // Completeness adjustment
    const completenessAdjustment = this.calculateCompletenessAdjustment(listing.components);
    adjustments.push(completenessAdjustment);
    
    // Market demand adjustment
    const demandAdjustment = this.calculateDemandAdjustment(listing.components);
    adjustments.push(demandAdjustment);
    
    // Calculate totals
    const baseTotal = componentValues.reduce((sum, cv) => sum + cv.baseValue, 0);
    const adjustedTotal = componentValues.reduce((sum, cv) => sum + cv.adjustedValue, 0);
    
    // Apply global adjustments
    let finalTotal = adjustedTotal;
    for (const adjustment of adjustments) {
      if (adjustment.type !== 'mining') { // Mining already applied to GPU
        finalTotal *= adjustment.factor;
      }
    }
    
    // Calculate confidence
    const avgConfidence = componentValues.length > 0
      ? componentValues.reduce((sum, cv) => sum + cv.confidence, 0) / componentValues.length
      : 0.5;
    
    // Price range
    const priceRange = this.calculatePriceRange(componentValues, adjustments);
    
    // Market insights
    if (componentValues.length < 4) {
      marketInsights.push('Limited component data - estimate may be less accurate');
    }
    if (finalTotal > listing.price * 1.5) {
      marketInsights.push('Listing appears underpriced - verify all components');
    }
    if (finalTotal < listing.price * 0.7) {
      marketInsights.push('Listing may be overpriced or missing key information');
    }
    
    return {
      total: Math.round(finalTotal),
      componentBreakdown: componentValues,
      confidence: avgConfidence,
      adjustments,
      priceRange,
      marketInsights
    };
  }

  /**
   * Determine overall condition from listing
   */
  private determineCondition(listing: Listing): ComponentCondition {
    if (typeof listing.condition === 'string') {
      switch (listing.condition) {
        case 'new': return 'new';
        case 'like-new': return 'excellent';
        case 'good': return 'good';
        case 'fair': return 'fair';
        case 'parts': return 'poor';
        default: return 'good';
      }
    }
    
    if (listing.condition?.overall) {
      switch (listing.condition.overall) {
        case 5: return 'excellent';
        case 4: return 'good';
        case 3: return 'fair';
        case 2: return 'poor';
        case 1: return 'poor';
        default: return 'fair';
      }
    }
    
    return 'good'; // Default
  }

  /**
   * Calculate component value using pricing tiers
   */
  private calculateComponentValue(
    type: 'CPU' | 'GPU',
    model: string,
    condition: ComponentCondition
  ): ComponentValue | null {
    const priceTier = findPriceTier(type, model);
    
    if (priceTier) {
      const baseValue = priceTier.prices[condition];
      return {
        type,
        name: model,
        condition,
        baseValue,
        adjustedValue: baseValue,
        confidence: 0.95,
        source: 'pricing_tiers'
      };
    }
    
    // Fallback to estimate
    const priceRange = getPriceRange(type);
    const estimate = this.estimateValue(type, model, condition, priceRange);
    
    return {
      type,
      name: model,
      condition,
      baseValue: estimate,
      adjustedValue: estimate,
      confidence: 0.7,
      source: 'estimate'
    };
  }

  /**
   * Estimate value when exact match not found
   */
  private estimateValue(
    type: string,
    model: string,
    condition: ComponentCondition,
    priceRange: { min: number; max: number; avg: number }
  ): number {
    const modelLower = model.toLowerCase();
    let tierMultiplier = 0.5; // Default mid-tier
    
    // CPU tier detection
    if (type === 'CPU') {
      if (modelLower.includes('i9') || modelLower.includes('ryzen 9')) tierMultiplier = 0.8;
      else if (modelLower.includes('i7') || modelLower.includes('ryzen 7')) tierMultiplier = 0.65;
      else if (modelLower.includes('i5') || modelLower.includes('ryzen 5')) tierMultiplier = 0.5;
      else if (modelLower.includes('i3') || modelLower.includes('ryzen 3')) tierMultiplier = 0.3;
    }
    
    // GPU tier detection
    if (type === 'GPU') {
      if (modelLower.includes('4090') || modelLower.includes('7900')) tierMultiplier = 0.9;
      else if (modelLower.includes('4080') || modelLower.includes('4070')) tierMultiplier = 0.75;
      else if (modelLower.includes('4060') || modelLower.includes('7600')) tierMultiplier = 0.6;
      else if (modelLower.includes('3080') || modelLower.includes('3070')) tierMultiplier = 0.65;
      else if (modelLower.includes('3060') || modelLower.includes('6600')) tierMultiplier = 0.5;
      else if (modelLower.includes('1660') || modelLower.includes('1650')) tierMultiplier = 0.3;
    }
    
    // Condition multiplier
    const conditionMultipliers: Record<ComponentCondition, number> = {
      'new': 1.0,
      'excellent': 0.88,
      'good': 0.75,
      'fair': 0.62,
      'poor': 0.45
    };
    
    const baseEstimate = priceRange.min + (priceRange.max - priceRange.min) * tierMultiplier;
    return Math.round(baseEstimate * conditionMultipliers[condition]);
  }

  /**
   * Calculate RAM value
   */
  private calculateRAMValue(ram: RAMComponent, condition: ComponentCondition): ComponentValue | null {
    const model = `${ram.capacity}GB ${ram.type}-${ram.speed}`;
    const priceTier = findPriceTier('RAM', model);
    
    if (priceTier) {
      const baseValue = priceTier.prices[condition];
      return {
        type: 'RAM',
        name: model,
        condition,
        baseValue,
        adjustedValue: baseValue,
        confidence: 0.9,
        source: 'pricing_tiers'
      };
    }
    
    // Estimate based on capacity and type
    let basePrice = 20; // Base for 8GB DDR4
    
    // Capacity multiplier
    basePrice *= (ram.capacity / 8);
    
    // DDR5 premium
    if (ram.type === 'DDR5') basePrice *= 1.5;
    
    // Speed bonus
    if (ram.speed >= 3600) basePrice *= 1.1;
    else if (ram.speed >= 3200) basePrice *= 1.05;
    
    // Condition adjustment
    const conditionMultipliers: Record<ComponentCondition, number> = {
      'new': 1.0,
      'excellent': 0.85,
      'good': 0.7,
      'fair': 0.55,
      'poor': 0.4
    };
    
    basePrice *= conditionMultipliers[condition];
    
    return {
      type: 'RAM',
      name: model,
      condition,
      baseValue: Math.round(basePrice),
      adjustedValue: Math.round(basePrice),
      confidence: 0.8,
      source: 'estimate'
    };
  }

  /**
   * Calculate storage value
   */
  private calculateStorageValue(storage: StorageComponent, condition: ComponentCondition): ComponentValue | null {
    const typeStr = storage.type.toUpperCase().includes('NVME') ? 'NVMe' : 
                   storage.type.toUpperCase().includes('SSD') ? 'SATA SSD' : 'HDD';
    const model = `${storage.capacity}GB ${typeStr}`;
    const priceTier = findPriceTier('Storage', model);
    
    if (priceTier) {
      const baseValue = priceTier.prices[condition];
      return {
        type: 'Storage',
        name: model,
        condition,
        baseValue,
        adjustedValue: baseValue,
        confidence: 0.9,
        source: 'pricing_tiers'
      };
    }
    
    // Estimate based on capacity and type
    let basePrice = 20;
    
    // Price by capacity
    if (storage.capacity <= 256) basePrice = 25;
    else if (storage.capacity <= 512) basePrice = 35;
    else if (storage.capacity <= 1000) basePrice = 50;
    else if (storage.capacity <= 2000) basePrice = 80;
    else basePrice = 100 + (storage.capacity - 2000) * 0.02;
    
    // Type multiplier
    if (typeStr === 'NVMe') basePrice *= 1.3;
    else if (typeStr === 'HDD') basePrice *= 0.5;
    
    // Condition adjustment
    const conditionMultipliers: Record<ComponentCondition, number> = {
      'new': 1.0,
      'excellent': 0.85,
      'good': 0.7,
      'fair': 0.55,
      'poor': 0.4
    };
    
    basePrice *= conditionMultipliers[condition];
    
    return {
      type: 'Storage',
      name: model,
      condition,
      baseValue: Math.round(basePrice),
      adjustedValue: Math.round(basePrice),
      confidence: 0.8,
      source: 'estimate'
    };
  }

  /**
   * Calculate motherboard value
   */
  private calculateMotherboardValue(mobo: MotherboardComponent, condition: ComponentCondition): ComponentValue | null {
    let basePrice = 80;
    
    // Adjust by chipset tier
    const chipset = mobo.chipset?.toLowerCase() || '';
    if (chipset.includes('x670') || chipset.includes('z790')) basePrice = 250;
    else if (chipset.includes('x570') || chipset.includes('z690')) basePrice = 200;
    else if (chipset.includes('b650') || chipset.includes('b760')) basePrice = 150;
    else if (chipset.includes('b550') || chipset.includes('b660')) basePrice = 120;
    else if (chipset.includes('a520') || chipset.includes('h610')) basePrice = 80;
    
    // Form factor adjustment
    if (mobo.formFactor?.includes('ITX')) basePrice *= 1.2;
    else if (mobo.formFactor?.includes('E-ATX')) basePrice *= 1.3;
    
    // Condition adjustment
    const conditionMultipliers: Record<ComponentCondition, number> = {
      'new': 1.0,
      'excellent': 0.85,
      'good': 0.7,
      'fair': 0.55,
      'poor': 0.4
    };
    
    basePrice *= conditionMultipliers[condition];
    
    return {
      type: 'Motherboard',
      name: `${mobo.brand || 'Generic'} ${mobo.chipset || mobo.model || 'Motherboard'}`,
      condition,
      baseValue: Math.round(basePrice),
      adjustedValue: Math.round(basePrice),
      confidence: 0.75,
      source: 'estimate'
    };
  }

  /**
   * Calculate PSU value
   */
  private calculatePSUValue(psu: PSUComponent, condition: ComponentCondition): ComponentValue | null {
    const model = `${psu.wattage}W ${psu.efficiency || '80+'}`;
    const priceTier = findPriceTier('PSU', model);
    
    if (priceTier) {
      const baseValue = priceTier.prices[condition];
      return {
        type: 'PSU',
        name: model,
        condition,
        baseValue,
        adjustedValue: baseValue,
        confidence: 0.9,
        source: 'pricing_tiers'
      };
    }
    
    // Estimate based on wattage and efficiency
    let basePrice = 40 + (psu.wattage - 400) * 0.08;
    
    // Efficiency multiplier
    const efficiency = psu.efficiency?.toLowerCase() || '';
    if (efficiency.includes('titanium')) basePrice *= 1.4;
    else if (efficiency.includes('platinum')) basePrice *= 1.25;
    else if (efficiency.includes('gold')) basePrice *= 1.1;
    else if (efficiency.includes('silver')) basePrice *= 1.05;
    
    // Modularity bonus
    const modular = psu.modular?.toLowerCase() || '';
    if (modular.includes('full')) basePrice *= 1.15;
    else if (modular.includes('semi')) basePrice *= 1.08;
    
    // Condition adjustment
    const conditionMultipliers: Record<ComponentCondition, number> = {
      'new': 1.0,
      'excellent': 0.85,
      'good': 0.7,
      'fair': 0.55,
      'poor': 0.4
    };
    
    basePrice *= conditionMultipliers[condition];
    
    return {
      type: 'PSU',
      name: model,
      condition,
      baseValue: Math.round(basePrice),
      adjustedValue: Math.round(basePrice),
      confidence: 0.8,
      source: 'estimate'
    };
  }

  /**
   * Calculate case value
   */
  private calculateCaseValue(pcCase: CaseComponent, condition: ComponentCondition): ComponentValue | null {
    let basePrice = 50;
    
    // Form factor
    const formFactor = pcCase.formFactor?.toLowerCase() || '';
    if (formFactor.includes('full')) basePrice = 90;
    else if (formFactor.includes('mid')) basePrice = 60;
    else if (formFactor.includes('itx')) basePrice = 80;
    
    // Premium features
    if (pcCase.sidePanel?.toLowerCase().includes('tempered')) basePrice *= 1.2;
    if (pcCase.rgb) basePrice *= 1.15;
    
    // Condition adjustment - cases depreciate less
    const conditionMultipliers: Record<ComponentCondition, number> = {
      'new': 1.0,
      'excellent': 0.9,
      'good': 0.8,
      'fair': 0.65,
      'poor': 0.5
    };
    
    basePrice *= conditionMultipliers[condition];
    
    return {
      type: 'Case',
      name: pcCase.brand ? `${pcCase.brand} ${pcCase.model || 'Case'}` : 'Generic Case',
      condition,
      baseValue: Math.round(basePrice),
      adjustedValue: Math.round(basePrice),
      confidence: 0.75,
      source: 'estimate'
    };
  }

  /**
   * Calculate cooling value
   */
  private calculateCoolingValue(cooling: CoolerComponent, condition: ComponentCondition): ComponentValue | null {
    let basePrice = 20;
    
    if (cooling.type === 'stock' || !cooling.type) {
      basePrice = 15;
    } else if (cooling.type === 'air') {
      basePrice = cooling.brand?.toLowerCase().includes('noctua') ? 80 : 40;
    } else if (cooling.type === 'aio') {
      // AIO pricing by radiator size
      if (cooling.radiatorSize) {
        if (cooling.radiatorSize >= 360) basePrice = 120;
        else if (cooling.radiatorSize >= 280) basePrice = 100;
        else if (cooling.radiatorSize >= 240) basePrice = 80;
        else basePrice = 60;
      } else {
        basePrice = 80; // Default AIO price
      }
    } else if (cooling.type === 'custom' || cooling.type === 'custom-loop') {
      basePrice = 300; // Custom loops are expensive
    }
    
    // RGB premium
    if (cooling.rgb) basePrice *= 1.1;
    
    // Condition adjustment
    const conditionMultipliers: Record<ComponentCondition, number> = {
      'new': 1.0,
      'excellent': 0.85,
      'good': 0.7,
      'fair': 0.55,
      'poor': 0.4
    };
    
    basePrice *= conditionMultipliers[condition];
    
    return {
      type: 'Cooling',
      name: cooling.brand ? `${cooling.brand} ${cooling.model || cooling.type}` : cooling.type,
      condition,
      baseValue: Math.round(basePrice),
      adjustedValue: Math.round(basePrice),
      confidence: 0.75,
      source: 'estimate'
    };
  }

  /**
   * Apply mining wear adjustment for GPUs
   */
  private applyMiningAdjustment(gpuValue: ComponentValue): Adjustment {
    return {
      type: 'mining',
      description: 'Potential mining wear adjustment',
      factor: 0.85,
      impact: -15
    };
  }

  /**
   * Age-based depreciation
   */
  private calculateAgeAdjustment(ageMonths: number): Adjustment {
    let factor = 1.0;
    
    if (ageMonths <= 6) factor = 0.95;
    else if (ageMonths <= 12) factor = 0.9;
    else if (ageMonths <= 24) factor = 0.8;
    else if (ageMonths <= 36) factor = 0.7;
    else factor = 0.6;
    
    return {
      type: 'age',
      description: `Age depreciation (${ageMonths} months)`,
      factor,
      impact: -(1 - factor) * 100
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
        type: 'completeness',
        description: 'Complete system premium',
        factor: 1.1,
        impact: 10
      };
    } else if (hasCore && hasMemory && hasStorage) {
      // Nearly complete
      return {
        type: 'completeness',
        description: 'Nearly complete system',
        factor: 1.0,
        impact: 0
      };
    } else {
      // Incomplete - parts only
      return {
        type: 'completeness',
        description: 'Incomplete system (parts value)',
        factor: 0.9,
        impact: -10
      };
    }
  }

  /**
   * Market demand adjustment based on component desirability
   */
  private calculateDemandAdjustment(components: ListingComponents | undefined): Adjustment {
    let demandScore = 1.0;
    
    // High-demand GPUs
    if (components?.gpu) {
      const highDemandGPUs = ['4060', '4070', '4080', '4090', '7600', '7700', '7800', '7900'];
      const gpuModel = components.gpu.model.toLowerCase();
      if (highDemandGPUs.some(model => gpuModel.includes(model))) {
        demandScore *= 1.05;
      }
    }
    
    // Current gen CPUs
    if (components?.cpu) {
      const cpuModel = components.cpu.model.toLowerCase();
      if (cpuModel.includes('13th') || cpuModel.includes('7000') || 
          cpuModel.includes('13') || cpuModel.includes('7')) {
        demandScore *= 1.03;
      }
    }
    
    // DDR5 systems
    if (components?.ram && components.ram.length > 0 && components.ram[0].type === 'DDR5') {
      demandScore *= 1.02;
    }
    
    return {
      type: 'demand',
      description: 'Market demand adjustment',
      factor: demandScore,
      impact: (demandScore - 1) * 100
    };
  }

  /**
   * Calculate price range based on confidence
   */
  private calculatePriceRange(
    componentValues: ComponentValue[],
    adjustments: Adjustment[]
  ): { min: number; max: number } {
    const total = componentValues.reduce((sum, cv) => sum + cv.adjustedValue, 0);
    const avgConfidence = componentValues.length > 0
      ? componentValues.reduce((sum, cv) => sum + cv.confidence, 0) / componentValues.length
      : 0.5;
    
    // Apply adjustments
    let adjustedTotal = total;
    for (const adj of adjustments) {
      if (adj.type !== 'mining') {
        adjustedTotal *= adj.factor;
      }
    }
    
    // Range based on confidence
    const variance = 1 - avgConfidence;
    const margin = adjustedTotal * variance * 0.2; // 20% max variance
    
    return {
      min: Math.round(adjustedTotal - margin),
      max: Math.round(adjustedTotal + margin)
    };
  }
}