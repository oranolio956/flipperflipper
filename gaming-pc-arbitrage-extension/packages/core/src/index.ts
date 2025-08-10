/**
 * Gaming PC Arbitrage Core Library
 * Centralized business logic and utilities
 */

// Types
export * from './types';

// Settings
export * from './settings/schema';
export * from './settings/defaults';

// Parsers
export * from './parsers/component-detector';
export * from './parsers/facebook';
export * from './parsers/craigslist';
export * from './parsers/offerup';

// Pricing
export * from './pricing/fmv-calculator';
export * from './pricing/pricing-tiers';

// Calculators
export * from './calculators/roi-calculator';

// Finance
export * from './finance/reporting';

// Analytics
export * from './analytics';

// Risk
export * from './risk';

// Backup
export * from './backup';

// Privacy
export * from './privacy/manager';

// Competition
export * from './competition/competitors';

// Performance
export * from './performance/tracker';

// Reliability
export * from './reliability/healthMonitor';

// A/B Testing
export * from './abtest/experiments';

// Automation
export * from './automation/detectionAvoidance';

// Capture/OCR
export * from './capture/ocr/photoExtractor';
export * from './capture/ocr/tesseractExtractor';

// ML Models
export * from './ml/models';
export * from './ml/tfPriceModel';
export * from './ml/statisticalAnomalyDetector';

// Export specific instances for convenience
export { ComponentDetector } from './parsers/component-detector';
export { FMVCalculator } from './pricing/fmv-calculator';
export { ROICalculator } from './calculators/roi-calculator';
export { FacebookMarketplaceParser } from './parsers/facebook';
export { CraigslistParser } from './parsers/craigslist';
export { OfferUpParser } from './parsers/offerup';
export { RiskEngine } from './risk/risk-engine';
export { PrivacyManager } from './privacy/manager';
export { tensorFlowPriceModel } from './ml/tfPriceModel';
export { statisticalAnomalyDetector } from './ml/statisticalAnomalyDetector';
export { tesseractExtractor } from './capture/ocr/tesseractExtractor';