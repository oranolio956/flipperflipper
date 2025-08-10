/**
 * @arbitrage/core
 * Core business logic for Gaming PC Arbitrage Extension
 */

// Types
export * from './types';

// Settings & Schema
export * from './settings/schema';
export * from './settings/defaults';

// Calculators
export * from './calculators/fmv-calculator';
export * from './calculators/roi-calculator';

// Parsers
export * from './parsers/facebook';
export * from './parsers/craigslist';
export * from './parsers/offerup';
export * from './parsers/advancedParser';

// ML & AI
export * from './ml/pricePredictor';
export * from './ml/anomalyDetector';
export * from './ml/models';
export * from './ml/priceModel';

// Risk Assessment
export * from './risk/engine';

// Market Comps
export * from './comps';

// Competitors
export * from './competitors';

// Experiments
export * from './experiments';

// Scraping
export * from './scraping/detectionAvoidance';

// Backup
export * from './backup';

// Export data
export * from './data/gpuHierarchy';

// Export pricing adjusters
export * from './pricing/adjusters';
export * from './pricing/integrations';

// Export strategy modules
export * from './strategy/upgradePath';
export * from './strategy/partOut';
export * from './strategy/quickFlip';

// Export operating costs
export * from './costs/operating';

// Export performance modules
export * from './perf/benchPredictor';
export * from './perf/bottleneck';

// Export capture modules
export * from './capture/ocr/photoExtractor';
export * from './capture/quickAdd';
export * from './capture/voiceNotes';

// Export automation modules
export * from './automation/dealFlow';
export * from './automation/workflowTemplates';

// Export enrichment modules
export * from './enrichment/dataEnricher';

// Export communication and scheduling modules
export * from './communication/messageTemplates';
export * from './scheduling/meetingScheduler';

// Export inventory and pipeline
export * from './inventory/inventoryManager';
export * from './pipeline/pipelineManager';

// Export analytics
export * from './analytics/advancedAnalytics';

// Export privacy and compliance
export * from './privacy/privacyManager';
export * from './compliance/complianceManager';

// Export performance and reliability
export * from './performance/performanceMonitor';
export * from './reliability/reliabilityManager';

// Export migration
export * from './migration/migrationManager';

// Constants
export const VERSION = '1.0.0';
export const SUPPORTED_PLATFORMS = ['facebook', 'craigslist', 'offerup'] as const;
export const MAX_ACTIVE_DEALS = 50;
export const MAX_INVENTORY_ITEMS = 200;
export const DEFAULT_CACHE_TTL = 300; // 5 minutes

// Feature flags
export const FEATURES = {
  ML_PREDICTIONS: true,
  OCR_PROCESSING: true,
  VOICE_COMMANDS: true,
  ADVANCED_ANALYTICS: true,
  AUTO_BUNDLING: true,
  ROUTE_OPTIMIZATION: true,
  COMPETITOR_TRACKING: true,
  AB_TESTING: true,
} as const;

// Platform limits
export const PLATFORM_LIMITS = {
  facebook: {
    messagesPerHour: 20,
    listingsPerDay: 5,
  },
  craigslist: {
    listingsPerCategory: 1,
    listingCooldown: 48 * 60 * 60 * 1000, // 48 hours
  },
  offerup: {
    messagesPerHour: 30,
    listingsPerDay: 10,
  },
} as const;