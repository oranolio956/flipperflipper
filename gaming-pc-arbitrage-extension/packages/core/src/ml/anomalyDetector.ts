/**
 * Anomaly Detection Module
 * Facade for the statistical anomaly detection system
 */

import { statisticalAnomalyDetector, type AnomalyResult } from './statisticalAnomalyDetector';
import { Listing } from '../types';

export interface Anomaly {
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  description: string;
  evidence?: string[];
  recommendation?: string;
}

export class AnomalyDetector {
  private initialized = false;

  /**
   * Initialize the detector
   */
  private async ensureInitialized(): Promise<void> {
    if (!this.initialized) {
      await statisticalAnomalyDetector.initialize();
      this.initialized = true;
    }
  }

  /**
   * Detect anomalies in a listing
   * @param listing - The listing to analyze
   * @returns Array of detected anomalies
   */
  async detect(listing: {
    price: number;
    title: string;
    description: string;
    components?: any;
    platform?: string;
    images?: string[];
  }): Promise<Anomaly[]> {
    await this.ensureInitialized();

    // Convert to full Listing object
    const fullListing: Listing = {
      id: `temp-${Date.now()}`,
      externalId: '',
      url: '',
      platform: listing.platform || 'unknown',
      title: listing.title,
      description: listing.description,
      price: listing.price,
      location: { city: '', state: '', zipCode: '' },
      seller: { id: '', name: 'Unknown', responseRate: 0, memberSince: new Date() },
      images: listing.images || [],
      condition: 'unknown',
      category: 'gaming-pc',
      subcategory: 'desktop',
      attributes: {},
      postedAt: new Date(),
      lastUpdated: new Date(),
      status: 'active',
      viewCount: 0,
      savedCount: 0,
      components: listing.components
    };

    // Get detailed analysis
    const result: AnomalyResult = await statisticalAnomalyDetector.detect(fullListing);

    // Convert to simplified format for backward compatibility
    return result.anomalies.map(anomaly => ({
      type: anomaly.type,
      severity: anomaly.severity,
      confidence: anomaly.confidence,
      description: anomaly.description,
      evidence: anomaly.evidence,
      recommendation: anomaly.recommendation
    }));
  }

  /**
   * Get anomaly analysis with full details
   */
  async analyze(listing: Listing): Promise<AnomalyResult> {
    await this.ensureInitialized();
    return statisticalAnomalyDetector.detect(listing);
  }
}

// Export types
export type { AnomalyResult, DetailedAnomaly } from './statisticalAnomalyDetector';