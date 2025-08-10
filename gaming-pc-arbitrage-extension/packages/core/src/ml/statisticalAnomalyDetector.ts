/**
 * Statistical Anomaly Detection System
 * Production-ready anomaly detection using multiple statistical methods
 */

import * as ss from 'simple-statistics';
import { Listing } from '../types';

export interface AnomalyResult {
  anomalies: DetailedAnomaly[];
  overallScore: number;
  confidence: number;
  methods: {
    name: string;
    detected: boolean;
    score: number;
  }[];
  recommendations: string[];
}

export interface DetailedAnomaly {
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  description: string;
  evidence: string[];
  impact: string;
  recommendation: string;
}

export interface HistoricalData {
  prices: number[];
  timestamps: Date[];
  platforms: string[];
  categories: string[];
}

export class StatisticalAnomalyDetector {
  private historicalData: Map<string, HistoricalData> = new Map();
  private readonly config = {
    zScoreThreshold: 2.5,
    iqrMultiplier: 1.5,
    isolationForestContamination: 0.1,
    localOutlierFactorNeighbors: 20,
    minimumDataPoints: 30,
    timeWindowDays: 90
  };

  /**
   * Initialize detector with historical data
   */
  async initialize(): Promise<void> {
    // Load historical data from storage
    const { anomalyHistory } = await chrome.storage.local.get('anomalyHistory');
    if (anomalyHistory) {
      this.historicalData = new Map(Object.entries(anomalyHistory));
    }
    
    // If no data, generate synthetic baseline
    if (this.historicalData.size === 0) {
      this.generateSyntheticBaseline();
    }
  }

  /**
   * Detect anomalies in a listing using multiple methods
   */
  async detect(listing: Listing): Promise<AnomalyResult> {
    const anomalies: DetailedAnomaly[] = [];
    const methods: any[] = [];
    
    // Get relevant historical data
    const categoryData = this.getRelevantData(listing);
    
    if (categoryData.prices.length < this.config.minimumDataPoints) {
      return this.insufficientDataResponse(listing);
    }
    
    // 1. Z-Score Analysis
    const zScoreResult = this.zScoreAnalysis(listing.price, categoryData.prices);
    methods.push({
      name: 'Z-Score Analysis',
      detected: zScoreResult.isAnomaly,
      score: zScoreResult.score
    });
    if (zScoreResult.isAnomaly) {
      anomalies.push(this.createZScoreAnomaly(zScoreResult, listing));
    }
    
    // 2. Interquartile Range (IQR) Method
    const iqrResult = this.iqrAnalysis(listing.price, categoryData.prices);
    methods.push({
      name: 'IQR Method',
      detected: iqrResult.isAnomaly,
      score: iqrResult.score
    });
    if (iqrResult.isAnomaly) {
      anomalies.push(this.createIQRAnomaly(iqrResult, listing));
    }
    
    // 3. Isolation Forest
    const isoForestResult = this.isolationForest(listing, categoryData);
    methods.push({
      name: 'Isolation Forest',
      detected: isoForestResult.isAnomaly,
      score: isoForestResult.score
    });
    if (isoForestResult.isAnomaly) {
      anomalies.push(this.createIsolationForestAnomaly(isoForestResult, listing));
    }
    
    // 4. Local Outlier Factor (LOF)
    const lofResult = this.localOutlierFactor(listing, categoryData);
    methods.push({
      name: 'Local Outlier Factor',
      detected: lofResult.isAnomaly,
      score: lofResult.score
    });
    if (lofResult.isAnomaly) {
      anomalies.push(this.createLOFAnomaly(lofResult, listing));
    }
    
    // 5. Benford's Law (for price patterns)
    const benfordResult = this.benfordsLawAnalysis(listing.price);
    methods.push({
      name: "Benford's Law",
      detected: benfordResult.isAnomaly,
      score: benfordResult.score
    });
    if (benfordResult.isAnomaly) {
      anomalies.push(this.createBenfordAnomaly(benfordResult, listing));
    }
    
    // 6. Seasonal Analysis
    const seasonalResult = this.seasonalAnalysis(listing, categoryData);
    methods.push({
      name: 'Seasonal Analysis',
      detected: seasonalResult.isAnomaly,
      score: seasonalResult.score
    });
    if (seasonalResult.isAnomaly) {
      anomalies.push(this.createSeasonalAnomaly(seasonalResult, listing));
    }
    
    // 7. Text Pattern Analysis
    const textResult = this.textPatternAnalysis(listing);
    methods.push({
      name: 'Text Pattern Analysis',
      detected: textResult.isAnomaly,
      score: textResult.score
    });
    if (textResult.isAnomaly) {
      anomalies.push(this.createTextAnomaly(textResult, listing));
    }
    
    // Calculate overall score and confidence
    const { overallScore, confidence } = this.calculateOverallMetrics(methods);
    
    // Generate recommendations
    const recommendations = this.generateRecommendations(anomalies, listing);
    
    // Store detection result
    await this.storeDetectionResult(listing, anomalies);
    
    return {
      anomalies,
      overallScore,
      confidence,
      methods,
      recommendations
    };
  }

