/**
 * Negotiation Script Management System
 * Provides templates and strategies for price negotiations
 */

import { Deal, Listing } from '../types';

export interface NegotiationScript {
  id: string;
  name: string;
  category: 'opening' | 'counter' | 'closing' | 'objection' | 'walkaway';
  scenario: string;
  targetDiscount: number; // Percentage
  script: string;
  variables: ScriptVariable[];
  tactics: NegotiationTactic[];
  successRate?: number;
  usageCount: number;
  tags: string[];
  createdAt: Date;
  updatedAt: Date;
}

export interface ScriptVariable {
  name: string;
  description: string;
  type: 'price' | 'percentage' | 'text' | 'reason';
  required: boolean;
  defaultValue?: any;
}

export interface NegotiationTactic {
  name: string;
  description: string;
  whenToUse: string;
  example: string;
  riskLevel: 'low' | 'medium' | 'high';
}

export interface NegotiationContext {
  listing: Listing;
  currentOffer?: number;
  targetPrice: number;
  marketAverage: number;
  sellerBehavior?: 'flexible' | 'firm' | 'desperate' | 'unknown';
  previousMessages?: string[];
}

export interface NegotiationRecommendation {
  script: NegotiationScript;
  confidence: number;
  reasoning: string[];
  variables: Record<string, any>;
  alternativeScripts: NegotiationScript[];
  tactics: NegotiationTactic[];
}

export class NegotiationScriptManager {
  private scripts: Map<string, NegotiationScript> = new Map();
  private readonly STORAGE_KEY = 'negotiationScripts';
  
  constructor() {
    this.loadScripts();
    this.initializeDefaultScripts();
  }

