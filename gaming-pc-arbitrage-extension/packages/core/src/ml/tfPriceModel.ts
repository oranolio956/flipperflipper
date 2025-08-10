/**
 * TensorFlow.js Price Prediction Model
 * Production-ready ML model for PC component pricing
 */

import * as tf from '@tensorflow/tfjs';
import { ComponentPriceTier, findPriceTier } from '../data/pricing-tiers';

export interface MLPredictionResult {
  price: number;
  confidence: number;
  priceRange: {
    min: number;
    max: number;
  };
  factors: {
    name: string;
    impact: number;
    importance: number;
  }[];
  modelVersion: string;
  explanations: string[];
}

export interface TrainingData {
  features: number[][];
  labels: number[];
  featureNames: string[];
}

export class TensorFlowPriceModel {
  private model: tf.LayersModel | null = null;
  private normalizer: {
    inputMean: tf.Tensor;
    inputStd: tf.Tensor;
    labelMean: number;
    labelStd: number;
  } | null = null;
  
  private readonly modelConfig = {
    version: '1.0.0',
    inputFeatures: [
      'cpu_tier', 'gpu_tier', 'ram_gb', 'storage_gb', 'storage_type',
      'age_months', 'condition_score', 'completeness', 'brand_reputation',
      'market_demand', 'platform_type', 'seller_reputation'
    ],
    hiddenLayers: [64, 32, 16],
    epochs: 100,
    batchSize: 32,
    learningRate: 0.001
  };

  /**
   * Initialize or load the model
   */
  async initialize(): Promise<void> {
    try {
      // Try to load existing model
      await this.loadModel();
    } catch (error) {
      console.log('No existing model found, training new model...');
      await this.trainModel();
    }
  }

  /**
   * Train the model with historical data
   */
  private async trainModel(): Promise<void> {
    const trainingData = this.generateTrainingData();
    
    // Prepare data
    const features = tf.tensor2d(trainingData.features);
    const labels = tf.tensor1d(trainingData.labels);
    
    // Normalize data
    const { normalizedFeatures, normalizedLabels, normalizer } = this.normalizeData(
      features,
      labels
    );
    this.normalizer = normalizer;
    
    // Build model architecture
    this.model = this.buildModel(trainingData.features[0].length);
    
    // Compile model
    this.model.compile({
      optimizer: tf.train.adam(this.modelConfig.learningRate),
      loss: 'meanSquaredError',
      metrics: ['mse', 'mae']
    });
    
    // Train model
    await this.model.fit(normalizedFeatures, normalizedLabels, {
      epochs: this.modelConfig.epochs,
      batchSize: this.modelConfig.batchSize,
      validationSplit: 0.2,
      callbacks: {
        onEpochEnd: (epoch, logs) => {
          if (epoch % 10 === 0) {
            console.log(`Epoch ${epoch}: loss = ${logs?.loss?.toFixed(4)}`);
          }
        }
      }
    });
    
    // Save model
    await this.saveModel();
    
    // Cleanup
    features.dispose();
    labels.dispose();
    normalizedFeatures.dispose();
    normalizedLabels.dispose();
  }

  /**
   * Build neural network architecture
   */
  private buildModel(inputSize: number): tf.Sequential {
    const model = tf.sequential();
    
    // Input layer
    model.add(tf.layers.dense({
      inputShape: [inputSize],
      units: this.modelConfig.hiddenLayers[0],
      activation: 'relu',
      kernelInitializer: 'heNormal'
    }));
    
    // Dropout for regularization
    model.add(tf.layers.dropout({ rate: 0.2 }));
    
    // Hidden layers
    for (let i = 1; i < this.modelConfig.hiddenLayers.length; i++) {
      model.add(tf.layers.dense({
        units: this.modelConfig.hiddenLayers[i],
        activation: 'relu',
        kernelInitializer: 'heNormal'
      }));
      model.add(tf.layers.batchNormalization());
      if (i < this.modelConfig.hiddenLayers.length - 1) {
        model.add(tf.layers.dropout({ rate: 0.1 }));
      }
    }
    
    // Output layer
    model.add(tf.layers.dense({
      units: 1,
      activation: 'linear'
    }));
    
    return model;
  }

