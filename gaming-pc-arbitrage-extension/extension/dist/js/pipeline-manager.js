// PipelineManager v3.5.0 - Deal pipeline state management
class PipelineManager {
  constructor() {
    this.deals = new Map();
    this.stages = [
      'scanner',
      'analysis', 
      'contacted',
      'negotiating',
      'scheduled',
      'purchased',
      'testing',
      'listed',
      'sold'
    ];
    
    this.init();
  }
  
  async init() {
    const stored = await chrome.storage.local.get(['deals']);
    if (stored.deals) {
      stored.deals.forEach(deal => {
        this.deals.set(deal.id, deal);
      });
    }
  }
  
  createDeal(listing) {
    const deal = {
      id: Date.now().toString(),
      listing: listing,
      stage: 'scanner',
      createdAt: Date.now(),
      updatedAt: Date.now(),
      notes: [],
      tasks: [],
      metrics: {
        daysInPipeline: 0,
        touchpoints: 0
      }
    };
    
    this.deals.set(deal.id, deal);
    this.save();
    
    return deal;
  }
  
  updateStage(dealId, newStage) {
    const deal = this.deals.get(dealId);
    if (!deal) throw new Error('Deal not found');
    
    const oldStage = deal.stage;
    deal.stage = newStage;
    deal.updatedAt = Date.now();
    
    // Update metrics
    deal.metrics.touchpoints++;
    deal.metrics.daysInPipeline = Math.floor(
      (Date.now() - deal.createdAt) / (1000 * 60 * 60 * 24)
    );
    
    this.save();
    
    return { deal, oldStage, newStage };
  }
  
  addNote(dealId, note) {
    const deal = this.deals.get(dealId);
    if (!deal) throw new Error('Deal not found');
    
    deal.notes.push({
      id: Date.now().toString(),
      text: note,
      timestamp: Date.now()
    });
    
    deal.updatedAt = Date.now();
    this.save();
    
    return deal;
  }
  
  addTask(dealId, task) {
    const deal = this.deals.get(dealId);
    if (!deal) throw new Error('Deal not found');
    
    deal.tasks.push({
      id: Date.now().toString(),
      text: task,
      completed: false,
      createdAt: Date.now()
    });
    
    deal.updatedAt = Date.now();
    this.save();
    
    return deal;
  }
  
  completeTask(dealId, taskId) {
    const deal = this.deals.get(dealId);
    if (!deal) throw new Error('Deal not found');
    
    const task = deal.tasks.find(t => t.id === taskId);
    if (task) {
      task.completed = true;
      task.completedAt = Date.now();
      deal.updatedAt = Date.now();
      this.save();
    }
    
    return deal;
  }
  
  getDealsByStage(stage) {
    return Array.from(this.deals.values())
      .filter(deal => deal.stage === stage);
  }
  
  getStats() {
    const stats = {
      total: this.deals.size,
      byStage: {},
      avgDaysInPipeline: 0,
      completionRate: 0
    };
    
    let totalDays = 0;
    let completed = 0;
    
    this.deals.forEach(deal => {
      stats.byStage[deal.stage] = (stats.byStage[deal.stage] || 0) + 1;
      totalDays += deal.metrics.daysInPipeline;
      
      if (deal.stage === 'sold') {
        completed++;
      }
    });
    
    stats.avgDaysInPipeline = this.deals.size > 0 
      ? totalDays / this.deals.size 
      : 0;
      
    stats.completionRate = this.deals.size > 0
      ? (completed / this.deals.size) * 100
      : 0;
    
    return stats;
  }
  
  async save() {
    const dealsArray = Array.from(this.deals.values());
    await chrome.storage.local.set({ deals: dealsArray });
  }
}

window.pipelineManager = new PipelineManager();
