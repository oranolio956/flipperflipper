/**
 * Message Template Manager
 * Handles message templates and auto-drafting for buyer/seller communications
 */

import { Listing, Deal } from '../types';

export interface MessageTemplate {
  id: string;
  name: string;
  category: 'inquiry' | 'offer' | 'negotiation' | 'closing' | 'follow-up';
  type: 'buyer' | 'seller';
  subject?: string;
  body: string;
  variables: TemplateVariable[];
  tags: string[];
  isDefault?: boolean;
  usageCount: number;
  successRate?: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface TemplateVariable {
  name: string;
  description: string;
  type: 'text' | 'number' | 'currency' | 'percentage' | 'date' | 'list';
  required: boolean;
  defaultValue?: any;
  options?: string[]; // For list type
}

export interface DraftMessage {
  template: MessageTemplate;
  variables: Record<string, any>;
  preview: string;
  suggestions: string[];
  tone: 'formal' | 'casual' | 'friendly' | 'professional';
  confidence: number;
}

export interface MessageContext {
  listing?: Listing;
  deal?: Deal;
  recipientName?: string;
  previousMessages?: string[];
  userPreferences?: any;
}

export class MessageTemplateManager {
  private templates: Map<string, MessageTemplate> = new Map();
  private readonly STORAGE_KEY = 'messageTemplates';
  private readonly ANALYTICS_KEY = 'messageAnalytics';

  constructor() {
    this.loadTemplates();
    this.initializeDefaultTemplates();
  }