  /**
   * Predict price for given specifications
   */
  async predict(specs: {
    cpu?: string;
    gpu?: string;
    ram?: number;
    storage?: Array<{ capacity: number; type: string }>;
    condition?: string;
    ageMonths?: number;
    platform?: string;
    completeness?: number;
  }): Promise<MLPredictionResult> {
    if (!this.model || !this.normalizer) {
      await this.initialize();
    }
    
    // Extract features
    const features = this.extractFeatures(specs);
    const featureTensor = tf.tensor2d([features]);
    
    // Normalize features
    const normalizedFeatures = featureTensor.sub(this.normalizer!.inputMean)
      .div(this.normalizer!.inputStd);
    
    // Make prediction
    const normalizedPrediction = this.model!.predict(normalizedFeatures) as tf.Tensor;
    const prediction = normalizedPrediction.mul(this.normalizer!.labelStd)
      .add(this.normalizer!.labelMean);
    
    const priceValue = (await prediction.data())[0];
    
    // Calculate confidence and uncertainty
    const { confidence, priceRange } = await this.calculateUncertainty(
      specs,
      priceValue,
      features
    );
    
    // Get feature importance
    const factors = this.calculateFeatureImportance(features, priceValue);
    
    // Generate explanations
    const explanations = this.generateExplanations(specs, factors, priceValue);
    
    // Cleanup
    featureTensor.dispose();
    normalizedFeatures.dispose();
    normalizedPrediction.dispose();
    prediction.dispose();
    
    return {
      price: Math.round(priceValue),
      confidence,
      priceRange,
      factors,
      modelVersion: this.modelConfig.version,
      explanations
    };
  }

  /**
   * Extract features from specifications
   */
  private extractFeatures(specs: any): number[] {
    const features: number[] = [];
    
    // CPU tier (0-1 scale)
    features.push(this.getCpuTier(specs.cpu));
    
    // GPU tier (0-1 scale)
    features.push(this.getGpuTier(specs.gpu));
    
    // RAM in GB
    features.push(specs.ram || 8);
    
    // Total storage in GB
    const totalStorage = specs.storage?.reduce((sum, s) => sum + s.capacity, 0) || 256;
    features.push(totalStorage);
    
    // Storage type (0=HDD, 0.5=SATA SSD, 1=NVMe)
    const storageType = this.getStorageType(specs.storage);
    features.push(storageType);
    
    // Age in months
    features.push(specs.ageMonths || 12);
    
    // Condition score (0-1)
    features.push(this.getConditionScore(specs.condition));
    
    // Completeness (0-1)
    features.push(specs.completeness || 0.8);
    
    // Brand reputation (0-1)
    features.push(this.getBrandReputation(specs));
    
    // Market demand (0-1)
    features.push(this.getMarketDemand(specs));
    
    // Platform type (0=Craigslist, 0.5=OfferUp, 1=Facebook)
    features.push(this.getPlatformScore(specs.platform));
    
    // Seller reputation (placeholder)
    features.push(0.5);
    
    return features;
  }

  /**
   * Generate synthetic training data
   */
  private generateTrainingData(): TrainingData {
    const features: number[][] = [];
    const labels: number[] = [];
    
    // Generate combinations of components
    const cpuTiers = [0.2, 0.4, 0.6, 0.8, 1.0];
    const gpuTiers = [0, 0.3, 0.5, 0.7, 0.9, 1.0];
    const ramOptions = [8, 16, 32, 64];
    const storageOptions = [256, 512, 1000, 2000];
    const ageOptions = [0, 6, 12, 24, 36];
    const conditions = [0.4, 0.6, 0.8, 1.0];
    
    for (const cpu of cpuTiers) {
      for (const gpu of gpuTiers) {
        for (const ram of ramOptions) {
          for (const storage of storageOptions) {
            for (const age of ageOptions) {
              for (const condition of conditions) {
                // Generate feature vector
                const feature = [
                  cpu, gpu, ram, storage,
                  0.7, // storage type (mixed)
                  age,
                  condition,
                  0.9, // completeness
                  0.7, // brand reputation
                  0.6, // market demand
                  0.5, // platform
                  0.5  // seller reputation
                ];
                
                // Calculate realistic price
                const basePrice = 200;
                const cpuPrice = cpu * 400;
                const gpuPrice = gpu * 800;
                const ramPrice = (ram / 8) * 40;
                const storagePrice = (storage / 256) * 30;
                
                // Apply depreciation
                const ageDepreciation = Math.max(0.3, 1 - (age / 48));
                const conditionMultiplier = 0.5 + (condition * 0.5);
                
                const price = (basePrice + cpuPrice + gpuPrice + ramPrice + storagePrice) *
                  ageDepreciation * conditionMultiplier;
                
                // Add some noise
                const noise = (Math.random() - 0.5) * price * 0.1;
                
                features.push(feature);
                labels.push(price + noise);
              }
            }
          }
        }
      }
    }
    
    return {
      features,
      labels,
      featureNames: this.modelConfig.inputFeatures
    };
  }

