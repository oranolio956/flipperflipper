/**
 * ROI (Return on Investment) Calculator
 * Calculates profit potential, margins, and ROI for arbitrage deals
 */

import Decimal from 'decimal.js';
import { Listing, Deal } from '../types';
import { Settings } from '../settings/schema';
import { FMVResult } from './fmv-calculator';

export interface ROIResult {
  // Core metrics
  askingPrice: number;
  fmv: number;
  estimatedResale: number;
  
  // Costs
  purchasePrice: number;
  transportCost: number;
  refurbCost: number;
  listingFees: number;
  taxes: number;
  holdingCost: number;
  totalInvestment: number;
  
  // Profits
  grossProfit: number;
  netProfit: number;
  profitMargin: number;
  roi: number;
  
  // Strategic metrics
  dealScore: number;
  recommendedOffer: number;
  walkAwayPrice: number;
  breakEvenPrice: number;
  
  // Time factors
  estimatedDaysToSell: number;
  dailyROI: number;
  
  // Risk assessment
  riskAdjustedROI: number;
  confidence: number;
}

export interface OfferStrategy {
  aggressive: number;
  fair: number;
  conservative: number;
  recommended: number;
  rationale: string;
}

export class ROICalculator {
  private settings: Settings;
  
  constructor(settings: Settings) {
    this.settings = settings;
  }
  
  /**
   * Calculate ROI for a listing
   */
  calculate(
    listing: Listing,
    fmvResult: FMVResult,
    negotiatedPrice?: number
  ): ROIResult {
    const d = (n: number) => new Decimal(n);
    
    // Prices
    const askingPrice = listing.price;
    const fmv = fmvResult.total;
    
    // Determine purchase price (negotiated or asking)
    const purchasePrice = negotiatedPrice || askingPrice;
    
    // Calculate costs
    const transportCost = this.calculateTransportCost(listing);
    const refurbCost = this.calculateRefurbCost(listing, fmvResult);
    const listingFees = this.calculateListingFees(fmv);
    const taxes = this.calculateTaxes(purchasePrice);
    const holdingCost = this.calculateHoldingCost(fmv);
    
    // Total investment
    const totalInvestment = d(purchasePrice)
      .add(transportCost)
      .add(refurbCost)
      .add(taxes)
      .toNumber();
    
    // Estimated resale price (with market strategy)
    const estimatedResale = this.calculateResalePrice(fmv, listing);
    
    // Gross profit (before fees and holding costs)
    const grossProfit = d(estimatedResale).sub(totalInvestment).toNumber();
    
    // Net profit (after all costs)
    const netProfit = d(grossProfit)
      .sub(listingFees)
      .sub(holdingCost)
      .toNumber();
    
    // Profit margin
    const profitMargin = estimatedResale > 0 
      ? (netProfit / estimatedResale) * 100 
      : 0;
    
    // ROI
    const roi = totalInvestment > 0 
      ? (netProfit / totalInvestment) * 100 
      : 0;
    
    // Strategic prices
    const walkAwayPrice = this.calculateWalkAwayPrice(
      fmv,
      transportCost,
      refurbCost,
      listingFees,
      taxes
    );
    
    const breakEvenPrice = d(estimatedResale)
      .sub(transportCost)
      .sub(refurbCost)
      .sub(listingFees)
      .sub(taxes)
      .sub(holdingCost)
      .toNumber();
    
    // Recommended offer
    const recommendedOffer = this.calculateRecommendedOffer(
      askingPrice,
      fmv,
      walkAwayPrice,
      listing
    );
    
    // Time factors
    const estimatedDaysToSell = this.estimateDaysToSell(listing, estimatedResale);
    const dailyROI = estimatedDaysToSell > 0 ? roi / estimatedDaysToSell : 0;
    
    // Deal scoring
    const dealScore = this.calculateDealScore(
      roi,
      profitMargin,
      netProfit,
      listing.risks.score,
      fmvResult.confidence,
      dailyROI
    );
    
    // Risk adjustment
    const riskAdjustedROI = this.calculateRiskAdjustedROI(
      roi,
      listing.risks.score,
      fmvResult.confidence
    );
    
    return {
      askingPrice,
      fmv,
      estimatedResale,
      purchasePrice,
      transportCost,
      refurbCost,
      listingFees,
      taxes,
      holdingCost,
      totalInvestment,
      grossProfit,
      netProfit,
      profitMargin,
      roi,
      dealScore,
      recommendedOffer,
      walkAwayPrice,
      breakEvenPrice,
      estimatedDaysToSell,
      dailyROI,
      riskAdjustedROI,
      confidence: fmvResult.confidence,
    };
  }
  
