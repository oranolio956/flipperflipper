/**
 * Scam Pattern Matcher
 * Detect likely scams with explainable ruleset
 */

import type { Listing } from '../types';
import type { CompStats } from '../comps';

export interface ScamSignal {
  scoreDelta: number; // Positive = more likely scam
  reason: string;
  level: 'low' | 'medium' | 'high';
  mitigation?: string;
}

export interface ScamRiskResult {
  score: number; // 0-100, higher = more likely scam
  reasons: ScamSignal[];
  recommendation: 'safe' | 'caution' | 'avoid';
}

/**
 * Check if price is suspiciously low
 */
function checkPriceAnomaly(
  listing: Listing,
  comps: CompStats | null
): ScamSignal | null {
  if (!comps || comps.n < 3) return null;
  
  const price = listing.price.amount;
  const percentBelow = (comps.p25 - price) / comps.p25;
  
  if (percentBelow > 0.5) {
    return {
      scoreDelta: 40,
      reason: `Price 50%+ below market (${Math.round(percentBelow * 100)}% below)`,
      level: 'high',
      mitigation: 'Request detailed photos and proof of ownership',
    };
  } else if (percentBelow > 0.3) {
    return {
      scoreDelta: 20,
      reason: `Price 30%+ below market`,
      level: 'medium',
      mitigation: 'Verify seller history and ask questions',
    };
  }
  
  return null;
}

/**
 * Check for stock photo usage
 */
function checkStockPhotos(listing: Listing): ScamSignal | null {
  // Simple heuristics - in production would use reverse image search
  const hasWatermark = listing.images?.some(img => 
    img.url.includes('watermark') || img.url.includes('stock')
  );
  
  const tooFewPhotos = (listing.images?.length || 0) < 3;
  const noBootScreen = !listing.description?.toLowerCase().includes('boot') &&
                      !listing.description?.toLowerCase().includes('bios');
  
  if (hasWatermark) {
    return {
      scoreDelta: 30,
      reason: 'Stock photos detected',
      level: 'high',
      mitigation: 'Request current photos with timestamp',
    };
  }
  
  if (tooFewPhotos && noBootScreen) {
    return {
      scoreDelta: 15,
      reason: 'Too few photos, no boot screen',
      level: 'medium',
      mitigation: 'Ask for photos showing PC running',
    };
  }
  
  return null;
}

/**
 * Check shipping-only red flag
 */
function checkShippingOnly(listing: Listing): ScamSignal | null {
  const desc = listing.description?.toLowerCase() || '';
  const title = listing.title.toLowerCase();
  const combined = `${title} ${desc}`;
  
  const shippingOnly = combined.includes('shipping only') || 
                      combined.includes('will not meet') ||
                      combined.includes('no local pickup');
  
  if (shippingOnly) {
    return {
      scoreDelta: 25,
      reason: 'Shipping only (no local inspection)',
      level: 'medium',
      mitigation: 'Strongly prefer local deals for high-value items',
    };
  }
  
  return null;
}

/**
 * Check for urgent payment requests
 */
function checkUrgentPayment(listing: Listing): ScamSignal | null {
  const text = `${listing.title} ${listing.description || ''}`.toLowerCase();
  
  const urgentTerms = ['wire', 'western union', 'moneygram', 'zelle only', 
                      'cashapp only', 'crypto only', 'urgent sale', 'must go today'];
  
  const hasUrgent = urgentTerms.some(term => text.includes(term));
  
  if (hasUrgent) {
    return {
      scoreDelta: 35,
      reason: 'Urgent payment / wire transfer requested',
      level: 'high',
      mitigation: 'Use platform payment methods only',
    };
  }
  
  return null;
}

/**
 * Check for removed serial numbers
 */
function checkSerialRemoved(listing: Listing): ScamSignal | null {
  const text = `${listing.title} ${listing.description || ''}`.toLowerCase();
  
  if (text.includes('serial removed') || text.includes('no serial')) {
    return {
      scoreDelta: 30,
      reason: 'Serial number removed',
      level: 'high',
      mitigation: 'Avoid - possible stolen goods',
    };
  }
  
  return null;
}

