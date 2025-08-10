/**
 * Core type definitions for the Gaming PC Arbitrage extension
 */

// Platform types
export type Platform = 'facebook' | 'craigslist' | 'offerup' | 'ebay';

// Component types
export interface CPUComponent {
  brand: 'Intel' | 'AMD';
  model: string;
  generation?: number;
  cores?: number;
  threads?: number;
  baseClock?: number;
  boostClock?: number;
  tdp?: number;
  socket?: string;
  value?: number; // Added for pricing
}

export interface GPUComponent {
  brand: 'NVIDIA' | 'AMD' | 'Intel';
  model: string;
  vram: number;
  vramType?: 'GDDR5' | 'GDDR6' | 'GDDR6X' | 'HBM2'; // Added
  architecture?: string;
  tdp?: number;
  displayOutputs?: string[];
  nvlinkSli?: boolean;
}

export interface RAMComponent {
  capacity: number; // GB
  size?: number; // Alias for capacity
  speed: number; // MHz
  type: 'DDR3' | 'DDR4' | 'DDR5';
  modules: number;
  ecc?: boolean;
  rgb?: boolean;
  latency?: string;
}

export interface StorageComponent {
  type: 'ssd' | 'hdd' | 'nvme' | 'm.2' | 'SATA SSD' | 'NVMe' | 'HDD'; // Extended
  capacity: number; // GB
  brand?: string;
  model?: string;
  readSpeed?: number;
  writeSpeed?: number;
  formFactor?: string;
  interface?: string;
  value?: number; // Added for pricing
}

export interface MotherboardComponent {
  brand?: string;
  model?: string;
  chipset?: string;
  socket?: string;
  formFactor?: 'ATX' | 'Micro-ATX' | 'Mini-ITX' | 'E-ATX' | 'mATX' | 'ITX'; // Extended
  ramSlots?: number;
  maxRam?: number;
  m2Slots?: number;
  pciSlots?: number;
  value?: number; // Added for pricing
}

export interface PSUComponent {
  wattage: number;
  efficiency?: '80+' | '80+ Bronze' | '80+ Silver' | '80+ Gold' | '80+ Platinum' | '80+ Titanium';
  modular?: 'Non-modular' | 'Semi-modular' | 'Fully-modular' | 'non-modular' | 'semi-modular' | 'full-modular';
  brand?: string;
  model?: string;
  value?: number; // Added for pricing
}

export interface CaseComponent {
  brand?: string;
  model?: string;
  formFactor?: string;
  color?: string;
  sidePanel?: 'Windowed' | 'Solid' | 'Tempered Glass' | 'Mesh' | 'windowed' | 'solid' | 'tempered glass';
  rgb?: boolean;
  value?: number; // Added for pricing
}

export interface CoolerComponent {
  type: 'air' | 'aio' | 'custom' | 'custom-loop';
  brand?: string;
  model?: string;
  radiatorSize?: number; // mm for AIO
  tdpRating?: number;
  rgb?: boolean;
}

// Alias for compatibility
export type CoolingComponent = CoolerComponent;

// Listing types
export interface ListingImage {
  url: string;
  width?: number;
  height?: number;
  primary: boolean;
}

export interface ListingComponents {
  cpu?: CPUComponent;
  gpu?: GPUComponent;
  ram?: RAMComponent[];
  storage?: StorageComponent[];
  motherboard?: MotherboardComponent;
  psu?: PSUComponent;
  case?: CaseComponent;
  cooler?: CoolerComponent;
  cooling?: CoolerComponent; // Alias
}

export interface ListingAnalysis {
  fmv: number;
  componentValue: number;
  profitPotential: number;
  roi: number;
  margin: number;
  dealScore: number;
  confidence: number;
}

export interface ListingRisks {
  score: number;
  flags: Array<{
    type: string;
    severity: string;
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
    severity: string;
  };
}

export interface ListingCondition {
  overall?: 1 | 2 | 3 | 4 | 5;
  notes?: string[];
  issues?: string[];
  ageEstimate?: number;
  usageType?: 'light' | 'moderate' | 'heavy';
}

export interface Listing {
  id: string;
  url: string;
  platform: Platform;
  externalId?: string; // Platform-specific ID
  title: string;
  price: number;
  location: {
    city?: string;
    state?: string;
    zipCode?: string;
    distance?: number;
  };
  description: string;
  images: string[]; // URLs
  imageData?: ListingImage[]; // Detailed image data
  seller: {
    id: string;
    name: string;
    profileUrl?: string;
    memberSince?: Date;
    responseTime?: string;
    responseRate?: number;
    listingCount?: number;
    rating?: number;
    badges?: string[];
    verified?: boolean; // Added
  };
  condition?: 'new' | 'like-new' | 'good' | 'fair' | 'parts' | ListingCondition;
  listingDate: Date;
  lastUpdated: Date;
  viewCount?: number;
  savedCount?: number;
  isLocalPickupOnly?: boolean;
  acceptsOffers?: boolean;
  isFirmPrice?: boolean;
  
  // Component specifications
  components?: ListingComponents;
  specs?: {
    components: ListingComponents;
    peripherals?: string[];
    os?: string;
  };
  