  /**
   * Calculate offer strategy with multiple options
   */
  calculateOfferStrategy(listing: Listing, roiResult: ROIResult): OfferStrategy {
    const askingPrice = listing.price;
    const fmv = roiResult.fmv;
    const walkAway = roiResult.walkAwayPrice;
    
    // Aggressive: Target 50% margin
    const aggressive = Math.min(
      fmv * 0.6,
      askingPrice * 0.7,
      walkAway
    );
    
    // Fair: Target 35% margin (settings default)
    const fair = Math.min(
      fmv * 0.7,
      askingPrice * 0.8,
      walkAway * 1.1
    );
    
    // Conservative: Target 25% margin
    const conservative = Math.min(
      fmv * 0.75,
      askingPrice * 0.85,
      walkAway * 1.2
    );
    
    // Determine recommended strategy
    let recommended = fair;
    let rationale = 'Standard fair offer based on market value';
    
    // Adjust based on market conditions
    if (listing.risks.score > 7) {
      recommended = aggressive;
      rationale = 'High risk detected - aggressive offer recommended';
    } else if (listing.metadata.priceHistory.length > 1) {
      // Price has been reduced
      const priceDrops = listing.metadata.priceHistory.filter(
        (p, i) => i > 0 && p.price < listing.metadata.priceHistory[i - 1].price
      );
      if (priceDrops.length > 0) {
        recommended = aggressive;
        rationale = 'Price reductions indicate seller motivation';
      }
    } else if (roiResult.confidence > 0.85 && roiResult.roi > 50) {
      recommended = fair;
      rationale = 'High confidence in strong ROI - fair offer appropriate';
    } else if (listing.components.gpu && listing.components.gpu.model.includes('4070')) {
      recommended = conservative;
      rationale = 'High-demand GPU - conservative offer to improve acceptance';
    }
    
    // Round to nearest $10
    return {
      aggressive: Math.round(aggressive / 10) * 10,
      fair: Math.round(fair / 10) * 10,
      conservative: Math.round(conservative / 10) * 10,
      recommended: Math.round(recommended / 10) * 10,
      rationale,
    };
  }
  
  /**
   * Calculate transport costs based on distance
   */
  private calculateTransportCost(listing: Listing): number {
    const distance = listing.location.distance || this.settings.geography.radius_miles / 2;
    const gasPerMile = this.settings.geography.gas_cost_per_mile;
    
    // Round trip
    const gasCost = distance * 2 * gasPerMile;
    
    // Add time cost if configured
    const driveTimeMinutes = distance * 2; // Assume 1 mile = 1 minute average
    const timeCost = (driveTimeMinutes / 60) * this.settings.financial.labor_rate_per_hour;
    
    return gasCost + timeCost;
  }
  
  /**
   * Calculate estimated refurbishment costs
   */
  private calculateRefurbCost(listing: Listing, fmvResult: FMVResult): number {
    let refurbCost = 0;
    
    // Basic cleaning/testing for all
    refurbCost += this.settings.parts_bin.cleaning_supplies;
    
    // Thermal paste if older than 2 years or thermal issues mentioned
    if (listing.condition.ageEstimate && listing.condition.ageEstimate > 24) {
      refurbCost += this.settings.parts_bin.thermal_paste;
    }
    if (listing.condition.issues.some(i => i.issue.includes('thermal'))) {
      refurbCost += this.settings.parts_bin.thermal_paste;
    }
    
    // Missing components
    if (!listing.components.storage || listing.components.storage.length === 0) {
      refurbCost += this.settings.parts_bin.sata_ssd_256gb;
    }
    
    // Case fan if cooling issues
    if (listing.condition.issues.some(i => i.component === 'cooling')) {
      refurbCost += this.settings.parts_bin.case_fan_120mm;
    }
    
    // RAM upgrade if only 8GB
    if (listing.components.ram && 
        listing.components.ram.reduce((sum, r) => sum + r.size, 0) < 16) {
      refurbCost += this.settings.parts_bin.ddr4_8gb;
    }
    
    // Add labor time
    const laborHours = 1.5; // Average refurb time
    refurbCost += laborHours * this.settings.financial.labor_rate_per_hour;
    
    return refurbCost;
  }
  
