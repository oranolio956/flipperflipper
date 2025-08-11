/**
 * Pipeline Manager v3.5.0 - Deal Lifecycle State Machine
 * Manages deals through stages with automation and tracking
 */

import { ParsedListing } from './parser';

export type DealStage = 
  | 'scanner'      // Just found, needs review
  | 'analysis'     // Being analyzed for profit potential
  | 'contacted'    // Seller contacted
  | 'negotiating'  // Price negotiation
  | 'scheduled'    // Pickup scheduled
  | 'purchased'    // Money exchanged
  | 'testing'      // Hardware testing
  | 'refurbing'    // Cleaning/upgrading
  | 'listed'       // Re-listed for sale
  | 'sold'         // Sold to buyer
  | 'archived';    // Deal complete or abandoned

export interface DealMetrics {
  timeInStage: number; // minutes
  totalTime: number; // minutes
  touchPoints: number; // interactions
  profitRealized?: number;
  roi?: number;
}

export interface DealAction {
  type: string;
  timestamp: string;
  user?: string;
  notes?: string;
  data?: any;
}

export interface PipelineDeal extends ParsedListing {
  // Pipeline metadata
  dealId: string;
  stage: DealStage;
  priority: 'urgent' | 'high' | 'normal' | 'low';
  
  // Timestamps
  addedToPipeline: string;
  stageHistory: Array<{
    stage: DealStage;
    enteredAt: string;
    exitedAt?: string;
    reason?: string;
  }>;
  
  // Financial tracking
  costs: {
    purchase: number;
    gas?: number;
    parts?: number;
    shipping?: number;
    fees?: number;
    total: number;
  };
  
  revenue: {
    askingPrice?: number;
    soldPrice?: number;
    shippingCollected?: number;
    total: number;
  };
  
  // Communication
  messages: Array<{
    timestamp: string;
    direction: 'sent' | 'received';
    content: string;
    platform: string;
  }>;
  
  // Tasks & reminders
  tasks: Array<{
    id: string;
    title: string;
    due?: string;
    completed: boolean;
    priority: 'high' | 'normal' | 'low';
  }>;
  
  // Notes & tags
  notes: string;
  tags: string[];
  
  // Automation flags
  autoAdvance: boolean;
  notifications: boolean;
  
  // Metrics
  metrics: DealMetrics;
  
  // Action log
  actions: DealAction[];
}

export interface PipelineStats {
  totalDeals: number;
  dealsByStage: Record<DealStage, number>;
  totalInvested: number;
  totalRevenue: number;
  totalProfit: number;
  avgTimeToSale: number; // days
  avgROI: number;
  successRate: number;
}

export interface StageTransition {
  from: DealStage;
  to: DealStage;
  condition?: (deal: PipelineDeal) => boolean;
  action?: (deal: PipelineDeal) => Promise<void>;
  requiresConfirmation?: boolean;
}

export class PipelineManager {
  private static instance: PipelineManager;
  private deals: Map<string, PipelineDeal> = new Map();
  private listeners: Set<(event: PipelineEvent) => void> = new Set();
  
  // Valid stage transitions
  private transitions: StageTransition[] = [
    // Scanner → Analysis (auto)
    { from: 'scanner', to: 'analysis' },
    
    // Analysis → Contacted or Archive
    { from: 'analysis', to: 'contacted', condition: (d) => d.analysis.dealQuality !== 'poor' },
    { from: 'analysis', to: 'archived', condition: (d) => d.analysis.dealQuality === 'poor' },
    
    // Contacted → Negotiating or Archive
    { from: 'contacted', to: 'negotiating' },
    { from: 'contacted', to: 'archived' },
    
    // Negotiating → Scheduled or Archive
    { from: 'negotiating', to: 'scheduled' },
    { from: 'negotiating', to: 'archived' },
    
    // Scheduled → Purchased or back to Negotiating
    { from: 'scheduled', to: 'purchased' },
    { from: 'scheduled', to: 'negotiating' }, // Deal fell through
    { from: 'scheduled', to: 'archived' },
    
    // Purchased → Testing
    { from: 'purchased', to: 'testing' },
    
    // Testing → Refurbing or Archive (if broken)
    { from: 'testing', to: 'refurbing' },
    { from: 'testing', to: 'archived' },
    
    // Refurbing → Listed
    { from: 'refurbing', to: 'listed' },
    
    // Listed → Sold or back to Listed (relist)
    { from: 'listed', to: 'sold' },
    { from: 'listed', to: 'listed' }, // Relist with changes
    
    // Sold → Archived
    { from: 'sold', to: 'archived' }
  ];
  