  /**
   * Initialize default negotiation scripts
   */
  private initializeDefaultScripts(): void {
    const defaults: Partial<NegotiationScript>[] = [
      // Opening scripts
      {
        name: 'Research-Based Opening',
        category: 'opening',
        scenario: 'First contact with data-backed offer',
        targetDiscount: 15,
        script: `Hi {{sellerName}},

I'm interested in your {{listingTitle}}. I've done some research on similar systems:

{{marketComparison}}

Based on this data and considering {{ageReason}}, would you consider {{offerPrice}}? 

I'm a serious buyer with cash ready and can pick up {{availability}}.

Thanks,
{{buyerName}}`,
        variables: [
          { name: 'sellerName', description: 'Seller name', type: 'text', required: true },
          { name: 'listingTitle', description: 'Listing title', type: 'text', required: true },
          { name: 'marketComparison', description: 'Market data points', type: 'text', required: true },
          { name: 'ageReason', description: 'Age/condition factor', type: 'text', required: true },
          { name: 'offerPrice', description: 'Your offer', type: 'price', required: true },
          { name: 'availability', description: 'Your availability', type: 'text', required: true, defaultValue: 'today or tomorrow' },
          { name: 'buyerName', description: 'Your name', type: 'text', required: true }
        ],
        tactics: [
          {
            name: 'Data Anchoring',
            description: 'Use market data to anchor price expectations',
            whenToUse: 'When you have solid comparable data',
            example: 'Similar RTX 3070 systems are selling for $800-900',
            riskLevel: 'low'
          }
        ],
        tags: ['data-driven', 'professional']
      },

      // Bundle discount opening
      {
        name: 'Bundle Discount Request',
        category: 'opening',
        scenario: 'Seller has multiple items',
        targetDiscount: 20,
        script: `Hi {{sellerName}},

I see you're selling {{listingTitle}} and also have {{otherItems}} listed.

I'm interested in buying multiple items from you. If I take {{bundleItems}}, would you do {{bundlePrice}} for everything?

This saves us both time and you get a guaranteed sale for multiple items today.

Let me know!
{{buyerName}}`,
        variables: [
          { name: 'sellerName', description: 'Seller name', type: 'text', required: true },
          { name: 'listingTitle', description: 'Main listing', type: 'text', required: true },
          { name: 'otherItems', description: 'Other items they have', type: 'text', required: true },
          { name: 'bundleItems', description: 'Items you want', type: 'text', required: true },
          { name: 'bundlePrice', description: 'Bundle offer', type: 'price', required: true },
          { name: 'buyerName', description: 'Your name', type: 'text', required: true }
        ],
        tactics: [
          {
            name: 'Bundle Psychology',
            description: 'Sellers often prefer one transaction over multiple',
            whenToUse: 'When seller has 3+ related items',
            example: 'Offer 80% of total asking for 3+ items',
            riskLevel: 'low'
          }
        ],
        tags: ['bundle', 'multi-item']
      },

      // Counter offer scripts
      {
        name: 'Split the Difference',
        category: 'counter',
        scenario: 'After initial rejection, find middle ground',
        targetDiscount: 10,
        script: `I understand you're looking for {{theirPrice}}, but that's above my budget.

How about we meet in the middle at {{middlePrice}}? That's fair for both of us:
- You get {{percentAboveOffer}}% more than my initial offer
- I stay within a reasonable budget
- We both save time going back and forth

I can pick up {{timeframe}} with cash. What do you say?`,
        variables: [
          { name: 'theirPrice', description: 'Their counter', type: 'price', required: true },
          { name: 'middlePrice', description: 'Middle ground price', type: 'price', required: true },
          { name: 'percentAboveOffer', description: 'Percent increase', type: 'percentage', required: true },
          { name: 'timeframe', description: 'Pickup timeframe', type: 'text', required: true, defaultValue: 'today' }
        ],
        tactics: [
          {
            name: 'Compromise Frame',
            description: 'Frame as mutual compromise',
            whenToUse: 'When seller shows some flexibility',
            example: 'We both give a little to make the deal work',
            riskLevel: 'low'
          }
        ],
        tags: ['compromise', 'middle-ground']
      },

      // Condition-based negotiation
      {
        name: 'Condition Adjustment',
        category: 'counter',
        scenario: 'Issues found during inspection',
        targetDiscount: 25,
        script: `Hi {{sellerName}},

I just noticed {{issueDescription}}. This would cost approximately {{repairCost}} to fix/replace.

Given this, would you consider {{adjustedOffer}}? This accounts for:
- {{repairCost}} for the {{issueType}}
- The time and effort needed to address it

I'm still interested and can work with it, but the price needs to reflect the actual condition.

Thanks for understanding,
{{buyerName}}`,
        variables: [
          { name: 'sellerName', description: 'Seller name', type: 'text', required: true },
          { name: 'issueDescription', description: 'Issue found', type: 'text', required: true },
          { name: 'repairCost', description: 'Estimated repair cost', type: 'price', required: true },
          { name: 'issueType', description: 'Type of issue', type: 'text', required: true },
          { name: 'adjustedOffer', description: 'New offer', type: 'price', required: true },
          { name: 'buyerName', description: 'Your name', type: 'text', required: true }
        ],
        tactics: [
          {
            name: 'Repair Cost Deduction',
            description: 'Deduct actual repair costs from offer',
            whenToUse: 'When you find undisclosed issues',
            example: 'Dead pixels = monitor replacement cost',
            riskLevel: 'medium'
          }
        ],
        tags: ['condition', 'inspection', 'adjustment']
      },

      // Objection handling
      {
        name: 'Handle "Too Low" Objection',
        category: 'objection',
        scenario: 'Seller says offer is too low',
        targetDiscount: 12,
        script: `I understand it seems low, but let me explain my reasoning:

1. {{reason1}}
2. {{reason2}}
3. {{reason3}}

I'm not trying to lowball you - this is based on {{basis}}. 

If you have recent sales data showing higher prices for similar items, I'm happy to look at it and adjust my offer accordingly.

What would you consider a fair price given these factors?`,
        variables: [
          { name: 'reason1', description: 'First reason', type: 'text', required: true },
          { name: 'reason2', description: 'Second reason', type: 'text', required: true },
          { name: 'reason3', description: 'Third reason', type: 'text', required: true },
          { name: 'basis', description: 'Basis for offer', type: 'text', required: true, defaultValue: 'current market data' }
        ],
        tactics: [
          {
            name: 'Reasoning Chain',
            description: 'Provide logical reasoning for your offer',
            whenToUse: 'When accused of lowballing',
            example: 'List 3 specific, verifiable reasons',
            riskLevel: 'low'
          },
          {
            name: 'Data Request',
            description: 'Ask for their data to counter yours',
            whenToUse: 'Put burden of proof on seller',
            example: 'Show me recent sales at your price',
            riskLevel: 'medium'
          }
        ],
        tags: ['objection', 'reasoning']
      },

      // Urgency/closing scripts
      {
        name: 'Today Only Offer',
        category: 'closing',
        scenario: 'Create urgency for decision',
        targetDiscount: 10,
        script: `{{sellerName}},

I can do {{finalOffer}} cash if we can meet today. I have:
- Cash in hand
- Transportation ready
- {{additionalIncentive}}

I'm looking at other options this evening, so this offer is only good for today. 

If you're ready to sell now, let's make it happen. Otherwise, no worries and good luck with your sale!

{{buyerName}}`,
        variables: [
          { name: 'sellerName', description: 'Seller name', type: 'text', required: true },
          { name: 'finalOffer', description: 'Final offer amount', type: 'price', required: true },
          { name: 'additionalIncentive', description: 'Extra incentive', type: 'text', required: true, defaultValue: 'Flexible on pickup time' },
          { name: 'buyerName', description: 'Your name', type: 'text', required: true }
        ],
        tactics: [
          {
            name: 'Time Pressure',
            description: 'Create legitimate urgency',
            whenToUse: 'When you have alternatives',
            example: 'Mention other options without bluffing',
            riskLevel: 'medium'
          }
        ],
        tags: ['urgency', 'closing', 'today']
      },

      // Walk away script
      {
        name: 'Professional Walk Away',
        category: 'walkaway',
        scenario: 'Seller won\'t budge on price',
        targetDiscount: 0,
        script: `{{sellerName}},

I appreciate your time, but it looks like we're too far apart on price.

My maximum budget for this is {{maxBudget}}, and I understand you need {{theirPrice}}.

If your situation changes or you decide you can work with my budget, feel free to reach out. Otherwise, I wish you the best of luck with your sale!

Thanks again,
{{buyerName}}`,
        variables: [
          { name: 'sellerName', description: 'Seller name', type: 'text', required: true },
          { name: 'maxBudget', description: 'Your max budget', type: 'price', required: true },
          { name: 'theirPrice', description: 'Their firm price', type: 'price', required: true },
          { name: 'buyerName', description: 'Your name', type: 'text', required: true }
        ],
        tactics: [
          {
            name: 'Door Open',
            description: 'Leave possibility for seller to reconsider',
            whenToUse: 'When walking away from negotiation',
            example: 'They often come back with better offer',
            riskLevel: 'low'
          }
        ],
        tags: ['walkaway', 'professional']
      }
    ];

    defaults.forEach(script => {
      if (script.name) {
        this.createScript(script as Omit<NegotiationScript, 'id' | 'createdAt' | 'updatedAt' | 'usageCount'>);
      }
    });
  }