  /**
   * Calculate marketplace/platform fees
   */
  private calculateListingFees(resalePrice: number): number {
    return resalePrice * (this.settings.financial.marketplace_fee_percent / 100);
  }
  
  /**
   * Calculate taxes on purchase
   */
  private calculateTaxes(purchasePrice: number): number {
    return purchasePrice * (this.settings.financial.tax_rate_percent / 100);
  }
  
  /**
   * Calculate holding costs based on expected time to sell
   */
  private calculateHoldingCost(fmv: number): number {
    const estimatedDays = this.estimateDaysToSellFromFMV(fmv);
    return estimatedDays * this.settings.financial.holding_cost_per_day;
  }
  
  /**
   * Calculate optimal resale price
   */
  private calculateResalePrice(fmv: number, listing: Listing): number {
    // Start with FMV
    let resalePrice = fmv;
    
    // Apply markup strategy
    const markupFactor = 1 + (this.settings.pricing.markup_percentage / 100);
    resalePrice *= markupFactor;
    
    // Adjust for quick sale if configured
    if (this.settings.pricing.negotiation_strategy === 'aggressive') {
      resalePrice *= 0.95; // 5% below market for quick sale
    } else if (this.settings.pricing.negotiation_strategy === 'conservative') {
      resalePrice *= 1.05; // 5% above market for patient sale
    }
    
    // Round to nice number
    if (resalePrice > 1000) {
      resalePrice = Math.round(resalePrice / 50) * 50; // Round to $50
    } else if (resalePrice > 500) {
      resalePrice = Math.round(resalePrice / 25) * 25; // Round to $25
    } else {
      resalePrice = Math.round(resalePrice / 10) * 10; // Round to $10
    }
    
    return resalePrice;
  }
  
  /**
   * Calculate walk-away price (maximum profitable purchase price)
   */
  private calculateWalkAwayPrice(
    fmv: number,
    transportCost: number,
    refurbCost: number,
    listingFees: number,
    taxes: number
  ): number {
    // Work backwards from minimum required profit
    const minProfit = this.settings.financial.min_profit_dollars;
    const minMargin = this.settings.financial.target_margin_percent / 100;
    
    // Expected resale price
    const resalePrice = this.calculateResalePrice(fmv, {} as Listing);
    
    // Required net after all costs
    const requiredNet = Math.max(
      minProfit,
      resalePrice * minMargin
    );
    
    // Walk away price = resale - required profit - all costs
    const walkAway = resalePrice - requiredNet - transportCost - 
                    refurbCost - listingFees - this.calculateHoldingCost(fmv);
    
    // Account for taxes (walk away is pre-tax)
    const walkAwayPreTax = walkAway / (1 + this.settings.financial.tax_rate_percent / 100);
    
    return Math.max(walkAwayPreTax, 0);
  }
  
  /**
   * Calculate recommended offer price
   */
  private calculateRecommendedOffer(
    askingPrice: number,
    fmv: number,
    walkAwayPrice: number,
    listing: Listing
  ): number {
    // Start with percentage of FMV based on strategy
    let offerPrice = fmv * 0.7; // Default 70% of FMV
    
    if (this.settings.pricing.negotiation_strategy === 'aggressive') {
      offerPrice = fmv * 0.65;
    } else if (this.settings.pricing.negotiation_strategy === 'conservative') {
      offerPrice = fmv * 0.75;
    }
    
    // Never exceed walk-away price
    offerPrice = Math.min(offerPrice, walkAwayPrice);
    
    // Consider asking price
    if (askingPrice < fmv * 0.8) {
      // Already well-priced, offer closer to asking
      offerPrice = Math.min(askingPrice * 0.9, walkAwayPrice);
    }
    
    // Adjust for risk
    if (listing.risks.score > 5) {
      offerPrice *= 0.9; // 10% reduction for high risk
    }
    
    // Round to nearest $10
    return Math.round(offerPrice / 10) * 10;
  }
  