  // Analysis results
  analysis?: ListingAnalysis;
  
  // Risk assessment
  risks?: ListingRisks;
  
  // Metadata
  metadata?: {
    createdAt: Date;
    updatedAt: Date;
    status?: string;
    source?: string;
  };
}

// Deal types
export interface Deal {
  id: string;
  listingId: string;
  listing?: Listing; // Added for compatibility
  platform: Platform;
  status: 'watching' | 'evaluating' | 'negotiating' | 'scheduled' | 'purchased' | 'testing' | 'listing' | 'sold' | 'completed' | 'cancelled';
  stage?: string; // For workflow compatibility
  
  // Pricing
  askingPrice: number;
  purchasePrice?: number;
  salePrice?: number;
  sellPrice?: number; // Alias for salePrice
  shippingCost?: number;
  fees?: number;
  
  // Risk assessment
  risk?: {
    score: number;
    flags: RiskFlag[];
    level: 'low' | 'medium' | 'high' | 'critical';
  };
  
  // Negotiation
  offers: Offer[];
  messages: Message[];
  
  // Logistics
  pickupScheduled?: Date;
  pickupLocation?: {
    address?: string;
    coordinates?: { lat: number; lng: number };
    notes?: string;
  };
  
  // Inventory
  acquiredDate?: Date;
  soldDate?: Date;
  soldAt?: Date; // Alias for soldDate
  category?: string;
  
  // Metadata
  metadata: {
    createdAt: Date;
    updatedAt: Date;
    source: string;
    version: number;
    lastViewedAt?: Date;
    notes?: string;
    tags?: string[];
  };
  
  // Stage history
  stageHistory?: Array<{
    from: string;
    to: string;
    timestamp: Date;
    reason?: string;
    automatic?: boolean;
  }>;
}

// Risk types
export interface RiskFlag {
  type: 'price' | 'seller' | 'content' | 'technical' | 'safety';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  details?: any;
  suggestedAction?: string;
}

export interface RiskAssessment {
  score: number;
  level: 'low' | 'medium' | 'high' | 'critical';
  flags: RiskFlag[];
  recommendation: 'proceed' | 'caution' | 'avoid';
  explanation: string;
}

// Offer types
export interface Offer {
  id: string;
  amount: number;
  type: 'initial' | 'counter' | 'final';
  status: 'draft' | 'sent' | 'accepted' | 'rejected' | 'expired';
  message?: string;
  sentAt?: Date;
  respondedAt?: Date;
  expiresAt?: Date;
}

// Message types
export interface Message {
  id: string;
  type: 'incoming' | 'outgoing';
  content: string;
  timestamp: Date;
  status: 'draft' | 'sent' | 'delivered' | 'read';
  isAutomated: boolean;
  templateId?: string;
  metadata?: {
    platform: Platform;
    threadId?: string;
    inReplyTo?: string;
  };
}

// Component value for FMV calculations
export interface ComponentValue {
  component: string;
  value: number;
  confidence: number;
  source: string;
  fmv?: number; // For compatibility
  adjustments?: Array<{
    type: string;
    amount: number;
    reason: string;
  }>;
}

// Settings types - moved to avoid conflicts
export interface ExtensionSettings {
  version: string;
  location: {
    zipCode: string;
    maxDistance: number;
    preferredMeetingSpots: string[];
  };
  pricing: {
    targetROI: number;
    minDealValue: number;
    includeShipping: boolean;
    includeFees: boolean;
  };
  notifications: {
    enabled: boolean;
    priceDrops: boolean;
    newListings: boolean;
    messages: boolean;
    dealUpdates: boolean;
  };
  automation: {
    autoRefresh: boolean;
    refreshInterval: number;
    autoAnalyze: boolean;
    bulkScanLimit: number;
  };
  privacy: {
    anonymizeData: boolean;
    shareAnalytics: boolean;
    backupEnabled: boolean;
    backupInterval: number;
  };
  advanced: {
    mlPredictions: boolean;
    ocrProcessing: boolean;
    competitorTracking: boolean;
    experimentalFeatures: boolean;
  };
}

// Analytics event
export interface AnalyticsEvent {
  id: string;
  name: string;
  category: string;
  timestamp: Date;
  properties?: Record<string, any>;
  actorUserId?: string;
}

// Comp stats
export interface CompStats {
  n: number;
  mean: number;
  median: number;
  p25: number;
  p75: number;
  stdDev: number;
  priceRange?: { min: number; max: number };
}

// OCR types
export interface OCRResult {
  text: string;
  confidence: number;
  regions: Array<{
    text: string;
    confidence: number;
    boundingBox: {
      x: number;
      y: number;
      width: number;
      height: number;
    };
  }>;
  metadata: {
    processingTime: number;
    imageSize: { width: number; height: number };
    language: string;
  };
}

export interface ExtractedSpecs {
  cpu?: string;
  gpu?: string;
  ram?: string;
  storage?: string[];
  motherboard?: string;
  psu?: string;
  confidence: number;
  rawText: string;
}

// Export all types
export type {
  Platform as PlatformType,
  Listing as ListingType,
  Deal as DealType,
  ExtensionSettings as SettingsType
};