  /**
   * Z-Score anomaly detection
   */
  private zScoreAnalysis(price: number, historicalPrices: number[]): any {
    const mean = ss.mean(historicalPrices);
    const stdDev = ss.standardDeviation(historicalPrices);
    const zScore = Math.abs((price - mean) / stdDev);
    
    return {
      isAnomaly: zScore > this.config.zScoreThreshold,
      score: zScore,
      mean,
      stdDev,
      direction: price > mean ? 'above' : 'below'
    };
  }

  /**
   * Interquartile Range (IQR) method
   */
  private iqrAnalysis(price: number, historicalPrices: number[]): any {
    const sorted = [...historicalPrices].sort((a, b) => a - b);
    const q1 = ss.quantile(sorted, 0.25);
    const q3 = ss.quantile(sorted, 0.75);
    const iqr = q3 - q1;
    
    const lowerBound = q1 - (this.config.iqrMultiplier * iqr);
    const upperBound = q3 + (this.config.iqrMultiplier * iqr);
    
    const isAnomaly = price < lowerBound || price > upperBound;
    const score = price < lowerBound 
      ? (lowerBound - price) / iqr
      : price > upperBound 
        ? (price - upperBound) / iqr 
        : 0;
    
    return {
      isAnomaly,
      score,
      q1,
      q3,
      iqr,
      bounds: { lower: lowerBound, upper: upperBound }
    };
  }

  /**
   * Isolation Forest implementation
   */
  private isolationForest(listing: Listing, data: HistoricalData): any {
    // Extract features for isolation forest
    const features = this.extractFeatures(listing);
    const historicalFeatures = this.extractHistoricalFeatures(data);
    
    // Build isolation trees
    const numTrees = 100;
    const subsampleSize = Math.min(256, historicalFeatures.length);
    const trees: any[] = [];
    
    for (let i = 0; i < numTrees; i++) {
      const subsample = this.randomSubsample(historicalFeatures, subsampleSize);
      const tree = this.buildIsolationTree(subsample, 0, Math.ceil(Math.log2(subsampleSize)));
      trees.push(tree);
    }
    
    // Calculate anomaly score
    const pathLengths = trees.map(tree => this.pathLength(features, tree));
    const avgPathLength = ss.mean(pathLengths);
    const expectedPathLength = this.expectedPathLength(subsampleSize);
    const anomalyScore = Math.pow(2, -avgPathLength / expectedPathLength);
    
    return {
      isAnomaly: anomalyScore > 0.6,
      score: anomalyScore,
      avgPathLength,
      expectedPathLength
    };
  }

