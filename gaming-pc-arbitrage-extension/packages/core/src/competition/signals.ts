/**
 * Competition Signals
 * Heuristic competition scoring without scraping
 */

export interface CompetitionSignals {
  commentCount?: number;
  interestedCount?: number;
  viewCount?: number;
  daysLive: number;
  relistCount?: number;
  sellerListingCount?: number;
  priceDrops?: number;
}

export interface CompetitionScore {
  score: number; // 0-100, higher = more competition
  reasons: string[];
  tips: string[];
}

/**
 * Calculate competition score from visible signals
 */
export function computeCompetitionScore(signals: CompetitionSignals): CompetitionScore {
  let score = 0;
  const reasons: string[] = [];
  const tips: string[] = [];
  
  // Comment activity (visible on listing)
  if (signals.commentCount !== undefined) {
    if (signals.commentCount > 20) {
      score += 25;
      reasons.push(`High comment activity (${signals.commentCount})`);
      tips.push('Act fast - many buyers engaged');
    } else if (signals.commentCount > 10) {
      score += 15;
      reasons.push(`Moderate comments (${signals.commentCount})`);
    } else if (signals.commentCount > 5) {
      score += 10;
      reasons.push(`Some interest (${signals.commentCount} comments)`);
    }
  }
  
  // "X interested" indicator
  if (signals.interestedCount !== undefined) {
    if (signals.interestedCount > 10) {
      score += 20;
      reasons.push(`${signals.interestedCount} people interested`);
      tips.push('Make a strong opening offer');
    } else if (signals.interestedCount > 5) {
      score += 10;
      reasons.push(`${signals.interestedCount} interested`);
    }
  }
  
  // Days live (longer = less competition usually)
  if (signals.daysLive > 14) {
    score -= 10;
    reasons.push('Listed 2+ weeks (stale)');
    tips.push('Seller may be more flexible');
  } else if (signals.daysLive > 7) {
    score += 5;
    reasons.push('Listed 1-2 weeks');
  } else if (signals.daysLive <= 1) {
    score += 20;
    reasons.push('Fresh listing (<24h)');
    tips.push('Early bird advantage - move quickly');
  } else {
    score += 10;
    reasons.push(`Listed ${signals.daysLive} days`);
  }
  
  // Relisted (visible if same item reposted)
  if (signals.relistCount && signals.relistCount > 0) {
    score -= 5 * signals.relistCount;
    reasons.push(`Relisted ${signals.relistCount} times`);
    tips.push('Previous buyers fell through - negotiate harder');
  }
  
  // Seller has many listings (from profile if viewed)
  if (signals.sellerListingCount !== undefined) {
    if (signals.sellerListingCount > 20) {
      score += 10;
      reasons.push('High-volume seller');
      tips.push('Likely a reseller - less emotional attachment');
    } else if (signals.sellerListingCount === 1) {
      score -= 5;
      reasons.push('Single item seller');
      tips.push('Personal seller - build rapport');
    }
  }
  
  // Price drops detected
  if (signals.priceDrops && signals.priceDrops > 0) {
    score -= 10;
    reasons.push(`Price dropped ${signals.priceDrops} times`);
    tips.push('Seller motivated - room for negotiation');
  }
  
  // Normalize score
  score = Math.max(0, Math.min(100, score));
  
  // Add general tips based on score
  if (score >= 70) {
    tips.push('High competition - be prepared to pay asking or close');
  } else if (score >= 40) {
    tips.push('Moderate competition - standard negotiation likely');
  } else {
    tips.push('Low competition - aggressive offers may work');
  }
  
  return {
    score,
    reasons,
    tips,
  };
}

/**
 * Extract competition signals from parsed listing
 */
export function extractSignalsFromListing(listing: any): CompetitionSignals {
  const now = Date.now();
  const createdAt = new Date(listing.metadata?.createdAt || now);
  const daysLive = Math.floor((now - createdAt.getTime()) / (1000 * 60 * 60 * 24));
  
  return {
    commentCount: listing.engagement?.commentCount,
    interestedCount: listing.engagement?.interestedCount,
    viewCount: listing.engagement?.viewCount,
    daysLive,
    relistCount: listing.metadata?.relistCount,
    // sellerListingCount would come from profile parser
  };
}