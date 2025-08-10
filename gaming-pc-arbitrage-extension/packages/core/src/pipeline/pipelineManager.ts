/**
 * Pipeline Manager
 * Track and manage deals through their lifecycle
 */

import type { Deal } from '../types';
import type { DealStage } from '../automation/dealFlow';

export interface PipelineStage {
  name: DealStage;
  deals: Deal[];
  metrics: {
    count: number;
    totalValue: number;
    avgAge: number; // days
    conversionRate: number;
  };
}

export interface PipelineMetrics {
  stages: PipelineStage[];
  velocity: {
    overall: number; // deals/day
    byStage: Record<DealStage, number>;
  };
  conversion: {
    overall: number;
    byStage: Record<string, number>;
  };
  bottlenecks: Array<{
    stage: DealStage;
    severity: 'high' | 'medium' | 'low';
    reason: string;
    impact: number; // lost deals
  }>;
  forecast: {
    expectedRevenue: number;
    expectedDeals: number;
    timeframe: number; // days
  };
}

export interface StageTransitionHistory {
  dealId: string;
  from: DealStage;
  to: DealStage;
  timestamp: Date;
  duration: number; // hours in previous stage
  metadata?: Record<string, any>;
}

/**
 * Build pipeline view
 */
export function buildPipeline(deals: Deal[]): PipelineStage[] {
  const stages: DealStage[] = [
    'discovered',
    'evaluating', 
    'negotiating',
    'scheduled',
    'acquired',
    'testing',
    'listing',
    'sold',
    'completed',
  ];
  
  const pipeline: PipelineStage[] = [];
  const now = new Date();
  
  for (const stage of stages) {
    const stageDeals = deals.filter(d => d.stage === stage);
    
    // Calculate metrics
    const totalValue = stageDeals.reduce((sum, d) => 
      sum + (d.purchasePrice || d.askingPrice || 0), 0
    );
    
    const avgAge = stageDeals.length > 0
      ? stageDeals.reduce((sum, d) => {
          const age = (now.getTime() - d.metadata.createdAt.getTime()) / (1000 * 60 * 60 * 24);
          return sum + age;
        }, 0) / stageDeals.length
      : 0;
    
    // Simple conversion rate (% that move to next stage)
    const nextStageIndex = stages.indexOf(stage) + 1;
    const conversionRate = nextStageIndex < stages.length
      ? calculateConversionRate(deals, stage, stages[nextStageIndex])
      : 100; // Completed stage
    
    pipeline.push({
      name: stage,
      deals: stageDeals,
      metrics: {
        count: stageDeals.length,
        totalValue,
        avgAge,
        conversionRate,
      },
    });
  }
  
  return pipeline;
}

/**
 * Calculate pipeline metrics
 */
export function calculatePipelineMetrics(
  deals: Deal[],
  history: StageTransitionHistory[]
): PipelineMetrics {
  const pipeline = buildPipeline(deals);
  
  // Calculate velocity
  const velocity = calculateVelocity(history);
  
  // Calculate conversion rates
  const conversion = calculateConversionRates(deals, history);
  
  // Identify bottlenecks
  const bottlenecks = identifyBottlenecks(pipeline, history);
  
  // Generate forecast
  const forecast = generateForecast(pipeline, velocity, conversion);
  
  return {
    stages: pipeline,
    velocity,
    conversion,
    bottlenecks,
    forecast,
  };
}

/**
 * Get deals stuck in stage
 */
export function getStuckDeals(
  deals: Deal[],
  thresholds: Partial<Record<DealStage, number>> = {}
): Array<{
  deal: Deal;
  stage: DealStage;
  daysInStage: number;
  threshold: number;
  priority: 'urgent' | 'high' | 'medium';
}> {
  const defaultThresholds: Record<DealStage, number> = {
    discovered: 2,
    evaluating: 3,
    negotiating: 5,
    scheduled: 1,
    acquired: 1,
    testing: 2,
    listing: 7,
    sold: 3,
    completed: 1,
    cancelled: 0,
  };
  
  const stuck: any[] = [];
  const now = new Date();
  
  for (const deal of deals) {
    if (deal.stage === 'completed' || deal.stage === 'cancelled') continue;
    
    const threshold = thresholds[deal.stage as DealStage] || 
                     defaultThresholds[deal.stage as DealStage];
    
    const lastUpdate = deal.metadata.updatedAt || deal.metadata.createdAt;
    const daysInStage = (now.getTime() - lastUpdate.getTime()) / (1000 * 60 * 60 * 24);
    
    if (daysInStage > threshold) {
      let priority: 'urgent' | 'high' | 'medium' = 'medium';
      if (daysInStage > threshold * 3) priority = 'urgent';
      else if (daysInStage > threshold * 2) priority = 'high';
      
      stuck.push({
        deal,
        stage: deal.stage,
        daysInStage,
        threshold,
        priority,
      });
    }
  }
  
  return stuck.sort((a, b) => b.daysInStage - a.daysInStage);
}

