/**
 * Anomaly Detector
 * Detects unusual patterns in listings
 */

export interface Anomaly {
  type: 'price' | 'specs' | 'description';
  severity: 'low' | 'medium' | 'high';
  message: string;
  confidence: number;
}

export class AnomalyDetector {
  detect(listing: {
    price: number;
    title: string;
    description: string;
    components?: any;
  }): Anomaly[] {
    const anomalies: Anomaly[] = [];
    
    // Check for suspiciously low prices
    if (listing.components?.gpu && listing.price < 200) {
      anomalies.push({
        type: 'price',
        severity: 'high',
        message: 'Price unusually low for a system with dedicated GPU',
        confidence: 0.9
      });
    }
    
    // Check for mismatched title/description
    const titleLower = listing.title.toLowerCase();
    const descLower = listing.description.toLowerCase();
    
    if (titleLower.includes('rtx') && !descLower.includes('rtx') && !descLower.includes('nvidia')) {
      anomalies.push({
        type: 'specs',
        severity: 'medium',
        message: 'GPU mentioned in title but not in description',
        confidence: 0.7
      });
    }
    
    // Check for scam keywords
    const scamKeywords = ['wire transfer', 'western union', 'gift card', 'zelle only'];
    for (const keyword of scamKeywords) {
      if (descLower.includes(keyword)) {
        anomalies.push({
          type: 'description',
          severity: 'high',
          message: `Suspicious payment method mentioned: ${keyword}`,
          confidence: 0.95
        });
      }
    }
    
    return anomalies;
  }
}