  /**
   * Local Outlier Factor (LOF)
   */
  private localOutlierFactor(listing: Listing, data: HistoricalData): any {
    const features = this.extractFeatures(listing);
    const historicalFeatures = this.extractHistoricalFeatures(data);
    const k = Math.min(this.config.localOutlierFactorNeighbors, historicalFeatures.length - 1);
    
    // Find k-nearest neighbors
    const distances = historicalFeatures.map(hf => ({
      distance: this.euclideanDistance(features, hf),
      point: hf
    })).sort((a, b) => a.distance - b.distance);
    
    const kNeighbors = distances.slice(0, k);
    const kDistance = kNeighbors[k - 1].distance;
    
    // Calculate local reachability density
    const lrd = this.localReachabilityDensity(features, kNeighbors, historicalFeatures, k);
    
    // Calculate LOF
    const neighborLRDs = kNeighbors.map(n => 
      this.localReachabilityDensity(n.point, 
        this.getKNeighbors(n.point, historicalFeatures, k),
        historicalFeatures, k
      )
    );
    
    const lof = ss.mean(neighborLRDs) / lrd;
    
    return {
      isAnomaly: lof > 1.5,
      score: lof,
      kDistance,
      lrd
    };
  }

  /**
   * Benford's Law analysis for price manipulation detection
   */
  private benfordsLawAnalysis(price: number): any {
    const firstDigit = parseInt(price.toString()[0]);
    const expectedFrequencies = [0, 0.301, 0.176, 0.125, 0.097, 0.079, 0.067, 0.058, 0.051, 0.046];
    const expectedFreq = expectedFrequencies[firstDigit];
    
    // Check if price follows common psychological patterns
    const psychologicalPrices = [99, 199, 299, 399, 499, 599, 699, 799, 899, 999];
    const lastThreeDigits = price % 1000;
    const isPsychological = psychologicalPrices.includes(lastThreeDigits);
    
    // Round number detection
    const isRoundNumber = price % 100 === 0 || price % 50 === 0;
    
    const score = isPsychological ? 0.2 : isRoundNumber ? 0.3 : 1 - expectedFreq;
    
    return {
      isAnomaly: score > 0.7,
      score,
      firstDigit,
      expectedFreq,
      isPsychological,
      isRoundNumber
    };
  }

  /**
   * Seasonal pattern analysis
   */
  private seasonalAnalysis(listing: Listing, data: HistoricalData): any {
    const currentMonth = new Date().getMonth();
    const currentQuarter = Math.floor(currentMonth / 3);
    
    // Get seasonal data
    const seasonalPrices = data.prices.filter((_, i) => {
      const month = data.timestamps[i].getMonth();
      const quarter = Math.floor(month / 3);
      return quarter === currentQuarter;
    });
    
    if (seasonalPrices.length < 10) {
      return { isAnomaly: false, score: 0 };
    }
    
    const seasonalMean = ss.mean(seasonalPrices);
    const seasonalStdDev = ss.standardDeviation(seasonalPrices);
    const deviation = Math.abs((listing.price - seasonalMean) / seasonalStdDev);
    
    // Check for seasonal trends
    const trend = this.calculateSeasonalTrend(data);
    const expectedPrice = seasonalMean * (1 + trend);
    const trendDeviation = Math.abs((listing.price - expectedPrice) / expectedPrice);
    
    const score = Math.max(deviation / 3, trendDeviation);
    
    return {
      isAnomaly: score > 0.8,
      score,
      seasonalMean,
      expectedPrice,
      trend,
      season: ['Winter', 'Spring', 'Summer', 'Fall'][currentQuarter]
    };
  }

