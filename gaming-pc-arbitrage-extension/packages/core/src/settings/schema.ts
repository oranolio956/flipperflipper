/**
 * Settings Schema with Zod validation
 * Implements the default configuration from the blueprint
 */

import { z } from 'zod';

// Geographic Settings Schema
export const GeographySettingsSchema = z.object({
  center: z.string().describe('Center location for searches'),
  radius_miles: z.number().min(1).max(100).default(25),
  max_drive_minutes: z.number().min(15).max(120).default(45),
  gas_cost_per_mile: z.number().min(0).max(1).default(0.15),
});

// Financial Settings Schema
export const FinancialSettingsSchema = z.object({
  target_margin_percent: z.number().min(10).max(100).default(35),
  min_profit_dollars: z.number().min(0).default(150),
  labor_rate_per_hour: z.number().min(0).default(30),
  marketplace_fee_percent: z.number().min(0).max(20).default(0),
  tax_rate_percent: z.number().min(0).max(30).default(8.31),
  holding_cost_per_day: z.number().min(0).default(2),
  max_investment: z.number().min(100).default(800),
});

// Parts Bin Schema
export const PartsBinSchema = z.object({
  thermal_paste: z.number().default(5),
  sata_ssd_256gb: z.number().default(25),
  case_fan_120mm: z.number().default(8),
  psu_bronze_550w: z.number().default(45),
  ddr4_8gb: z.number().default(20),
  cleaning_supplies: z.number().default(3),
}).catchall(z.number().min(0)); // Allow additional parts

// Risk Tolerance Schema
export const RiskToleranceSchema = z.object({
  max_unit_investment: z.number().min(50).default(800),
  require_power_on_video: z.boolean().default(true),
  min_seller_age_days: z.number().min(0).default(30),
  avoid_water_cooling: z.boolean().default(false),
  max_risk_score: z.number().min(1).max(10).default(7),
  require_serial_photo: z.boolean().default(true),
  blacklisted_sellers: z.array(z.string()).default([]),
});

// Operations Settings Schema
export const OperationsSettingsSchema = z.object({
  follow_up_hours: z.array(z.number()).default([24, 72, 168]),
  max_active_deals: z.number().min(1).max(50).default(10),
  pickup_days: z.array(z.string()).default(['Tuesday', 'Thursday', 'Saturday']),
  preferred_meetup_locations: z.array(z.string()).default([
    'Police Station',
    'Bank',
    'Grocery Store',
  ]),
  auto_calculate: z.boolean().default(true),
  auto_follow_up: z.boolean().default(true),
  working_hours: z.object({
    start: z.string().regex(/^\d{2}:\d{2}$/).default('09:00'),
    end: z.string().regex(/^\d{2}:\d{2}$/).default('17:00'),
    days: z.array(z.number().min(0).max(6)).default([1, 2, 3, 4, 5]), // Mon-Fri
  }),
});

// Automation Settings Schema
export const AutomationSettingsSchema = z.object({
  mode: z.enum(['off', 'assist', 'max-auto']).default('assist'),
  rules: z.array(z.object({
    name: z.string(),
    enabled: z.boolean().default(true),
    condition: z.string(),
    action: z.string(),
    params: z.record(z.unknown()).optional(),
  })).default([]),
  confirmActions: z.object({
    sendMessage: z.boolean().default(true), // Always true for ToS compliance
    makeOffer: z.boolean().default(true),
    schedulePickup: z.boolean().default(false),
    markComplete: z.boolean().default(false),
  }),
});

// Notification Preferences Schema
export const NotificationPreferencesSchema = z.object({
  enabled: z.boolean().default(true),
  sound: z.boolean().default(true),
  desktop: z.boolean().default(true),
  triggers: z.object({
    newDeal: z.boolean().default(true),
    priceChange: z.boolean().default(true),
    followUpDue: z.boolean().default(true),
    highValueDeal: z.boolean().default(true),
    riskAlert: z.boolean().default(true),
  }),
  priceDropThreshold: z.number().min(1).max(50).default(10),
});

// Pricing Settings Schema
export const PricingSettingsSchema = z.object({
  markup_percentage: z.number().min(0).max(100).default(10),
  price_update_frequency: z.enum(['daily', 'weekly', 'monthly']).default('weekly'),
  use_market_pricing: z.boolean().default(true),
  custom_pricing: z.record(z.number()).default({}),
  negotiation_strategy: z.enum(['aggressive', 'fair', 'conservative']).default('fair'),
});

