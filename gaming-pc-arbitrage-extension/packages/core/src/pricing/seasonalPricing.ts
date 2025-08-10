/**
 * Seasonal Pricing Module
 * Implements time-based pricing adjustments based on seasonal patterns
 */

import { SeasonalPattern } from '../types';

export interface SeasonalPricingRule {
  id: string;
  name: string;
  enabled: boolean;
  category: 'all' | 'gpu' | 'cpu' | 'full-system' | 'peripherals';
  timeframe: TimeFrame;
  adjustment: PriceAdjustment;
  conditions?: RuleCondition[];
  priority: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface TimeFrame {
  type: 'date-range' | 'recurring' | 'event-based';
  startDate?: Date;
  endDate?: Date;
  recurringPattern?: RecurringPattern;
  event?: MarketEvent;
}

export interface RecurringPattern {
  frequency: 'daily' | 'weekly' | 'monthly' | 'yearly';
  interval: number;
  daysOfWeek?: number[]; // 0-6 (Sunday-Saturday)
  monthsOfYear?: number[]; // 0-11 (January-December)
  weekOfMonth?: number; // 1-5
}

export interface MarketEvent {
  name: string;
  type: 'holiday' | 'sales-event' | 'product-launch' | 'custom';
  date?: Date;
  duration?: number; // days
}

export interface PriceAdjustment {
  type: 'percentage' | 'fixed' | 'multiplier';
  value: number;
  direction: 'increase' | 'decrease';
  capPercentage?: number; // Maximum adjustment
}

export interface RuleCondition {
  field: 'price' | 'category' | 'brand' | 'age' | 'demand';
  operator: 'equals' | 'contains' | 'greater' | 'less' | 'between';
  value: any;
}

export interface SeasonalAnalysis {
  currentSeason: string;
  activePricingRules: SeasonalPricingRule[];
  suggestedAdjustment: number;
  historicalPatterns: SeasonalPattern[];
  nextEventImpact: {
    event: MarketEvent;
    daysUntil: number;
    expectedImpact: number;
  } | null;
}

export class SeasonalPricingManager {
  private rules: Map<string, SeasonalPricingRule> = new Map();
  private historicalData: SeasonalPattern[] = [];
  private marketEvents: MarketEvent[] = [];
  
  constructor() {
    this.initializeDefaultRules();
    this.loadHistoricalData();
  }

  /**
   * Initialize default seasonal pricing rules
   */
  private initializeDefaultRules(): void {
    const defaultRules: Partial<SeasonalPricingRule>[] = [
      // Black Friday / Cyber Monday
      {
        name: 'Black Friday GPU Surge',
        category: 'gpu',
        enabled: true,
        timeframe: {
          type: 'recurring',
          recurringPattern: {
            frequency: 'yearly',
            interval: 1,
            monthsOfYear: [10], // November
            weekOfMonth: 4
          }
        },
        adjustment: {
          type: 'percentage',
          value: 15,
          direction: 'increase',
          capPercentage: 25
        },
        conditions: [
          { field: 'category', operator: 'equals', value: 'gpu' },
          { field: 'price', operator: 'greater', value: 500 }
        ],
        priority: 10
      },

      // Holiday Season
      {
        name: 'Holiday Gaming PC Demand',
        category: 'full-system',
        enabled: true,
        timeframe: {
          type: 'date-range',
          startDate: new Date(new Date().getFullYear(), 11, 1), // Dec 1
          endDate: new Date(new Date().getFullYear(), 11, 25)  // Dec 25
        },
        adjustment: {
          type: 'percentage',
          value: 20,
          direction: 'increase'
        },
        conditions: [
          { field: 'category', operator: 'equals', value: 'gaming-pc' }
        ],
        priority: 9
      },

      // Back to School
      {
        name: 'Back to School Budget PCs',
        category: 'full-system',
        enabled: true,
        timeframe: {
          type: 'recurring',
          recurringPattern: {
            frequency: 'yearly',
            interval: 1,
            monthsOfYear: [7, 8] // August, September
          }
        },
        adjustment: {
          type: 'percentage',
          value: 10,
          direction: 'decrease'
        },
        conditions: [
          { field: 'price', operator: 'less', value: 800 }
        ],
        priority: 8
      },

      // GPU Mining Crash Pattern
      {
        name: 'Crypto Market Correlation',
        category: 'gpu',
        enabled: true,
        timeframe: {
          type: 'event-based',
          event: {
            name: 'Crypto Bear Market',
            type: 'custom',
            duration: 90
          }
        },
        adjustment: {
          type: 'percentage',
          value: 30,
          direction: 'decrease'
        },
        conditions: [
          { field: 'category', operator: 'equals', value: 'gpu' },
          { field: 'demand', operator: 'less', value: 0.7 }
        ],
        priority: 7
      },

      // New Product Launch Impact
      {
        name: 'Previous Gen Depreciation',
        category: 'all',
        enabled: true,
        timeframe: {
          type: 'event-based',
          event: {
            name: 'New Generation Launch',
            type: 'product-launch',
            duration: 30
          }
        },
        adjustment: {
          type: 'percentage',
          value: 15,
          direction: 'decrease'
        },
        conditions: [
          { field: 'age', operator: 'greater', value: 365 } // Older than 1 year
        ],
        priority: 6
      },

      // Summer Gaming Season
      {
        name: 'Summer Gaming Demand',
        category: 'all',
        enabled: true,
        timeframe: {
          type: 'recurring',
          recurringPattern: {
            frequency: 'yearly',
            interval: 1,
            monthsOfYear: [5, 6, 7] // June, July, August
          }
        },
        adjustment: {
          type: 'percentage',
          value: 8,
          direction: 'increase'
        },
        priority: 5
      },

      // Tax Return Season
      {
        name: 'Tax Return Spending',
        category: 'full-system',
        enabled: true,
        timeframe: {
          type: 'recurring',
          recurringPattern: {
            frequency: 'yearly',
            interval: 1,
            monthsOfYear: [2, 3] // March, April
          }
        },
        adjustment: {
          type: 'percentage',
          value: 12,
          direction: 'increase'
        },
        conditions: [
          { field: 'price', operator: 'between', value: [1000, 2000] }
        ],
        priority: 5
      }
    ];

    defaultRules.forEach(rule => {
      this.createRule(rule as Omit<SeasonalPricingRule, 'id' | 'createdAt' | 'updatedAt'>);
    });
  }