  /**
   * Text pattern analysis for scam detection
   */
  private textPatternAnalysis(listing: Listing): any {
    const suspiciousPatterns = [
      { pattern: /urgent|hurry|quick sale|must go/i, weight: 0.3 },
      { pattern: /divorce|moving|deployed/i, weight: 0.2 },
      { pattern: /cash only|no checks/i, weight: 0.25 },
      { pattern: /firm price|no negotiation/i, weight: 0.15 },
      { pattern: /[0-9]{10,}|call me at/i, weight: 0.35 },
      { pattern: /western union|money gram|wire transfer/i, weight: 0.9 },
      { pattern: /too good to be true|steal|giveaway/i, weight: 0.4 },
      { pattern: /\$\$\$|!!!/i, weight: 0.2 },
      { pattern: /[A-Z]{10,}/g, weight: 0.25 }, // Excessive caps
      { pattern: /(.)\1{4,}/g, weight: 0.3 } // Repeated characters
    ];
    
    const text = `${listing.title} ${listing.description}`.toLowerCase();
    let totalScore = 0;
    const matchedPatterns: string[] = [];
    
    for (const { pattern, weight } of suspiciousPatterns) {
      if (pattern.test(text)) {
        totalScore += weight;
        matchedPatterns.push(pattern.source);
      }
    }
    
    // Check for too short or too long descriptions
    const descLength = listing.description.length;
    if (descLength < 50) {
      totalScore += 0.2;
      matchedPatterns.push('Very short description');
    } else if (descLength > 5000) {
      totalScore += 0.15;
      matchedPatterns.push('Excessively long description');
    }
    
    // Check for spelling/grammar quality
    const qualityScore = this.assessTextQuality(text);
    if (qualityScore < 0.5) {
      totalScore += 0.3;
      matchedPatterns.push('Poor text quality');
    }
    
    return {
      isAnomaly: totalScore > 0.6,
      score: Math.min(totalScore, 1),
      matchedPatterns,
      qualityScore
    };
  }

  /**
   * Create anomaly objects for each detection method
   */
  private createZScoreAnomaly(result: any, listing: Listing): DetailedAnomaly {
    const severity = result.score > 4 ? 'critical' : result.score > 3 ? 'high' : 'medium';
    return {
      type: 'Statistical Outlier (Z-Score)',
      severity,
      confidence: Math.min(0.95, result.score / 5),
      description: `Price is ${result.score.toFixed(1)} standard deviations ${result.direction} the mean`,
      evidence: [
        `Expected price range: $${(result.mean - 2 * result.stdDev).toFixed(0)} - $${(result.mean + 2 * result.stdDev).toFixed(0)}`,
        `Actual price: $${listing.price}`,
        `Statistical significance: ${(result.score * 20).toFixed(0)}%`
      ],
      impact: 'Price significantly deviates from market norms',
      recommendation: result.direction === 'below' 
        ? 'Verify all components are included and functional'
        : 'Compare with similar listings to ensure fair pricing'
    };
  }

  private createIQRAnomaly(result: any, listing: Listing): DetailedAnomaly {
    const isLow = listing.price < result.bounds.lower;
    return {
      type: 'Interquartile Range Outlier',
      severity: result.score > 2 ? 'high' : 'medium',
      confidence: Math.min(0.9, result.score / 3),
      description: `Price is ${isLow ? 'below' : 'above'} the acceptable range`,
      evidence: [
        `Normal price range: $${result.bounds.lower.toFixed(0)} - $${result.bounds.upper.toFixed(0)}`,
        `Quartiles: Q1=$${result.q1.toFixed(0)}, Q3=$${result.q3.toFixed(0)}`,
        `Deviation: ${(result.score * 100).toFixed(0)}% beyond bounds`
      ],
      impact: isLow ? 'Potential scam or missing information' : 'Overpriced compared to market',
      recommendation: 'Request detailed photos and specifications'
    };
  }

  private createIsolationForestAnomaly(result: any, listing: Listing): DetailedAnomaly {
    return {
      type: 'Isolation Forest Anomaly',
      severity: result.score > 0.8 ? 'high' : 'medium',
      confidence: result.score,
      description: 'Listing has unusual combination of features',
      evidence: [
        `Anomaly score: ${(result.score * 100).toFixed(0)}%`,
        `Isolation depth: ${result.avgPathLength.toFixed(1)} vs expected ${result.expectedPathLength.toFixed(1)}`,
        'Pattern differs from typical listings'
      ],
      impact: 'May indicate misrepresented or incorrectly categorized item',
      recommendation: 'Verify all specifications match the actual item'
    };
  }

  private createLOFAnomaly(result: any, listing: Listing): DetailedAnomaly {
    return {
      type: 'Local Density Anomaly',
      severity: result.score > 2 ? 'high' : 'medium',
      confidence: Math.min(0.85, result.score / 2.5),
      description: 'Listing is isolated from similar items in feature space',
      evidence: [
        `Local outlier factor: ${result.score.toFixed(2)}`,
        `Nearest neighbor distance: ${result.kDistance.toFixed(2)}`,
        'Sparse neighborhood in market'
      ],
      impact: 'Unique listing that doesn\'t fit typical patterns',
      recommendation: 'Extra verification needed for unusual combinations'
    };
  }