  /**
   * Get negotiation recommendation based on context
   */
  getRecommendation(context: NegotiationContext): NegotiationRecommendation {
    const scripts = Array.from(this.scripts.values());
    const recommendations: Array<{ script: NegotiationScript; score: number; reasoning: string[] }> = [];

    // Score each script based on context
    scripts.forEach(script => {
      let score = 0;
      const reasoning: string[] = [];

      // Category matching
      if (!context.currentOffer && script.category === 'opening') {
        score += 30;
        reasoning.push('Suitable for initial contact');
      } else if (context.currentOffer && script.category === 'counter') {
        score += 30;
        reasoning.push('Appropriate for counter-offer');
      }

      // Discount alignment
      const askingPrice = context.listing.price;
      const targetPrice = context.targetPrice;
      const desiredDiscount = ((askingPrice - targetPrice) / askingPrice) * 100;
      const discountDiff = Math.abs(desiredDiscount - script.targetDiscount);
      
      if (discountDiff < 5) {
        score += 20;
        reasoning.push(`Discount target aligns well (${script.targetDiscount}% vs ${desiredDiscount.toFixed(0)}%)`);
      }

      // Market conditions
      if (context.marketAverage < askingPrice * 0.9 && script.tags.includes('data-driven')) {
        score += 15;
        reasoning.push('Market data supports negotiation');
      }

      // Seller behavior matching
      if (context.sellerBehavior === 'flexible' && script.category === 'counter') {
        score += 10;
        reasoning.push('Seller seems open to negotiation');
      } else if (context.sellerBehavior === 'firm' && script.category === 'walkaway') {
        score += 10;
        reasoning.push('Seller appears inflexible');
      }

      // Success rate
      if (script.successRate && script.successRate > 0.7) {
        score += 10;
        reasoning.push(`High success rate (${(script.successRate * 100).toFixed(0)}%)`);
      }

      recommendations.push({ script, score, reasoning });
    });

    // Sort by score
    recommendations.sort((a, b) => b.score - a.score);
    const best = recommendations[0];

    // Generate variables
    const variables = this.generateVariables(best.script, context);

    // Get applicable tactics
    const tactics = this.getApplicableTactics(context, best.script);

    return {
      script: best.script,
      confidence: Math.min(best.score / 100, 0.95),
      reasoning: best.reasoning,
      variables,
      alternativeScripts: recommendations.slice(1, 4).map(r => r.script),
      tactics
    };
  }

