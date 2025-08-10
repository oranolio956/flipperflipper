/**
 * Core type definitions for Gaming PC Arbitrage Extension
 * Implements all data models from the blueprint
 */

export type Platform = 'facebook' | 'craigslist' | 'offerup';
export type DealStage = 
  | 'discovered'
  | 'analyzing'
  | 'contacting'
  | 'negotiating'
  | 'agreed'
  | 'pickup_scheduled'
  | 'in_transit'
  | 'received'
  | 'testing'
  | 'refurbishing'
  | 'photographing'
  | 'listing'
  | 'selling'
  | 'sold'
  | 'completed'
  | 'cancelled';

export type ComponentCondition = 'new' | 'like-new' | 'good' | 'fair' | 'poor';
export type ListingStatus = 'active' | 'saved' | 'contacted' | 'archived';
export type AutomationMode = 'off' | 'assist' | 'max-auto';

// Component Types
export interface CPUComponent {
  brand: 'Intel' | 'AMD';
  model: string;
  generation?: number;
  cores: number;
  threads: number;
  baseClock: number; // GHz
  boostClock?: number; // GHz
  tdp: number; // Watts
  socket: string;
  value: number;
  condition: ComponentCondition;
}

export interface GPUComponent {
  brand: 'NVIDIA' | 'AMD' | 'Intel';
  model: string;
  vram: number; // GB
  vramType: 'GDDR5' | 'GDDR6' | 'GDDR6X' | 'HBM2' | 'HBM3';
  tdp: number;
  outputs: string[];
  value: number;
  condition: ComponentCondition;
  miningRisk: boolean;
}

export interface RAMComponent {
  size: number; // GB
  speed: number; // MHz
  type: 'DDR3' | 'DDR4' | 'DDR5';
  modules: number;
  value: number;
  condition: ComponentCondition;
}

export interface StorageComponent {
  type: 'HDD' | 'SATA SSD' | 'NVMe';
  capacity: number; // GB
  brand?: string;
  model?: string;
  health?: number; // percentage
  value: number;
  condition: ComponentCondition;
}

export interface MotherboardComponent {
  brand: string;
  model: string;
  chipset: string;
  socket: string;
  formFactor: 'ATX' | 'mATX' | 'ITX';
  ramSlots: number;
  maxRam: number;
  value: number;
  condition: ComponentCondition;
}

export interface PSUComponent {
  wattage: number;
  efficiency: '80+' | '80+ Bronze' | '80+ Silver' | '80+ Gold' | '80+ Platinum' | '80+ Titanium';
  modular: 'non-modular' | 'semi-modular' | 'full-modular';
  brand?: string;
  value: number;
  condition: ComponentCondition;
}

export interface CaseComponent {
  brand?: string;
  model?: string;
  formFactor: 'Full Tower' | 'Mid Tower' | 'Mini Tower' | 'SFF';
  color: string;
  sidePanel: 'solid' | 'windowed' | 'tempered glass';
  value: number;
  condition: ComponentCondition;
}

export interface CoolingComponent {
  type: 'stock' | 'air' | 'aio' | 'custom-loop';
  brand?: string;
  model?: string;
  size?: number; // mm for radiators
  value: number;
  condition: ComponentCondition;
}

// Main Listing Type
export interface Listing {
  // Identifiers
  id: string;
  url: string;
  platform: Platform;
  externalId?: string;
  
  // Basic Info
  title: string;
  description: string;
  price: number;
  currency: 'USD';
  
  // Location
  location: {
    city: string;
    state: string;
    zip?: string;
    coordinates?: {
      lat: number;
      lng: number;
    };
    distance?: number; // miles from user
  };
  
  // Seller
  seller: {
    id: string;
    name: string;
    profileUrl?: string;
    memberSince?: Date;
    responseRate?: number;
    responseTime?: number; // minutes
    listingCount?: number;
    rating?: number;
    verified?: boolean;
  };
  
  // Media
  images: Array<{
    url: string;
    width?: number;
    height?: number;
    primary: boolean;
  }>;
  