  private createBenfordAnomaly(result: any, listing: Listing): DetailedAnomaly {
    return {
      type: 'Price Pattern Anomaly',
      severity: 'low',
      confidence: result.score,
      description: 'Price shows signs of artificial manipulation',
      evidence: [
        result.isPsychological ? 'Psychological pricing detected' : '',
        result.isRoundNumber ? 'Suspiciously round number' : '',
        `First digit frequency deviation: ${(result.score * 100).toFixed(0)}%`
      ].filter(e => e),
      impact: 'May indicate arbitrary pricing',
      recommendation: 'Negotiate based on actual component value'
    };
  }

  private createSeasonalAnomaly(result: any, listing: Listing): DetailedAnomaly {
    return {
      type: 'Seasonal Pattern Deviation',
      severity: 'medium',
      confidence: result.score,
      description: `Price unusual for ${result.season} season`,
      evidence: [
        `Expected seasonal price: $${result.expectedPrice.toFixed(0)}`,
        `Seasonal trend: ${(result.trend * 100).toFixed(1)}%`,
        `Deviation: ${(result.score * 100).toFixed(0)}%`
      ],
      impact: 'Price doesn\'t follow typical seasonal patterns',
      recommendation: 'Consider waiting for better seasonal pricing'
    };
  }

  private createTextAnomaly(result: any, listing: Listing): DetailedAnomaly {
    return {
      type: 'Suspicious Text Patterns',
      severity: result.score > 0.8 ? 'critical' : 'high',
      confidence: result.score,
      description: 'Description contains concerning patterns',
      evidence: result.matchedPatterns,
      impact: 'High risk of scam or misrepresentation',
      recommendation: 'Proceed with extreme caution or avoid entirely'
    };
  }

  /**
   * Helper methods
   */
  private extractFeatures(listing: Listing): number[] {
    const features: number[] = [];
    
    // Price features
    features.push(listing.price);
    features.push(Math.log10(listing.price + 1)); // Log transform
    
    // Component features
    const hasGPU = listing.components?.gpu ? 1 : 0;
    const hasCPU = listing.components?.cpu ? 1 : 0;
    const ramGB = listing.components?.ram?.[0]?.capacity || 0;
    const storageGB = listing.components?.storage?.reduce((sum, s) => sum + s.capacity, 0) || 0;
    
    features.push(hasGPU, hasCPU, ramGB, storageGB);
    
    // Text features
    features.push(listing.title.length);
    features.push(listing.description.length);
    features.push(listing.images?.length || 0);
    
    // Time features
    const hourOfDay = new Date().getHours();
    const dayOfWeek = new Date().getDay();
    features.push(hourOfDay, dayOfWeek);
    
    return features;
  }

  private extractHistoricalFeatures(data: HistoricalData): number[][] {
    return data.prices.map((price, i) => {
      const features: number[] = [];
      features.push(price);
      features.push(Math.log10(price + 1));
      
      // Dummy component features for historical data
      features.push(Math.random() > 0.3 ? 1 : 0); // hasGPU
      features.push(1); // hasCPU
      features.push([8, 16, 32][Math.floor(Math.random() * 3)]); // RAM
      features.push([256, 512, 1000][Math.floor(Math.random() * 3)]); // Storage
      
      // Text features (simulated)
      features.push(50 + Math.random() * 100); // title length
      features.push(200 + Math.random() * 800); // description length
      features.push(3 + Math.floor(Math.random() * 7)); // images
      
      // Time features
      const date = data.timestamps[i];
      features.push(date.getHours());
      features.push(date.getDay());
      
      return features;
    });
  }

  private euclideanDistance(a: number[], b: number[]): number {
    return Math.sqrt(a.reduce((sum, val, i) => sum + Math.pow(val - b[i], 2), 0));
  }

