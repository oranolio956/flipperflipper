/**
 * Default settings values
 */

import type { Settings } from './schema';

export const DEFAULT_SETTINGS: Settings = {
  version: '1.0.0',
  geography: {
    center: '',
    radius_miles: 25,
    max_drive_minutes: 45,
    gas_cost_per_mile: 0.15,
  },
  financial: {
    target_margin_percent: 35,
    min_profit_dollars: 150,
    labor_rate_per_hour: 30,
    sales_tax_rate: 0.0875,
    platform_fee_percent: 5,
    shipping_buffer_percent: 10,
  },
  risk_tolerance: {
    max_condition_score: 3,
    require_working_photos: true,
    avoid_keywords: ['parts', 'broken', 'repair', 'issue'],
    preferred_sellers: {
      min_rating_stars: 4.0,
      min_reviews_count: 5,
      max_response_time_hours: 24,
    },
  },
  automation: {
    enable_bulk_analysis: true,
    auto_calculate_fmv: true,
    refresh_comps_days: 7,
    max_concurrent_tabs: 5,
    typing_delay_ms: {
      min: 50,
      max: 150,
    },
  },
  notifications: {
    new_listings: {
      enabled: true,
      min_roi_percent: 25,
      max_risk_score: 50,
    },
    price_drops: {
      enabled: true,
      min_drop_percent: 10,
      min_drop_dollars: 50,
    },
    competitor_activity: {
      enabled: false,
      tracked_seller_ids: [],
    },
  },
  display: {
    overlay_position: 'top-right',
    show_debug_info: false,
    currency_symbol: '$',
    decimal_places: 0,
    roi_good_threshold: 25,
    roi_great_threshold: 40,
  },
  integrations: {
    google_sheets: {
      enabled: false,
      spreadsheet_id: '',
      sync_interval_minutes: 30,
    },
    backup: {
      enabled: true,
      interval_hours: 24,
      retention_days: 30,
    },
  },
  privacy: {
    mask_pii: true,
    store_seller_names: false,
    analytics_opt_in: false,
    clear_data_on_uninstall: true,
  },
  experimental: {
    ml_pricing: false,
    ocr_specs: false,
    voice_notes: false,
    team_mode: false,
  },
  cpuTiers: {
    low: ['i3', 'i5-2xxx', 'i5-3xxx', 'i5-4xxx', 'i5-6xxx', 'Ryzen 3'],
    mid: ['i5-7xxx', 'i5-8xxx', 'i5-9xxx', 'i5-10xxx', 'i7-6xxx', 'i7-7xxx', 'Ryzen 5'],
    high: ['i7-8xxx', 'i7-9xxx', 'i7-10xxx', 'i9', 'Ryzen 7', 'Ryzen 9'],
  },
  gpuTiers: {
    low: ['GTX 1050', 'GTX 1060', 'GTX 1650', 'RX 570', 'RX 580'],
    mid: ['GTX 1070', 'GTX 1080', 'RTX 2060', 'RTX 3060', 'RX 5700'],
    high: ['RTX 2070', 'RTX 2080', 'RTX 3070', 'RTX 3080', 'RTX 3090', 'RTX 4070', 'RTX 4080', 'RTX 4090'],
  },
  scamRules: {
    suspiciousWords: ['shipped', 'wire', 'cashapp', 'zelle', 'paypal', 'friends family'],
    tooGoodToBeTrue: {
      maxDiscountPercent: 70,
      flagMessage: 'Price seems too good to be true',
    },
    requiredPhotos: ['powered on', 'specs screen', 'all sides'],
    maxStockPhotos: 2,
  },
  negotiation: {
    autoGenerateOpeners: true,
    startingOfferPercent: 75,
    incrementPercent: 5,
    maxAttempts: 3,
    templates: {
      opener: "Hi! I'm interested in your {title}. Is it still available?",
      offer: "Would you consider ${amount} for it? I can pick up {timeframe}.",
      counter: "I understand. How about ${amount}? That's my best offer.",
    },
  },
  meetupSpots: {
    preferred: ['police station', 'bank', 'busy shopping center'],
    avoid: ['residence', 'empty lot', 'industrial area'],
    maxDistanceFromPublicPlace: 0.5,
  },
  qualityBar: {
    minComponentAge: 2,
    maxAcceptableIssues: 2,
    requiredBenchmarks: ['userbenchmark', '3dmark', 'crystaldiskinfo'],
    dealBreakers: ['no post', 'bsod', 'artifacts', 'damaged pins'],
  },
  pricingAdjusters: {
    seasonal: {
      enabled: true,
      multipliers: [
        { month: 11, multiplier: 1.15, reason: 'Black Friday demand' },
        { month: 12, multiplier: 1.10, reason: 'Holiday season' },
        { month: 1, multiplier: 0.95, reason: 'Post-holiday slump' },
        { month: 6, multiplier: 0.90, reason: 'Summer slowdown' },
        { month: 7, multiplier: 0.90, reason: 'Summer slowdown' },
        { month: 8, multiplier: 1.05, reason: 'Back-to-school' },
        { month: 9, multiplier: 1.08, reason: 'Back-to-school peak' },
      ],
    },
    regional: {
      enabled: true,
      premiums: [
        { state: 'CA', multiplier: 1.10, notes: 'Tech hub premium' },
        { state: 'NY', multiplier: 1.08, notes: 'High demand market' },
        { state: 'TX', multiplier: 1.05, notes: 'Growing tech market' },
        { state: 'WA', multiplier: 1.12, notes: 'Seattle tech premium' },
      ],
    },
    brand: {
      enabled: true,
      premiums: [
        { brand: 'ASUS ROG', category: 'gpu', premium: 1.05 },
        { brand: 'EVGA', category: 'gpu', premium: 1.08 },
        { brand: 'Noctua', category: 'cooling', premium: 1.15 },
        { brand: 'Corsair', category: 'ram', premium: 1.05 },
        { brand: 'Samsung', category: 'storage', premium: 1.10 },
      ],
    },
  },
  operatingCosts: {
    electricityRate: 0.12,
    defaultUsageHours: 8,
    miningProfitability: {
      enabled: false,
      electricityRate: 0.10,
      poolFee: 0.02,
    },
    warrantyMultipliers: {
      none: 0.90,
      limited: 0.95,
      full: 1.05,
      transferable: 1.10,
    },
    holdingCostPerDay: 2.50,
  },
};