  /**
   * Create a new seasonal pricing rule
   */
  createRule(rule: Omit<SeasonalPricingRule, 'id' | 'createdAt' | 'updatedAt'>): SeasonalPricingRule {
    const newRule: SeasonalPricingRule = {
      ...rule,
      id: `rule_${Date.now()}`,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    this.rules.set(newRule.id, newRule);
    this.saveRules();

    return newRule;
  }

  /**
   * Calculate price adjustment for an item
   */
  calculateAdjustment(
    basePrice: number,
    category: string,
    additionalContext?: {
      brand?: string;
      age?: number;
      demand?: number;
    }
  ): { adjustedPrice: number; appliedRules: SeasonalPricingRule[]; totalAdjustment: number } {
    const activeRules = this.getActiveRules();
    const applicableRules: SeasonalPricingRule[] = [];
    let cumulativeAdjustment = 0;

    // Sort by priority (higher priority first)
    activeRules.sort((a, b) => b.priority - a.priority);

    for (const rule of activeRules) {
      if (this.isRuleApplicable(rule, basePrice, category, additionalContext)) {
        applicableRules.push(rule);
        
        const adjustment = this.applyAdjustment(
          basePrice + cumulativeAdjustment,
          rule.adjustment
        );
        
        cumulativeAdjustment += adjustment - (basePrice + cumulativeAdjustment);
      }
    }

    const adjustedPrice = Math.max(0, basePrice + cumulativeAdjustment);

    return {
      adjustedPrice: Math.round(adjustedPrice * 100) / 100,
      appliedRules: applicableRules,
      totalAdjustment: cumulativeAdjustment
    };
  }

  /**
   * Get active rules for current date/time
   */
  getActiveRules(): SeasonalPricingRule[] {
    const now = new Date();
    return Array.from(this.rules.values()).filter(rule => {
      if (!rule.enabled) return false;
      return this.isTimeFrameActive(rule.timeframe, now);
    });
  }

  /**
   * Check if timeframe is currently active
   */
  private isTimeFrameActive(timeframe: TimeFrame, date: Date): boolean {
    switch (timeframe.type) {
      case 'date-range':
        if (!timeframe.startDate || !timeframe.endDate) return false;
        return date >= timeframe.startDate && date <= timeframe.endDate;

      case 'recurring':
        if (!timeframe.recurringPattern) return false;
        return this.isRecurringPatternActive(timeframe.recurringPattern, date);

      case 'event-based':
        if (!timeframe.event) return false;
        return this.isEventActive(timeframe.event, date);

      default:
        return false;
    }
  }

  /**
   * Check if recurring pattern is active
   */
  private isRecurringPatternActive(pattern: RecurringPattern, date: Date): boolean {
    // Check day of week
    if (pattern.daysOfWeek && pattern.daysOfWeek.length > 0) {
      if (!pattern.daysOfWeek.includes(date.getDay())) return false;
    }

    // Check month of year
    if (pattern.monthsOfYear && pattern.monthsOfYear.length > 0) {
      if (!pattern.monthsOfYear.includes(date.getMonth())) return false;
    }

    // Check week of month
    if (pattern.weekOfMonth !== undefined) {
      const weekOfMonth = Math.ceil(date.getDate() / 7);
      if (weekOfMonth !== pattern.weekOfMonth) return false;
    }

    return true;
  }

  /**
   * Check if market event is active
   */
  private isEventActive(event: MarketEvent, date: Date): boolean {
    // Check predefined events
    const eventDates = this.getEventDates(event);
    
    for (const eventDate of eventDates) {
      const duration = event.duration || 1;
      const endDate = new Date(eventDate);
      endDate.setDate(endDate.getDate() + duration);
      
      if (date >= eventDate && date <= endDate) {
        return true;
      }
    }

    return false;
  }

  /**
   * Get dates for market events
   */
  private getEventDates(event: MarketEvent): Date[] {
    const currentYear = new Date().getFullYear();
    const dates: Date[] = [];

    switch (event.name) {
      case 'Black Friday':
        // Fourth Thursday of November + 1 day
        const thanksgiving = this.getNthWeekdayOfMonth(currentYear, 10, 4, 4);
        dates.push(new Date(thanksgiving.getTime() + 24 * 60 * 60 * 1000));
        break;

      case 'Cyber Monday':
        // Monday after Thanksgiving
        const blackFriday = this.getNthWeekdayOfMonth(currentYear, 10, 4, 4);
        dates.push(new Date(blackFriday.getTime() + 4 * 24 * 60 * 60 * 1000));
        break;

      case 'Christmas':
        dates.push(new Date(currentYear, 11, 25));
        break;

      case 'Back to School':
        dates.push(new Date(currentYear, 7, 15)); // Mid-August
        break;

      default:
        if (event.date) {
          dates.push(event.date);
        }
    }

    return dates;
  }

  /**
   * Get Nth weekday of a month
   */
  private getNthWeekdayOfMonth(year: number, month: number, n: number, weekday: number): Date {
    const firstDay = new Date(year, month, 1);
    const firstWeekday = firstDay.getDay();
    
    let date = 1 + ((weekday - firstWeekday + 7) % 7);
    date += (n - 1) * 7;
    
    return new Date(year, month, date);
  }

  /**
   * Check if rule conditions are met
   */
  private isRuleApplicable(
    rule: SeasonalPricingRule,
    price: number,
    category: string,
    context?: any
  ): boolean {
    // Check category
    if (rule.category !== 'all' && rule.category !== category) {
      return false;
    }

    // Check conditions
    if (!rule.conditions || rule.conditions.length === 0) {
      return true;
    }

    return rule.conditions.every(condition => {
      const value = condition.field === 'price' ? price :
                   condition.field === 'category' ? category :
                   context?.[condition.field];

      switch (condition.operator) {
        case 'equals':
          return value === condition.value;
        case 'contains':
          return String(value).includes(condition.value);
        case 'greater':
          return value > condition.value;
        case 'less':
          return value < condition.value;
        case 'between':
          return value >= condition.value[0] && value <= condition.value[1];
        default:
          return false;
      }
    });
  }

  /**
   * Apply price adjustment
   */
  private applyAdjustment(price: number, adjustment: PriceAdjustment): number {
    let adjustedPrice = price;

    switch (adjustment.type) {
      case 'percentage':
        const percentChange = price * (adjustment.value / 100);
        adjustedPrice = adjustment.direction === 'increase' 
          ? price + percentChange 
          : price - percentChange;
        break;

      case 'fixed':
        adjustedPrice = adjustment.direction === 'increase'
          ? price + adjustment.value
          : price - adjustment.value;
        break;

      case 'multiplier':
        adjustedPrice = adjustment.direction === 'increase'
          ? price * adjustment.value
          : price / adjustment.value;
        break;
    }

    // Apply cap if specified
    if (adjustment.capPercentage) {
      const maxChange = price * (adjustment.capPercentage / 100);
      const actualChange = Math.abs(adjustedPrice - price);
      
      if (actualChange > maxChange) {
        adjustedPrice = adjustment.direction === 'increase'
          ? price + maxChange
          : price - maxChange;
      }
    }

    return Math.max(0, adjustedPrice);
  }

  /**
   * Analyze seasonal patterns
   */
  analyzeSeasonalTrends(category?: string): SeasonalAnalysis {
    const now = new Date();
    const season = this.getCurrentSeason();
    const activeRules = this.getActiveRules();
    
    // Filter by category if specified
    const relevantRules = category 
      ? activeRules.filter(r => r.category === 'all' || r.category === category)
      : activeRules;

    // Calculate suggested adjustment
    const samplePrice = 1000;
    const { totalAdjustment } = this.calculateAdjustment(samplePrice, category || 'all');
    const suggestedAdjustment = (totalAdjustment / samplePrice) * 100;

    // Find next upcoming event
    const nextEvent = this.getNextMarketEvent();

    return {
      currentSeason: season,
      activePricingRules: relevantRules,
      suggestedAdjustment,
      historicalPatterns: this.getHistoricalPatterns(category),
      nextEventImpact: nextEvent ? {
        event: nextEvent.event,
        daysUntil: nextEvent.daysUntil,
        expectedImpact: this.estimateEventImpact(nextEvent.event)
      } : null
    };
  }

  /**
   * Get current season
   */
  private getCurrentSeason(): string {
    const month = new Date().getMonth();
    
    if (month >= 2 && month <= 4) return 'Spring';
    if (month >= 5 && month <= 7) return 'Summer';
    if (month >= 8 && month <= 10) return 'Fall';
    return 'Winter';
  }

  /**
   * Get next market event
   */
  private getNextMarketEvent(): { event: MarketEvent; daysUntil: number } | null {
    const now = new Date();
    const upcomingEvents: Array<{ event: MarketEvent; date: Date }> = [];

    // Check all rules for event-based timeframes
    this.rules.forEach(rule => {
      if (rule.timeframe.type === 'event-based' && rule.timeframe.event) {
        const eventDates = this.getEventDates(rule.timeframe.event);
        eventDates.forEach(date => {
          if (date > now) {
            upcomingEvents.push({ event: rule.timeframe.event, date });
          }
        });
      }
    });

    // Add standard market events
    const standardEvents: MarketEvent[] = [
      { name: 'Black Friday', type: 'sales-event' },
      { name: 'Cyber Monday', type: 'sales-event' },
      { name: 'Christmas', type: 'holiday' },
      { name: 'Back to School', type: 'sales-event' }
    ];

    standardEvents.forEach(event => {
      const dates = this.getEventDates(event);
      dates.forEach(date => {
        if (date > now) {
          upcomingEvents.push({ event, date });
        }
      });
    });

    // Sort by date and return nearest
    upcomingEvents.sort((a, b) => a.date.getTime() - b.date.getTime());
    
    if (upcomingEvents.length > 0) {
      const next = upcomingEvents[0];
      const daysUntil = Math.ceil((next.date.getTime() - now.getTime()) / (24 * 60 * 60 * 1000));
      return { event: next.event, daysUntil };
    }

    return null;
  }

  /**
   * Estimate impact of an event
   */
  private estimateEventImpact(event: MarketEvent): number {
    // Based on historical data and event type
    const impactMap: Record<string, number> = {
      'Black Friday': 25,
      'Cyber Monday': 20,
      'Christmas': 15,
      'Back to School': 10,
      'New Generation Launch': -20,
      'Crypto Bear Market': -30
    };

    return impactMap[event.name] || 0;
  }

  /**
   * Get historical patterns
   */
  private getHistoricalPatterns(category?: string): SeasonalPattern[] {
    return this.historicalData.filter(pattern => 
      !category || pattern.category === category
    );
  }

  /**
   * Update rule
   */
  updateRule(id: string, updates: Partial<SeasonalPricingRule>): void {
    const rule = this.rules.get(id);
    if (!rule) throw new Error('Rule not found');

    Object.assign(rule, updates);
    rule.updatedAt = new Date();
    
    this.saveRules();
  }

  /**
   * Delete rule
   */
  deleteRule(id: string): void {
    this.rules.delete(id);
    this.saveRules();
  }

  /**
   * Load historical data
   */
  private async loadHistoricalData(): Promise<void> {
    const { seasonalHistory } = await chrome.storage.local.get('seasonalHistory');
    if (seasonalHistory) {
      this.historicalData = seasonalHistory;
    }
  }

  /**
   * Save rules
   */
  private async saveRules(): Promise<void> {
    const rulesArray = Array.from(this.rules.values());
    await chrome.storage.local.set({ seasonalRules: rulesArray });
  }

  /**
   * Get all rules
   */
  getAllRules(): SeasonalPricingRule[] {
    return Array.from(this.rules.values());
  }
}

// Export singleton instance
export const seasonalPricingManager = new SeasonalPricingManager();