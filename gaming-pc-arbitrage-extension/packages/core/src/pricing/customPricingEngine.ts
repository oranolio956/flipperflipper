/**
 * Custom Pricing Formula Engine
 * Allows users to create and manage custom pricing formulas with variables,
 * functions, conditions, and real-time evaluation
 */

import { Listing, Deal, ListingComponents } from '../types';

export interface PricingFormula {
  id: string;
  name: string;
  description: string;
  formula: string; // The actual formula expression
  variables: FormulaVariable[];
  category: 'buying' | 'selling' | 'both';
  isActive: boolean;
  testCases?: TestCase[];
  performance?: FormulaPerformance;
  createdAt: Date;
  updatedAt: Date;
}

export interface FormulaVariable {
  name: string;
  type: 'number' | 'percentage' | 'boolean' | 'component' | 'market' | 'condition';
  source: 'listing' | 'market' | 'user' | 'computed';
  defaultValue?: any;
  description: string;
}

export interface TestCase {
  id: string;
  inputs: Record<string, any>;
  expectedOutput: number;
  actualOutput?: number;
  passed?: boolean;
}

export interface FormulaPerformance {
  totalEvaluations: number;
  avgAccuracy: number; // Compared to actual sales
  profitImpact: number;
  lastUsed: Date;
}

export interface FormulaContext {
  listing?: Listing;
  deal?: Deal;
  marketData?: MarketData;
  userVariables?: Record<string, any>;
}

export interface MarketData {
  avgPrice: number;
  medianPrice: number;
  priceRange: { min: number; max: number };
  demandScore: number;
  seasonalMultiplier: number;
  competitorCount: number;
}

export interface EvaluationResult {
  price: number;
  confidence: number;
  breakdown: CalculationBreakdown[];
  warnings?: string[];
  suggestions?: string[];
}

export interface CalculationBreakdown {
  step: string;
  expression: string;
  value: number;
  description?: string;
}

export class CustomPricingEngine {
  private formulas: Map<string, PricingFormula> = new Map();
  private builtInFunctions: Map<string, Function> = new Map();
  private marketDataCache: Map<string, MarketData> = new Map();

  constructor() {
    this.initializeBuiltInFunctions();
    this.initializeDefaultFormulas();
    this.loadData();
  }

  private initializeBuiltInFunctions(): void {
    // Math functions
    this.builtInFunctions.set('min', Math.min);
    this.builtInFunctions.set('max', Math.max);
    this.builtInFunctions.set('round', Math.round);
    this.builtInFunctions.set('floor', Math.floor);
    this.builtInFunctions.set('ceil', Math.ceil);
    this.builtInFunctions.set('abs', Math.abs);
    this.builtInFunctions.set('sqrt', Math.sqrt);
    this.builtInFunctions.set('pow', Math.pow);

    // Custom functions
    this.builtInFunctions.set('percentage', (value: number, percent: number) => value * (percent / 100));
    this.builtInFunctions.set('markup', (cost: number, percent: number) => cost * (1 + percent / 100));
    this.builtInFunctions.set('discount', (price: number, percent: number) => price * (1 - percent / 100));
    this.builtInFunctions.set('clamp', (value: number, min: number, max: number) => Math.max(min, Math.min(max, value)));
    
    // Component value functions
    this.builtInFunctions.set('componentValue', (components: ListingComponents, type: string) => {
      const componentMap: Record<string, number> = {
        cpu: components.cpu?.value || 0,
        gpu: components.gpu?.value || 0,
        ram: components.ram?.value || 0,
        storage: components.storage?.value || 0,
        motherboard: components.motherboard?.value || 0,
        psu: components.psu?.value || 0,
        case: components.case?.value || 0
      };
      return componentMap[type.toLowerCase()] || 0;
    });

    this.builtInFunctions.set('totalComponentValue', (components: ListingComponents) => {
      let total = 0;
      if (components.cpu?.value) total += components.cpu.value;
      if (components.gpu?.value) total += components.gpu.value;
      if (components.ram?.value) total += components.ram.value;
      if (components.storage?.value) total += components.storage.value;
      if (components.motherboard?.value) total += components.motherboard.value;
      if (components.psu?.value) total += components.psu.value;
      if (components.case?.value) total += components.case.value;
      return total;
    });

    // Condition functions
    this.builtInFunctions.set('if', (condition: boolean, trueValue: any, falseValue: any) => 
      condition ? trueValue : falseValue
    );
    
    this.builtInFunctions.set('switch', (value: any, ...cases: any[]) => {
      for (let i = 0; i < cases.length - 1; i += 2) {
        if (value === cases[i]) return cases[i + 1];
      }
      return cases.length % 2 === 1 ? cases[cases.length - 1] : 0;
    });

    // Market functions
    this.builtInFunctions.set('marketAdjustment', (basePrice: number, demandScore: number) => {
      const adjustment = (demandScore - 50) / 100; // -50% to +50% adjustment
      return basePrice * (1 + adjustment);
    });

    this.builtInFunctions.set('competitionFactor', (competitorCount: number) => {
      return Math.max(0.7, 1 - (competitorCount * 0.05)); // 5% reduction per competitor, min 70%
    });
  }