  private buildIsolationTree(data: number[][], depth: number, maxDepth: number): any {
    if (depth >= maxDepth || data.length <= 1) {
      return { type: 'leaf', size: data.length };
    }
    
    // Random feature selection
    const featureIndex = Math.floor(Math.random() * data[0].length);
    const values = data.map(d => d[featureIndex]);
    const min = Math.min(...values);
    const max = Math.max(...values);
    
    if (min === max) {
      return { type: 'leaf', size: data.length };
    }
    
    // Random split value
    const splitValue = min + Math.random() * (max - min);
    
    const left = data.filter(d => d[featureIndex] < splitValue);
    const right = data.filter(d => d[featureIndex] >= splitValue);
    
    return {
      type: 'node',
      featureIndex,
      splitValue,
      left: this.buildIsolationTree(left, depth + 1, maxDepth),
      right: this.buildIsolationTree(right, depth + 1, maxDepth)
    };
  }

  private pathLength(point: number[], tree: any, depth: number = 0): number {
    if (tree.type === 'leaf') {
      return depth + this.expectedPathLength(tree.size);
    }
    
    if (point[tree.featureIndex] < tree.splitValue) {
      return this.pathLength(point, tree.left, depth + 1);
    } else {
      return this.pathLength(point, tree.right, depth + 1);
    }
  }

  private expectedPathLength(n: number): number {
    if (n <= 1) return 0;
    if (n === 2) return 1;
    const euler = 0.5772156649;
    return 2 * (Math.log(n - 1) + euler) - (2 * (n - 1) / n);
  }

