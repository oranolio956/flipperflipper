/**
 * Risk Bridge
 * Compose existing risk engine with scam pattern detection
 */

import { calculateScamRisk, type ScamRiskResult } from '@/core/risk/scamRules';
import { RiskAssessment } from '@/core/risk';
import type { Listing } from '@/core';
import type { CompStats } from '@/core/comps';
import { db } from './db';

export interface EnhancedRiskAssessment extends RiskAssessment {
  scamRisk: ScamRiskResult;
  combinedScore: number;
  highestRisk: 'operational' | 'scam' | 'both';
}

/**
 * Calculate enhanced risk with scam detection
 */
export async function calculateEnhancedRisk(
  listing: Listing,
  existingRisk: RiskAssessment,
  comps?: CompStats | null
): Promise<EnhancedRiskAssessment> {
  // Get seller metadata if available
  const sellerMeta = await getSellerMetadata(listing.seller.id);
  
  // Calculate scam risk
  const scamRisk = calculateScamRisk(listing, comps, sellerMeta);
  
  // Combine scores (weighted average)
  const operationalScore = existingRisk.score;
  const scamScore = scamRisk.score;
  const combinedScore = Math.round(operationalScore * 0.4 + scamScore * 0.6);
  
  // Determine highest risk type
  let highestRisk: 'operational' | 'scam' | 'both';
  if (operationalScore > 60 && scamScore > 60) {
    highestRisk = 'both';
  } else if (scamScore > operationalScore) {
    highestRisk = 'scam';
  } else {
    highestRisk = 'operational';
  }
  
  // Persist scam risk details
  await persistScamRisk(listing.id, scamRisk);
  
  return {
    ...existingRisk,
    scamRisk,
    combinedScore,
    highestRisk,
  };
}

/**
 * Get seller metadata from cache
 */
async function getSellerMetadata(sellerId: string) {
  try {
    // Check if we have cached seller data
    const listings = await db.listings
      .where('seller.id')
      .equals(sellerId)
      .toArray();
    
    return {
      otherListingsCount: listings.length,
      responseRate: 0.75, // Placeholder - would track actual responses
    };
  } catch (error) {
    console.error('Failed to get seller metadata:', error);
    return null;
  }
}

/**
 * Persist scam risk for analytics
 */
async function persistScamRisk(listingId: string, scamRisk: ScamRiskResult) {
  try {
    // Store as an event for tracking
    await db.events.add({
      timestamp: new Date(),
      category: 'risk',
      name: 'scam_risk_calculated',
      properties: {
        listingId,
        score: scamRisk.score,
        recommendation: scamRisk.recommendation,
        signalCount: scamRisk.reasons.length,
        topReason: scamRisk.reasons[0]?.reason,
      },
    });
  } catch (error) {
    console.error('Failed to persist scam risk:', error);
  }
}