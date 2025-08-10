/**
 * Sample CPU/GPU Pricing Tiers
 * Based on market data - should be updated monthly
 */

import { ComponentCondition, PriceTier } from '../types';

export interface ComponentPriceTier {
  component: string;
  type: 'CPU' | 'GPU' | 'RAM' | 'Storage' | 'PSU' | 'Motherboard' | 'Case';
  brand: string;
  model: string;
  specs?: Record<string, unknown>;
  prices: Record<ComponentCondition, number>;
  lastUpdated: Date;
  notes?: string;
}

// Sample CPU Pricing Tiers
export const CPU_PRICING_TIERS: ComponentPriceTier[] = [
  // Intel CPUs
  {
    component: 'Intel Core i5-10400F',
    type: 'CPU',
    brand: 'Intel',
    model: 'i5-10400F',
    specs: { cores: 6, threads: 12, generation: 10 },
    prices: {
      'new': 150,
      'like-new': 105,
      'good': 90,
      'fair': 75,
      'poor': 60,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'Intel Core i7-10700K',
    type: 'CPU',
    brand: 'Intel',
    model: 'i7-10700K',
    specs: { cores: 8, threads: 16, generation: 10, unlocked: true },
    prices: {
      'new': 280,
      'like-new': 195,
      'good': 170,
      'fair': 145,
      'poor': 120,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'Intel Core i5-12400F',
    type: 'CPU',
    brand: 'Intel',
    model: 'i5-12400F',
    specs: { cores: 6, threads: 12, generation: 12 },
    prices: {
      'new': 180,
      'like-new': 140,
      'good': 120,
      'fair': 100,
      'poor': 80,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'Intel Core i7-12700K',
    type: 'CPU',
    brand: 'Intel',
    model: 'i7-12700K',
    specs: { cores: 12, threads: 20, generation: 12, unlocked: true },
    prices: {
      'new': 350,
      'like-new': 280,
      'good': 240,
      'fair': 200,
      'poor': 160,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  
  // AMD CPUs
  {
    component: 'AMD Ryzen 5 5600X',
    type: 'CPU',
    brand: 'AMD',
    model: 'Ryzen 5 5600X',
    specs: { cores: 6, threads: 12, generation: 5000 },
    prices: {
      'new': 200,
      'like-new': 160,
      'good': 140,
      'fair': 120,
      'poor': 100,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD Ryzen 7 5800X',
    type: 'CPU',
    brand: 'AMD',
    model: 'Ryzen 7 5800X',
    specs: { cores: 8, threads: 16, generation: 5000 },
    prices: {
      'new': 280,
      'like-new': 220,
      'good': 190,
      'fair': 160,
      'poor': 130,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD Ryzen 5 3600',
    type: 'CPU',
    brand: 'AMD',
    model: 'Ryzen 5 3600',
    specs: { cores: 6, threads: 12, generation: 3000 },
    prices: {
      'new': 150,
      'like-new': 110,
      'good': 90,
      'fair': 75,
      'poor': 60,
    },
    lastUpdated: new Date('2024-01-01'),
  },
];

// Sample GPU Pricing Tiers
export const GPU_PRICING_TIERS: ComponentPriceTier[] = [
  // NVIDIA GPUs
  {
    component: 'NVIDIA GTX 1060 6GB',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'GTX 1060',
    specs: { vram: 6, architecture: 'Pascal' },
    prices: {
      'new': 200,
      'like-new': 140,
      'good': 120,
      'fair': 100,
      'poor': 80,
    },
    lastUpdated: new Date('2024-01-01'),
    notes: 'Check for mining wear',
  },
  {
    component: 'NVIDIA RTX 2060',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 2060',
    specs: { vram: 6, architecture: 'Turing', rtx: true },
    prices: {
      'new': 300,
      'like-new': 240,
      'good': 210,
      'fair': 180,
      'poor': 150,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'NVIDIA RTX 3060 12GB',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 3060',
    specs: { vram: 12, architecture: 'Ampere', rtx: true },
    prices: {
      'new': 400,
      'like-new': 320,
      'good': 280,
      'fair': 240,
      'poor': 200,
    },
    lastUpdated: new Date('2024-01-01'),
    notes: 'High demand, 12GB variant worth more',
  },
  {
    component: 'NVIDIA RTX 3070',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 3070',
    specs: { vram: 8, architecture: 'Ampere', rtx: true },
    prices: {
      'new': 500,
      'like-new': 450,
      'good': 400,
      'fair': 350,
      'poor': 300,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'NVIDIA RTX 3080 10GB',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 3080',
    specs: { vram: 10, architecture: 'Ampere', rtx: true },
    prices: {
      'new': 700,
      'like-new': 600,
      'good': 550,
      'fair': 500,
      'poor': 450,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'NVIDIA RTX 4060',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 4060',
    specs: { vram: 8, architecture: 'Ada Lovelace', rtx: true },
    prices: {
      'new': 300,
      'like-new': 270,
      'good': 250,
      'fair': 230,
      'poor': 210,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  
  // AMD GPUs
  {
    component: 'AMD RX 580 8GB',
    type: 'GPU',
    brand: 'AMD',
    model: 'RX 580',
    specs: { vram: 8, architecture: 'Polaris' },
    prices: {
      'new': 180,
      'like-new': 120,
      'good': 100,
      'fair': 80,
      'poor': 60,
    },
    lastUpdated: new Date('2024-01-01'),
    notes: 'Common mining card, check carefully',
  },
  {
    component: 'AMD RX 6600',
    type: 'GPU',
    brand: 'AMD',
    model: 'RX 6600',
    specs: { vram: 8, architecture: 'RDNA2' },
    prices: {
      'new': 250,
      'like-new': 200,
      'good': 180,
      'fair': 160,
      'poor': 140,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD RX 6700 XT',
    type: 'GPU',
    brand: 'AMD',
    model: 'RX 6700 XT',
    specs: { vram: 12, architecture: 'RDNA2' },
    prices: {
      'new': 380,
      'like-new': 320,
      'good': 290,
      'fair': 260,
      'poor': 230,
    },
    lastUpdated: new Date('2024-01-01'),
  },
];

// Other Component Pricing
export const RAM_PRICING_TIERS: ComponentPriceTier[] = [
  {
    component: 'DDR4 8GB 3200MHz',
    type: 'RAM',
    brand: 'Generic',
    model: 'DDR4-3200',
    specs: { capacity: 8, speed: 3200, type: 'DDR4' },
    prices: {
      'new': 30,
      'like-new': 25,
      'good': 20,
      'fair': 15,
      'poor': 10,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'DDR4 16GB 3200MHz',
    type: 'RAM',
    brand: 'Generic',
    model: 'DDR4-3200',
    specs: { capacity: 16, speed: 3200, type: 'DDR4' },
    prices: {
      'new': 55,
      'like-new': 45,
      'good': 40,
      'fair': 35,
      'poor': 25,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'DDR5 16GB 5600MHz',
    type: 'RAM',
    brand: 'Generic',
    model: 'DDR5-5600',
    specs: { capacity: 16, speed: 5600, type: 'DDR5' },
    prices: {
      'new': 80,
      'like-new': 70,
      'good': 60,
      'fair': 50,
      'poor': 40,
    },
    lastUpdated: new Date('2024-01-01'),
  },
];

export const STORAGE_PRICING_TIERS: ComponentPriceTier[] = [
  {
    component: '256GB SATA SSD',
    type: 'Storage',
    brand: 'Generic',
    model: 'SATA SSD',
    specs: { capacity: 256, type: 'SATA SSD' },
    prices: {
      'new': 35,
      'like-new': 30,
      'good': 25,
      'fair': 20,
      'poor': 15,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: '500GB NVMe SSD',
    type: 'Storage',
    brand: 'Generic',
    model: 'NVMe SSD',
    specs: { capacity: 500, type: 'NVMe' },
    prices: {
      'new': 50,
      'like-new': 45,
      'good': 40,
      'fair': 35,
      'poor': 25,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: '1TB NVMe SSD',
    type: 'Storage',
    brand: 'Generic',
    model: 'NVMe SSD',
    specs: { capacity: 1000, type: 'NVMe' },
    prices: {
      'new': 80,
      'like-new': 70,
      'good': 60,
      'fair': 50,
      'poor': 40,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: '1TB HDD',
    type: 'Storage',
    brand: 'Generic',
    model: 'HDD',
    specs: { capacity: 1000, type: 'HDD' },
    prices: {
      'new': 40,
      'like-new': 30,
      'good': 20,
      'fair': 15,
      'poor': 10,
    },
    lastUpdated: new Date('2024-01-01'),
  },
];

export const PSU_PRICING_TIERS: ComponentPriceTier[] = [
  {
    component: '550W 80+ Bronze',
    type: 'PSU',
    brand: 'Generic',
    model: '550W Bronze',
    specs: { wattage: 550, efficiency: '80+ Bronze' },
    prices: {
      'new': 60,
      'like-new': 50,
      'good': 45,
      'fair': 35,
      'poor': 25,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: '650W 80+ Gold',
    type: 'PSU',
    brand: 'Generic',
    model: '650W Gold',
    specs: { wattage: 650, efficiency: '80+ Gold' },
    prices: {
      'new': 90,
      'like-new': 75,
      'good': 65,
      'fair': 55,
      'poor': 40,
    },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: '750W 80+ Gold',
    type: 'PSU',
    brand: 'Generic',
    model: '750W Gold',
    specs: { wattage: 750, efficiency: '80+ Gold' },
    prices: {
      'new': 110,
      'like-new': 90,
      'good': 80,
      'fair': 70,
      'poor': 50,
    },
    lastUpdated: new Date('2024-01-01'),
  },
];

// All pricing tiers combined
export const ALL_PRICING_TIERS: ComponentPriceTier[] = [
  ...CPU_PRICING_TIERS,
  ...GPU_PRICING_TIERS,
  ...RAM_PRICING_TIERS,
  ...STORAGE_PRICING_TIERS,
  ...PSU_PRICING_TIERS,
];

// Helper functions
export function findPriceTier(
  type: string,
  model: string,
  condition: ComponentCondition
): number | undefined {
  const tier = ALL_PRICING_TIERS.find(
    t => t.type === type && t.model.toLowerCase().includes(model.toLowerCase())
  );
  
  return tier?.prices[condition];
}

export function getComponentValue(
  component: { model: string; condition: ComponentCondition },
  type: string
): number {
  return findPriceTier(type, component.model, component.condition) || 0;
}