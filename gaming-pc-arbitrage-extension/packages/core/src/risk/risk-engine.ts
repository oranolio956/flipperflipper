/**
 * Risk Assessment Engine
 * Evaluates risks for deals including fraud, stolen goods, technical issues
 */

import { Listing, Deal } from '../types';
import { Settings } from '../settings/schema';

export interface RiskFlag {
  type: 'fraud' | 'stolen' | 'technical' | 'financial' | 'safety';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  mitigation?: string;
  autoBlock: boolean;
}

export interface RiskAssessment {
  overallScore: number; // 0-10
  flags: RiskFlag[];
  recommendation: 'proceed' | 'caution' | 'avoid';
  requiresUserConfirmation: boolean;
  suggestedQuestions: string[];
}

export class RiskEngine {
  private settings: Settings;
  
  constructor(settings: Settings) {
    this.settings = settings;
  }
  
  /**
   * Comprehensive risk assessment for a listing
   */
  assessListing(listing: Listing): RiskAssessment {
    const flags: RiskFlag[] = [];
    let score = 0;
    
    // Price-based risks
    const priceFlags = this.assessPriceRisks(listing);
    flags.push(...priceFlags);
    score += priceFlags.reduce((sum, f) => this.flagToScore(f), 0);
    
    // Seller-based risks
    const sellerFlags = this.assessSellerRisks(listing);
    flags.push(...sellerFlags);
    score += sellerFlags.reduce((sum, f) => this.flagToScore(f), 0);
    
    // Content-based risks
    const contentFlags = this.assessContentRisks(listing);
    flags.push(...contentFlags);
    score += contentFlags.reduce((sum, f) => this.flagToScore(f), 0);
    
    // Technical risks
    const technicalFlags = this.assessTechnicalRisks(listing);
    flags.push(...technicalFlags);
    score += technicalFlags.reduce((sum, f) => this.flagToScore(f), 0);
    
    // Safety risks
    const safetyFlags = this.assessSafetyRisks(listing);
    flags.push(...safetyFlags);
    score += safetyFlags.reduce((sum, f) => this.flagToScore(f), 0);
    
    // Generate recommendations
    const recommendation = this.generateRecommendation(score, flags);
    const requiresConfirmation = flags.some(f => f.severity === 'high' || f.severity === 'critical');
    const questions = this.generateQuestions(flags, listing);
    
    return {
      overallScore: Math.min(score, 10),
      flags,
      recommendation,
      requiresUserConfirmation: requiresConfirmation,
      suggestedQuestions: questions,
    };
  }
  
  /**
   * Price-based risk assessment
   */
  private assessPriceRisks(listing: Listing): RiskFlag[] {
    const flags: RiskFlag[] = [];
    const fmv = listing.analysis.fmv;
    const askingPrice = listing.price;
    
    // Too good to be true
    if (fmv > 0 && askingPrice < fmv * 0.5) {
      flags.push({
        type: 'fraud',
        severity: 'high',
        description: 'Price is less than 50% of estimated market value',
        mitigation: 'Request detailed photos and power-on video',
        autoBlock: false,
      });
    } else if (fmv > 0 && askingPrice < fmv * 0.7) {
      flags.push({
        type: 'fraud',
        severity: 'medium',
        description: 'Price is significantly below market value',
        mitigation: 'Ask about reason for low price',
        autoBlock: false,
      });
    }
    
    // High-value components at low price
    if (listing.components.gpu) {
      const gpu = listing.components.gpu;
      if (gpu.model.includes('3080') || gpu.model.includes('4070')) {
        if (askingPrice < 500) {
          flags.push({
            type: 'stolen',
            severity: 'high',
            description: 'High-end GPU at unusually low price',
            mitigation: 'Request serial number photo and proof of purchase',
            autoBlock: false,
          });
        }
      }
    }
    
    // Free or near-free listings
    if (askingPrice < 50) {
      flags.push({
        type: 'fraud',
        severity: 'medium',
        description: 'Extremely low price may indicate scam or broken item',
        mitigation: 'Confirm actual condition and reason for price',
        autoBlock: false,
      });
    }
    
    return flags;
  }
  
