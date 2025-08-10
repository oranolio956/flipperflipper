/**
 * ML Price Predictor
 * Simple in-browser price prediction
 */

export interface PricePrediction {
  price: number;
  confidence: number;
  factors: Array<{
    name: string;
    impact: number;
  }>;
}

export class PricePredictor {
  predict(specs: {
    cpu?: string;
    gpu?: string;
    ram?: number;
    storage?: number;
  }): PricePrediction {
    // Simplified price prediction based on components
    let basePrice = 300;
    const factors: Array<{ name: string; impact: number }> = [];
    
    // CPU impact
    if (specs.cpu) {
      if (specs.cpu.includes('i9') || specs.cpu.includes('Ryzen 9')) {
        basePrice += 300;
        factors.push({ name: 'High-end CPU', impact: 300 });
      } else if (specs.cpu.includes('i7') || specs.cpu.includes('Ryzen 7')) {
        basePrice += 200;
        factors.push({ name: 'Mid-high CPU', impact: 200 });
      } else if (specs.cpu.includes('i5') || specs.cpu.includes('Ryzen 5')) {
        basePrice += 100;
        factors.push({ name: 'Mid-range CPU', impact: 100 });
      }
    }
    
    // GPU impact
    if (specs.gpu) {
      if (specs.gpu.includes('4090') || specs.gpu.includes('4080')) {
        basePrice += 1200;
        factors.push({ name: 'High-end GPU', impact: 1200 });
      } else if (specs.gpu.includes('3080') || specs.gpu.includes('3070')) {
        basePrice += 600;
        factors.push({ name: 'Last-gen high GPU', impact: 600 });
      } else if (specs.gpu.includes('3060') || specs.gpu.includes('2070')) {
        basePrice += 300;
        factors.push({ name: 'Mid-range GPU', impact: 300 });
      }
    }
    
    // RAM impact
    if (specs.ram) {
      const ramPrice = specs.ram * 3; // $3 per GB
      basePrice += ramPrice;
      factors.push({ name: `${specs.ram}GB RAM`, impact: ramPrice });
    }
    
    // Storage impact
    if (specs.storage) {
      const storagePrice = specs.storage * 0.05; // $0.05 per GB
      basePrice += storagePrice;
      factors.push({ name: `${specs.storage}GB Storage`, impact: storagePrice });
    }
    
    return {
      price: Math.round(basePrice),
      confidence: 0.75,
      factors
    };
  }
}