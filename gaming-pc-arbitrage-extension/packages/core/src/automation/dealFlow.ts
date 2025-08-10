/**
 * Deal Flow Automation
 * Automated stage transitions and workflow triggers
 */

import type { Deal } from '../types';

export type DealStage = 
  | 'discovered'
  | 'evaluating'
  | 'negotiating'
  | 'scheduled'
  | 'acquired'
  | 'testing'
  | 'listing'
  | 'sold'
  | 'completed'
  | 'cancelled';

export interface StageTransition {
  from: DealStage;
  to: DealStage;
  trigger: TransitionTrigger;
  conditions?: TransitionCondition[];
  actions: TransitionAction[];
  automatic: boolean;
}

export interface TransitionTrigger {
  type: 'manual' | 'time' | 'event' | 'condition';
  value?: any;
}

export interface TransitionCondition {
  field: string;
  operator: 'eq' | 'gt' | 'lt' | 'gte' | 'lte' | 'contains' | 'exists';
  value: any;
}

export interface TransitionAction {
  type: 'notify' | 'email' | 'calendar' | 'followup' | 'log' | 'update';
  config: Record<string, any>;
}

export interface AutomationRule {
  id: string;
  name: string;
  enabled: boolean;
  stage?: DealStage;
  conditions: TransitionCondition[];
  actions: TransitionAction[];
  priority: number;
}

// Default stage transitions
export const DEFAULT_TRANSITIONS: StageTransition[] = [
  // Discovery → Evaluation
  {
    from: 'discovered',
    to: 'evaluating',
    trigger: { type: 'manual' },
    actions: [
      { type: 'log', config: { message: 'Started evaluation' } },
      { type: 'notify', config: { title: 'New deal to evaluate' } },
    ],
    automatic: false,
  },
  
  // Evaluation → Negotiation
  {
    from: 'evaluating',
    to: 'negotiating',
    trigger: { type: 'condition' },
    conditions: [
      { field: 'roi', operator: 'gt', value: 20 },
      { field: 'risk.score', operator: 'lt', value: 70 },
    ],
    actions: [
      { type: 'notify', config: { title: 'Good deal - start negotiation' } },
      { type: 'followup', config: { hours: 24, message: 'Follow up on offer' } },
    ],
    automatic: true,
  },
  
  // Negotiation → Scheduled
  {
    from: 'negotiating',
    to: 'scheduled',
    trigger: { type: 'event', value: 'pickup_scheduled' },
    actions: [
      { type: 'calendar', config: { type: 'pickup' } },
      { type: 'notify', config: { title: 'Pickup scheduled', urgent: true } },
    ],
    automatic: true,
  },
  
  // Scheduled → Acquired
  {
    from: 'scheduled',
    to: 'acquired',
    trigger: { type: 'manual' },
    actions: [
      { type: 'log', config: { message: 'Item acquired' } },
      { type: 'update', config: { field: 'acquiredAt', value: 'now' } },
    ],
    automatic: false,
  },
  
  // Acquired → Testing
  {
    from: 'acquired',
    to: 'testing',
    trigger: { type: 'time', value: { hours: 2 } },
    actions: [
      { type: 'notify', config: { title: 'Time to test the system' } },
    ],
    automatic: true,
  },
  
  // Testing → Listing
  {
    from: 'testing',
    to: 'listing',
    trigger: { type: 'condition' },
    conditions: [
      { field: 'testResults.passed', operator: 'eq', value: true },
    ],
    actions: [
      { type: 'notify', config: { title: 'Ready to list' } },
      { type: 'update', config: { field: 'listingReady', value: true } },
    ],
    automatic: true,
  },
  
  // Listing → Sold
  {
    from: 'listing',
    to: 'sold',
    trigger: { type: 'event', value: 'buyer_confirmed' },
    actions: [
      { type: 'notify', config: { title: 'Item sold!', sound: true } },
      { type: 'update', config: { field: 'soldAt', value: 'now' } },
    ],
    automatic: true,
  },
  
  // Sold → Completed
  {
    from: 'sold',
    to: 'completed',
    trigger: { type: 'manual' },
    actions: [
      { type: 'log', config: { message: 'Deal completed' } },
      { type: 'update', config: { field: 'completedAt', value: 'now' } },
    ],
    automatic: false,
  },
];

// Default automation rules
export const DEFAULT_AUTOMATION_RULES: AutomationRule[] = [
  // Auto-reject low ROI
  {
    id: 'auto-reject-low-roi',
    name: 'Auto-reject deals with ROI < 10%',
    enabled: true,
    stage: 'evaluating',
    conditions: [
      { field: 'roi', operator: 'lt', value: 10 },
    ],
    actions: [
      { type: 'update', config: { field: 'stage', value: 'cancelled' } },
      { type: 'log', config: { message: 'Auto-rejected: Low ROI' } },
    ],
    priority: 100,
  },
  
  // High-value alert
  {
    id: 'high-value-alert',
    name: 'Alert on high-value deals',
    enabled: true,
    conditions: [
      { field: 'estimatedProfit', operator: 'gt', value: 500 },
    ],
    actions: [
      { type: 'notify', config: { title: 'High-value deal!', urgent: true } },
      { type: 'email', config: { template: 'high-value-alert' } },
    ],
    priority: 90,
  },
  
  // Stale negotiation reminder
  {
    id: 'stale-negotiation',
    name: 'Remind on stale negotiations',
    enabled: true,
    stage: 'negotiating',
    conditions: [
      { field: 'lastActivityDays', operator: 'gt', value: 3 },
    ],
    actions: [
      { type: 'notify', config: { title: 'Follow up needed' } },
      { type: 'followup', config: { hours: 4 } },
    ],
    priority: 80,
  },
  
  // Price drop opportunity
  {
    id: 'price-drop-opportunity',
    name: 'Re-engage on price drops',
    enabled: true,
    stage: 'evaluating',
    conditions: [
      { field: 'priceDropPercent', operator: 'gt', value: 10 },
    ],
    actions: [
      { type: 'notify', config: { title: 'Price dropped!', sound: true } },
      { type: 'update', config: { field: 'priority', value: 'high' } },
    ],
    priority: 85,
  },
];