  /**
   * Seller-based risk assessment
   */
  private assessSellerRisks(listing: Listing): RiskFlag[] {
    const flags: RiskFlag[] = [];
    const seller = listing.seller;
    
    // New seller
    if (!seller.memberSince || 
        (seller.memberSince && this.daysSince(seller.memberSince) < this.settings.risk_tolerance.min_seller_age_days)) {
      flags.push({
        type: 'fraud',
        severity: 'medium',
        description: 'Seller account is very new',
        mitigation: 'Meet in safe public location only',
        autoBlock: false,
      });
    }
    
    // Unverified seller
    if (seller.verified === false) {
      flags.push({
        type: 'fraud',
        severity: 'low',
        description: 'Seller is not verified on platform',
        mitigation: 'Extra verification of item condition',
        autoBlock: false,
      });
    }
    
    // Blacklisted seller
    if (this.settings.risk_tolerance.blacklisted_sellers.includes(seller.id)) {
      flags.push({
        type: 'fraud',
        severity: 'critical',
        description: 'Seller is on your blacklist',
        autoBlock: true,
      });
    }
    
    return flags;
  }
  
  /**
   * Content-based risk assessment
   */
  private assessContentRisks(listing: Listing): RiskFlag[] {
    const flags: RiskFlag[] = [];
    const description = listing.description.toLowerCase();
    const title = listing.title.toLowerCase();
    
    // Shipping only (no local pickup)
    if ((description.includes('shipping only') || description.includes('mail only')) &&
        !description.includes('local pickup')) {
      flags.push({
        type: 'fraud',
        severity: 'high',
        description: 'Seller refuses local pickup - common scam pattern',
        mitigation: 'Avoid unless seller agrees to local meetup',
        autoBlock: false,
      });
    }
    
    // Urgency indicators
    const urgencyPhrases = ['must sell today', 'urgent sale', 'moving tomorrow', 'need gone asap'];
    if (urgencyPhrases.some(phrase => description.includes(phrase))) {
      flags.push({
        type: 'stolen',
        severity: 'medium',
        description: 'Urgent sale language may indicate stolen goods',
        mitigation: 'Ask for proof of ownership',
        autoBlock: false,
      });
    }
    
    // Missing information
    if (description.length < 50) {
      flags.push({
        type: 'fraud',
        severity: 'low',
        description: 'Very brief description lacks detail',
        mitigation: 'Request detailed specs and condition info',
        autoBlock: false,
      });
    }
    
    // No photos or stock photos only
    if (listing.images.length === 0) {
      flags.push({
        type: 'fraud',
        severity: 'high',
        description: 'No photos provided',
        mitigation: 'Request multiple photos before proceeding',
        autoBlock: false,
      });
    } else if (listing.images.length === 1) {
      flags.push({
        type: 'fraud',
        severity: 'medium',
        description: 'Only one photo provided',
        mitigation: 'Request additional photos from different angles',
        autoBlock: false,
      });
    }
    
    // No power-on demonstration
    if (this.settings.risk_tolerance.require_power_on_video &&
        !listing.images.some(img => img.url.includes('powered') || img.url.includes('running'))) {
      flags.push({
        type: 'technical',
        severity: 'medium',
        description: 'No power-on demonstration in photos',
        mitigation: 'Request video of system running',
        autoBlock: false,
      });
    }
    
    return flags;
  }
  
  /**
   * Technical risk assessment
   */
  private assessTechnicalRisks(listing: Listing): RiskFlag[] {
    const flags: RiskFlag[] = [];
    const description = listing.description.toLowerCase();
    
    // Mining GPU
    if (listing.components.gpu && 
        (description.includes('mining') || description.includes('mined'))) {
      flags.push({
        type: 'technical',
        severity: 'high',
        description: 'GPU used for cryptocurrency mining',
        mitigation: 'Negotiate lower price and plan for potential early failure',
        autoBlock: false,
      });
    }
    
    // Water cooling risks
    if (listing.components.cooling?.type === 'custom-loop' ||
        listing.components.cooling?.type === 'aio') {
      if (this.settings.risk_tolerance.avoid_water_cooling) {
        flags.push({
          type: 'technical',
          severity: 'medium',
          description: 'Water cooling requires maintenance and has leak risk',
          mitigation: 'Check for leaks and maintenance history',
          autoBlock: false,
        });
      }
    }
    
    // Old components
    if (listing.condition.ageEstimate && listing.condition.ageEstimate > 60) {
      flags.push({
        type: 'technical',
        severity: 'medium',
        description: 'System is over 5 years old',
        mitigation: 'Factor in higher failure risk and shorter resale window',
        autoBlock: false,
      });
    }
    
    // Overclocking
    if (description.includes('overclocked') || description.includes('oc')) {
      flags.push({
        type: 'technical',
        severity: 'medium',
        description: 'Components have been overclocked',
        mitigation: 'Test stability thoroughly and check temperatures',
        autoBlock: false,
      });
    }
    
    // No-name PSU
    if (listing.components.psu && !listing.components.psu.brand) {
      flags.push({
        type: 'technical',
        severity: 'high',
        description: 'Generic/unknown PSU brand - fire and component damage risk',
        mitigation: 'Budget for PSU replacement',
        autoBlock: false,
      });
    }
    
    return flags;
  }
  