  // Parsed Components
  components: {
    cpu?: CPUComponent;
    gpu?: GPUComponent;
    ram?: RAMComponent[];
    storage?: StorageComponent[];
    motherboard?: MotherboardComponent;
    psu?: PSUComponent;
    case?: CaseComponent;
    cooling?: CoolingComponent;
    peripherals?: Array<{
      type: string;
      description: string;
      value: number;
    }>;
  };
  
  // Condition & Quality
  condition: {
    overall: 1 | 2 | 3 | 4 | 5;
    notes: string[];
    issues: Array<{
      component: string;
      issue: string;
      severity: 'minor' | 'moderate' | 'major';
    }>;
    ageEstimate?: number; // months
    usageType?: 'light' | 'moderate' | 'heavy';
  };
  
  // Analysis Results
  analysis: {
    fmv: number;
    componentValue: number;
    profitPotential: number;
    roi: number;
    margin: number;
    dealScore: number; // 0-100
    confidence: number; // 0-100
  };
  
  // Risk Assessment
  risks: {
    score: number; // 0-10
    flags: Array<{
      type: string;
      severity: 'low' | 'medium' | 'high';
      description: string;
    }>;
    stolen: {
      probability: number;
      indicators: string[];
    };
    scam: {
      probability: number;
      patterns: string[];
    };
    technical: {
      issues: string[];
      severity: 'low' | 'medium' | 'high';
    };
  };
  
  // Metadata
  metadata: {
    createdAt: Date;
    updatedAt: Date;
    lastViewedAt: Date;
    viewCount: number;
    priceHistory: Array<{
      date: Date;
      price: number;
    }>;
    status: ListingStatus;
    starred: boolean;
    hidden: boolean;
    notes: string;
    tags: string[];
  };
}

// Deal Management
export interface Offer {
  id: string;
  amount: number;
  message: string;
  timestamp: Date;
  response?: {
    type: 'accepted' | 'rejected' | 'counter';
    amount?: number;
    message?: string;
    timestamp: Date;
  };
}

export interface Message {
  id: string;
  type: 'sent' | 'received' | 'template';
  content: string;
  timestamp: Date;
  read: boolean;
}

export interface Deal {
  // Identifiers
  id: string;
  listingId: string;
  listing: Listing;
  
  // Pipeline Stage
  stage: DealStage;
  stageHistory: Array<{
    from: DealStage;
    to: DealStage;
    timestamp: Date;
    reason?: string;
    automatic: boolean;
  }>;
  
  // Negotiation
  negotiation: {
    askingPrice: number;
    offers: Offer[];
    currentOffer?: number;
    agreedPrice?: number;
    walkAwayPrice: number;
    targetPrice: number;
  };
  
  // Communication
  communication: {
    messages: Message[];
    templates: Array<{
      id: string;
      name: string;
      content: string;
    }>;
    lastContact?: Date;
    nextFollowUp?: Date;
    responseTime?: number;
    sellerEngagement: 'low' | 'medium' | 'high';
  };
  
  // Logistics
  logistics: {
    pickup: {
      scheduled?: Date;
      location?: {
        address: string;
        lat: number;
        lng: number;
        safetyRating: number;
      };
      confirmed: boolean;
      notes: string;
    };
    transport: {
      method: 'personal' | 'friend' | 'delivery';
      cost: number;
      distance: number;
      time: number; // minutes
    };
  };
  
  // Financials
  financials: {
    purchasePrice?: number;
    listingFees: number;
    transportCost: number;
    refurbCosts: Array<{
      item: string;
      cost: number;
      notes?: string;
    }>;
    totalInvestment: number;
    estimatedResale: number;
    estimatedProfit: number;
    actualResale?: number;
    actualProfit?: number;
  };
  
  // Inventory
  inventory?: {
    receivedDate?: Date;
    location: string;
    condition: string;
    refurbStatus: 'pending' | 'in-progress' | 'completed';
    listedDate?: Date;
    soldDate?: Date;
    buyer?: string;
  };
  