  /**
   * Initialize with default templates
   */
  private initializeDefaultTemplates(): void {
    const defaultTemplates: Partial<MessageTemplate>[] = [
      // Buyer inquiry templates
      {
        name: 'Initial Inquiry - Detailed',
        category: 'inquiry',
        type: 'buyer',
        subject: 'Interested in your {{listingTitle}}',
        body: `Hi {{sellerName}},

I saw your listing for the {{listingTitle}} and I'm very interested. 

A few questions:
1. Is it still available?
2. What's the reason for selling?
3. Has it been used for mining or heavy gaming?
4. Are all original accessories included?
5. Would you be open to {{paymentMethod}}?

I can meet at {{meetupLocation}} if that works for you. Looking forward to hearing back!

Best regards,
{{buyerName}}`,
        variables: [
          { name: 'sellerName', description: 'Seller\'s name', type: 'text', required: true },
          { name: 'listingTitle', description: 'Title of the listing', type: 'text', required: true },
          { name: 'paymentMethod', description: 'Preferred payment method', type: 'list', required: true, options: ['cash', 'Venmo', 'PayPal'] },
          { name: 'meetupLocation', description: 'Suggested meetup spot', type: 'text', required: true },
          { name: 'buyerName', description: 'Your name', type: 'text', required: true }
        ],
        tags: ['detailed', 'first-contact', 'questions']
      },
      
      // Quick inquiry
      {
        name: 'Quick Availability Check',
        category: 'inquiry',
        type: 'buyer',
        subject: 'Is the {{listingTitle}} still available?',
        body: `Hi, is this still available? If so, I'm interested and can meet today. Thanks!`,
        variables: [
          { name: 'listingTitle', description: 'Title of the listing', type: 'text', required: true }
        ],
        tags: ['quick', 'availability']
      },

      // Offer templates
      {
        name: 'Fair Offer with Reasoning',
        category: 'offer',
        type: 'buyer',
        subject: 'Offer for {{listingTitle}}',
        body: `Hi {{sellerName}},

I'm interested in your {{listingTitle}}. Based on:
- Current market prices for similar specs
- The age of the components ({{componentAge}})
- {{additionalReason}}

I'd like to offer {{offerAmount}} cash. I can pick up {{pickupTimeframe}} at your convenience.

This is a fair offer considering {{marketComparison}}. Let me know if you'd like to discuss.

Thanks,
{{buyerName}}`,
        variables: [
          { name: 'sellerName', description: 'Seller\'s name', type: 'text', required: true },
          { name: 'listingTitle', description: 'Title of the listing', type: 'text', required: true },
          { name: 'componentAge', description: 'Age of components', type: 'text', required: true },
          { name: 'additionalReason', description: 'Additional reason for offer', type: 'text', required: false },
          { name: 'offerAmount', description: 'Offer amount', type: 'currency', required: true },
          { name: 'pickupTimeframe', description: 'When you can pick up', type: 'text', required: true, defaultValue: 'today or tomorrow' },
          { name: 'marketComparison', description: 'Market comparison', type: 'text', required: true },
          { name: 'buyerName', description: 'Your name', type: 'text', required: true }
        ],
        tags: ['offer', 'reasoning', 'cash']
      },

      // Negotiation templates
      {
        name: 'Counter-Offer Response',
        category: 'negotiation',
        type: 'buyer',
        subject: 'Re: {{listingTitle}}',
        body: `Hi {{sellerName}},

Thanks for getting back to me. I understand you're looking for {{theirPrice}}, but that's a bit above my budget.

How about we meet in the middle at {{counterOffer}}? This would be a fair deal for both of us because:
{{reasoningPoints}}

I'm a serious buyer with cash in hand and can meet {{availability}}.

What do you think?

{{buyerName}}`,
        variables: [
          { name: 'sellerName', description: 'Seller\'s name', type: 'text', required: true },
          { name: 'listingTitle', description: 'Title of the listing', type: 'text', required: true },
          { name: 'theirPrice', description: 'Their asking price', type: 'currency', required: true },
          { name: 'counterOffer', description: 'Your counter offer', type: 'currency', required: true },
          { name: 'reasoningPoints', description: 'Reasons for counter offer', type: 'text', required: true },
          { name: 'availability', description: 'Your availability', type: 'text', required: true },
          { name: 'buyerName', description: 'Your name', type: 'text', required: true }
        ],
        tags: ['negotiation', 'counter-offer']
      },

      // Seller response templates
      {
        name: 'Professional Seller Response',
        category: 'inquiry',
        type: 'seller',
        subject: 'Re: {{listingTitle}}',
        body: `Hi {{buyerName}},

Thanks for your interest in my {{listingTitle}}!

To answer your questions:
{{answers}}

The system has been well-maintained and includes:
{{includedItems}}

My asking price of {{askingPrice}} is firm, but I'm happy to demonstrate everything working when we meet.

I'm available {{availability}}. Let me know what works best for you.

Best,
{{sellerName}}`,
        variables: [
          { name: 'buyerName', description: 'Buyer\'s name', type: 'text', required: true },
          { name: 'listingTitle', description: 'Title of the listing', type: 'text', required: true },
          { name: 'answers', description: 'Answers to buyer questions', type: 'text', required: true },
          { name: 'includedItems', description: 'What\'s included', type: 'text', required: true },
          { name: 'askingPrice', description: 'Your asking price', type: 'currency', required: true },
          { name: 'availability', description: 'Your availability', type: 'text', required: true },
          { name: 'sellerName', description: 'Your name', type: 'text', required: true }
        ],
        tags: ['seller', 'professional', 'detailed']
      },

      // Closing templates
      {
        name: 'Confirm Meetup Details',
        category: 'closing',
        type: 'buyer',
        subject: 'Confirming meetup for {{listingTitle}}',
        body: `Hi {{sellerName}},

Great! I'll see you:
📅 {{meetupDate}} at {{meetupTime}}
📍 {{meetupLocation}}
💵 {{agreedPrice}} in cash

My phone number is {{phoneNumber}} in case you need to reach me.

See you then!

{{buyerName}}`,
        variables: [
          { name: 'sellerName', description: 'Seller\'s name', type: 'text', required: true },
          { name: 'listingTitle', description: 'Title of the listing', type: 'text', required: true },
          { name: 'meetupDate', description: 'Meetup date', type: 'date', required: true },
          { name: 'meetupTime', description: 'Meetup time', type: 'text', required: true },
          { name: 'meetupLocation', description: 'Meetup location', type: 'text', required: true },
          { name: 'agreedPrice', description: 'Agreed price', type: 'currency', required: true },
          { name: 'phoneNumber', description: 'Your phone number', type: 'text', required: true },
          { name: 'buyerName', description: 'Your name', type: 'text', required: true }
        ],
        tags: ['closing', 'meetup', 'confirmation']
      }
    ];

    defaultTemplates.forEach(template => {
      if (template.name) {
        this.createTemplate(template as Omit<MessageTemplate, 'id' | 'createdAt' | 'updatedAt' | 'usageCount'>);
      }
    });
  }

