/**
 * ML Price Model
 * Lightweight in-browser price prediction using Ridge Regression
 */

import type { Deal } from '../types';
import { ComponentDetector } from '../parsers/component-detector';

export interface ModelFeatures {
  // GPU features
  gpuTier: number; // 1-5 (low to high)
  gpuVram: number; // GB
  gpuGeneration: number; // relative age
  
  // CPU features
  cpuTier: number; // 1-5
  cpuCores: number;
  cpuGeneration: number;
  
  // Memory & Storage
  ramSize: number; // GB
  ssdSize: number; // GB
  hddSize: number; // GB
  
  // Condition
  conditionScore: number; // 1-5
  
  // Market features
  daysLive: number;
  regionCode: number; // encoded region
}

export interface ModelWeights {
  bias: number;
  weights: number[];
  featureNames: string[];
  metrics?: {
    mae: number;
    r2: number;
    trainSamples: number;
  };
}

export interface TrainingData {
  features: ModelFeatures;
  price: number;
}

/**
 * Extract features from a deal
 */
export function extractFeatures(deal: Deal): ModelFeatures {
  const detector = new ComponentDetector();
  const components = detector.detectAll(
    `${deal.listing.title} ${deal.listing.description}`
  );
  
  // GPU features
  let gpuTier = 3;
  let gpuVram = 4;
  let gpuGen = 0;
  
  if (components.gpu) {
    const model = components.gpu.model.toLowerCase();
    // Simplified tier mapping
    if (model.includes('4090') || model.includes('4080')) gpuTier = 5;
    else if (model.includes('4070') || model.includes('3080')) gpuTier = 4;
    else if (model.includes('3070') || model.includes('3060')) gpuTier = 3;
    else if (model.includes('1660') || model.includes('2060')) gpuTier = 2;
    else gpuTier = 1;
    
    gpuVram = components.gpu.vram || 4;
    
    // Generation (newer = higher)
    if (model.includes('40')) gpuGen = 4;
    else if (model.includes('30')) gpuGen = 3;
    else if (model.includes('20')) gpuGen = 2;
    else if (model.includes('16')) gpuGen = 1;
    else gpuGen = 0;
  }
  
  // CPU features
  let cpuTier = 3;
  let cpuCores = 6;
  let cpuGen = 0;
  
  if (components.cpu) {
    const model = components.cpu.model.toLowerCase();
    // Simplified tier mapping
    if (model.includes('i9') || model.includes('ryzen 9')) cpuTier = 5;
    else if (model.includes('i7') || model.includes('ryzen 7')) cpuTier = 4;
    else if (model.includes('i5') || model.includes('ryzen 5')) cpuTier = 3;
    else if (model.includes('i3') || model.includes('ryzen 3')) cpuTier = 2;
    else cpuTier = 1;
    
    cpuCores = components.cpu.cores || 6;
    
    // Extract generation from model number
    const genMatch = model.match(/(\d+)\d{3}/);
    if (genMatch) {
      cpuGen = Math.min(parseInt(genMatch[1]) - 8, 5); // Normalize to 0-5
    }
  }
  
  // Memory & Storage
  const ramSize = components.ram?.reduce((sum, r) => sum + (r.capacity || 0), 0) || 16;
  const storage = components.storage || [];
  const ssdSize = storage.filter(s => s.type === 'ssd').reduce((sum, s) => sum + (s.capacity || 0), 0);
  const hddSize = storage.filter(s => s.type === 'hdd').reduce((sum, s) => sum + (s.capacity || 0), 0);
  
  // Condition
  let conditionScore = 3;
  const desc = deal.listing.description.toLowerCase();
  if (desc.includes('new') || desc.includes('mint')) conditionScore = 5;
  else if (desc.includes('excellent') || desc.includes('great')) conditionScore = 4;
  else if (desc.includes('good')) conditionScore = 3;
  else if (desc.includes('fair') || desc.includes('parts')) conditionScore = 2;
  else conditionScore = 1;
  
  // Market features
  const createdAt = new Date(deal.listing.metadata.createdAt);
  const daysLive = Math.floor((Date.now() - createdAt.getTime()) / (1000 * 60 * 60 * 24));
  
  // Simple region encoding
  const state = deal.listing.location.state;
  const regionCode = ['CA', 'NY', 'TX', 'FL', 'WA'].indexOf(state) + 1;
  
  return {
    gpuTier,
    gpuVram,
    gpuGeneration: gpuGen,
    cpuTier,
    cpuCores,
    cpuGeneration: cpuGen,
    ramSize,
    ssdSize,
    hddSize,
    conditionScore,
    daysLive,
    regionCode,
  };
}

/**
 * Normalize features for training
 */
function normalizeFeatures(features: ModelFeatures): number[] {
  return [
    features.gpuTier / 5,
    features.gpuVram / 24, // Max 24GB VRAM
    features.gpuGeneration / 5,
    features.cpuTier / 5,
    features.cpuCores / 24, // Max 24 cores
    features.cpuGeneration / 5,
    Math.log(features.ramSize + 1) / Math.log(129), // Log scale up to 128GB
    Math.log(features.ssdSize + 1) / Math.log(4097), // Log scale up to 4TB
    Math.log(features.hddSize + 1) / Math.log(8193), // Log scale up to 8TB
    features.conditionScore / 5,
    Math.min(features.daysLive / 30, 1), // Cap at 30 days
    features.regionCode / 6,
  ];
}

/**
 * Ridge Regression implementation
 */
export class RidgeRegression {
  private weights: number[] = [];
  private bias = 0;
  private lambda = 1.0; // Regularization parameter
  