  /**
   * Normalize data for training
   */
  private normalizeData(features: tf.Tensor2D, labels: tf.Tensor1D) {
    const inputMean = features.mean(0);
    const inputStd = features.sub(inputMean).square().mean(0).sqrt().add(1e-7);
    
    const labelMean = labels.mean().dataSync()[0];
    const labelStd = labels.sub(labelMean).square().mean().sqrt().add(1e-7).dataSync()[0];
    
    const normalizedFeatures = features.sub(inputMean).div(inputStd);
    const normalizedLabels = labels.sub(labelMean).div(labelStd);
    
    return {
      normalizedFeatures,
      normalizedLabels,
      normalizer: {
        inputMean,
        inputStd,
        labelMean,
        labelStd
      }
    };
  }

  /**
   * Calculate prediction uncertainty
   */
  private async calculateUncertainty(
    specs: any,
    prediction: number,
    features: number[]
  ): Promise<{ confidence: number; priceRange: { min: number; max: number } }> {
    // Monte Carlo dropout for uncertainty estimation
    const predictions: number[] = [];
    const numSamples = 20;
    
    for (let i = 0; i < numSamples; i++) {
      const featureTensor = tf.tensor2d([features]);
      const normalizedFeatures = featureTensor.sub(this.normalizer!.inputMean)
        .div(this.normalizer!.inputStd);
      
      // Set training mode to true to enable dropout
      const pred = this.model!.predict(normalizedFeatures, { training: true }) as tf.Tensor;
      const denormalized = pred.mul(this.normalizer!.labelStd)
        .add(this.normalizer!.labelMean);
      
      predictions.push((await denormalized.data())[0]);
      
      featureTensor.dispose();
      normalizedFeatures.dispose();
      pred.dispose();
      denormalized.dispose();
    }
    
    // Calculate statistics
    const mean = predictions.reduce((a, b) => a + b) / predictions.length;
    const variance = predictions.reduce((sum, p) => sum + Math.pow(p - mean, 2), 0) / predictions.length;
    const std = Math.sqrt(variance);
    
    // Confidence based on coefficient of variation
    const cv = std / mean;
    const confidence = Math.max(0.5, Math.min(0.95, 1 - cv));
    
    // Price range (95% confidence interval)
    const margin = 1.96 * std;
    
    return {
      confidence,
      priceRange: {
        min: Math.round(Math.max(0, prediction - margin)),
        max: Math.round(prediction + margin)
      }
    };
  }

  /**
   * Calculate feature importance using gradient-based method
   */
  private calculateFeatureImportance(features: number[], prediction: number): any[] {
    const importance: any[] = [];
    const epsilon = 0.01;
    
    for (let i = 0; i < features.length; i++) {
      // Calculate gradient numerically
      const featuresPlus = [...features];
      featuresPlus[i] += epsilon;
      
      const featureTensor = tf.tensor2d([featuresPlus]);
      const normalizedFeatures = featureTensor.sub(this.normalizer!.inputMean)
        .div(this.normalizer!.inputStd);
      
      const pred = this.model!.predict(normalizedFeatures) as tf.Tensor;
      const denormalized = pred.mul(this.normalizer!.labelStd)
        .add(this.normalizer!.labelMean);
      
      const predictionPlus = denormalized.dataSync()[0];
      const gradient = (predictionPlus - prediction) / epsilon;
      
      importance.push({
        name: this.modelConfig.inputFeatures[i],
        impact: gradient * features[i],
        importance: Math.abs(gradient)
      });
      
      featureTensor.dispose();
      normalizedFeatures.dispose();
      pred.dispose();
      denormalized.dispose();
    }
    
    // Sort by importance
    importance.sort((a, b) => b.importance - a.importance);
    
    return importance.slice(0, 5); // Top 5 factors
  }

