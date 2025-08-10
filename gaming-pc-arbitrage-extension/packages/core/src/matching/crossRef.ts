/**
 * Cross-Reference Matcher
 * Find duplicate listings across platforms
 */

import { Listing } from '../types';
import { ComponentDetector } from '../parsers/component-detector';

export interface CrossRefMatch {
  listingId: string;
  platform: string;
  url: string;
  similarity: number; // 0-1
  reasons: string[];
}

export interface CrossRefResult {
  matches: CrossRefMatch[];
  confidence: number;
}

/**
 * Find cross-platform matches for a listing
 */
export async function findCrossReferences(
  listing: Listing,
  candidates: Listing[]
): Promise<CrossRefResult> {
  const matches: CrossRefMatch[] = [];
  
  for (const candidate of candidates) {
    // Skip same listing
    if (candidate.id === listing.id) continue;
    
    const similarity = calculateSimilarity(listing, candidate);
    
    if (similarity.score > 0.7) {
      matches.push({
        listingId: candidate.id,
        platform: candidate.platform,
        url: candidate.url,
        similarity: similarity.score,
        reasons: similarity.reasons,
      });
    }
  }
  
  // Sort by similarity
  matches.sort((a, b) => b.similarity - a.similarity);
  
  // Calculate overall confidence
  const confidence = matches.length > 0 ? matches[0].similarity : 0;
  
  return {
    matches,
    confidence,
  };
}

/**
 * Calculate similarity between two listings
 */
function calculateSimilarity(
  listing1: Listing,
  listing2: Listing
): { score: number; reasons: string[] } {
  const reasons: string[] = [];
  let score = 0;
  let weights = 0;
  
  // Price similarity (30% weight)
  const priceDiff = Math.abs(listing1.price - listing2.price);
  const avgPrice = (listing1.price + listing2.price) / 2;
  const priceRatio = priceDiff / avgPrice;
  
  if (priceRatio < 0.05) {
    score += 0.3;
    weights += 0.3;
    reasons.push('Nearly identical price');
  } else if (priceRatio < 0.15) {
    score += 0.2;
    weights += 0.3;
    reasons.push('Similar price');
  } else if (priceRatio < 0.3) {
    score += 0.1;
    weights += 0.3;
  } else {
    weights += 0.3;
  }
  
  // Component similarity (40% weight)
  const detector = new ComponentDetector();
  const comp1 = detector.detectAll(`${listing1.title} ${listing1.description}`);
  const comp2 = detector.detectAll(`${listing2.title} ${listing2.description}`);
  
  let componentScore = 0;
  
  // CPU match
  if (comp1.cpu && comp2.cpu && comp1.cpu.model === comp2.cpu.model) {
    componentScore += 0.15;
    reasons.push(`Same CPU: ${comp1.cpu.model}`);
  }
  
  // GPU match
  if (comp1.gpu && comp2.gpu && comp1.gpu.model === comp2.gpu.model) {
    componentScore += 0.15;
    reasons.push(`Same GPU: ${comp1.gpu.model}`);
  }
  
  // RAM match
  const ram1 = comp1.ram?.reduce((sum, r) => sum + (r.capacity || 0), 0) || 0;
  const ram2 = comp2.ram?.reduce((sum, r) => sum + (r.capacity || 0), 0) || 0;
  if (ram1 > 0 && ram1 === ram2) {
    componentScore += 0.05;
    reasons.push(`Same RAM: ${ram1}GB`);
  }
  
  // Storage match
  const storage1 = comp1.storage?.reduce((sum, s) => sum + (s.capacity || 0), 0) || 0;
  const storage2 = comp2.storage?.reduce((sum, s) => sum + (s.capacity || 0), 0) || 0;
  if (storage1 > 0 && Math.abs(storage1 - storage2) < 100) {
    componentScore += 0.05;
    reasons.push('Similar storage');
  }
  
  score += componentScore;
  weights += 0.4;
  
  // Title similarity (20% weight)
  const titleSimilarity = calculateTextSimilarity(listing1.title, listing2.title);
  if (titleSimilarity > 0.8) {
    score += 0.2;
    reasons.push('Very similar title');
  } else if (titleSimilarity > 0.6) {
    score += 0.1;
    reasons.push('Similar title');
  }
  weights += 0.2;
  
  // Location proximity (10% weight)
  if (listing1.location.city === listing2.location.city) {
    score += 0.1;
    weights += 0.1;
    reasons.push('Same city');
  } else if (listing1.location.state === listing2.location.state) {
    score += 0.05;
    weights += 0.1;
    reasons.push('Same state');
  } else {
    weights += 0.1;
  }
  
  // Normalize score
  const finalScore = weights > 0 ? score / weights : 0;
  
  return {
    score: finalScore,
    reasons,
  };
}

/**
 * Calculate text similarity using simple token overlap
 */
function calculateTextSimilarity(text1: string, text2: string): number {
  const tokens1 = tokenize(text1);
  const tokens2 = tokenize(text2);
  
  if (tokens1.size === 0 || tokens2.size === 0) return 0;
  
  let overlap = 0;
  for (const token of tokens1) {
    if (tokens2.has(token)) {
      overlap++;
    }
  }
  
  // Jaccard similarity
  const union = new Set([...tokens1, ...tokens2]).size;
  return overlap / union;
}

/**
 * Tokenize text for comparison
 */
function tokenize(text: string): Set<string> {
  return new Set(
    text
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, '')
      .split(/\s+/)
      .filter(token => token.length > 2)
  );
}

/**
 * Check if listings are likely duplicates
 */
export function areLikelyDuplicates(
  listing1: Listing,
  listing2: Listing
): boolean {
  const similarity = calculateSimilarity(listing1, listing2);
  return similarity.score > 0.85;
}