  // Documentation
  documentation: {
    receipts: Array<{
      id: string;
      type: 'purchase' | 'transport' | 'parts' | 'sale';
      amount: number;
      date: Date;
      imageUrl?: string;
    }>;
    photos: Array<{
      id: string;
      type: 'listing' | 'received' | 'damage' | 'serial' | 'completed';
      url: string;
      caption?: string;
      timestamp: Date;
    }>;
    serialNumbers: Array<{
      component: string;
      serial: string;
      verified: boolean;
    }>;
    testResults: Array<{
      test: string;
      result: 'pass' | 'fail' | 'warning';
      notes?: string;
      timestamp: Date;
    }>;
  };
  
  // Analytics
  analytics: {
    daysInStage: Record<DealStage, number>;
    totalCycleDays: number;
    profitMargin: number;
    roi: number;
    scorecard: {
      negotiation: number;
      timing: number;
      execution: number;
      overall: number;
    };
  };
  
  // Metadata
  metadata: {
    createdAt: Date;
    updatedAt: Date;
    completedAt?: Date;
    createdBy: string;
    tags: string[];
    priority: 'low' | 'medium' | 'high';
    archived: boolean;
  };
}

// Analytics Types
export interface AnalyticsSnapshot {
  id: string;
  type: 'daily' | 'weekly' | 'monthly';
  date: Date;
  
  performance: {
    totalDeals: number;
    activeDeals: number;
    completedDeals: number;
    successRate: number;
    averageMargin: number;
    averageROI: number;
    totalProfit: number;
    totalRevenue: number;
  };
  
  time: {
    averageDealCycle: number; // days
    averageTimeInStage: Record<DealStage, number>;
    fastestDeal: number;
    slowestDeal: number;
  };
  
  financial: {
    investedCapital: number;
    availableCapital: number;
    monthlyProfit: number[];
    profitTrend: 'up' | 'down' | 'stable';
  };
  
  operational: {
    listingsAnalyzed: number;
    contactRate: number;
    responseRate: number;
    conversionRate: number;
    averageNegotiationDiscount: number;
  };
  
  categories: Record<string, {
    count: number;
    totalProfit: number;
    averageMargin: number;
    averageCycle: number;
  }>;
}

// Market Data
export interface MarketComp {
  id: string;
  componentType: string;
  brand: string;
  model: string;
  specs: Record<string, unknown>;
  condition: ComponentCondition;
  soldPrice: number;
  soldDate: Date;
  platform: Platform;
  daysToSell: number;
  source: 'manual' | 'scraped' | 'api';
}

export interface PriceTier {
  component: string;
  condition: ComponentCondition;
  percentile25: number;
  median: number;
  percentile75: number;
  average: number;
  sampleSize: number;
  lastUpdated: Date;
}

// Feature Flags
export interface FeatureFlags {
  // A - Sourcing & Discovery
  typoKeywordExpander: boolean;
  gpuGenerationTranslator: boolean;
  bundleValueCalculator: boolean;
  distanceOptimizer: boolean;
  duplicateDetector: boolean;
  priceDropTracker: boolean;
  newListingNotifier: boolean;
  sellerRatingParser: boolean;
  multiLocationSearch: boolean;
  savedFilterTemplates: boolean;
  commuteCostCalculator: boolean;
  photoCountAnalyzer: boolean;
  listingAgeHighlighter: boolean;
  keywordCombinationMatrix: boolean;
  priceAnomalyDetector: boolean;
  
  // B - Listing Understanding
  gpuVramDetector: boolean;
  psuWattageEstimator: boolean;
  cpuGenerationParser: boolean;
  photoSpecExtractor: boolean;
  bundleComponentItemizer: boolean;
  missingComponentDetector: boolean;
  overclockingFlag: boolean;
  waterCoolingIdentifier: boolean;
  caseFormFactorDetector: boolean;
  ramSpeedCapacityParser: boolean;
  storageTypeIdentifier: boolean;
  motherboardChipsetParser: boolean;
  rgbAestheticScorer: boolean;
  buildAgeEstimator: boolean;
  warrantyStatusChecker: boolean;
  
  // ... (continue for all feature categories)
}

// Event Types for Analytics
export interface AnalyticsEvent {
  id: string;
  name: string;
  category: string;
  timestamp: Date;
  userId?: string;
  properties: Record<string, unknown>;
  metrics?: {
    value?: number;
    duration?: number;
    count?: number;
  };
}