  /**
   * Estimate days to sell based on components and price
   */
  private estimateDaysToSell(listing: Listing, resalePrice: number): number {
    let baseDays = 7; // Default estimate
    
    // Adjust for GPU desirability
    if (listing.components.gpu) {
      const hotGPUs = ['3060', '3070', '3080', '4060', '4070'];
      if (hotGPUs.some(model => listing.components.gpu!.model.includes(model))) {
        baseDays -= 2;
      }
    }
    
    // Adjust for completeness
    if (listing.components.cpu && listing.components.gpu && 
        listing.components.ram && listing.components.storage) {
      baseDays -= 1; // Complete systems sell faster
    }
    
    // Adjust for price point
    if (resalePrice < 500) baseDays -= 1;
    else if (resalePrice > 1500) baseDays += 3;
    
    // Seasonal adjustment
    const month = new Date().getMonth();
    if (month >= 10 || month <= 1) {
      baseDays -= 1; // Holiday season sells faster
    } else if (month >= 5 && month <= 7) {
      baseDays += 2; // Summer slower
    }
    
    return Math.max(baseDays, 3); // Minimum 3 days
  }
  
  /**
   * Simple FMV-based days estimate
   */
  private estimateDaysToSellFromFMV(fmv: number): number {
    if (fmv < 500) return 5;
    if (fmv < 1000) return 7;
    if (fmv < 1500) return 10;
    return 14;
  }
  
  /**
   * Calculate overall deal score (0-100)
   */
  private calculateDealScore(
    roi: number,
    margin: number,
    profit: number,
    riskScore: number,
    confidence: number,
    dailyROI: number
  ): number {
    let score = 50; // Base score
    
    // ROI contribution (up to 30 points)
    if (roi > 50) score += 30;
    else if (roi > 35) score += 20;
    else if (roi > 20) score += 10;
    else if (roi < 10) score -= 10;
    
    // Margin contribution (up to 20 points)
    if (margin > 40) score += 20;
    else if (margin > 30) score += 15;
    else if (margin > 20) score += 10;
    else if (margin < 15) score -= 10;
    
    // Profit contribution (up to 20 points)
    if (profit > 300) score += 20;
    else if (profit > 200) score += 15;
    else if (profit > 150) score += 10;
    else if (profit < 100) score -= 10;
    
    // Risk penalty (up to -20 points)
    score -= riskScore * 2;
    
    // Confidence bonus (up to 10 points)
    score += confidence * 10;
    
    // Daily ROI bonus (up to 10 points)
    if (dailyROI > 5) score += 10;
    else if (dailyROI > 3) score += 5;
    
    // Ensure score is between 0 and 100
    return Math.max(0, Math.min(100, score));
  }
  
  /**
   * Calculate risk-adjusted ROI
   */
  private calculateRiskAdjustedROI(
    baseROI: number,
    riskScore: number,
    confidence: number
  ): number {
    // Apply risk discount
    const riskFactor = 1 - (riskScore / 20); // Max 50% discount at risk score 10
    
    // Apply confidence factor
    const confidenceFactor = 0.5 + (confidence * 0.5); // 50-100% based on confidence
    
    return baseROI * riskFactor * confidenceFactor;
  }
  
  /**
   * Calculate metrics for a completed deal
   */
  calculateActualROI(deal: Deal): Partial<ROIResult> {
    if (!deal.financials.actualResale || !deal.financials.purchasePrice) {
      return {};
    }
    
    const actualRevenue = deal.financials.actualResale;
    const totalCosts = deal.financials.totalInvestment;
    const actualProfit = deal.financials.actualProfit || (actualRevenue - totalCosts);
    
    const actualROI = totalCosts > 0 ? (actualProfit / totalCosts) * 100 : 0;
    const actualMargin = actualRevenue > 0 ? (actualProfit / actualRevenue) * 100 : 0;
    
    return {
      roi: actualROI,
      profitMargin: actualMargin,
      netProfit: actualProfit,
    };
  }
}