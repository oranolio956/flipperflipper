/**
 * Competitor Tracking
 * Monitor other sellers and their pricing strategies
 */

export interface Competitor {
  id: string;
  name: string;
  platform: string;
  listingCount: number;
  avgPrice: number;
  lastSeen: Date;
}

export class CompetitorTracker {
  private competitors: Map<string, Competitor> = new Map();
  
  track(sellerId: string, sellerName: string, platform: string, price: number): void {
    const existing = this.competitors.get(sellerId);
    
    if (existing) {
      existing.listingCount++;
      existing.avgPrice = (existing.avgPrice * (existing.listingCount - 1) + price) / existing.listingCount;
      existing.lastSeen = new Date();
    } else {
      this.competitors.set(sellerId, {
        id: sellerId,
        name: sellerName,
        platform,
        listingCount: 1,
        avgPrice: price,
        lastSeen: new Date()
      });
    }
  }
  
  getTopCompetitors(limit: number = 10): Competitor[] {
    return Array.from(this.competitors.values())
      .sort((a, b) => b.listingCount - a.listingCount)
      .slice(0, limit);
  }
  
  getCompetitor(sellerId: string): Competitor | undefined {
    return this.competitors.get(sellerId);
  }
}