/**
 * Tests for Operating Costs
 */

import { describe, it, expect } from 'vitest';
import {
  electricityCostWattHours,
  estimateSystemWattage,
  miningProfitability,
  warrantyValue,
  calculateTCO,
} from '../operating';

describe('Electricity Cost', () => {
  it('should calculate electricity cost correctly', () => {
    const cost = electricityCostWattHours(
      300, // 300W system
      8,   // 8 hours/day
      0.12 // $0.12/kWh
    );
    
    // 300W * 8h = 2.4 kWh/day * $0.12 = $0.288/day
    expect(cost.dailyCost).toBeCloseTo(0.288, 2);
    expect(cost.monthlyCost).toBeCloseTo(8.64, 2);
    expect(cost.yearlyCost).toBeCloseTo(105.12, 2);
  });

  it('should estimate system wattage', () => {
    const wattage = estimateSystemWattage({
      cpu: 'Intel i7-12700K',
      gpu: 'RTX 3080',
      ram: 32,
      storage: [
        { type: 'ssd' },
        { type: 'hdd' },
      ],
    });
    
    // Base 50 + CPU 95 + GPU 320 + RAM 12 + Storage 15 = 492 * 1.2 = ~590W
    expect(wattage).toBeGreaterThan(550);
    expect(wattage).toBeLessThan(650);
  });

  it('should handle minimal system', () => {
    const wattage = estimateSystemWattage({
      cpu: 'Intel i3',
      ram: 8,
      storage: [{ type: 'ssd' }],
    });
    
    // Base 50 + CPU 45 + RAM 3 + Storage 5 = 103 * 1.2 = ~124W
    expect(wattage).toBeLessThan(150);
  });
});

describe('Mining Profitability', () => {
  it('should calculate profitable mining', () => {
    const result = miningProfitability(
      'RTX 3080',
      0.10, // $0.10/kWh
      {
        algorithm: 'ethash',
        revenuePerMhPerDay: 0.02, // $0.02 per MH/s per day
      }
    );
    
    // RTX 3080: 100 MH/s * $0.02 = $2/day revenue
    // Power: 320W * 24h * 0.10 = $0.768/day cost
    expect(result.dailyRevenue).toBe(2);
    expect(result.dailyCost).toBeCloseTo(0.768, 2);
    expect(result.dailyProfit).toBeCloseTo(1.232, 2);
    expect(result.breakEvenDays).toBeGreaterThan(100); // GPU costs ~$500
  });

  it('should warn on unprofitable mining', () => {
    const result = miningProfitability(
      'RTX 3060',
      0.25, // High electricity cost
      {
        algorithm: 'ethash',
        revenuePerMhPerDay: 0.01, // Low revenue
      }
    );
    
    expect(result.dailyProfit).toBeLessThan(0);
    expect(result.warnings).toContain('Mining is not profitable at current rates');
  });

  it('should handle unknown GPU', () => {
    const result = miningProfitability(
      'Unknown GPU',
      0.12,
      {
        algorithm: 'ethash',
        revenuePerMhPerDay: 0.02,
      }
    );
    
    expect(result.dailyRevenue).toBe(0);
    expect(result.warnings).toContain('GPU mining data not available');
  });
});

describe('Warranty Value', () => {
  it('should calculate warranty value for GPU', () => {
    const value = warrantyValue(
      24, // 2 years remaining
      'EVGA',
      'gpu',
      1000 // Original price
    );
    
    // GPU: 12% annual * 2 years * 1.3 EVGA multiplier
    expect(value.estimatedValue).toBe(312); // 1000 * 0.12 * 2 * 1.3
    expect(value.transferable).toBe(true);
    expect(value.coverage).toBe('manufacturer');
  });

  it('should identify extended warranty', () => {
    const value = warrantyValue(48, 'ASUS', 'motherboard');
    
    expect(value.coverage).toBe('extended');
  });

  it('should calculate without original price', () => {
    const value = warrantyValue(12, 'Corsair', 'psu');
    
    expect(value.estimatedValue).toBeGreaterThan(0);
    expect(value.estimatedValue).toBeLessThan(50);
  });

  it('should apply brand multipliers', () => {
    const evgaValue = warrantyValue(12, 'EVGA', 'gpu', 1000);
    const genericValue = warrantyValue(12, 'Generic', 'gpu', 1000);
    
    expect(evgaValue.estimatedValue).toBeGreaterThan(genericValue.estimatedValue);
  });
});

describe('Total Cost of Ownership', () => {
  it('should calculate TCO for typical usage', () => {
    const tco = calculateTCO(
      1000,  // Purchase price
      400,   // System wattage
      8,     // Hours per day
      0.12,  // Electricity rate
      12,    // 12 months holding
      0      // No warranty
    );
    
    expect(tco.electricityCost.yearlyCost).toBeCloseTo(140.16, 1);
    expect(tco.maintenanceCost).toBe(60); // $5 * 12 months
    expect(tco.opportunityCost).toBe(50); // 5% of $1000
    expect(tco.totalFirstYear).toBeGreaterThan(1200);
  });

  it('should include warranty benefit', () => {
    const tcoWithWarranty = calculateTCO(1000, 400, 8, 0.12, 12, 24);
    const tcoWithoutWarranty = calculateTCO(1000, 400, 8, 0.12, 12, 0);
    
    expect(tcoWithWarranty.effectiveValue).toBeGreaterThan(tcoWithoutWarranty.effectiveValue);
  });

  it('should scale with holding period', () => {
    const tco6Months = calculateTCO(1000, 400, 8, 0.12, 6, 0);
    const tco12Months = calculateTCO(1000, 400, 8, 0.12, 12, 0);
    
    expect(tco6Months.maintenanceCost).toBe(30); // $5 * 6
    expect(tco12Months.maintenanceCost).toBe(60); // $5 * 12
    
    expect(tco6Months.opportunityCost).toBeLessThan(tco12Months.opportunityCost);
  });

  it('should calculate effective value', () => {
    const tco = calculateTCO(1000, 300, 4, 0.10, 6, 12);
    
    // Effective value = purchase - electricity - maintenance - opportunity + warranty
    const expectedElectricity = 300 / 1000 * 4 * 0.10 * 30 * 6; // ~21.6
    const expectedMaintenance = 30;
    const expectedOpportunity = 1000 * 0.05 * 0.5; // 25
    
    expect(tco.effectiveValue).toBeLessThan(1000); // Costs reduce value
  });
});