  /**
   * Generate variables for a script based on context
   */
  private generateVariables(
    script: NegotiationScript,
    context: NegotiationContext
  ): Record<string, any> {
    const variables: Record<string, any> = {};

    script.variables.forEach(variable => {
      switch (variable.name) {
        case 'sellerName':
          variables[variable.name] = context.listing.seller.name;
          break;
        
        case 'listingTitle':
          variables[variable.name] = context.listing.title;
          break;
        
        case 'offerPrice':
          variables[variable.name] = context.currentOffer || context.targetPrice;
          break;
        
        case 'marketComparison':
          variables[variable.name] = this.generateMarketComparison(context);
          break;
        
        case 'ageReason':
          variables[variable.name] = this.generateAgeReason(context);
          break;
        
        case 'theirPrice':
          variables[variable.name] = context.listing.price;
          break;
        
        case 'middlePrice':
          const their = context.listing.price;
          const our = context.currentOffer || context.targetPrice;
          variables[variable.name] = Math.round((their + our) / 2);
          break;
        
        case 'percentAboveOffer':
          const middle = Math.round((context.listing.price + (context.currentOffer || context.targetPrice)) / 2);
          const percent = ((middle - (context.currentOffer || context.targetPrice)) / (context.currentOffer || context.targetPrice)) * 100;
          variables[variable.name] = percent.toFixed(0);
          break;
        
        default:
          variables[variable.name] = variable.defaultValue || '';
      }
    });

    return variables;
  }

  /**
   * Generate market comparison text
   */
  private generateMarketComparison(context: NegotiationContext): string {
    const comparisons: string[] = [];
    
    if (context.marketAverage) {
      const diff = ((context.listing.price - context.marketAverage) / context.marketAverage) * 100;
      comparisons.push(`• Average price for similar systems: $${context.marketAverage} (yours is ${diff.toFixed(0)}% higher)`);
    }

    if (context.listing.components?.gpu) {
      comparisons.push(`• ${context.listing.components.gpu.model} systems typically sell for $${context.marketAverage - 100} - $${context.marketAverage + 100}`);
    }

    comparisons.push(`• Checking eBay sold listings shows similar specs at $${context.marketAverage - 50} - $${context.marketAverage}`);

    return comparisons.join('\n');
  }

  /**
   * Generate age/condition reasoning
   */
  private generateAgeReason(context: NegotiationContext): string {
    const reasons: string[] = [];
    
    // Component age
    if (context.listing.components?.cpu) {
      const cpu = context.listing.components.cpu.model;
      if (cpu.includes('10th') || cpu.includes('3000')) {
        reasons.push('3+ generation old components');
      } else if (cpu.includes('11th') || cpu.includes('5000')) {
        reasons.push('2 generation old components');
      }
    }

    // Condition
    if (context.listing.condition === 'used') {
      reasons.push('used condition');
    } else if (context.listing.condition === 'refurbished') {
      reasons.push('refurbished status');
    }

    return reasons.join(' and ') || 'current market conditions';
  }

  /**
   * Get applicable tactics for the situation
   */
  private getApplicableTactics(
    context: NegotiationContext,
    script: NegotiationScript
  ): NegotiationTactic[] {
    const tactics: NegotiationTactic[] = [...script.tactics];

    // Add context-specific tactics
    if (context.sellerBehavior === 'desperate') {
      tactics.push({
        name: 'Quick Close',
        description: 'Seller needs fast sale - emphasize immediate payment',
        whenToUse: 'When seller mentions urgency',
        example: 'I can pick up within 2 hours with cash',
        riskLevel: 'low'
      });
    }

    if (context.listing.price > context.marketAverage * 1.2) {
      tactics.push({
        name: 'Reality Check',
        description: 'Politely show overpricing with data',
        whenToUse: 'When significantly overpriced',
        example: 'Share screenshot of similar sold listings',
        riskLevel: 'medium'
      });
    }

    return tactics;
  }