  /**
   * Fit the model using normal equation with L2 regularization
   */
  fit(X: number[][], y: number[], lambda = 1.0): void {
    this.lambda = lambda;
    const n = X.length;
    const m = X[0].length;
    
    // Add bias column
    const Xb = X.map(row => [1, ...row]);
    
    // X^T * X
    const XtX = this.matmul(this.transpose(Xb), Xb);
    
    // Add regularization term (lambda * I)
    for (let i = 1; i < XtX.length; i++) {
      XtX[i][i] += lambda;
    }
    
    // X^T * y
    const Xty = this.matvec(this.transpose(Xb), y);
    
    // Solve (X^T * X + lambda * I) * w = X^T * y
    const w = this.solve(XtX, Xty);
    
    this.bias = w[0];
    this.weights = w.slice(1);
  }
  
  /**
   * Make predictions
   */
  predict(X: number[][]): number[] {
    return X.map(x => {
      let pred = this.bias;
      for (let i = 0; i < x.length; i++) {
        pred += x[i] * this.weights[i];
      }
      return pred;
    });
  }
  
  /**
   * Calculate mean absolute error
   */
  mae(yTrue: number[], yPred: number[]): number {
    let sum = 0;
    for (let i = 0; i < yTrue.length; i++) {
      sum += Math.abs(yTrue[i] - yPred[i]);
    }
    return sum / yTrue.length;
  }
  
  /**
   * Calculate R-squared
   */
  r2(yTrue: number[], yPred: number[]): number {
    const mean = yTrue.reduce((a, b) => a + b, 0) / yTrue.length;
    let ssRes = 0;
    let ssTot = 0;
    
    for (let i = 0; i < yTrue.length; i++) {
      ssRes += Math.pow(yTrue[i] - yPred[i], 2);
      ssTot += Math.pow(yTrue[i] - mean, 2);
    }
    
    return 1 - (ssRes / ssTot);
  }
  
  // Matrix operations
  private transpose(A: number[][]): number[][] {
    return A[0].map((_, i) => A.map(row => row[i]));
  }
  
  private matmul(A: number[][], B: number[][]): number[][] {
    const result: number[][] = [];
    for (let i = 0; i < A.length; i++) {
      result[i] = [];
      for (let j = 0; j < B[0].length; j++) {
        let sum = 0;
        for (let k = 0; k < B.length; k++) {
          sum += A[i][k] * B[k][j];
        }
        result[i][j] = sum;
      }
    }
    return result;
  }
  
  private matvec(A: number[][], b: number[]): number[] {
    return A.map(row => row.reduce((sum, a, i) => sum + a * b[i], 0));
  }
  
  // Solve linear system using Gaussian elimination
  private solve(A: number[][], b: number[]): number[] {
    const n = A.length;
    const Ab = A.map((row, i) => [...row, b[i]]);
    
    // Forward elimination
    for (let i = 0; i < n; i++) {
      // Partial pivoting
      let maxRow = i;
      for (let k = i + 1; k < n; k++) {
        if (Math.abs(Ab[k][i]) > Math.abs(Ab[maxRow][i])) {
          maxRow = k;
        }
      }
      [Ab[i], Ab[maxRow]] = [Ab[maxRow], Ab[i]];
      
      // Eliminate column
      for (let k = i + 1; k < n; k++) {
        const factor = Ab[k][i] / Ab[i][i];
        for (let j = i; j <= n; j++) {
          Ab[k][j] -= factor * Ab[i][j];
        }
      }
    }
    
    // Back substitution
    const x = new Array(n);
    for (let i = n - 1; i >= 0; i--) {
      x[i] = Ab[i][n];
      for (let j = i + 1; j < n; j++) {
        x[i] -= Ab[i][j] * x[j];
      }
      x[i] /= Ab[i][i];
    }
    
    return x;
  }
  
  getWeights(): ModelWeights {
    return {
      bias: this.bias,
      weights: this.weights,
      featureNames: [
        'gpuTier', 'gpuVram', 'gpuGeneration',
        'cpuTier', 'cpuCores', 'cpuGeneration',
        'ramSize', 'ssdSize', 'hddSize',
        'conditionScore', 'daysLive', 'regionCode',
      ],
    };
  }
  
  loadWeights(weights: ModelWeights): void {
    this.bias = weights.bias;
    this.weights = weights.weights;
  }
}

/**
 * Train model on deals
 */
export function trainModel(deals: Deal[]): ModelWeights {
  const validDeals = deals.filter(d => d.stage === 'sold' && d.sellPrice);
  
  if (validDeals.length < 10) {
    throw new Error('Need at least 10 sold deals to train model');
  }
  
  // Extract features and prices
  const X: number[][] = [];
  const y: number[] = [];
  
  validDeals.forEach(deal => {
    const features = extractFeatures(deal);
    X.push(normalizeFeatures(features));
    y.push(deal.sellPrice!);
  });
  
  // Train model
  const model = new RidgeRegression();
  model.fit(X, y, 10.0); // Higher lambda for small datasets
  
  // Calculate metrics
  const predictions = model.predict(X);
  const mae = model.mae(y, predictions);
  const r2 = model.r2(y, predictions);
  
  const weights = model.getWeights();
  weights.metrics = {
    mae,
    r2,
    trainSamples: validDeals.length,
  };
  
  return weights;
}

/**
 * Make price prediction
 */
export function predictPrice(
  deal: Deal,
  weights: ModelWeights
): number {
  const features = extractFeatures(deal);
  const normalized = normalizeFeatures(features);
  
  const model = new RidgeRegression();
  model.loadWeights(weights);
  
  const [prediction] = model.predict([normalized]);
  return Math.max(0, Math.round(prediction));
}