  /**
   * Create a new template
   */
  async createTemplate(
    template: Omit<MessageTemplate, 'id' | 'createdAt' | 'updatedAt' | 'usageCount'>
  ): Promise<MessageTemplate> {
    const newTemplate: MessageTemplate = {
      ...template,
      id: `template_${Date.now()}`,
      usageCount: 0,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    this.templates.set(newTemplate.id, newTemplate);
    await this.saveTemplates();

    return newTemplate;
  }

  /**
   * Generate auto-draft message
   */
  async generateDraft(
    context: MessageContext,
    category: MessageTemplate['category']
  ): Promise<DraftMessage> {
    // Find best matching template
    const template = this.selectBestTemplate(context, category);
    
    if (!template) {
      throw new Error('No suitable template found');
    }

    // Extract variables from context
    const variables = this.extractVariables(template, context);

    // Generate preview
    const preview = this.renderTemplate(template, variables);

    // Generate suggestions
    const suggestions = this.generateSuggestions(context, template, variables);

    // Determine tone
    const tone = this.analyzeTone(preview);

    return {
      template,
      variables,
      preview,
      suggestions,
      tone,
      confidence: this.calculateConfidence(template, variables, context)
    };
  }

  /**
   * Select best template based on context
   */
  private selectBestTemplate(
    context: MessageContext,
    category: MessageTemplate['category']
  ): MessageTemplate | null {
    const templates = Array.from(this.templates.values()).filter(t => 
      t.category === category && 
      (!context.listing || t.type === 'buyer') // Adjust based on context
    );

    if (templates.length === 0) return null;

    // Score templates based on context match
    const scored = templates.map(template => ({
      template,
      score: this.scoreTemplate(template, context)
    }));

    // Sort by score and success rate
    scored.sort((a, b) => {
      const scoreA = a.score + (a.template.successRate || 0.5);
      const scoreB = b.score + (b.template.successRate || 0.5);
      return scoreB - scoreA;
    });

    return scored[0].template;
  }

  /**
   * Score template relevance
   */
  private scoreTemplate(template: MessageTemplate, context: MessageContext): number {
    let score = 0;

    // Check if all required variables can be filled
    const canFillRequired = template.variables
      .filter(v => v.required)
      .every(v => this.canExtractVariable(v, context));
    
    if (!canFillRequired) return -1;

    // Prefer templates with matching tags
    if (context.listing) {
      if (context.listing.price < 500 && template.tags.includes('budget')) score += 0.2;
      if (context.listing.price > 1500 && template.tags.includes('premium')) score += 0.2;
    }

    // Prefer recently successful templates
    if (template.successRate && template.successRate > 0.7) score += 0.3;

    // Prefer frequently used templates (but not too much)
    if (template.usageCount > 5 && template.usageCount < 50) score += 0.1;

    return score;
  }

  /**
   * Extract variables from context
   */
  private extractVariables(
    template: MessageTemplate,
    context: MessageContext
  ): Record<string, any> {
    const variables: Record<string, any> = {};

    template.variables.forEach(variable => {
      let value = this.extractSingleVariable(variable, context);
      
      if (value === undefined && variable.defaultValue !== undefined) {
        value = variable.defaultValue;
      }

      if (value !== undefined) {
        variables[variable.name] = value;
      }
    });

    return variables;
  }

  /**
   * Extract single variable from context
   */
  private extractSingleVariable(
    variable: TemplateVariable,
    context: MessageContext
  ): any {
    switch (variable.name) {
      case 'listingTitle':
        return context.listing?.title;
      
      case 'sellerName':
        return context.listing?.seller.name || context.recipientName;
      
      case 'buyerName':
        return context.userPreferences?.name || 'John';
      
      case 'askingPrice':
        return context.listing?.price;
      
      case 'offerAmount':
        if (context.listing?.analysis?.suggestedOffer) {
          return context.listing.analysis.suggestedOffer;
        }
        return context.listing ? Math.round(context.listing.price * 0.85) : undefined;
      
      case 'meetupLocation':
        return context.userPreferences?.preferredMeetupSpots?.[0] || 'a public location';
      
      case 'componentAge':
        // Estimate based on components
        if (context.listing?.components?.cpu) {
          const cpu = context.listing.components.cpu.model;
          if (cpu.includes('13th') || cpu.includes('7000')) return 'less than 1 year';
          if (cpu.includes('12th') || cpu.includes('5000')) return '1-2 years';
          return '2-3 years';
        }
        return 'unknown age';
      
      case 'marketComparison':
        if (context.listing?.analysis?.marketComparison) {
          return context.listing.analysis.marketComparison;
        }
        return 'similar systems are selling for this range';
      
      default:
        return undefined;
    }
  }

  /**
   * Check if variable can be extracted
   */
  private canExtractVariable(
    variable: TemplateVariable,
    context: MessageContext
  ): boolean {
    const value = this.extractSingleVariable(variable, context);
    return value !== undefined || variable.defaultValue !== undefined;
  }

  /**
   * Render template with variables
   */
  renderTemplate(
    template: MessageTemplate,
    variables: Record<string, any>
  ): string {
    let rendered = template.body;

    // Replace variables
    Object.entries(variables).forEach(([name, value]) => {
      const placeholder = new RegExp(`{{${name}}}`, 'g');
      rendered = rendered.replace(placeholder, this.formatValue(value, template.variables.find(v => v.name === name)));
    });

    // Remove any remaining placeholders
    rendered = rendered.replace(/{{[^}]+}}/g, '[MISSING]');

    return rendered;
  }