  /**
   * Create a new negotiation script
   */
  async createScript(
    script: Omit<NegotiationScript, 'id' | 'createdAt' | 'updatedAt' | 'usageCount'>
  ): Promise<NegotiationScript> {
    const newScript: NegotiationScript = {
      ...script,
      id: `script_${Date.now()}`,
      usageCount: 0,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    this.scripts.set(newScript.id, newScript);
    await this.saveScripts();

    return newScript;
  }

  /**
   * Update script with usage data
   */
  async recordUsage(scriptId: string, wasSuccessful: boolean): Promise<void> {
    const script = this.scripts.get(scriptId);
    if (!script) return;

    script.usageCount++;
    
    // Update success rate
    if (script.successRate === undefined) {
      script.successRate = wasSuccessful ? 1 : 0;
    } else {
      // Running average
      const totalUses = script.usageCount;
      const successCount = Math.round(script.successRate * (totalUses - 1)) + (wasSuccessful ? 1 : 0);
      script.successRate = successCount / totalUses;
    }

    script.updatedAt = new Date();
    await this.saveScripts();
  }

  /**
   * Search scripts by criteria
   */
  searchScripts(criteria: {
    category?: NegotiationScript['category'];
    tags?: string[];
    minSuccessRate?: number;
    searchTerm?: string;
  }): NegotiationScript[] {
    let results = Array.from(this.scripts.values());

    if (criteria.category) {
      results = results.filter(s => s.category === criteria.category);
    }

    if (criteria.tags && criteria.tags.length > 0) {
      results = results.filter(s => 
        criteria.tags!.some(tag => s.tags.includes(tag))
      );
    }

    if (criteria.minSuccessRate !== undefined) {
      results = results.filter(s => 
        s.successRate !== undefined && s.successRate >= criteria.minSuccessRate
      );
    }

    if (criteria.searchTerm) {
      const term = criteria.searchTerm.toLowerCase();
      results = results.filter(s => 
        s.name.toLowerCase().includes(term) ||
        s.script.toLowerCase().includes(term) ||
        s.scenario.toLowerCase().includes(term)
      );
    }

    return results;
  }

  /**
   * Get script by ID
   */
  getScript(id: string): NegotiationScript | undefined {
    return this.scripts.get(id);
  }

  /**
   * Get all scripts
   */
  getAllScripts(): NegotiationScript[] {
    return Array.from(this.scripts.values());
  }

  /**
   * Delete a script
   */
  async deleteScript(id: string): Promise<void> {
    this.scripts.delete(id);
    await this.saveScripts();
  }

  /**
   * Load scripts from storage
   */
  private async loadScripts(): Promise<void> {
    try {
      const { negotiationScripts } = await chrome.storage.local.get(this.STORAGE_KEY);
      if (negotiationScripts) {
        negotiationScripts.forEach((script: NegotiationScript) => {
          this.scripts.set(script.id, {
            ...script,
            createdAt: new Date(script.createdAt),
            updatedAt: new Date(script.updatedAt)
          });
        });
      }
    } catch (error) {
      console.error('Failed to load negotiation scripts:', error);
    }
  }

  /**
   * Save scripts to storage
   */
  private async saveScripts(): Promise<void> {
    const scriptsArray = Array.from(this.scripts.values());
    await chrome.storage.local.set({ [this.STORAGE_KEY]: scriptsArray });
  }

  /**
   * Export scripts for backup
   */
  exportScripts(): string {
    const scripts = Array.from(this.scripts.values());
    return JSON.stringify(scripts, null, 2);
  }

  /**
   * Import scripts from backup
   */
  async importScripts(jsonData: string): Promise<void> {
    try {
      const scripts = JSON.parse(jsonData);
      scripts.forEach((script: NegotiationScript) => {
        this.scripts.set(script.id, {
          ...script,
          createdAt: new Date(script.createdAt),
          updatedAt: new Date(script.updatedAt)
        });
      });
      await this.saveScripts();
    } catch (error) {
      throw new Error('Invalid script data format');
    }
  }
}

// Export singleton instance
export const negotiationScriptManager = new NegotiationScriptManager();