// Integration Settings Schema
export const IntegrationSettingsSchema = z.object({
  googleMaps: z.object({
    enabled: z.boolean().default(true),
    apiKey: z.string().optional(),
  }),
  googleSheets: z.object({
    enabled: z.boolean().default(false),
    spreadsheetId: z.string().optional(),
    syncInterval: z.number().default(3600), // seconds
  }),
  exportFormat: z.enum(['csv', 'excel', 'json']).default('csv'),
  autoBackup: z.boolean().default(true),
  backupFrequency: z.enum(['daily', 'weekly']).default('weekly'),
});

// Privacy Settings Schema
export const PrivacySettingsSchema = z.object({
  collectAnalytics: z.boolean().default(false),
  shareData: z.boolean().default(false),
  anonymizeData: z.boolean().default(true),
  retentionDays: z.number().min(30).max(365).default(90),
  clearDataOnUninstall: z.boolean().default(true),
});

// Integrations Schema
const IntegrationsSchema = z.object({
  sheets: z.object({
    enabled: z.boolean().default(false),
    clientId: z.string().default(''),
    spreadsheetId: z.string().default(''),
    auth: z.object({
      email: z.string().optional(),
      accessToken: z.string().optional(),
      expiresAt: z.number().optional(),
    }).optional(),
    sync: z.object({
      enabled: z.boolean().default(false),
      direction: z.enum(['push', 'pull', 'both']).default('both'),
      cadenceMin: z.number().min(0).default(60),
    }).default({}),
    mappings: z.object({
      deals: z.any().optional(),
      analytics: z.any().optional(),
      inventory: z.any().optional(),
    }).default({}),
  }).default({}),
});

// Team Schema
const TeamSchema = z.object({
  currentUserId: z.string().optional(),
});

// Backup Schema
const BackupSchema = z.object({
  enabled: z.boolean().default(false),
  frequency: z.enum(['weekly', 'monthly']).default('weekly'),
  retention: z.number().min(1).max(20).default(5),
  passphrase: z.string().default(''),
});

// Macro Schema
const MacroSchema = z.object({
  enabled: z.boolean().default(true),
  showHotkeys: z.boolean().default(true),
  buttons: z.object({
    draftOpener: z.boolean().default(true),
    followUp24h: z.boolean().default(true),
    priceCalculator: z.boolean().default(true),
    addCalendar: z.boolean().default(true),
    markAcquired: z.boolean().default(true),
    createInvoice: z.boolean().default(false),
  }),
  customHotkeys: z.record(z.string()).default({}),
});

// Price Drop Schema
const PriceDropSchema = z.object({
  enabled: z.boolean().default(true),
  defaultThreshold: z.number().min(1).max(50).default(10),
  checkFrequency: z.enum(['manual', 'daily', 'twice-daily']).default('daily'),
  autoRemoveAfterDays: z.number().min(7).max(90).default(30),
});

// Pricing Adjusters Schema
const PricingAdjustersSchema = z.object({
  enabled: z.boolean().default(true),
  seasonal: z.object({
    enabled: z.boolean().default(true),
    multipliers: z.array(z.object({
      month: z.number().min(1).max(12),
      multiplier: z.number().min(0.5).max(2),
      reason: z.string(),
    })).default([]),
  }),
  regional: z.object({
    enabled: z.boolean().default(true),
    multipliers: z.array(z.object({
      state: z.string().length(2),
      multiplier: z.number().min(0.5).max(2),
      notes: z.string().optional(),
    })).default([]),
  }),
  brand: z.object({
    enabled: z.boolean().default(true),
    premiums: z.array(z.object({
      brand: z.string(),
      category: z.enum(['cpu', 'gpu', 'case', 'psu', 'motherboard']),
      premium: z.number().min(-50).max(50),
    })).default([]),
  }),
});

// Operating Costs Schema
const OperatingCostsSchema = z.object({
  enabled: z.boolean().default(true),
  electricity: z.object({
    kwhRate: z.number().min(0).max(1).default(0.12), // US average ~$0.12/kWh
    defaultUsageHours: z.number().min(0).max(24).default(8),
    includeInTCO: z.boolean().default(true),
  }),
  mining: z.object({
    enabled: z.boolean().default(false), // Off by default
    algorithm: z.enum(['ethash', 'kawpow', 'autolykos']).default('ethash'),
    revenuePerMhPerDay: z.number().min(0).default(0.05),
    warnOnUsedGpu: z.boolean().default(true),
  }),
  warranty: z.object({
    enabled: z.boolean().default(true),
    multipliers: z.record(z.string(), z.number()).default({
      'evga': 1.3,
      'asus': 1.2,
      'msi': 1.1,
      'corsair': 1.2,
    }),
  }),
  holdingCosts: z.object({
    perDayAmount: z.number().min(0).default(2),
    includeOpportunityCost: z.boolean().default(true),
    opportunityRate: z.number().min(0).max(0.5).default(0.05), // 5% annual
  }),
});