/**
 * Check new seller with high-value item
 */
function checkNewSeller(listing: Listing): ScamSignal | null {
  const isNewSeller = listing.seller.memberSince && 
    (Date.now() - new Date(listing.seller.memberSince).getTime()) < 30 * 24 * 60 * 60 * 1000;
  
  const isHighValue = listing.price.amount > 1000;
  
  if (isNewSeller && isHighValue) {
    return {
      scoreDelta: 20,
      reason: 'New seller with high-value item',
      level: 'medium',
      mitigation: 'Meet in safe public location, test thoroughly',
    };
  }
  
  return null;
}

/**
 * Check for template/spam patterns
 */
function checkTemplateSpam(listing: Listing): ScamSignal | null {
  const desc = listing.description || '';
  
  // Common spam patterns
  const spamPatterns = [
    /contact.{0,10}(email|gmail|yahoo)/i,
    /text.{0,10}\d{3}.{0,3}\d{3}.{0,3}\d{4}/i,
    /whatsapp/i,
    /!!+/,
    /\$\$+/,
  ];
  
  const hasSpam = spamPatterns.some(pattern => pattern.test(desc));
  
  if (hasSpam) {
    return {
      scoreDelta: 15,
      reason: 'Spam patterns detected',
      level: 'medium',
      mitigation: 'Communicate only through platform',
    };
  }
  
  return null;
}

/**
 * Check mismatched specs
 */
function checkMismatchedSpecs(listing: Listing): ScamSignal | null {
  const components = listing.specs?.components;
  if (!components) return null;
  
  // Check for impossible combinations
  const cpu = components.cpu;
  const gpu = components.gpu;
  
  if (cpu && gpu) {
    // Example: Old CPU with brand new GPU
    const oldCpu = /i[357]-[234]\d{3}/i.test(cpu.model || '');
    const newGpu = /RTX [34]0\d{2}/i.test(gpu.model || '');
    
    if (oldCpu && newGpu) {
      return {
        scoreDelta: 10,
        reason: 'Mismatched components (old CPU, new GPU)',
        level: 'low',
        mitigation: 'Verify actual components match listing',
      };
    }
  }
  
  return null;
}

/**
 * Calculate scam risk from all signals
 */
export function calculateScamRisk(
  listing: Listing,
  comps?: CompStats | null,
  sellerMeta?: { 
    otherListingsCount?: number;
    responseRate?: number;
  }
): ScamRiskResult {
  const signals: ScamSignal[] = [];
  
  // Run all checks
  const checks = [
    checkPriceAnomaly(listing, comps || null),
    checkStockPhotos(listing),
    checkShippingOnly(listing),
    checkUrgentPayment(listing),
    checkSerialRemoved(listing),
    checkNewSeller(listing),
    checkTemplateSpam(listing),
    checkMismatchedSpecs(listing),
  ];
  
  // Additional check for seller with many listings
  if (sellerMeta?.otherListingsCount && sellerMeta.otherListingsCount > 20) {
    signals.push({
      scoreDelta: 15,
      reason: 'Seller has many listings (possible reseller)',
      level: 'low',
      mitigation: 'Verify business legitimacy',
    });
  }
  
  // Collect non-null signals
  checks.forEach(signal => {
    if (signal) signals.push(signal);
  });
  
  // Calculate total score
  const score = Math.min(100, signals.reduce((sum, s) => sum + s.scoreDelta, 0));
  
  // Determine recommendation
  let recommendation: 'safe' | 'caution' | 'avoid';
  if (score >= 60) {
    recommendation = 'avoid';
  } else if (score >= 30) {
    recommendation = 'caution';
  } else {
    recommendation = 'safe';
  }
  
  return {
    score,
    reasons: signals.sort((a, b) => b.scoreDelta - a.scoreDelta),
    recommendation,
  };
}