  private constructor() {
    this.loadDeals();
    this.startAutoSave();
    this.startMetricsUpdater();
  }
  
  static getInstance(): PipelineManager {
    if (!PipelineManager.instance) {
      PipelineManager.instance = new PipelineManager();
    }
    return PipelineManager.instance;
  }
  
  /**
   * Add a parsed listing to the pipeline
   */
  async addToPipeline(listing: ParsedListing, stage: DealStage = 'scanner'): Promise<PipelineDeal> {
    const dealId = `deal_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const deal: PipelineDeal = {
      ...listing,
      dealId,
      stage,
      priority: this.calculatePriority(listing),
      
      addedToPipeline: new Date().toISOString(),
      stageHistory: [{
        stage,
        enteredAt: new Date().toISOString()
      }],
      
      costs: {
        purchase: listing.price,
        total: listing.price
      },
      
      revenue: {
        total: 0
      },
      
      messages: [],
      tasks: this.generateInitialTasks(listing, stage),
      notes: '',
      tags: this.generateTags(listing),
      
      autoAdvance: true,
      notifications: true,
      
      metrics: {
        timeInStage: 0,
        totalTime: 0,
        touchPoints: 0
      },
      
      actions: [{
        type: 'added_to_pipeline',
        timestamp: new Date().toISOString(),
        data: { source: 'scanner', stage }
      }]
    };
    
    this.deals.set(dealId, deal);
    await this.saveDeals();
    
    this.emit({
      type: 'deal_added',
      deal,
      stage
    });
    
    // Auto-advance if configured
    if (deal.autoAdvance && stage === 'scanner') {
      setTimeout(() => this.advanceStage(dealId, 'analysis'), 1000);
    }
    
    return deal;
  }
  
  /**
   * Advance deal to next stage
   */
  async advanceStage(dealId: string, toStage: DealStage, notes?: string): Promise<boolean> {
    const deal = this.deals.get(dealId);
    if (!deal) return false;
    
    // Check if transition is valid
    const transition = this.transitions.find(t => 
      t.from === deal.stage && t.to === toStage
    );
    
    if (!transition) {
      console.error(`Invalid transition: ${deal.stage} → ${toStage}`);
      return false;
    }
    
    // Check condition if any
    if (transition.condition && !transition.condition(deal)) {
      console.error(`Transition condition not met: ${deal.stage} → ${toStage}`);
      return false;
    }
    
    // Update stage history
    const currentStage = deal.stageHistory[deal.stageHistory.length - 1];
    currentStage.exitedAt = new Date().toISOString();
    
    deal.stageHistory.push({
      stage: toStage,
      enteredAt: new Date().toISOString(),
      reason: notes
    });
    
    // Update current stage
    const oldStage = deal.stage;
    deal.stage = toStage;
    
    // Log action
    deal.actions.push({
      type: 'stage_changed',
      timestamp: new Date().toISOString(),
      notes,
      data: { from: oldStage, to: toStage }
    });
    
    // Update metrics
    deal.metrics.touchPoints++;
    
    // Run transition action if any
    if (transition.action) {
      await transition.action(deal);
    }
    
    // Generate new tasks for stage
    deal.tasks.push(...this.generateTasksForStage(deal, toStage));
    
    await this.saveDeals();
    
    this.emit({
      type: 'stage_changed',
      deal,
      from: oldStage,
      to: toStage
    });
    
    // Handle stage-specific automations
    await this.handleStageAutomation(deal, toStage);
    
    return true;
  }
  
  /**
   * Update deal data
   */
  async updateDeal(dealId: string, updates: Partial<PipelineDeal>): Promise<boolean> {
    const deal = this.deals.get(dealId);
    if (!deal) return false;
    
    // Merge updates
    Object.assign(deal, updates);
    
    // Log action
    deal.actions.push({
      type: 'deal_updated',
      timestamp: new Date().toISOString(),
      data: { fields: Object.keys(updates) }
    });
    
    deal.metrics.touchPoints++;
    
    await this.saveDeals();
    
    this.emit({
      type: 'deal_updated',
      deal,
      updates
    });
    
    return true;
  }
  
  /**
   * Add message to deal
   */
  async addMessage(dealId: string, message: PipelineDeal['messages'][0]): Promise<void> {
    const deal = this.deals.get(dealId);
    if (!deal) return;
    
    deal.messages.push(message);
    deal.metrics.touchPoints++;
    
    deal.actions.push({
      type: 'message_added',
      timestamp: new Date().toISOString(),
      data: { direction: message.direction }
    });
    
    await this.saveDeals();
    
    this.emit({
      type: 'message_added',
      deal,
      message
    });
  }
  
  /**
   * Complete a task
   */
  async completeTask(dealId: string, taskId: string): Promise<void> {
    const deal = this.deals.get(dealId);
    if (!deal) return;
    
    const task = deal.tasks.find(t => t.id === taskId);
    if (!task) return;
    
    task.completed = true;
    
    deal.actions.push({
      type: 'task_completed',
      timestamp: new Date().toISOString(),
      data: { taskId, title: task.title }
    });
    
    await this.saveDeals();
    
    this.emit({
      type: 'task_completed',
      deal,
      task
    });
    
    // Check if all tasks for stage are complete
    const stageTasks = deal.tasks.filter(t => !t.completed);
    if (stageTasks.length === 0 && deal.autoAdvance) {
      // Suggest next stage
      this.suggestNextStage(deal);
    }
  }
  
  /**
   * Get deals by stage
   */
  getDealsByStage(stage?: DealStage): PipelineDeal[] {
    const deals = Array.from(this.deals.values());
    
    if (stage) {
      return deals.filter(d => d.stage === stage);
    }
    
    return deals;
  }
  
  /**
   * Get deal by ID
   */
  getDeal(dealId: string): PipelineDeal | undefined {
    return this.deals.get(dealId);
  }
  
  /**
   * Get pipeline statistics
   */
  getStats(): PipelineStats {
    const deals = Array.from(this.deals.values());
    
    const stats: PipelineStats = {
      totalDeals: deals.length,
      dealsByStage: {} as Record<DealStage, number>,
      totalInvested: 0,
      totalRevenue: 0,
      totalProfit: 0,
      avgTimeToSale: 0,
      avgROI: 0,
      successRate: 0
    };
    
    // Count by stage
    const stages: DealStage[] = ['scanner', 'analysis', 'contacted', 'negotiating', 
                                 'scheduled', 'purchased', 'testing', 'refurbing', 
                                 'listed', 'sold', 'archived'];
    
    stages.forEach(stage => {
      stats.dealsByStage[stage] = deals.filter(d => d.stage === stage).length;
    });
    
    // Financial metrics
    deals.forEach(deal => {
      stats.totalInvested += deal.costs.total;
      stats.totalRevenue += deal.revenue.total;
    });
    
    stats.totalProfit = stats.totalRevenue - stats.totalInvested;
    
    // Success metrics
    const soldDeals = deals.filter(d => d.stage === 'sold' || 
                                       (d.stage === 'archived' && d.revenue.soldPrice));
    
    if (soldDeals.length > 0) {
      stats.successRate = (soldDeals.length / deals.length) * 100;
      
      // Calculate average time to sale
      const saleTimes = soldDeals.map(d => {
        const start = new Date(d.addedToPipeline);
        const sold = d.stageHistory.find(h => h.stage === 'sold')?.enteredAt;
        if (sold) {
          return (new Date(sold).getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
        }
        return 0;
      }).filter(t => t > 0);
      
      if (saleTimes.length > 0) {
        stats.avgTimeToSale = saleTimes.reduce((a, b) => a + b) / saleTimes.length;
      }
      
      // Calculate average ROI
      const rois = soldDeals.map(d => 
        ((d.revenue.total - d.costs.total) / d.costs.total) * 100
      ).filter(r => r > -100);
      
      if (rois.length > 0) {
        stats.avgROI = rois.reduce((a, b) => a + b) / rois.length;
      }
    }
    
    return stats;
  }
  
  /**
   * Search deals
   */
  searchDeals(query: string): PipelineDeal[] {
    const deals = Array.from(this.deals.values());
    const lowerQuery = query.toLowerCase();
    
    return deals.filter(deal => 
      deal.title.toLowerCase().includes(lowerQuery) ||
      deal.description.toLowerCase().includes(lowerQuery) ||
      deal.specs.cpu?.model.toLowerCase().includes(lowerQuery) ||
      deal.specs.gpu?.model.toLowerCase().includes(lowerQuery) ||
      deal.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
    );
  }
  
  /**
   * Archive old deals
   */
  async archiveOldDeals(daysOld: number = 90): Promise<number> {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - daysOld);
    
    let archived = 0;
    
    for (const [dealId, deal] of this.deals) {
      if (deal.stage !== 'archived' && new Date(deal.addedToPipeline) < cutoff) {
        await this.advanceStage(dealId, 'archived', 'Auto-archived due to age');
        archived++;
      }
    }
    
    return archived;
  }
  
  /**
   * Subscribe to events
   */
  subscribe(listener: (event: PipelineEvent) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
  
  private emit(event: PipelineEvent): void {
    this.listeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('[Pipeline] Listener error:', error);
      }
    });
  }
  
  private calculatePriority(listing: ParsedListing): PipelineDeal['priority'] {
    if (listing.analysis.roi > 100 && listing.flags.isUrgent) return 'urgent';
    if (listing.analysis.roi > 50) return 'high';
    if (listing.analysis.roi > 20) return 'normal';
    return 'low';
  }
  
  private generateTags(listing: ParsedListing): string[] {
    const tags = [...listing.keywords];
    
    if (listing.analysis.dealQuality === 'excellent') tags.push('hot-deal');
    if (listing.flags.isBundle) tags.push('bundle');
    if (listing.flags.isUrgent) tags.push('urgent');
    if (listing.scores.legitimacy < 60) tags.push('verify');
    
    return tags;
  }
  
  private generateInitialTasks(listing: ParsedListing, stage: DealStage): PipelineDeal['tasks'] {
    const tasks: PipelineDeal['tasks'] = [];
    
    if (stage === 'scanner' || stage === 'analysis') {
      tasks.push({
        id: `task_${Date.now()}_1`,
        title: 'Review listing details',
        priority: 'high',
        completed: false
      });
      
      if (listing.scores.legitimacy < 70) {
        tasks.push({
          id: `task_${Date.now()}_2`,
          title: 'Verify seller legitimacy',
          priority: 'high',
          completed: false
        });
      }
      
      tasks.push({
        id: `task_${Date.now()}_3`,
        title: 'Research market comps',
        priority: 'normal',
        completed: false
      });
    }
    
    return tasks;
  }
  
  private generateTasksForStage(deal: PipelineDeal, stage: DealStage): PipelineDeal['tasks'] {
    const tasks: PipelineDeal['tasks'] = [];
    const taskIdPrefix = `task_${Date.now()}`;
    
    switch (stage) {
      case 'contacted':
        tasks.push({
          id: `${taskIdPrefix}_1`,
          title: 'Send initial message',
          priority: 'high',
          completed: false
        });
        break;
        
      case 'negotiating':
        tasks.push({
          id: `${taskIdPrefix}_1`,
          title: 'Make offer',
          priority: 'high',
          completed: false
        });
        break;
        
      case 'scheduled':
        tasks.push({
          id: `${taskIdPrefix}_1`,
          title: 'Confirm pickup time',
          priority: 'high',
          completed: false,
          due: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
        });
        break;
        
      case 'purchased':
        tasks.push({
          id: `${taskIdPrefix}_1`,
          title: 'Update actual purchase price',
          priority: 'high',
          completed: false
        });
        break;
        
      case 'testing':
        tasks.push(
          {
            id: `${taskIdPrefix}_1`,
            title: 'Run hardware diagnostics',
            priority: 'high',
            completed: false
          },
          {
            id: `${taskIdPrefix}_2`,
            title: 'Test all components',
            priority: 'high',
            completed: false
          }
        );
        break;
        
      case 'refurbing':
        tasks.push({
          id: `${taskIdPrefix}_1`,
          title: 'Clean and photograph',
          priority: 'normal',
          completed: false
        });
        break;
        
      case 'listed':
        tasks.push({
          id: `${taskIdPrefix}_1`,
          title: 'Create listing',
          priority: 'high',
          completed: false
        });
        break;
    }
    
    return tasks;
  }
  
  private async handleStageAutomation(deal: PipelineDeal, stage: DealStage): Promise<void> {
    if (!deal.autoAdvance) return;
    
    switch (stage) {
      case 'analysis':
        // Auto-advance poor deals to archive
        if (deal.analysis.dealQuality === 'poor') {
          setTimeout(() => {
            this.advanceStage(deal.dealId, 'archived', 'Poor deal - auto archived');
          }, 5000);
        }
        break;
        
      case 'contacted':
        // Set reminder to follow up
        const followUpTask: PipelineDeal['tasks'][0] = {
          id: `task_followup_${Date.now()}`,
          title: 'Follow up if no response',
          priority: 'normal',
          completed: false,
          due: new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString()
        };
        deal.tasks.push(followUpTask);
        break;
    }
  }
  
  private suggestNextStage(deal: PipelineDeal): void {
    const suggestions: Partial<Record<DealStage, DealStage>> = {
      'analysis': 'contacted',
      'contacted': 'negotiating',
      'negotiating': 'scheduled',
      'scheduled': 'purchased',
      'purchased': 'testing',
      'testing': 'refurbing',
      'refurbing': 'listed',
      'listed': 'sold'
    };
    
    const nextStage = suggestions[deal.stage];
    if (nextStage) {
      this.emit({
        type: 'stage_suggested',
        deal,
        suggestedStage: nextStage
      });
    }
  }
  
  private async loadDeals(): Promise<void> {
    try {
      const { pipelineDeals = {} } = await chrome.storage.local.get(['pipelineDeals']);
      
      Object.entries(pipelineDeals).forEach(([id, deal]) => {
        this.deals.set(id, deal as PipelineDeal);
      });
      
      console.log('[Pipeline] Loaded', this.deals.size, 'deals');
    } catch (error) {
      console.error('[Pipeline] Failed to load deals:', error);
    }
  }
  
  private async saveDeals(): Promise<void> {
    try {
      const pipelineDeals: Record<string, PipelineDeal> = {};
      
      this.deals.forEach((deal, id) => {
        pipelineDeals[id] = deal;
      });
      
      await chrome.storage.local.set({ pipelineDeals });
    } catch (error) {
      console.error('[Pipeline] Failed to save deals:', error);
    }
  }
  
  private startAutoSave(): void {
    // Auto-save every 30 seconds
    setInterval(() => {
      this.saveDeals();
    }, 30000);
  }
  
  private startMetricsUpdater(): void {
    // Update time metrics every minute
    setInterval(() => {
      const now = new Date();
      
      this.deals.forEach(deal => {
        // Update time in current stage
        const currentStage = deal.stageHistory[deal.stageHistory.length - 1];
        if (!currentStage.exitedAt) {
          const stageTime = (now.getTime() - new Date(currentStage.enteredAt).getTime()) / (1000 * 60);
          deal.metrics.timeInStage = Math.round(stageTime);
        }
        
        // Update total time
        const totalTime = (now.getTime() - new Date(deal.addedToPipeline).getTime()) / (1000 * 60);
        deal.metrics.totalTime = Math.round(totalTime);
      });
    }, 60000);
  }
}

// Event types
export type PipelineEvent = 
  | { type: 'deal_added'; deal: PipelineDeal; stage: DealStage }
  | { type: 'stage_changed'; deal: PipelineDeal; from: DealStage; to: DealStage }
  | { type: 'deal_updated'; deal: PipelineDeal; updates: Partial<PipelineDeal> }
  | { type: 'message_added'; deal: PipelineDeal; message: PipelineDeal['messages'][0] }
  | { type: 'task_completed'; deal: PipelineDeal; task: PipelineDeal['tasks'][0] }
  | { type: 'stage_suggested'; deal: PipelineDeal; suggestedStage: DealStage };

// Export singleton
export const pipelineManager = PipelineManager.getInstance();