// Main Settings Schema
export const SettingsSchema = z.object({
  version: z.string().default('1.0.0'),
  
  // User Preferences
  preferences: z.object({
    theme: z.enum(['light', 'dark', 'auto']).default('dark'),
    language: z.string().default('en'),
    currency: z.string().default('USD'),
    units: z.enum(['metric', 'imperial']).default('imperial'),
    notifications: NotificationPreferencesSchema,
  }),
  
  // Business Settings
  geography: GeographySettingsSchema,
  financial: FinancialSettingsSchema,
  parts_bin: PartsBinSchema,
  risk_tolerance: RiskToleranceSchema,
  operations: OperationsSettingsSchema,
  pricing: PricingSettingsSchema,
  
  // System Settings
  automation: AutomationSettingsSchema,
  integrations: IntegrationsSchema,
  privacy: PrivacySettingsSchema,
  team: TeamSchema,
  backup: BackupSchema,
  macros: MacroSchema,
  priceDrops: PriceDropSchema,
  pricingAdjusters: PricingAdjustersSchema,
  operatingCosts: OperatingCostsSchema,
  
  // Feature Flags
  features: z.object({
    // A - Sourcing & Discovery
    typoKeywordExpander: z.boolean().default(true),
    gpuGenerationTranslator: z.boolean().default(true),
    bundleValueCalculator: z.boolean().default(true),
    distanceOptimizer: z.boolean().default(true),
    duplicateDetector: z.boolean().default(true),
    priceDropTracker: z.boolean().default(true),
    newListingNotifier: z.boolean().default(false), // Manual refresh only
    sellerRatingParser: z.boolean().default(true),
    multiLocationSearch: z.boolean().default(true),
    savedFilterTemplates: z.boolean().default(true),
    commuteCostCalculator: z.boolean().default(true),
    photoCountAnalyzer: z.boolean().default(true),
    listingAgeHighlighter: z.boolean().default(true),
    keywordCombinationMatrix: z.boolean().default(true),
    priceAnomalyDetector: z.boolean().default(true),
    
    // B - Listing Understanding
    gpuVramDetector: z.boolean().default(true),
    psuWattageEstimator: z.boolean().default(true),
    cpuGenerationParser: z.boolean().default(true),
    photoSpecExtractor: z.boolean().default(false), // Requires WASM OCR
    bundleComponentItemizer: z.boolean().default(true),
    missingComponentDetector: z.boolean().default(true),
    overclockingFlag: z.boolean().default(true),
    waterCoolingIdentifier: z.boolean().default(true),
    caseFormFactorDetector: z.boolean().default(true),
    ramSpeedCapacityParser: z.boolean().default(true),
    storageTypeIdentifier: z.boolean().default(true),
    motherboardChipsetParser: z.boolean().default(true),
    rgbAestheticScorer: z.boolean().default(true),
    buildAgeEstimator: z.boolean().default(true),
    warrantyStatusChecker: z.boolean().default(true),
    
    // Enable all features by default (can be toggled by user)
  }).catchall(z.boolean()),
});

// Type inference
export type Settings = z.infer<typeof SettingsSchema>;
export type ExtensionSettingsSchema = Settings; // Alias to avoid conflicts
export type GeographySettings = z.infer<typeof GeographySettingsSchema>;
export type FinancialSettings = z.infer<typeof FinancialSettingsSchema>;
export type RiskToleranceSettings = z.infer<typeof RiskToleranceSchema>;
export type AutomationSettings = z.infer<typeof AutomationSettingsSchema>;

// Default settings generator
export function getDefaultSettings(): Settings {
  return SettingsSchema.parse({});
}

// Settings validation
export function validateSettings(settings: unknown): Settings {
  return SettingsSchema.parse(settings);
}

// Partial settings update
export function updateSettings(current: Settings, updates: Partial<Settings>): Settings {
  return SettingsSchema.parse({ ...current, ...updates });
}

// Export settings to JSON
export function exportSettings(settings: Settings): string {
  return JSON.stringify(settings, null, 2);
}

// Import settings from JSON
export function importSettings(json: string): Settings {
  try {
    const parsed = JSON.parse(json);
    return validateSettings(parsed);
  } catch (error) {
    throw new Error(`Invalid settings JSON: ${error}`);
  }
}