  /**
   * Safety risk assessment
   */
  private assessSafetyRisks(listing: Listing): RiskFlag[] {
    const flags: RiskFlag[] = [];
    const description = listing.description.toLowerCase();
    
    // Unsafe meeting location
    if (description.includes('my home') || description.includes('my house') ||
        description.includes('my apartment')) {
      flags.push({
        type: 'safety',
        severity: 'high',
        description: 'Seller wants to meet at private residence',
        mitigation: 'Insist on public location like police station parking lot',
        autoBlock: false,
      });
    }
    
    // Night meetup only
    if (description.includes('after 9pm') || description.includes('night only')) {
      flags.push({
        type: 'safety',
        severity: 'medium',
        description: 'Seller only available at night',
        mitigation: 'Prefer daytime meetup or well-lit public area',
        autoBlock: false,
      });
    }
    
    // Remote location
    if (listing.location.distance && listing.location.distance > this.settings.geography.max_drive_minutes) {
      flags.push({
        type: 'safety',
        severity: 'low',
        description: 'Location is beyond your configured safe distance',
        mitigation: 'Consider if profit justifies the drive',
        autoBlock: false,
      });
    }
    
    // Cash safety for high-value items
    if (listing.price > this.settings.risk_tolerance.max_unit_investment) {
      flags.push({
        type: 'financial',
        severity: 'medium',
        description: 'High cash amount increases robbery risk',
        mitigation: 'Bring a friend and meet at police station',
        autoBlock: false,
      });
    }
    
    return flags;
  }
  
  /**
   * Convert flag to risk score
   */
  private flagToScore(flag: RiskFlag): number {
    switch (flag.severity) {
      case 'low': return 1;
      case 'medium': return 2;
      case 'high': return 3;
      case 'critical': return 4;
    }
  }
  
  /**
   * Generate overall recommendation
   */
  private generateRecommendation(score: number, flags: RiskFlag[]): RiskAssessment['recommendation'] {
    // Any critical flags = avoid
    if (flags.some(f => f.severity === 'critical')) {
      return 'avoid';
    }
    
    // Score-based recommendation
    if (score >= this.settings.risk_tolerance.max_risk_score) {
      return 'avoid';
    } else if (score >= 5) {
      return 'caution';
    }
    
    return 'proceed';
  }
  
  /**
   * Generate questions to ask seller
   */
  private generateQuestions(flags: RiskFlag[], listing: Listing): string[] {
    const questions: string[] = [];
    
    // Always ask these
    questions.push('Can you provide a short video of the computer running?');
    questions.push('Are you the original owner? Do you have the receipt?');
    
    // Flag-specific questions
    if (flags.some(f => f.description.includes('mining'))) {
      questions.push('How long was the GPU used for mining? What were the temperatures?');
    }
    
    if (flags.some(f => f.description.includes('water cooling'))) {
      questions.push('When was the water cooling last maintained? Any leak history?');
    }
    
    if (flags.some(f => f.type === 'fraud')) {
      questions.push('Why are you selling at this price?');
      questions.push('Can we meet at a police station for the exchange?');
    }
    
    if (!listing.components.psu?.brand) {
      questions.push('What brand and model is the power supply?');
    }
    
    if (listing.components.storage?.some(s => s.type === 'HDD')) {
      questions.push('Can you run CrystalDiskInfo and share the SMART data?');
    }
    
    return questions;
  }
  
  /**
   * Calculate days since date
   */
  private daysSince(date: Date): number {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    return Math.floor(diffMs / (1000 * 60 * 60 * 24));
  }
}