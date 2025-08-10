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
}

export interface GPUComponent {
  brand: 'NVIDIA' | 'AMD' | 'Intel';
  model: string;
  vram: number;
  architecture?: string;
  tdp?: number;
  displayOutputs?: string[];
  nvlinkSli?: boolean;
}

export interface RAMComponent {
  capacity: number; // GB
  speed: number; // MHz
  type: 'DDR3' | 'DDR4' | 'DDR5';
  modules: number;
  ecc?: boolean;
  rgb?: boolean;
  latency?: string;
}

export interface StorageComponent {
  type: 'ssd' | 'hdd' | 'nvme' | 'm.2';
  capacity: number; // GB
  brand?: string;
  model?: string;
  readSpeed?: number;
  writeSpeed?: number;
  formFactor?: string;
  interface?: string;
}

export interface MotherboardComponent {
  brand?: string;
  model?: string;
  chipset?: string;
  socket?: string;
  formFactor?: 'ATX' | 'Micro-ATX' | 'Mini-ITX' | 'E-ATX';
  ramSlots?: number;
  maxRam?: number;
  m2Slots?: number;
  pciSlots?: number;
}

export interface PSUComponent {
  wattage: number;
  efficiency?: '80+ Bronze' | '80+ Silver' | '80+ Gold' | '80+ Platinum' | '80+ Titanium';
  modular?: 'Non-modular' | 'Semi-modular' | 'Fully-modular';
  brand?: string;
  model?: string;
}

export interface CaseComponent {
  brand?: string;
  model?: string;
  formFactor?: string;
  color?: string;
  sidePanel?: 'Windowed' | 'Solid' | 'Tempered Glass' | 'Mesh';
  rgb?: boolean;
}

export interface CoolerComponent {
  type: 'air' | 'aio' | 'custom';
  brand?: string;
  model?: string;
  radiatorSize?: number; // mm for AIO
  tdpRating?: number;
  rgb?: boolean;
}

// Listing types
export interface ListingImage {
  url: string;
  width?: number;
  height?: number;
  primary: boolean;
}

export interface Listing {
  id: string;
  url: string;
  platform: Platform;
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
  };
  condition?: 'new' | 'like-new' | 'good' | 'fair' | 'parts';
  listingDate: Date;
  lastUpdated: Date;
  viewCount?: number;
  savedCount?: number;
  isLocalPickupOnly?: boolean;
  acceptsOffers?: boolean;
  isFirmPrice?: boolean;
  specs?: {
    components: {
      cpu?: CPUComponent;
      gpu?: GPUComponent;
      ram?: RAMComponent[];
      storage?: StorageComponent[];
      motherboard?: MotherboardComponent;
      psu?: PSUComponent;
      case?: CaseComponent;
      cooler?: CoolerComponent;
    };
    peripherals?: string[];
    os?: string;
  };
}

// Deal types
export interface Deal {
  id: string;
  listingId: string;
  platform: Platform;
  status: 'watching' | 'evaluating' | 'negotiating' | 'scheduled' | 'purchased' | 'testing' | 'listing' | 'sold' | 'completed' | 'cancelled';
  stage?: string; // For workflow compatibility
  
  // Pricing
  askingPrice: number;
  purchasePrice?: number;
  salePrice?: number;
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
  fmv?: number; // Added for compatibility
  adjustments?: Array<{
    type: string;
    amount: number;
    reason: string;
  }>;
}

// Settings types
export interface Settings {
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

// Export all types
export type {
  Platform as PlatformType,
  Listing as ListingType,
  Deal as DealType,
  Settings as SettingsType
};