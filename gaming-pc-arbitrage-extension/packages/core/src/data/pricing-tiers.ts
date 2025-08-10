/**
 * Component Pricing Tiers
 * Real market prices for PC components by condition
 * Updated: January 2024
 */

type ComponentCondition = 'new' | 'excellent' | 'good' | 'fair' | 'poor';

export interface ComponentPriceTier {
  component: string;
  type: 'CPU' | 'GPU' | 'RAM' | 'Storage' | 'PSU' | 'Motherboard' | 'Case' | 'Cooling';
  brand: string;
  model: string;
  specs?: Record<string, unknown>;
  prices: Record<ComponentCondition, number>;
  lastUpdated: Date;
  notes?: string;
}

// CPU Pricing - Intel
export const CPU_PRICING_TIERS: ComponentPriceTier[] = [
  // 13th Gen Intel
  {
    component: 'Intel Core i9-13900K',
    type: 'CPU',
    brand: 'Intel',
    model: 'i9-13900K',
    specs: { cores: 24, threads: 32, baseClock: 3.0, boostClock: 5.8 },
    prices: { new: 589, excellent: 520, good: 450, fair: 380, poor: 300 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'Intel Core i7-13700K',
    type: 'CPU',
    brand: 'Intel',
    model: 'i7-13700K',
    specs: { cores: 16, threads: 24, baseClock: 3.4, boostClock: 5.4 },
    prices: { new: 409, excellent: 360, good: 310, fair: 260, poor: 200 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'Intel Core i5-13600K',
    type: 'CPU',
    brand: 'Intel',
    model: 'i5-13600K',
    specs: { cores: 14, threads: 20, baseClock: 3.5, boostClock: 5.1 },
    prices: { new: 319, excellent: 280, good: 240, fair: 200, poor: 150 },
    lastUpdated: new Date('2024-01-01'),
  },
  // 12th Gen Intel
  {
    component: 'Intel Core i9-12900K',
    type: 'CPU',
    brand: 'Intel',
    model: 'i9-12900K',
    specs: { cores: 16, threads: 24, baseClock: 3.2, boostClock: 5.2 },
    prices: { new: 419, excellent: 370, good: 320, fair: 270, poor: 200 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'Intel Core i7-12700K',
    type: 'CPU',
    brand: 'Intel',
    model: 'i7-12700K',
    specs: { cores: 12, threads: 20, baseClock: 3.6, boostClock: 5.0 },
    prices: { new: 319, excellent: 280, good: 240, fair: 200, poor: 150 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'Intel Core i5-12600K',
    type: 'CPU',
    brand: 'Intel',
    model: 'i5-12600K',
    specs: { cores: 10, threads: 16, baseClock: 3.7, boostClock: 4.9 },
    prices: { new: 229, excellent: 200, good: 170, fair: 140, poor: 100 },
    lastUpdated: new Date('2024-01-01'),
  },
  // 11th Gen Intel
  {
    component: 'Intel Core i9-11900K',
    type: 'CPU',
    brand: 'Intel',
    model: 'i9-11900K',
    specs: { cores: 8, threads: 16, baseClock: 3.5, boostClock: 5.3 },
    prices: { new: 299, excellent: 260, good: 220, fair: 180, poor: 140 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'Intel Core i7-11700K',
    type: 'CPU',
    brand: 'Intel',
    model: 'i7-11700K',
    specs: { cores: 8, threads: 16, baseClock: 3.6, boostClock: 5.0 },
    prices: { new: 249, excellent: 220, good: 190, fair: 160, poor: 120 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'Intel Core i5-11600K',
    type: 'CPU',
    brand: 'Intel',
    model: 'i5-11600K',
    specs: { cores: 6, threads: 12, baseClock: 3.9, boostClock: 4.9 },
    prices: { new: 179, excellent: 160, good: 140, fair: 120, poor: 90 },
    lastUpdated: new Date('2024-01-01'),
  },
  // 10th Gen Intel
  {
    component: 'Intel Core i9-10900K',
    type: 'CPU',
    brand: 'Intel',
    model: 'i9-10900K',
    specs: { cores: 10, threads: 20, baseClock: 3.7, boostClock: 5.3 },
    prices: { new: 279, excellent: 240, good: 200, fair: 160, poor: 120 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'Intel Core i7-10700K',
    type: 'CPU',
    brand: 'Intel',
    model: 'i7-10700K',
    specs: { cores: 8, threads: 16, baseClock: 3.8, boostClock: 5.1 },
    prices: { new: 219, excellent: 190, good: 160, fair: 130, poor: 100 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'Intel Core i5-10600K',
    type: 'CPU',
    brand: 'Intel',
    model: 'i5-10600K',
    specs: { cores: 6, threads: 12, baseClock: 4.1, boostClock: 4.8 },
    prices: { new: 169, excellent: 150, good: 130, fair: 110, poor: 80 },
    lastUpdated: new Date('2024-01-01'),
  },
  // AMD Ryzen 7000 Series
  {
    component: 'AMD Ryzen 9 7950X',
    type: 'CPU',
    brand: 'AMD',
    model: 'Ryzen 9 7950X',
    specs: { cores: 16, threads: 32, baseClock: 4.5, boostClock: 5.7 },
    prices: { new: 699, excellent: 620, good: 540, fair: 460, poor: 350 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD Ryzen 9 7900X',
    type: 'CPU',
    brand: 'AMD',
    model: 'Ryzen 9 7900X',
    specs: { cores: 12, threads: 24, baseClock: 4.7, boostClock: 5.6 },
    prices: { new: 549, excellent: 480, good: 420, fair: 360, poor: 280 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD Ryzen 7 7700X',
    type: 'CPU',
    brand: 'AMD',
    model: 'Ryzen 7 7700X',
    specs: { cores: 8, threads: 16, baseClock: 4.5, boostClock: 5.4 },
    prices: { new: 399, excellent: 350, good: 300, fair: 250, poor: 190 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD Ryzen 5 7600X',
    type: 'CPU',
    brand: 'AMD',
    model: 'Ryzen 5 7600X',
    specs: { cores: 6, threads: 12, baseClock: 4.7, boostClock: 5.3 },
    prices: { new: 299, excellent: 260, good: 220, fair: 180, poor: 140 },
    lastUpdated: new Date('2024-01-01'),
  },
  // AMD Ryzen 5000 Series
  {
    component: 'AMD Ryzen 9 5950X',
    type: 'CPU',
    brand: 'AMD',
    model: 'Ryzen 9 5950X',
    specs: { cores: 16, threads: 32, baseClock: 3.4, boostClock: 4.9 },
    prices: { new: 459, excellent: 400, good: 340, fair: 280, poor: 220 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD Ryzen 9 5900X',
    type: 'CPU',
    brand: 'AMD',
    model: 'Ryzen 9 5900X',
    specs: { cores: 12, threads: 24, baseClock: 3.7, boostClock: 4.8 },
    prices: { new: 349, excellent: 300, good: 260, fair: 220, poor: 170 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD Ryzen 7 5800X',
    type: 'CPU',
    brand: 'AMD',
    model: 'Ryzen 7 5800X',
    specs: { cores: 8, threads: 16, baseClock: 3.8, boostClock: 4.7 },
    prices: { new: 249, excellent: 220, good: 190, fair: 160, poor: 120 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD Ryzen 5 5600X',
    type: 'CPU',
    brand: 'AMD',
    model: 'Ryzen 5 5600X',
    specs: { cores: 6, threads: 12, baseClock: 3.7, boostClock: 4.6 },
    prices: { new: 189, excellent: 170, good: 150, fair: 130, poor: 100 },
    lastUpdated: new Date('2024-01-01'),
  },
];

// GPU Pricing - NVIDIA RTX 40 Series
export const GPU_PRICING_TIERS: ComponentPriceTier[] = [
  // RTX 4090
  {
    component: 'NVIDIA RTX 4090',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 4090',
    specs: { vram: 24, vramType: 'GDDR6X', tdp: 450 },
    prices: { new: 1599, excellent: 1450, good: 1300, fair: 1150, poor: 900 },
    lastUpdated: new Date('2024-01-01'),
  },
  // RTX 4080
  {
    component: 'NVIDIA RTX 4080',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 4080',
    specs: { vram: 16, vramType: 'GDDR6X', tdp: 320 },
    prices: { new: 1199, excellent: 1050, good: 900, fair: 750, poor: 600 },
    lastUpdated: new Date('2024-01-01'),
  },
  // RTX 4070 Ti
  {
    component: 'NVIDIA RTX 4070 Ti',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 4070 Ti',
    specs: { vram: 12, vramType: 'GDDR6X', tdp: 285 },
    prices: { new: 799, excellent: 720, good: 640, fair: 560, poor: 450 },
    lastUpdated: new Date('2024-01-01'),
  },
  // RTX 4070
  {
    component: 'NVIDIA RTX 4070',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 4070',
    specs: { vram: 12, vramType: 'GDDR6X', tdp: 200 },
    prices: { new: 599, excellent: 540, good: 480, fair: 420, poor: 340 },
    lastUpdated: new Date('2024-01-01'),
  },
  // RTX 4060 Ti
  {
    component: 'NVIDIA RTX 4060 Ti 16GB',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 4060 Ti',
    specs: { vram: 16, vramType: 'GDDR6', tdp: 165 },
    prices: { new: 499, excellent: 450, good: 400, fair: 350, poor: 280 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'NVIDIA RTX 4060 Ti 8GB',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 4060 Ti',
    specs: { vram: 8, vramType: 'GDDR6', tdp: 160 },
    prices: { new: 399, excellent: 360, good: 320, fair: 280, poor: 220 },
    lastUpdated: new Date('2024-01-01'),
  },
  // RTX 4060
  {
    component: 'NVIDIA RTX 4060',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 4060',
    specs: { vram: 8, vramType: 'GDDR6', tdp: 115 },
    prices: { new: 299, excellent: 270, good: 240, fair: 210, poor: 170 },
    lastUpdated: new Date('2024-01-01'),
  },
  // RTX 30 Series
  {
    component: 'NVIDIA RTX 3090 Ti',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 3090 Ti',
    specs: { vram: 24, vramType: 'GDDR6X', tdp: 450 },
    prices: { new: 999, excellent: 850, good: 700, fair: 550, poor: 400 },
    lastUpdated: new Date('2024-01-01'),
    notes: 'Mining card - check carefully',
  },
  {
    component: 'NVIDIA RTX 3090',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 3090',
    specs: { vram: 24, vramType: 'GDDR6X', tdp: 350 },
    prices: { new: 899, excellent: 750, good: 600, fair: 450, poor: 350 },
    lastUpdated: new Date('2024-01-01'),
    notes: 'Mining card - check carefully',
  },
  {
    component: 'NVIDIA RTX 3080 Ti',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 3080 Ti',
    specs: { vram: 12, vramType: 'GDDR6X', tdp: 350 },
    prices: { new: 699, excellent: 600, good: 500, fair: 400, poor: 300 },
    lastUpdated: new Date('2024-01-01'),
    notes: 'Mining card - check carefully',
  },
  {
    component: 'NVIDIA RTX 3080 10GB',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 3080',
    specs: { vram: 10, vramType: 'GDDR6X', tdp: 320 },
    prices: { new: 599, excellent: 500, good: 400, fair: 300, poor: 220 },
    lastUpdated: new Date('2024-01-01'),
    notes: 'Mining card - check carefully',
  },
  {
    component: 'NVIDIA RTX 3070 Ti',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 3070 Ti',
    specs: { vram: 8, vramType: 'GDDR6X', tdp: 290 },
    prices: { new: 499, excellent: 420, good: 340, fair: 260, poor: 200 },
    lastUpdated: new Date('2024-01-01'),
    notes: 'Mining card - check carefully',
  },
  {
    component: 'NVIDIA RTX 3070',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 3070',
    specs: { vram: 8, vramType: 'GDDR6', tdp: 220 },
    prices: { new: 399, excellent: 340, good: 280, fair: 220, poor: 170 },
    lastUpdated: new Date('2024-01-01'),
    notes: 'Mining card - check carefully',
  },
  {
    component: 'NVIDIA RTX 3060 Ti',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 3060 Ti',
    specs: { vram: 8, vramType: 'GDDR6', tdp: 200 },
    prices: { new: 329, excellent: 280, good: 230, fair: 180, poor: 140 },
    lastUpdated: new Date('2024-01-01'),
    notes: 'Mining card - check carefully',
  },
  {
    component: 'NVIDIA RTX 3060 12GB',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'RTX 3060',
    specs: { vram: 12, vramType: 'GDDR6', tdp: 170 },
    prices: { new: 279, excellent: 240, good: 200, fair: 160, poor: 120 },
    lastUpdated: new Date('2024-01-01'),
  },
  // GTX 16 Series
  {
    component: 'NVIDIA GTX 1660 Super',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'GTX 1660 Super',
    specs: { vram: 6, vramType: 'GDDR6', tdp: 125 },
    prices: { new: 179, excellent: 150, good: 120, fair: 90, poor: 70 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'NVIDIA GTX 1660 Ti',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'GTX 1660 Ti',
    specs: { vram: 6, vramType: 'GDDR6', tdp: 120 },
    prices: { new: 199, excellent: 170, good: 140, fair: 110, poor: 80 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'NVIDIA GTX 1650 Super',
    type: 'GPU',
    brand: 'NVIDIA',
    model: 'GTX 1650 Super',
    specs: { vram: 4, vramType: 'GDDR6', tdp: 100 },
    prices: { new: 149, excellent: 130, good: 110, fair: 90, poor: 70 },
    lastUpdated: new Date('2024-01-01'),
  },
  // AMD Radeon RX 7000 Series
  {
    component: 'AMD RX 7900 XTX',
    type: 'GPU',
    brand: 'AMD',
    model: 'RX 7900 XTX',
    specs: { vram: 24, vramType: 'GDDR6', tdp: 355 },
    prices: { new: 999, excellent: 880, good: 760, fair: 640, poor: 500 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD RX 7900 XT',
    type: 'GPU',
    brand: 'AMD',
    model: 'RX 7900 XT',
    specs: { vram: 20, vramType: 'GDDR6', tdp: 315 },
    prices: { new: 799, excellent: 700, good: 600, fair: 500, poor: 400 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD RX 7800 XT',
    type: 'GPU',
    brand: 'AMD',
    model: 'RX 7800 XT',
    specs: { vram: 16, vramType: 'GDDR6', tdp: 263 },
    prices: { new: 499, excellent: 440, good: 380, fair: 320, poor: 250 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD RX 7700 XT',
    type: 'GPU',
    brand: 'AMD',
    model: 'RX 7700 XT',
    specs: { vram: 12, vramType: 'GDDR6', tdp: 245 },
    prices: { new: 449, excellent: 400, good: 350, fair: 300, poor: 240 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD RX 7600',
    type: 'GPU',
    brand: 'AMD',
    model: 'RX 7600',
    specs: { vram: 8, vramType: 'GDDR6', tdp: 165 },
    prices: { new: 269, excellent: 240, good: 210, fair: 180, poor: 140 },
    lastUpdated: new Date('2024-01-01'),
  },
  // AMD Radeon RX 6000 Series
  {
    component: 'AMD RX 6950 XT',
    type: 'GPU',
    brand: 'AMD',
    model: 'RX 6950 XT',
    specs: { vram: 16, vramType: 'GDDR6', tdp: 335 },
    prices: { new: 649, excellent: 560, good: 470, fair: 380, poor: 300 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD RX 6900 XT',
    type: 'GPU',
    brand: 'AMD',
    model: 'RX 6900 XT',
    specs: { vram: 16, vramType: 'GDDR6', tdp: 300 },
    prices: { new: 549, excellent: 480, good: 410, fair: 340, poor: 270 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD RX 6800 XT',
    type: 'GPU',
    brand: 'AMD',
    model: 'RX 6800 XT',
    specs: { vram: 16, vramType: 'GDDR6', tdp: 300 },
    prices: { new: 449, excellent: 390, good: 330, fair: 270, poor: 210 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD RX 6800',
    type: 'GPU',
    brand: 'AMD',
    model: 'RX 6800',
    specs: { vram: 16, vramType: 'GDDR6', tdp: 250 },
    prices: { new: 379, excellent: 330, good: 280, fair: 230, poor: 180 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD RX 6700 XT',
    type: 'GPU',
    brand: 'AMD',
    model: 'RX 6700 XT',
    specs: { vram: 12, vramType: 'GDDR6', tdp: 230 },
    prices: { new: 329, excellent: 290, good: 250, fair: 210, poor: 170 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD RX 6650 XT',
    type: 'GPU',
    brand: 'AMD',
    model: 'RX 6650 XT',
    specs: { vram: 8, vramType: 'GDDR6', tdp: 180 },
    prices: { new: 279, excellent: 240, good: 200, fair: 160, poor: 130 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD RX 6600 XT',
    type: 'GPU',
    brand: 'AMD',
    model: 'RX 6600 XT',
    specs: { vram: 8, vramType: 'GDDR6', tdp: 160 },
    prices: { new: 239, excellent: 210, good: 180, fair: 150, poor: 120 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'AMD RX 6600',
    type: 'GPU',
    brand: 'AMD',
    model: 'RX 6600',
    specs: { vram: 8, vramType: 'GDDR6', tdp: 132 },
    prices: { new: 199, excellent: 170, good: 140, fair: 110, poor: 90 },
    lastUpdated: new Date('2024-01-01'),
  },
];

// RAM Pricing
export const RAM_PRICING_TIERS: ComponentPriceTier[] = [
  // DDR5
  {
    component: 'DDR5 32GB (2x16GB) 6000MHz',
    type: 'RAM',
    brand: 'Generic',
    model: '32GB DDR5-6000',
    specs: { capacity: 32, speed: 6000, type: 'DDR5', modules: 2 },
    prices: { new: 189, excellent: 170, good: 150, fair: 130, poor: 100 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'DDR5 32GB (2x16GB) 5600MHz',
    type: 'RAM',
    brand: 'Generic',
    model: '32GB DDR5-5600',
    specs: { capacity: 32, speed: 5600, type: 'DDR5', modules: 2 },
    prices: { new: 169, excellent: 150, good: 130, fair: 110, poor: 85 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'DDR5 16GB (2x8GB) 5600MHz',
    type: 'RAM',
    brand: 'Generic',
    model: '16GB DDR5-5600',
    specs: { capacity: 16, speed: 5600, type: 'DDR5', modules: 2 },
    prices: { new: 89, excellent: 80, good: 70, fair: 60, poor: 45 },
    lastUpdated: new Date('2024-01-01'),
  },
  // DDR4
  {
    component: 'DDR4 32GB (2x16GB) 3600MHz',
    type: 'RAM',
    brand: 'Generic',
    model: '32GB DDR4-3600',
    specs: { capacity: 32, speed: 3600, type: 'DDR4', modules: 2 },
    prices: { new: 109, excellent: 95, good: 80, fair: 65, poor: 50 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'DDR4 32GB (2x16GB) 3200MHz',
    type: 'RAM',
    brand: 'Generic',
    model: '32GB DDR4-3200',
    specs: { capacity: 32, speed: 3200, type: 'DDR4', modules: 2 },
    prices: { new: 99, excellent: 85, good: 70, fair: 55, poor: 40 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'DDR4 16GB (2x8GB) 3600MHz',
    type: 'RAM',
    brand: 'Generic',
    model: '16GB DDR4-3600',
    specs: { capacity: 16, speed: 3600, type: 'DDR4', modules: 2 },
    prices: { new: 59, excellent: 50, good: 40, fair: 30, poor: 22 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'DDR4 16GB (2x8GB) 3200MHz',
    type: 'RAM',
    brand: 'Generic',
    model: '16GB DDR4-3200',
    specs: { capacity: 16, speed: 3200, type: 'DDR4', modules: 2 },
    prices: { new: 49, excellent: 42, good: 35, fair: 28, poor: 20 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'DDR4 8GB (2x4GB) 3200MHz',
    type: 'RAM',
    brand: 'Generic',
    model: '8GB DDR4-3200',
    specs: { capacity: 8, speed: 3200, type: 'DDR4', modules: 2 },
    prices: { new: 29, excellent: 25, good: 20, fair: 15, poor: 10 },
    lastUpdated: new Date('2024-01-01'),
  },
];

// Storage Pricing
export const STORAGE_PRICING_TIERS: ComponentPriceTier[] = [
  // NVMe Gen4
  {
    component: 'Samsung 990 PRO 2TB NVMe',
    type: 'Storage',
    brand: 'Samsung',
    model: '990 PRO 2TB',
    specs: { capacity: 2000, type: 'NVMe', gen: 4, readSpeed: 7450 },
    prices: { new: 179, excellent: 160, good: 140, fair: 120, poor: 90 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'Samsung 990 PRO 1TB NVMe',
    type: 'Storage',
    brand: 'Samsung',
    model: '990 PRO 1TB',
    specs: { capacity: 1000, type: 'NVMe', gen: 4, readSpeed: 7450 },
    prices: { new: 99, excellent: 85, good: 70, fair: 55, poor: 40 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'WD Black SN850X 2TB NVMe',
    type: 'Storage',
    brand: 'Western Digital',
    model: 'SN850X 2TB',
    specs: { capacity: 2000, type: 'NVMe', gen: 4, readSpeed: 7300 },
    prices: { new: 159, excellent: 140, good: 120, fair: 100, poor: 75 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'WD Black SN850X 1TB NVMe',
    type: 'Storage',
    brand: 'Western Digital',
    model: 'SN850X 1TB',
    specs: { capacity: 1000, type: 'NVMe', gen: 4, readSpeed: 7300 },
    prices: { new: 89, excellent: 75, good: 60, fair: 45, poor: 35 },
    lastUpdated: new Date('2024-01-01'),
  },
  // NVMe Gen3
  {
    component: 'Samsung 970 EVO Plus 2TB',
    type: 'Storage',
    brand: 'Samsung',
    model: '970 EVO Plus 2TB',
    specs: { capacity: 2000, type: 'NVMe', gen: 3, readSpeed: 3500 },
    prices: { new: 139, excellent: 120, good: 100, fair: 80, poor: 60 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'Samsung 970 EVO Plus 1TB',
    type: 'Storage',
    brand: 'Samsung',
    model: '970 EVO Plus 1TB',
    specs: { capacity: 1000, type: 'NVMe', gen: 3, readSpeed: 3500 },
    prices: { new: 79, excellent: 70, good: 60, fair: 50, poor: 35 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'Crucial MX500 1TB SATA',
    type: 'Storage',
    brand: 'Crucial',
    model: 'MX500 1TB',
    specs: { capacity: 1000, type: 'SATA SSD', readSpeed: 560 },
    prices: { new: 69, excellent: 60, good: 50, fair: 40, poor: 30 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'Crucial MX500 500GB SATA',
    type: 'Storage',
    brand: 'Crucial',
    model: 'MX500 500GB',
    specs: { capacity: 500, type: 'SATA SSD', readSpeed: 560 },
    prices: { new: 39, excellent: 35, good: 30, fair: 25, poor: 18 },
    lastUpdated: new Date('2024-01-01'),
  },
  // Hard Drives
  {
    component: 'Seagate BarraCuda 4TB HDD',
    type: 'Storage',
    brand: 'Seagate',
    model: 'BarraCuda 4TB',
    specs: { capacity: 4000, type: 'HDD', rpm: 7200 },
    prices: { new: 79, excellent: 70, good: 60, fair: 50, poor: 35 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'WD Blue 2TB HDD',
    type: 'Storage',
    brand: 'Western Digital',
    model: 'Blue 2TB',
    specs: { capacity: 2000, type: 'HDD', rpm: 7200 },
    prices: { new: 49, excellent: 42, good: 35, fair: 28, poor: 20 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'WD Blue 1TB HDD',
    type: 'Storage',
    brand: 'Western Digital',
    model: 'Blue 1TB',
    specs: { capacity: 1000, type: 'HDD', rpm: 7200 },
    prices: { new: 39, excellent: 34, good: 28, fair: 22, poor: 15 },
    lastUpdated: new Date('2024-01-01'),
  },
];

// PSU Pricing
export const PSU_PRICING_TIERS: ComponentPriceTier[] = [
  // 1000W+
  {
    component: 'Corsair RM1000x 1000W Gold',
    type: 'PSU',
    brand: 'Corsair',
    model: 'RM1000x',
    specs: { wattage: 1000, efficiency: '80+ Gold', modular: 'Full' },
    prices: { new: 189, excellent: 165, good: 140, fair: 115, poor: 85 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'EVGA SuperNOVA 1000 G6',
    type: 'PSU',
    brand: 'EVGA',
    model: 'SuperNOVA 1000 G6',
    specs: { wattage: 1000, efficiency: '80+ Gold', modular: 'Full' },
    prices: { new: 179, excellent: 155, good: 130, fair: 105, poor: 80 },
    lastUpdated: new Date('2024-01-01'),
  },
  // 850W
  {
    component: 'Corsair RM850x 850W Gold',
    type: 'PSU',
    brand: 'Corsair',
    model: 'RM850x',
    specs: { wattage: 850, efficiency: '80+ Gold', modular: 'Full' },
    prices: { new: 149, excellent: 130, good: 110, fair: 90, poor: 65 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'Seasonic Focus GX-850',
    type: 'PSU',
    brand: 'Seasonic',
    model: 'Focus GX-850',
    specs: { wattage: 850, efficiency: '80+ Gold', modular: 'Full' },
    prices: { new: 139, excellent: 120, good: 100, fair: 80, poor: 60 },
    lastUpdated: new Date('2024-01-01'),
  },
  // 750W
  {
    component: 'Corsair RM750x 750W Gold',
    type: 'PSU',
    brand: 'Corsair',
    model: 'RM750x',
    specs: { wattage: 750, efficiency: '80+ Gold', modular: 'Full' },
    prices: { new: 129, excellent: 110, good: 90, fair: 70, poor: 50 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'EVGA SuperNOVA 750 GT',
    type: 'PSU',
    brand: 'EVGA',
    model: 'SuperNOVA 750 GT',
    specs: { wattage: 750, efficiency: '80+ Gold', modular: 'Full' },
    prices: { new: 109, excellent: 95, good: 80, fair: 65, poor: 45 },
    lastUpdated: new Date('2024-01-01'),
  },
  // 650W
  {
    component: 'Corsair RM650x 650W Gold',
    type: 'PSU',
    brand: 'Corsair',
    model: 'RM650x',
    specs: { wattage: 650, efficiency: '80+ Gold', modular: 'Full' },
    prices: { new: 109, excellent: 95, good: 80, fair: 65, poor: 45 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'Seasonic Focus GX-650',
    type: 'PSU',
    brand: 'Seasonic',
    model: 'Focus GX-650',
    specs: { wattage: 650, efficiency: '80+ Gold', modular: 'Full' },
    prices: { new: 99, excellent: 85, good: 70, fair: 55, poor: 40 },
    lastUpdated: new Date('2024-01-01'),
  },
  // 550W
  {
    component: 'Corsair CV550 550W Bronze',
    type: 'PSU',
    brand: 'Corsair',
    model: 'CV550',
    specs: { wattage: 550, efficiency: '80+ Bronze', modular: 'Non' },
    prices: { new: 59, excellent: 50, good: 40, fair: 30, poor: 20 },
    lastUpdated: new Date('2024-01-01'),
  },
  {
    component: 'EVGA BR 550W Bronze',
    type: 'PSU',
    brand: 'EVGA',
    model: 'BR 550',
    specs: { wattage: 550, efficiency: '80+ Bronze', modular: 'Non' },
    prices: { new: 49, excellent: 42, good: 35, fair: 28, poor: 18 },
    lastUpdated: new Date('2024-01-01'),
  },
];

// Combine all tiers
export const ALL_PRICING_TIERS: ComponentPriceTier[] = [
  ...CPU_PRICING_TIERS,
  ...GPU_PRICING_TIERS,
  ...RAM_PRICING_TIERS,
  ...STORAGE_PRICING_TIERS,
  ...PSU_PRICING_TIERS,
];

// Helper to find best match
export function findPriceTier(
  type: ComponentPriceTier['type'],
  model: string
): ComponentPriceTier | undefined {
  const normalizedModel = model.toLowerCase().replace(/[^a-z0-9]/g, '');
  
  return ALL_PRICING_TIERS.find(tier => {
    if (tier.type !== type) return false;
    const tierModel = tier.model.toLowerCase().replace(/[^a-z0-9]/g, '');
    return normalizedModel.includes(tierModel) || tierModel.includes(normalizedModel);
  });
}

// Get price range for a component type
export function getPriceRange(type: ComponentPriceTier['type']): {
  min: number;
  max: number;
  avg: number;
} {
  const tiers = ALL_PRICING_TIERS.filter(t => t.type === type);
  const prices = tiers.flatMap(t => Object.values(t.prices));
  
  return {
    min: Math.min(...prices),
    max: Math.max(...prices),
    avg: prices.reduce((a, b) => a + b, 0) / prices.length,
  };
}