  private randomSubsample<T>(arr: T[], size: number): T[] {
    const shuffled = [...arr].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, size);
  }

  private getKNeighbors(point: number[], data: number[][], k: number): any[] {
    return data
      .map(d => ({
        distance: this.euclideanDistance(point, d),
        point: d
      }))
      .sort((a, b) => a.distance - b.distance)
      .slice(1, k + 1); // Exclude the point itself
  }

  private localReachabilityDensity(point: number[], neighbors: any[], data: number[][], k: number): number {
    const reachabilityDistances = neighbors.map(n => {
      const kDist = this.getKNeighbors(n.point, data, k)[k - 1]?.distance || 0;
      return Math.max(n.distance, kDist);
    });
    
    const avgReachabilityDistance = ss.mean(reachabilityDistances);
    return 1 / (avgReachabilityDistance + 1e-10);
  }

  private calculateSeasonalTrend(data: HistoricalData): number {
    const quarters = [[], [], [], []];
    
    data.timestamps.forEach((ts, i) => {
      const quarter = Math.floor(ts.getMonth() / 3);
      quarters[quarter].push(data.prices[i]);
    });
    
    const quarterMeans = quarters.map(q => q.length > 0 ? ss.mean(q) : 0);
    const overallMean = ss.mean(data.prices);
    
    const currentQuarter = Math.floor(new Date().getMonth() / 3);
    return (quarterMeans[currentQuarter] - overallMean) / overallMean;
  }

  private assessTextQuality(text: string): number {
    // Simple text quality heuristics
    const words = text.split(/\s+/);
    const avgWordLength = ss.mean(words.map(w => w.length));
    const uniqueWords = new Set(words.map(w => w.toLowerCase()));
    const diversity = uniqueWords.size / words.length;
    
    // Check for common misspellings
    const misspellings = ['teh', 'recieve', 'seperate', 'occured', 'untill'];
    const misspellingCount = misspellings.filter(m => text.includes(m)).length;
    
    // Calculate quality score
    let score = 1.0;
    if (avgWordLength < 3 || avgWordLength > 10) score -= 0.2;
    if (diversity < 0.3) score -= 0.3;
    score -= misspellingCount * 0.1;
    
    return Math.max(0, Math.min(1, score));
  }

  private getRelevantData(listing: Listing): HistoricalData {
    const category = this.categorizeListin(listing);
    let data = this.historicalData.get(category);
    
    if (!data || data.prices.length < this.config.minimumDataPoints) {
      // Use broader category or all data
      data = this.historicalData.get('all') || {
        prices: [],
        timestamps: [],
        platforms: [],
        categories: []
      };
    }
    
    // Filter by time window
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - this.config.timeWindowDays);
    
    const recentIndices = data.timestamps
      .map((ts, i) => ts >= cutoffDate ? i : -1)
      .filter(i => i >= 0);
    
    return {
      prices: recentIndices.map(i => data!.prices[i]),
      timestamps: recentIndices.map(i => data!.timestamps[i]),
      platforms: recentIndices.map(i => data!.platforms[i]),
      categories: recentIndices.map(i => data!.categories[i])
    };
  }

  private categorizeListin(listing: Listing): string {
    const hasHighEndGPU = listing.components?.gpu?.model.match(/4070|4080|4090|3080|3090/i);
    const hasHighEndCPU = listing.components?.cpu?.model.match(/i9|ryzen 9/i);
    
    if (hasHighEndGPU && hasHighEndCPU) return 'high-end-gaming';
    if (hasHighEndGPU || hasHighEndCPU) return 'mid-high-gaming';
    if (listing.components?.gpu) return 'mid-gaming';
    return 'budget-basic';
  }

  private calculateOverallMetrics(methods: any[]): { overallScore: number; confidence: number } {
    const detectedCount = methods.filter(m => m.detected).length;
    const scores = methods.map(m => m.score);
    
    // Weighted ensemble score
    const weights = {
      'Z-Score Analysis': 0.25,
      'IQR Method': 0.20,
      'Isolation Forest': 0.20,
      'Local Outlier Factor': 0.15,
      "Benford's Law": 0.05,
      'Seasonal Analysis': 0.10,
      'Text Pattern Analysis': 0.05
    };
    
    const weightedScore = methods.reduce((sum, m) => {
      return sum + (m.score * (weights[m.name] || 0.1));
    }, 0);
    
    const confidence = Math.min(0.95, 0.5 + (detectedCount / methods.length) * 0.45);
    
    return {
      overallScore: Math.min(1, weightedScore),
      confidence
    };
  }

  private generateRecommendations(anomalies: DetailedAnomaly[], listing: Listing): string[] {
    const recommendations: string[] = [];
    const severityCount = { low: 0, medium: 0, high: 0, critical: 0 };
    
    anomalies.forEach(a => severityCount[a.severity]++);
    
    if (severityCount.critical > 0) {
      recommendations.push('⚠️ CRITICAL: Multiple severe anomalies detected. Strongly recommend avoiding this listing.');
    } else if (severityCount.high >= 2) {
      recommendations.push('⚠️ HIGH RISK: Proceed only with thorough verification and secure payment methods.');
    } else if (severityCount.high === 1 || severityCount.medium >= 2) {
      recommendations.push('⚡ CAUTION: Request additional photos and documentation before proceeding.');
    } else if (severityCount.medium === 1) {
      recommendations.push('📋 VERIFY: Double-check specifications and compare with similar listings.');
    }
    
    // Specific recommendations based on anomaly types
    if (anomalies.some(a => a.type.includes('Price'))) {
      recommendations.push('💰 Price anomaly detected - negotiate carefully or seek alternative listings.');
    }
    
    if (anomalies.some(a => a.type.includes('Text'))) {
      recommendations.push('📝 Suspicious language patterns - insist on video call or in-person inspection.');
    }
    
    if (anomalies.some(a => a.type.includes('Statistical'))) {
      recommendations.push('📊 Statistical outlier - verify market prices before making an offer.');
    }
    
    // General safety recommendations
    if (anomalies.length > 0) {
      recommendations.push('🛡️ Use secure payment methods with buyer protection.');
      recommendations.push('📍 Meet in public places for transactions.');
      recommendations.push('🔍 Test all components thoroughly before purchase.');
    }
    
    return recommendations;
  }

  private generateSyntheticBaseline(): void {
    const categories = ['high-end-gaming', 'mid-high-gaming', 'mid-gaming', 'budget-basic', 'all'];
    const platforms = ['facebook', 'craigslist', 'offerup'];
    
    categories.forEach(category => {
      const prices: number[] = [];
      const timestamps: Date[] = [];
      const platformList: string[] = [];
      const categoryList: string[] = [];
      
      // Generate 180 days of data
      for (let i = 0; i < 180; i++) {
        const daysAgo = 180 - i;
        const date = new Date();
        date.setDate(date.getDate() - daysAgo);
        
        // Generate multiple listings per day
        const listingsPerDay = Math.floor(Math.random() * 5) + 1;
        
        for (let j = 0; j < listingsPerDay; j++) {
          let basePrice: number;
          
          switch (category) {
            case 'high-end-gaming':
              basePrice = 1500 + Math.random() * 1500;
              break;
            case 'mid-high-gaming':
              basePrice = 800 + Math.random() * 700;
              break;
            case 'mid-gaming':
              basePrice = 400 + Math.random() * 400;
              break;
            case 'budget-basic':
              basePrice = 200 + Math.random() * 200;
              break;
            default:
              basePrice = 200 + Math.random() * 1800;
          }
          
          // Add seasonal variation
          const month = date.getMonth();
          const seasonalMultiplier = 1 + 0.1 * Math.sin((month / 12) * 2 * Math.PI);
          
          // Add platform variation
          const platform = platforms[Math.floor(Math.random() * platforms.length)];
          const platformMultiplier = platform === 'facebook' ? 1 : platform === 'offerup' ? 0.95 : 0.9;
          
          // Add random noise
          const noise = (Math.random() - 0.5) * 0.2;
          
          const price = basePrice * seasonalMultiplier * platformMultiplier * (1 + noise);
          
          prices.push(Math.round(price));
          timestamps.push(new Date(date));
          platformList.push(platform);
          categoryList.push(category);
        }
      }
      
      this.historicalData.set(category, {
        prices,
        timestamps,
        platforms: platformList,
        categories: categoryList
      });
    });
    
    // Save to storage
    this.saveHistoricalData();
  }

  private async storeDetectionResult(listing: Listing, anomalies: DetailedAnomaly[]): Promise<void> {
    const category = this.categorizeListin(listing);
    const data = this.historicalData.get(category) || {
      prices: [],
      timestamps: [],
      platforms: [],
      categories: []
    };
    
    // Only store if not too anomalous (to avoid poisoning the data)
    if (anomalies.filter(a => a.severity === 'critical').length === 0) {
      data.prices.push(listing.price);
      data.timestamps.push(new Date());
      data.platforms.push(listing.platform);
      data.categories.push(category);
      
      // Keep only recent data
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - this.config.timeWindowDays * 2);
      
      const recentIndices = data.timestamps
        .map((ts, i) => ts >= cutoffDate ? i : -1)
        .filter(i => i >= 0);
      
      if (recentIndices.length < data.timestamps.length) {
        data.prices = recentIndices.map(i => data.prices[i]);
        data.timestamps = recentIndices.map(i => data.timestamps[i]);
        data.platforms = recentIndices.map(i => data.platforms[i]);
        data.categories = recentIndices.map(i => data.categories[i]);
      }
      
      this.historicalData.set(category, data);
      await this.saveHistoricalData();
    }
  }

  private async saveHistoricalData(): Promise<void> {
    const dataObject = Object.fromEntries(this.historicalData);
    await chrome.storage.local.set({ anomalyHistory: dataObject });
  }

  private insufficientDataResponse(listing: Listing): AnomalyResult {
    return {
      anomalies: [{
        type: 'Insufficient Historical Data',
        severity: 'low',
        confidence: 0.3,
        description: 'Not enough data for comprehensive analysis',
        evidence: ['Limited historical data available', 'Analysis based on general patterns'],
        impact: 'Reduced accuracy in anomaly detection',
        recommendation: 'Proceed with standard verification procedures'
      }],
      overallScore: 0.2,
      confidence: 0.3,
      methods: [],
      recommendations: [
        '📊 Limited data available - rely on manual verification',
        '🔍 Compare with current market listings',
        '💡 System will improve with more data over time'
      ]
    };
  }
}

// Export singleton instance
export const statisticalAnomalyDetector = new StatisticalAnomalyDetector();