/**
 * Predict stage completion
 */
export function predictStageCompletion(
  deal: Deal,
  history: StageTransitionHistory[]
): {
  estimatedDays: number;
  confidence: number;
  factors: Array<{ factor: string; impact: number }>;
} {
  const stage = deal.stage as DealStage;
  
  // Get historical data for this stage
  const stageHistory = history.filter(h => h.from === stage);
  if (stageHistory.length === 0) {
    return {
      estimatedDays: 3, // Default
      confidence: 0.3,
      factors: [{ factor: 'No historical data', impact: -0.7 }],
    };
  }
  
  // Calculate average duration
  const avgDuration = stageHistory.reduce((sum, h) => 
    sum + h.duration, 0
  ) / stageHistory.length / 24; // Convert to days
  
  // Adjust based on deal characteristics
  const factors: Array<{ factor: string; impact: number }> = [];
  let adjustment = 1.0;
  
  // High value deals take longer
  if (deal.purchasePrice && deal.purchasePrice > 1000) {
    adjustment *= 1.2;
    factors.push({ factor: 'High value deal', impact: 0.2 });
  }
  
  // Deals with issues take longer
  if (deal.risk && deal.risk.score > 70) {
    adjustment *= 1.5;
    factors.push({ factor: 'High risk', impact: 0.5 });
  }
  
  // Recently active deals move faster
  const daysSinceUpdate = (new Date().getTime() - deal.metadata.updatedAt.getTime()) / (1000 * 60 * 60 * 24);
  if (daysSinceUpdate < 1) {
    adjustment *= 0.8;
    factors.push({ factor: 'Recently active', impact: -0.2 });
  }
  
  const estimatedDays = avgDuration * adjustment;
  const confidence = Math.min(0.9, 0.3 + (stageHistory.length / 50));
  
  return { estimatedDays, confidence, factors };
}

/**
 * Generate pipeline report
 */
export function generatePipelineReport(
  metrics: PipelineMetrics,
  period: { start: Date; end: Date }
): {
  summary: string;
  highlights: string[];
  concerns: string[];
  recommendations: string[];
} {
  const summary = `Pipeline contains ${metrics.stages.reduce((sum, s) => sum + s.metrics.count, 0)} deals ` +
    `worth $${Math.round(metrics.stages.reduce((sum, s) => sum + s.metrics.totalValue, 0)).toLocaleString()}. ` +
    `Overall velocity: ${metrics.velocity.overall.toFixed(1)} deals/day, ` +
    `conversion rate: ${(metrics.conversion.overall * 100).toFixed(1)}%`;
  
  const highlights: string[] = [];
  const concerns: string[] = [];
  const recommendations: string[] = [];
  
  // Find high-performing stages
  const highConverters = metrics.stages.filter(s => s.metrics.conversionRate > 80);
  if (highConverters.length > 0) {
    highlights.push(
      `Strong conversion in: ${highConverters.map(s => s.name).join(', ')}`
    );
  }
  
  // Find concerning stages
  const lowConverters = metrics.stages.filter(s => 
    s.metrics.conversionRate < 50 && s.metrics.count > 0
  );
  if (lowConverters.length > 0) {
    concerns.push(
      `Low conversion in: ${lowConverters.map(s => s.name).join(', ')}`
    );
  }
  
  // Check for bottlenecks
  const severeBottlenecks = metrics.bottlenecks.filter(b => b.severity === 'high');
  if (severeBottlenecks.length > 0) {
    concerns.push(
      `Critical bottlenecks: ${severeBottlenecks.map(b => b.stage).join(', ')}`
    );
  }
  
  // Generate recommendations
  if (metrics.velocity.overall < 1) {
    recommendations.push('Increase sourcing to maintain pipeline flow');
  }
  
  if (metrics.conversion.overall < 0.3) {
    recommendations.push('Review qualification criteria - too many deals failing');
  }
  
  const stuckInNegotiation = metrics.stages.find(s => s.name === 'negotiating');
  if (stuckInNegotiation && stuckInNegotiation.metrics.avgAge > 5) {
    recommendations.push('Speed up negotiation phase - consider more aggressive initial offers');
  }
  
  return { summary, highlights, concerns, recommendations };
}