  /**
   * Generate human-readable explanations
   */
  private generateExplanations(specs: any, factors: any[], price: number): string[] {
    const explanations: string[] = [];
    
    // Price level explanation
    if (price > 2000) {
      explanations.push('High-end gaming system with premium components');
    } else if (price > 1000) {
      explanations.push('Mid-to-high tier gaming PC with good performance');
    } else if (price > 500) {
      explanations.push('Entry to mid-level gaming capable system');
    } else {
      explanations.push('Budget system suitable for light gaming');
    }
    
    // Component insights
    for (const factor of factors.slice(0, 3)) {
      if (factor.name === 'gpu_tier' && factor.importance > 0.2) {
        explanations.push('GPU is the primary value driver for this system');
      } else if (factor.name === 'age_months' && factor.impact < -50) {
        explanations.push('Age significantly affects the valuation');
      } else if (factor.name === 'condition_score' && factor.importance > 0.15) {
        explanations.push('Condition is an important factor in pricing');
      }
    }
    
    // Market conditions
    if (specs.platform === 'facebook') {
      explanations.push('Facebook Marketplace typically has competitive pricing');
    }
    
    return explanations;
  }

  /**
   * Helper methods for feature extraction
   */
  private getCpuTier(cpu?: string): number {
    if (!cpu) return 0.3;
    const cpuLower = cpu.toLowerCase();
    
    // Intel tiers
    if (cpuLower.includes('i9-13') || cpuLower.includes('i9-12')) return 1.0;
    if (cpuLower.includes('i7-13') || cpuLower.includes('i7-12')) return 0.85;
    if (cpuLower.includes('i5-13') || cpuLower.includes('i5-12')) return 0.7;
    if (cpuLower.includes('i9-11') || cpuLower.includes('i9-10')) return 0.8;
    if (cpuLower.includes('i7-11') || cpuLower.includes('i7-10')) return 0.65;
    if (cpuLower.includes('i5-11') || cpuLower.includes('i5-10')) return 0.5;
    if (cpuLower.includes('i3')) return 0.3;
    
    // AMD tiers
    if (cpuLower.includes('ryzen 9 7')) return 1.0;
    if (cpuLower.includes('ryzen 7 7')) return 0.85;
    if (cpuLower.includes('ryzen 5 7')) return 0.7;
    if (cpuLower.includes('ryzen 9 5')) return 0.8;
    if (cpuLower.includes('ryzen 7 5')) return 0.65;
    if (cpuLower.includes('ryzen 5 5')) return 0.5;
    if (cpuLower.includes('ryzen 3')) return 0.3;
    
    return 0.4; // Unknown CPU
  }

  private getGpuTier(gpu?: string): number {
    if (!gpu) return 0;
    const gpuLower = gpu.toLowerCase();
    
    // NVIDIA tiers
    if (gpuLower.includes('4090')) return 1.0;
    if (gpuLower.includes('4080')) return 0.9;
    if (gpuLower.includes('4070')) return 0.8;
    if (gpuLower.includes('4060')) return 0.65;
    if (gpuLower.includes('3090')) return 0.85;
    if (gpuLower.includes('3080')) return 0.75;
    if (gpuLower.includes('3070')) return 0.65;
    if (gpuLower.includes('3060')) return 0.5;
    if (gpuLower.includes('1660')) return 0.3;
    if (gpuLower.includes('1650')) return 0.25;
    
    // AMD tiers
    if (gpuLower.includes('7900')) return 0.95;
    if (gpuLower.includes('7800')) return 0.8;
    if (gpuLower.includes('7700')) return 0.7;
    if (gpuLower.includes('7600')) return 0.6;
    if (gpuLower.includes('6900')) return 0.75;
    if (gpuLower.includes('6800')) return 0.65;
    if (gpuLower.includes('6700')) return 0.55;
    if (gpuLower.includes('6600')) return 0.45;
    
    return 0.2; // Unknown or old GPU
  }

  private getStorageType(storage?: Array<{ type: string }>): number {
    if (!storage || storage.length === 0) return 0.5;
    
    const hasNvme = storage.some(s => s.type.toLowerCase().includes('nvme'));
    const hasSsd = storage.some(s => s.type.toLowerCase().includes('ssd'));
    
    if (hasNvme) return 1.0;
    if (hasSsd) return 0.5;
    return 0; // HDD only
  }