  /**
   * Format value based on type
   */
  private formatValue(value: any, variable?: TemplateVariable): string {
    if (value === undefined || value === null) return '';

    if (variable) {
      switch (variable.type) {
        case 'currency':
          return `$${value.toLocaleString()}`;
        case 'percentage':
          return `${value}%`;
        case 'date':
          return new Date(value).toLocaleDateString();
        default:
          return String(value);
      }
    }

    return String(value);
  }

  /**
   * Generate message suggestions
   */
  private generateSuggestions(
    context: MessageContext,
    template: MessageTemplate,
    variables: Record<string, any>
  ): string[] {
    const suggestions: string[] = [];

    // Price-based suggestions
    if (context.listing?.price && variables.offerAmount) {
      const discount = ((context.listing.price - variables.offerAmount) / context.listing.price) * 100;
      if (discount > 20) {
        suggestions.push('Consider starting with a higher offer (10-15% below asking) to show serious interest');
      }
    }

    // Timing suggestions
    const now = new Date();
    const hour = now.getHours();
    if (hour < 9 || hour > 21) {
      suggestions.push('Consider scheduling this message during business hours for better response rates');
    }

    // Tone suggestions
    if (template.category === 'inquiry' && !template.body.includes('?')) {
      suggestions.push('Add specific questions to increase engagement');
    }

    // Platform-specific suggestions
    if (context.listing?.platform === 'facebook') {
      suggestions.push('Facebook users often prefer quick, casual communication');
    } else if (context.listing?.platform === 'craigslist') {
      suggestions.push('Craigslist users may be more cautious - emphasize safety and public meetups');
    }

    return suggestions;
  }

  /**
   * Analyze message tone
   */
  private analyzeTone(message: string): DraftMessage['tone'] {
    const casualIndicators = ['hey', 'hi!', 'thanks!', '👍', '😊', 'lol'];
    const formalIndicators = ['dear', 'sincerely', 'regards', 'mr.', 'ms.'];
    const friendlyIndicators = ['great', 'awesome', 'love', 'excited', '!'];
    
    const lower = message.toLowerCase();
    
    let casualScore = casualIndicators.filter(i => lower.includes(i)).length;
    let formalScore = formalIndicators.filter(i => lower.includes(i)).length;
    let friendlyScore = friendlyIndicators.filter(i => lower.includes(i)).length;

    if (formalScore > casualScore && formalScore > friendlyScore) return 'formal';
    if (casualScore > formalScore && casualScore > friendlyScore) return 'casual';
    if (friendlyScore > 0) return 'friendly';
    
    return 'professional';
  }