  private initializeDefaultFormulas(): void {
    // Component-based pricing formula
    const componentFormula: PricingFormula = {
      id: 'component-based',
      name: 'Component-Based Pricing',
      description: 'Calculates price based on individual component values with market adjustment',
      formula: `
        let basePrice = totalComponentValue(components) * 0.85;
        let marketAdjusted = marketAdjustment(basePrice, market.demandScore);
        let finalPrice = round(marketAdjusted * competitionFactor(market.competitorCount));
        return clamp(finalPrice, market.priceRange.min, market.priceRange.max);
      `,
      variables: [
        {
          name: 'components',
          type: 'component',
          source: 'listing',
          description: 'PC components detected from listing'
        },
        {
          name: 'market',
          type: 'market',
          source: 'market',
          description: 'Current market conditions'
        }
      ],
      category: 'both',
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    // ROI-focused formula
    const roiFormula: PricingFormula = {
      id: 'roi-focused',
      name: 'ROI Maximizer',
      description: 'Optimizes pricing for maximum return on investment',
      formula: `
        let cost = listing.price;
        let targetROI = user.targetROI || 30;
        let basePrice = markup(cost, targetROI);
        let riskAdjustment = if(listing.risks.length > 2, 0.9, 1);
        let conditionMultiplier = switch(listing.condition,
          'excellent', 1.1,
          'good', 1.0,
          'fair', 0.85,
          'poor', 0.7,
          0.9
        );
        return round(basePrice * riskAdjustment * conditionMultiplier);
      `,
      variables: [
        {
          name: 'listing',
          type: 'component',
          source: 'listing',
          description: 'Original listing data'
        },
        {
          name: 'user.targetROI',
          type: 'percentage',
          source: 'user',
          defaultValue: 30,
          description: 'Target ROI percentage'
        }
      ],
      category: 'selling',
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    // Quick flip formula
    const quickFlipFormula: PricingFormula = {
      id: 'quick-flip',
      name: 'Quick Flip Pricing',
      description: 'Aggressive pricing for fast turnover',
      formula: `
        let componentTotal = totalComponentValue(components);
        let marketAvg = market.avgPrice;
        let basePrice = min(componentTotal * 0.75, marketAvg * 0.85);
        let urgencyDiscount = percentage(basePrice, user.urgencyLevel || 10);
        return round(basePrice - urgencyDiscount);
      `,
      variables: [
        {
          name: 'components',
          type: 'component',
          source: 'listing',
          description: 'PC components'
        },
        {
          name: 'market',
          type: 'market',
          source: 'market',
          description: 'Market data'
        },
        {
          name: 'user.urgencyLevel',
          type: 'percentage',
          source: 'user',
          defaultValue: 10,
          description: 'Urgency discount percentage'
        }
      ],
      category: 'selling',
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    this.formulas.set(componentFormula.id, componentFormula);
    this.formulas.set(roiFormula.id, roiFormula);
    this.formulas.set(quickFlipFormula.id, quickFlipFormula);
  }

  // Create new formula
  async createFormula(formula: Omit<PricingFormula, 'id' | 'createdAt' | 'updatedAt'>): Promise<string> {
    const id = `formula-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newFormula: PricingFormula = {
      ...formula,
      id,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    // Validate formula syntax
    const validation = await this.validateFormula(newFormula);
    if (!validation.isValid) {
      throw new Error(`Invalid formula: ${validation.errors.join(', ')}`);
    }

    this.formulas.set(id, newFormula);
    await this.saveData();
    
    return id;
  }

  // Evaluate formula
  async evaluateFormula(
    formulaId: string, 
    context: FormulaContext
  ): Promise<EvaluationResult> {
    const formula = this.formulas.get(formulaId);
    if (!formula) {
      throw new Error('Formula not found');
    }

    // Get market data
    const marketData = await this.getMarketData(context.listing);
    
    // Build evaluation context
    const evalContext = this.buildEvaluationContext(formula, context, marketData);
    
    // Track calculation steps
    const breakdown: CalculationBreakdown[] = [];
    
    try {
      // Create sandboxed evaluation function
      const evalFunction = this.createEvaluationFunction(formula.formula, evalContext, breakdown);
      const price = evalFunction();

      // Validate result
      if (typeof price !== 'number' || isNaN(price) || price <= 0) {
        throw new Error('Formula returned invalid price');
      }

      // Calculate confidence based on data completeness
      const confidence = this.calculateConfidence(context, marketData);

      // Generate warnings and suggestions
      const warnings = this.generateWarnings(price, marketData, context);
      const suggestions = this.generateSuggestions(price, marketData, formula);

      return {
        price,
        confidence,
        breakdown,
        warnings,
        suggestions
      };
    } catch (error) {
      throw new Error(`Formula evaluation failed: ${error.message}`);
    }
  }

  // Build evaluation context with all variables
  private buildEvaluationContext(
    formula: PricingFormula, 
    context: FormulaContext,
    marketData: MarketData
  ): Record<string, any> {
    const evalContext: Record<string, any> = {
      // Built-in functions
      ...Object.fromEntries(this.builtInFunctions),
      
      // Context data
      listing: context.listing || {},
      deal: context.deal || {},
      components: context.listing?.components || {},
      market: marketData,
      user: context.userVariables || {},
      
      // Helper variables
      Math: Math,
      Date: Date
    };

    // Add default values for missing variables
    for (const variable of formula.variables) {
      const path = variable.name.split('.');
      let current = evalContext;
      
      for (let i = 0; i < path.length - 1; i++) {
        if (!current[path[i]]) {
          current[path[i]] = {};
        }
        current = current[path[i]];
      }
      
      if (current[path[path.length - 1]] === undefined && variable.defaultValue !== undefined) {
        current[path[path.length - 1]] = variable.defaultValue;
      }
    }

    return evalContext;
  }

  // Create sandboxed evaluation function
  private createEvaluationFunction(
    formula: string, 
    context: Record<string, any>,
    breakdown: CalculationBreakdown[]
  ): () => number {
    // Create a function that tracks intermediate calculations
    const trackedContext = new Proxy(context, {
      get(target, prop) {
        const value = target[prop];
        if (typeof value === 'function') {
          return (...args: any[]) => {
            const result = value(...args);
            breakdown.push({
              step: `${String(prop)}(${args.join(', ')})`,
              expression: `${String(prop)}`,
              value: typeof result === 'number' ? result : 0,
              description: `Called ${String(prop)} function`
            });
            return result;
          };
        }
        return value;
      }
    });

    // Create function with tracked context
    const functionBody = `
      with (this) {
        ${formula}
      }
    `;

    try {
      return new Function(functionBody).bind(trackedContext);
    } catch (error) {
      throw new Error(`Failed to compile formula: ${error.message}`);
    }
  }

  // Validate formula syntax and logic
  async validateFormula(formula: PricingFormula): Promise<{ isValid: boolean; errors: string[] }> {
    const errors: string[] = [];

    // Check for required variables
    const requiredVars = formula.variables.filter(v => !v.defaultValue);
    if (requiredVars.length > 0) {
      // Validate variable references in formula
      for (const variable of requiredVars) {
        if (!formula.formula.includes(variable.name)) {
          errors.push(`Required variable '${variable.name}' not used in formula`);
        }
      }
    }

    // Try to compile the formula
    try {
      new Function(`with(this) { ${formula.formula} }`);
    } catch (error) {
      errors.push(`Syntax error: ${error.message}`);
    }

    // Run test cases if provided
    if (formula.testCases && formula.testCases.length > 0) {
      for (const testCase of formula.testCases) {
        try {
          const result = await this.evaluateFormula(formula.id, {
            userVariables: testCase.inputs
          });
          
          const tolerance = 0.01; // 1 cent tolerance
          if (Math.abs(result.price - testCase.expectedOutput) > tolerance) {
            errors.push(`Test case ${testCase.id} failed: expected ${testCase.expectedOutput}, got ${result.price}`);
          }
        } catch (error) {
          errors.push(`Test case ${testCase.id} error: ${error.message}`);
        }
      }
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  // Get market data for context
  private async getMarketData(listing?: Listing): Promise<MarketData> {
    // Check cache first
    const cacheKey = listing ? `${listing.platform}-${listing.location}` : 'default';
    const cached = this.marketDataCache.get(cacheKey);
    
    if (cached && (Date.now() - cached.lastUpdated) < 3600000) { // 1 hour cache
      return cached;
    }

    // Generate mock market data (would fetch real data in production)
    const marketData: MarketData = {
      avgPrice: 850,
      medianPrice: 800,
      priceRange: { min: 400, max: 1500 },
      demandScore: 65, // 0-100
      seasonalMultiplier: 1.1, // Holiday season boost
      competitorCount: 12
    };

    // Adjust based on listing if provided
    if (listing) {
      const componentValue = this.builtInFunctions.get('totalComponentValue')!(listing.components || {});
      marketData.avgPrice = componentValue * 1.2;
      marketData.medianPrice = componentValue * 1.1;
      marketData.priceRange = {
        min: componentValue * 0.7,
        max: componentValue * 1.8
      };
    }

    this.marketDataCache.set(cacheKey, { ...marketData, lastUpdated: Date.now() });
    return marketData;
  }

  // Calculate confidence score
  private calculateConfidence(context: FormulaContext, marketData: MarketData): number {
    let confidence = 100;

    // Reduce confidence for missing data
    if (!context.listing) confidence -= 20;
    if (!context.listing?.components) confidence -= 15;
    if (!marketData) confidence -= 10;
    
    // Reduce confidence for incomplete component data
    if (context.listing?.components) {
      const components = context.listing.components;
      if (!components.cpu) confidence -= 5;
      if (!components.gpu) confidence -= 5;
      if (!components.ram) confidence -= 3;
      if (!components.storage) confidence -= 3;
    }

    return Math.max(0, confidence);
  }

  // Generate warnings
  private generateWarnings(price: number, marketData: MarketData, context: FormulaContext): string[] {
    const warnings: string[] = [];

    // Price range warnings
    if (price < marketData.priceRange.min) {
      warnings.push(`Price is ${((marketData.priceRange.min - price) / marketData.priceRange.min * 100).toFixed(1)}% below market minimum`);
    }
    if (price > marketData.priceRange.max) {
      warnings.push(`Price is ${((price - marketData.priceRange.max) / marketData.priceRange.max * 100).toFixed(1)}% above market maximum`);
    }

    // Component value warnings
    if (context.listing?.components) {
      const componentValue = this.builtInFunctions.get('totalComponentValue')!(context.listing.components);
      if (price < componentValue * 0.6) {
        warnings.push('Price is significantly below component value - potential loss');
      }
    }

    // Market condition warnings
    if (marketData.competitorCount > 20) {
      warnings.push('High competition in market - consider aggressive pricing');
    }
    if (marketData.demandScore < 30) {
      warnings.push('Low market demand - expect longer selling time');
    }

    return warnings;
  }

  // Generate suggestions
  private generateSuggestions(price: number, marketData: MarketData, formula: PricingFormula): string[] {
    const suggestions: string[] = [];

    // Price optimization suggestions
    const priceDiff = Math.abs(price - marketData.avgPrice);
    if (priceDiff > marketData.avgPrice * 0.2) {
      if (price > marketData.avgPrice) {
        suggestions.push(`Consider pricing closer to market average ($${marketData.avgPrice}) for faster sale`);
      } else {
        suggestions.push(`You may be able to increase price closer to market average ($${marketData.avgPrice})`);
      }
    }

    // Formula suggestions
    if (formula.category === 'selling' && !formula.formula.includes('seasonalMultiplier')) {
      suggestions.push('Consider adding seasonal adjustments to your formula');
    }

    if (!formula.formula.includes('competitionFactor')) {
      suggestions.push('Add competition factor to adjust for market saturation');
    }

    return suggestions;
  }

  // Update formula
  async updateFormula(id: string, updates: Partial<PricingFormula>): Promise<void> {
    const formula = this.formulas.get(id);
    if (!formula) {
      throw new Error('Formula not found');
    }

    const updatedFormula = {
      ...formula,
      ...updates,
      updatedAt: new Date()
    };

    // Validate if formula changed
    if (updates.formula || updates.variables) {
      const validation = await this.validateFormula(updatedFormula);
      if (!validation.isValid) {
        throw new Error(`Invalid formula: ${validation.errors.join(', ')}`);
      }
    }

    this.formulas.set(id, updatedFormula);
    await this.saveData();
  }

  // Delete formula
  async deleteFormula(id: string): Promise<void> {
    this.formulas.delete(id);
    await this.saveData();
  }

  // Get all formulas
  getFormulas(category?: PricingFormula['category']): PricingFormula[] {
    const allFormulas = Array.from(this.formulas.values());
    if (category) {
      return allFormulas.filter(f => f.category === category || f.category === 'both');
    }
    return allFormulas;
  }

  // Get formula by ID
  getFormula(id: string): PricingFormula | undefined {
    return this.formulas.get(id);
  }

  // Run test cases for a formula
  async runTestCases(formulaId: string): Promise<TestCase[]> {
    const formula = this.formulas.get(formulaId);
    if (!formula || !formula.testCases) {
      return [];
    }

    const results: TestCase[] = [];
    
    for (const testCase of formula.testCases) {
      try {
        const result = await this.evaluateFormula(formulaId, {
          userVariables: testCase.inputs
        });
        
        const updatedTest = {
          ...testCase,
          actualOutput: result.price,
          passed: Math.abs(result.price - testCase.expectedOutput) < 0.01
        };
        
        results.push(updatedTest);
      } catch (error) {
        results.push({
          ...testCase,
          actualOutput: 0,
          passed: false
        });
      }
    }

    // Update formula with test results
    formula.testCases = results;
    await this.saveData();

    return results;
  }

  // Export formula as shareable code
  exportFormula(formulaId: string): string {
    const formula = this.formulas.get(formulaId);
    if (!formula) {
      throw new Error('Formula not found');
    }

    return JSON.stringify({
      name: formula.name,
      description: formula.description,
      formula: formula.formula,
      variables: formula.variables,
      category: formula.category,
      testCases: formula.testCases
    }, null, 2);
  }

  // Import formula from code
  async importFormula(formulaCode: string): Promise<string> {
    try {
      const imported = JSON.parse(formulaCode);
      
      // Validate required fields
      if (!imported.name || !imported.formula || !imported.variables) {
        throw new Error('Invalid formula format');
      }

      return await this.createFormula({
        name: `${imported.name} (Imported)`,
        description: imported.description || 'Imported formula',
        formula: imported.formula,
        variables: imported.variables,
        category: imported.category || 'both',
        isActive: true,
        testCases: imported.testCases
      });
    } catch (error) {
      throw new Error(`Failed to import formula: ${error.message}`);
    }
  }

  // Save data
  private async saveData(): Promise<void> {
    try {
      await chrome.storage.local.set({
        'customPricing:formulas': Array.from(this.formulas.entries())
      });
    } catch (error) {
      console.error('Failed to save custom pricing data:', error);
    }
  }

  // Load data
  private async loadData(): Promise<void> {
    try {
      const data = await chrome.storage.local.get(['customPricing:formulas']);
      
      if (data['customPricing:formulas']) {
        this.formulas = new Map(data['customPricing:formulas']);
      }
    } catch (error) {
      console.error('Failed to load custom pricing data:', error);
    }
  }
}

// Export singleton instance
export const customPricingEngine = new CustomPricingEngine();