// Helper functions
function calculateConversionRate(
  deals: Deal[],
  fromStage: DealStage,
  toStage: DealStage
): number {
  const fromCount = deals.filter(d => d.stage === fromStage).length;
  const movedCount = deals.filter(d => {
    // Would need transition history to be accurate
    return d.stage === toStage || 
           ['completed', 'sold'].includes(d.stage);
  }).length;
  
  return fromCount > 0 ? (movedCount / fromCount) * 100 : 0;
}

function calculateVelocity(history: StageTransitionHistory[]): {
  overall: number;
  byStage: Record<DealStage, number>;
} {
  const now = new Date();
  const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
  
  const recentTransitions = history.filter(h => h.timestamp > thirtyDaysAgo);
  const overall = recentTransitions.length / 30;
  
  const byStage: Record<string, number> = {};
  const stages: DealStage[] = [
    'discovered', 'evaluating', 'negotiating', 'scheduled',
    'acquired', 'testing', 'listing', 'sold', 'completed', 'cancelled'
  ];
  
  for (const stage of stages) {
    const stageTransitions = recentTransitions.filter(h => h.from === stage);
    byStage[stage] = stageTransitions.length / 30;
  }
  
  return { overall, byStage: byStage as Record<DealStage, number> };
}

function calculateConversionRates(
  deals: Deal[],
  history: StageTransitionHistory[]
): {
  overall: number;
  byStage: Record<string, number>;
} {
  const completed = deals.filter(d => d.stage === 'completed').length;
  const total = deals.length;
  const overall = total > 0 ? completed / total : 0;
  
  const byStage: Record<string, number> = {};
  const stages: DealStage[] = [
    'discovered', 'evaluating', 'negotiating', 'scheduled',
    'acquired', 'testing', 'listing', 'sold'
  ];
  
  for (let i = 0; i < stages.length - 1; i++) {
    const fromStage = stages[i];
    const toStage = stages[i + 1];
    
    const transitions = history.filter(h => 
      h.from === fromStage && h.to === toStage
    ).length;
    
    const attempts = history.filter(h => h.from === fromStage).length;
    
    byStage[`${fromStage}_to_${toStage}`] = attempts > 0 ? transitions / attempts : 0;
  }
  
  return { overall, byStage };
}

function identifyBottlenecks(
  pipeline: PipelineStage[],
  history: StageTransitionHistory[]
): Array<{
  stage: DealStage;
  severity: 'high' | 'medium' | 'low';
  reason: string;
  impact: number;
}> {
  const bottlenecks: any[] = [];
  
  for (const stage of pipeline) {
    // Check for high deal count
    if (stage.metrics.count > 10) {
      bottlenecks.push({
        stage: stage.name,
        severity: stage.metrics.count > 20 ? 'high' : 'medium',
        reason: 'High deal accumulation',
        impact: stage.metrics.count - 10,
      });
    }
    
    // Check for low conversion
    if (stage.metrics.conversionRate < 50 && stage.metrics.count > 0) {
      bottlenecks.push({
        stage: stage.name,
        severity: stage.metrics.conversionRate < 30 ? 'high' : 'medium',
        reason: 'Low conversion rate',
        impact: Math.floor(stage.metrics.count * (1 - stage.metrics.conversionRate / 100)),
      });
    }
    
    // Check for long average age
    if (stage.metrics.avgAge > 7) {
      bottlenecks.push({
        stage: stage.name,
        severity: stage.metrics.avgAge > 14 ? 'high' : 'low',
        reason: 'Deals aging in stage',
        impact: stage.metrics.count,
      });
    }
  }
  
  return bottlenecks;
}

function generateForecast(
  pipeline: PipelineStage[],
  velocity: any,
  conversion: any
): {
  expectedRevenue: number;
  expectedDeals: number;
  timeframe: number;
} {
  // Simple 30-day forecast
  const activeDealCount = pipeline
    .filter(s => !['completed', 'cancelled'].includes(s.name))
    .reduce((sum, s) => sum + s.metrics.count, 0);
  
  const avgDealValue = pipeline.reduce((sum, s) => 
    sum + s.metrics.totalValue, 0
  ) / Math.max(1, activeDealCount);
  
  const expectedDeals = Math.floor(activeDealCount * conversion.overall);
  const expectedRevenue = expectedDeals * avgDealValue * 1.3; // 30% markup
  
  return {
    expectedRevenue,
    expectedDeals,
    timeframe: 30,
  };
}