  /**
   * Calculate confidence score
   */
  private calculateConfidence(
    template: MessageTemplate,
    variables: Record<string, any>,
    context: MessageContext
  ): number {
    let confidence = 0.5; // Base confidence

    // All required variables filled
    const requiredFilled = template.variables
      .filter(v => v.required)
      .every(v => variables[v.name] !== undefined);
    
    if (requiredFilled) confidence += 0.2;

    // Template success rate
    if (template.successRate) {
      confidence += template.successRate * 0.2;
    }

    // Context completeness
    if (context.listing?.components) confidence += 0.1;
    if (context.previousMessages?.length) confidence += 0.1;

    return Math.min(confidence, 0.95);
  }

  /**
   * Track template usage
   */
  async trackUsage(
    templateId: string,
    success: boolean,
    responseTime?: number
  ): Promise<void> {
    const template = this.templates.get(templateId);
    if (!template) return;

    template.usageCount++;
    
    // Update success rate
    const previousSuccesses = (template.successRate || 0.5) * (template.usageCount - 1);
    template.successRate = (previousSuccesses + (success ? 1 : 0)) / template.usageCount;

    template.updatedAt = new Date();
    
    await this.saveTemplates();
    await this.saveAnalytics(templateId, success, responseTime);
  }

  /**
   * Get template by ID
   */
  getTemplate(id: string): MessageTemplate | undefined {
    return this.templates.get(id);
  }

  /**
   * Get all templates
   */
  getAllTemplates(): MessageTemplate[] {
    return Array.from(this.templates.values());
  }

  /**
   * Search templates
   */
  searchTemplates(query: string): MessageTemplate[] {
    const queryLower = query.toLowerCase();
    return this.getAllTemplates().filter(template =>
      template.name.toLowerCase().includes(queryLower) ||
      template.body.toLowerCase().includes(queryLower) ||
      template.tags.some(tag => tag.toLowerCase().includes(queryLower))
    );
  }

  /**
   * Update template
   */
  async updateTemplate(
    id: string,
    updates: Partial<MessageTemplate>
  ): Promise<MessageTemplate | null> {
    const template = this.templates.get(id);
    if (!template) return null;

    Object.assign(template, updates, {
      updatedAt: new Date()
    });

    await this.saveTemplates();
    return template;
  }

  /**
   * Delete template
   */
  async deleteTemplate(id: string): Promise<boolean> {
    const deleted = this.templates.delete(id);
    if (deleted) {
      await this.saveTemplates();
    }
    return deleted;
  }

  /**
   * Persistence methods
   */
  private async loadTemplates(): Promise<void> {
    const { [this.STORAGE_KEY]: saved } = await chrome.storage.local.get(this.STORAGE_KEY);
    if (saved) {
      Object.entries(saved).forEach(([id, template]: [string, any]) => {
        this.templates.set(id, {
          ...template,
          createdAt: new Date(template.createdAt),
          updatedAt: new Date(template.updatedAt)
        });
      });
    }
  }

  private async saveTemplates(): Promise<void> {
    const data: Record<string, any> = {};
    this.templates.forEach((template, id) => {
      data[id] = {
        ...template,
        createdAt: template.createdAt.toISOString(),
        updatedAt: template.updatedAt.toISOString()
      };
    });
    await chrome.storage.local.set({ [this.STORAGE_KEY]: data });
  }

  private async saveAnalytics(
    templateId: string,
    success: boolean,
    responseTime?: number
  ): Promise<void> {
    const { [this.ANALYTICS_KEY]: analytics = {} } = await chrome.storage.local.get(this.ANALYTICS_KEY);
    
    if (!analytics[templateId]) {
      analytics[templateId] = {
        uses: 0,
        successes: 0,
        avgResponseTime: null
      };
    }

    analytics[templateId].uses++;
    if (success) analytics[templateId].successes++;
    
    if (responseTime) {
      const prev = analytics[templateId].avgResponseTime || responseTime;
      analytics[templateId].avgResponseTime = 
        (prev * (analytics[templateId].uses - 1) + responseTime) / analytics[templateId].uses;
    }

    await chrome.storage.local.set({ [this.ANALYTICS_KEY]: analytics });
  }
}

// Export singleton instance
export const messageTemplateManager = new MessageTemplateManager();