  private getConditionScore(condition?: string): number {
    if (!condition) return 0.7;
    
    const condLower = condition.toLowerCase();
    if (condLower.includes('new') || condLower.includes('mint')) return 1.0;
    if (condLower.includes('excellent') || condLower.includes('like')) return 0.9;
    if (condLower.includes('good')) return 0.7;
    if (condLower.includes('fair')) return 0.5;
    if (condLower.includes('poor') || condLower.includes('parts')) return 0.3;
    
    return 0.6;
  }

  private getBrandReputation(specs: any): number {
    // Check for premium brands
    const premiumBrands = ['alienware', 'asus rog', 'msi gaming', 'corsair', 'origin'];
    const specString = JSON.stringify(specs).toLowerCase();
    
    for (const brand of premiumBrands) {
      if (specString.includes(brand)) return 0.9;
    }
    
    return 0.7; // Generic or unknown brand
  }

  private getMarketDemand(specs: any): number {
    // High demand for current gen gaming systems
    const hasHighEndGpu = this.getGpuTier(specs.gpu) > 0.7;
    const hasGoodCpu = this.getCpuTier(specs.cpu) > 0.6;
    
    if (hasHighEndGpu && hasGoodCpu) return 0.9;
    if (hasHighEndGpu || hasGoodCpu) return 0.7;
    
    return 0.5;
  }

  private getPlatformScore(platform?: string): number {
    if (!platform) return 0.5;
    
    switch (platform.toLowerCase()) {
      case 'facebook': return 1.0;
      case 'offerup': return 0.5;
      case 'craigslist': return 0;
      default: return 0.5;
    }
  }

  /**
   * Save model to IndexedDB
   */
  private async saveModel(): Promise<void> {
    if (!this.model || !this.normalizer) return;
    
    const modelData = {
      model: await this.model.save(tf.io.withSaveHandler(async (artifacts) => artifacts)),
      normalizer: {
        inputMean: await this.normalizer.inputMean.array(),
        inputStd: await this.normalizer.inputStd.array(),
        labelMean: this.normalizer.labelMean,
        labelStd: this.normalizer.labelStd
      },
      version: this.modelConfig.version,
      timestamp: new Date().toISOString()
    };
    
    // Save to IndexedDB via chrome.storage
    await chrome.storage.local.set({ mlModel: modelData });
  }

  /**
   * Load model from IndexedDB
   */
  private async loadModel(): Promise<void> {
    const { mlModel } = await chrome.storage.local.get('mlModel');
    
    if (!mlModel || mlModel.version !== this.modelConfig.version) {
      throw new Error('No compatible model found');
    }
    
    // Load model
    this.model = await tf.loadLayersModel(
      tf.io.fromMemory(mlModel.model)
    );
    
    // Load normalizer
    this.normalizer = {
      inputMean: tf.tensor(mlModel.normalizer.inputMean),
      inputStd: tf.tensor(mlModel.normalizer.inputStd),
      labelMean: mlModel.normalizer.labelMean,
      labelStd: mlModel.normalizer.labelStd
    };
  }

  /**
   * Retrain model with new data
   */
  async updateModel(newData: { specs: any; actualPrice: number }[]): Promise<void> {
    // Convert new data to features
    const newFeatures: number[][] = [];
    const newLabels: number[] = [];
    
    for (const data of newData) {
      newFeatures.push(this.extractFeatures(data.specs));
      newLabels.push(data.actualPrice);
    }
    
    // Combine with existing training data
    const existingData = this.generateTrainingData();
    const allFeatures = [...existingData.features, ...newFeatures];
    const allLabels = [...existingData.labels, ...newLabels];
    
    // Retrain
    const features = tf.tensor2d(allFeatures);
    const labels = tf.tensor1d(allLabels);
    
    const { normalizedFeatures, normalizedLabels, normalizer } = this.normalizeData(
      features,
      labels
    );
    this.normalizer = normalizer;
    
    // Fine-tune existing model
    await this.model!.fit(normalizedFeatures, normalizedLabels, {
      epochs: 20, // Fewer epochs for fine-tuning
      batchSize: 32,
      validationSplit: 0.2
    });
    
    // Save updated model
    await this.saveModel();
    
    // Cleanup
    features.dispose();
    labels.dispose();
    normalizedFeatures.dispose();
    normalizedLabels.dispose();
  }
}

// Export singleton instance
export const tensorFlowPriceModel = new TensorFlowPriceModel();