/**
 * Check if transition is allowed
 */
export function canTransition(
  deal: Deal,
  from: DealStage,
  to: DealStage,
  transitions: StageTransition[] = DEFAULT_TRANSITIONS
): { allowed: boolean; reason?: string } {
  // Find applicable transition
  const transition = transitions.find(t => t.from === from && t.to === to);
  
  if (!transition) {
    return { allowed: false, reason: 'No transition path defined' };
  }
  
  // Check conditions
  if (transition.conditions) {
    for (const condition of transition.conditions) {
      if (!evaluateCondition(deal, condition)) {
        return { 
          allowed: false, 
          reason: `Condition not met: ${condition.field} ${condition.operator} ${condition.value}` 
        };
      }
    }
  }
  
  return { allowed: true };
}

/**
 * Execute stage transition
 */
export function executeTransition(
  deal: Deal,
  to: DealStage,
  transitions: StageTransition[] = DEFAULT_TRANSITIONS
): {
  success: boolean;
  actions: TransitionAction[];
  error?: string;
} {
  const from = deal.stage as DealStage;
  const canTransitionResult = canTransition(deal, from, to, transitions);
  
  if (!canTransitionResult.allowed) {
    return {
      success: false,
      actions: [],
      error: canTransitionResult.reason,
    };
  }
  
  const transition = transitions.find(t => t.from === from && t.to === to);
  if (!transition) {
    return {
      success: false,
      actions: [],
      error: 'Transition not found',
    };
  }
  
  return {
    success: true,
    actions: transition.actions,
  };
}

/**
 * Evaluate automation rules
 */
export function evaluateAutomationRules(
  deal: Deal,
  rules: AutomationRule[] = DEFAULT_AUTOMATION_RULES
): AutomationRule[] {
  const applicableRules = rules
    .filter(rule => rule.enabled)
    .filter(rule => !rule.stage || rule.stage === deal.stage)
    .filter(rule => {
      // Check all conditions
      return rule.conditions.every(condition => evaluateCondition(deal, condition));
    })
    .sort((a, b) => b.priority - a.priority);
  
  return applicableRules;
}

/**
 * Evaluate a single condition
 */
function evaluateCondition(deal: any, condition: TransitionCondition): boolean {
  const value = getNestedValue(deal, condition.field);
  
  switch (condition.operator) {
    case 'eq':
      return value === condition.value;
    case 'gt':
      return value > condition.value;
    case 'lt':
      return value < condition.value;
    case 'gte':
      return value >= condition.value;
    case 'lte':
      return value <= condition.value;
    case 'contains':
      return String(value).includes(String(condition.value));
    case 'exists':
      return value !== undefined && value !== null;
    default:
      return false;
  }
}

/**
 * Get nested object value
 */
function getNestedValue(obj: any, path: string): any {
  return path.split('.').reduce((current, key) => current?.[key], obj);
}

/**
 * Get next suggested stages
 */
export function getNextStages(
  currentStage: DealStage,
  transitions: StageTransition[] = DEFAULT_TRANSITIONS
): DealStage[] {
  return transitions
    .filter(t => t.from === currentStage)
    .map(t => t.to);
}

/**
 * Get stage metadata
 */
export function getStageMetadata(stage: DealStage): {
  label: string;
  color: string;
  icon: string;
  description: string;
} {
  const metadata: Record<DealStage, any> = {
    discovered: {
      label: 'Discovered',
      color: 'gray',
      icon: '🔍',
      description: 'New listing found',
    },
    evaluating: {
      label: 'Evaluating',
      color: 'blue',
      icon: '📊',
      description: 'Analyzing deal potential',
    },
    negotiating: {
      label: 'Negotiating',
      color: 'yellow',
      icon: '💬',
      description: 'In negotiation with seller',
    },
    scheduled: {
      label: 'Scheduled',
      color: 'purple',
      icon: '📅',
      description: 'Pickup scheduled',
    },
    acquired: {
      label: 'Acquired',
      color: 'indigo',
      icon: '📦',
      description: 'Item in possession',
    },
    testing: {
      label: 'Testing',
      color: 'orange',
      icon: '🔧',
      description: 'Testing functionality',
    },
    listing: {
      label: 'Listing',
      color: 'teal',
      icon: '📢',
      description: 'Listed for sale',
    },
    sold: {
      label: 'Sold',
      color: 'green',
      icon: '💰',
      description: 'Sold to buyer',
    },
    completed: {
      label: 'Completed',
      color: 'green',
      icon: '✅',
      description: 'Deal finalized',
    },
    cancelled: {
      label: 'Cancelled',
      color: 'red',
      icon: '❌',
      description: 'Deal cancelled',
    },
  };
  
  return metadata[stage] || {
    label: stage,
    color: 'gray',
    icon: '❓',
    description: 'Unknown stage',
  };
}