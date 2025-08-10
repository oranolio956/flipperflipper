/**
 * Competitor Tracking Module
 * Re-exports the enhanced competitor tracking system
 */

export { 
  EnhancedCompetitorTracker as CompetitorTracker,
  competitorTracker 
} from './competitorTracker';

export type {
  Competitor,
  CompetitorListing,
  PriceChange,
  PricePoint,
  CompetitorInsight
} from './competitorTracker';