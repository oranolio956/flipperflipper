/**
 * Core Package - Main Export
 * Central export point for all core functionality
 */

// Types
export * from './types';

// Settings
export * from './settings/schema';

// Data
export * from './data/pricing-tiers';

// Parsers
export { ListingParser } from './parsers';
export { ComponentDetector } from './parsers/component-detector';
export type { ParsedListing, ParserStrategy } from './parsers';

// Calculators
export { FMVCalculator } from './calculators/fmv-calculator';
export { ROICalculator } from './calculators/roi-calculator';
export type { FMVResult, ComponentValue, Adjustment } from './calculators/fmv-calculator';
export type { ROIResult, OfferStrategy } from './calculators/roi-calculator';

// Negotiation
export * from './negotiation/templates';

// Risk Engine
export { RiskEngine } from './risk/risk-engine';
export type { RiskAssessment, RiskFlag } from './risk/risk-engine';
export * from './risk/scamRules';

// Utilities
export { formatCurrency, formatPercentage, formatNumber } from './utils/formatters';
export { calculateDistance, isWithinRadius } from './utils/geo';
export { generateId, hashString } from './utils/crypto';

// Constants
// Export analytics
export * from './analytics';

// Export A/B testing
export * from './abtest';

// Export comps
export * from './comps';

// Export pricing integrations
export * from './pricing/integrations';

// Export competition
export * from './competition/signals';

// Export finance
export * from './finance/pnl';

// Export ML
export * from './ml/priceModel';

// Export data
export * from './data/gpuHierarchy';

// Export pricing adjusters
export * from './pricing/adjusters';

// Export strategy modules
export * from './strategy/upgradePath';
export * from './strategy/partOut';
export * from './strategy/quickFlip';

// Export operating costs
export * from './costs/operating';

// Export performance modules
export * from './perf/benchPredictor';
export * from './perf/bottleneck';

export const VERSION = '1.0.0';
export const SUPPORTED_PLATFORMS = ['facebook', 'craigslist', 'offerup'] as const;
export const MAX_ACTIVE_DEALS = 50;
export const MAX_LISTING_AGE_DAYS = 30;