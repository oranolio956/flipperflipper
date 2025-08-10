/**
 * Workflow Templates
 * Pre-built workflows for common scenarios
 */

import type { StageTransition, AutomationRule } from './dealFlow';

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: 'sourcing' | 'negotiation' | 'fulfillment' | 'custom';
  transitions: StageTransition[];
  rules: AutomationRule[];
  settings: Record<string, any>;
}

export const WORKFLOW_TEMPLATES: WorkflowTemplate[] = [
  // Quick Flip Workflow
  {
    id: 'quick-flip',
    name: 'Quick Flip (Same Day)',
    description: 'Fast turnaround for high-demand items',
    category: 'fulfillment',
    transitions: [
      {
        from: 'discovered',
        to: 'negotiating',
        trigger: { type: 'condition' },
        conditions: [
          { field: 'quickFlipScore', operator: 'gt', value: 70 },
        ],
        actions: [
          { type: 'notify', config: { title: 'Quick flip opportunity!', urgent: true } },
          { type: 'update', config: { field: 'priority', value: 'urgent' } },
        ],
        automatic: true,
      },
      {
        from: 'acquired',
        to: 'listing',
        trigger: { type: 'time', value: { minutes: 30 } },
        actions: [
          { type: 'notify', config: { title: 'List now for quick sale' } },
        ],
        automatic: true,
      },
    ],
    rules: [
      {
        id: 'quick-flip-pricing',
        name: 'Aggressive pricing for quick sale',
        enabled: true,
        stage: 'listing',
        conditions: [
          { field: 'dealType', operator: 'eq', value: 'quick-flip' },
        ],
        actions: [
          { type: 'update', config: { field: 'pricingStrategy', value: 'undercut-10%' } },
        ],
        priority: 100,
      },
    ],
    settings: {
      maxHoldTime: 24, // hours
      minROI: 15,
      autoPrice: true,
    },
  },
  
  // High-Value Negotiation
  {
    id: 'high-value',
    name: 'High-Value Deal',
    description: 'Careful approach for expensive items',
    category: 'negotiation',
    transitions: [
      {
        from: 'evaluating',
        to: 'negotiating',
        trigger: { type: 'manual' },
        conditions: [
          { field: 'value', operator: 'gt', value: 1000 },
        ],
        actions: [
          { type: 'notify', config: { title: 'Review high-value deal carefully' } },
          { type: 'followup', config: { hours: 12, message: 'Research market comps' } },
        ],
        automatic: false,
      },
    ],
    rules: [
      {
        id: 'high-value-verification',
        name: 'Extra verification for high-value',
        enabled: true,
        stage: 'evaluating',
        conditions: [
          { field: 'value', operator: 'gt', value: 1500 },
        ],
        actions: [
          { type: 'notify', config: { title: 'Verify seller and item condition' } },
          { type: 'update', config: { field: 'requiresVerification', value: true } },
        ],
        priority: 95,
      },
      {
        id: 'high-value-testing',
        name: 'Thorough testing required',
        enabled: true,
        stage: 'testing',
        conditions: [
          { field: 'value', operator: 'gt', value: 1000 },
        ],
        actions: [
          { type: 'notify', config: { title: 'Run full test suite', checklist: true } },
        ],
        priority: 90,
      },
    ],
    settings: {
      requirePhotos: true,
      requireSerialVerification: true,
      minSellerRating: 4.0,
    },
  },
  
  // Bundle Builder
  {
    id: 'bundle-builder',
    name: 'Bundle Builder',
    description: 'Combine items for higher value',
    category: 'sourcing',
    transitions: [
      {
        from: 'evaluating',
        to: 'negotiating',
        trigger: { type: 'condition' },
        conditions: [
          { field: 'bundlePotential', operator: 'exists', value: true },
        ],
        actions: [
          { type: 'notify', config: { title: 'Good bundle candidate' } },
          { type: 'update', config: { field: 'dealType', value: 'bundle' } },
        ],
        automatic: true,
      },
    ],
    rules: [
      {
        id: 'bundle-match',
        name: 'Find matching items',
        enabled: true,
        stage: 'acquired',
        conditions: [
          { field: 'dealType', operator: 'eq', value: 'bundle' },
        ],
        actions: [
          { type: 'notify', config: { title: 'Search for complementary items' } },
        ],
        priority: 85,
      },
    ],
    settings: {
      targetBundleSize: 3,
      minBundleROI: 30,
      compatibilityCheck: true,
    },
  },
  
  // Part-Out Specialist
  {
    id: 'part-out',
    name: 'Part-Out Workflow',
    description: 'Maximize value by selling components',
    category: 'fulfillment',
    transitions: [
      {
        from: 'testing',
        to: 'listing',
        trigger: { type: 'condition' },
        conditions: [
          { field: 'partOutValue', operator: 'gt', value: 'wholeValue * 1.3' },
        ],
        actions: [
          { type: 'notify', config: { title: 'Part-out recommended' } },
          { type: 'update', config: { field: 'listingType', value: 'parts' } },
        ],
        automatic: true,
      },
    ],
    rules: [
      {
        id: 'part-inventory',
        name: 'Create part inventory',
        enabled: true,
        stage: 'acquired',
        conditions: [
          { field: 'dealType', operator: 'eq', value: 'part-out' },
        ],
        actions: [
          { type: 'notify', config: { title: 'Document all components' } },
          { type: 'update', config: { field: 'requiresInventory', value: true } },
        ],
        priority: 88,
      },
    ],
    settings: {
      photoEachPart: true,
      testEachPart: true,
      trackPartSerials: true,
    },
  },
  
  // Low-Risk Beginner
  {
    id: 'beginner',
    name: 'Low-Risk Beginner',
    description: 'Conservative approach for new operators',
    category: 'custom',
    transitions: [],
    rules: [
      {
        id: 'beginner-risk-limit',
        name: 'Limit risk for beginners',
        enabled: true,
        conditions: [
          { field: 'risk.score', operator: 'gt', value: 60 },
        ],
        actions: [
          { type: 'notify', config: { title: 'High risk - consider passing' } },
          { type: 'update', config: { field: 'requiresReview', value: true } },
        ],
        priority: 100,
      },
      {
        id: 'beginner-value-limit',
        name: 'Start with lower values',
        enabled: true,
        conditions: [
          { field: 'value', operator: 'gt', value: 500 },
        ],
        actions: [
          { type: 'notify', config: { title: 'High value - get second opinion' } },
        ],
        priority: 95,
      },
    ],
    settings: {
      maxDealValue: 500,
      minROI: 25,
      requireLocalPickup: true,
      maxActiveDeals: 3,
    },
  },
];

/**
 * Get workflow template by ID
 */
export function getWorkflowTemplate(id: string): WorkflowTemplate | undefined {
  return WORKFLOW_TEMPLATES.find(t => t.id === id);
}

/**
 * Get workflow templates by category
 */
export function getWorkflowsByCategory(category: WorkflowTemplate['category']): WorkflowTemplate[] {
  return WORKFLOW_TEMPLATES.filter(t => t.category === category);
}

/**
 * Create custom workflow from template
 */
export function customizeWorkflow(
  templateId: string,
  customizations: {
    name?: string;
    transitions?: Partial<StageTransition>[];
    rules?: Partial<AutomationRule>[];
    settings?: Record<string, any>;
  }
): WorkflowTemplate | null {
  const template = getWorkflowTemplate(templateId);
  if (!template) return null;
  
  return {
    ...template,
    id: `${template.id}-custom-${Date.now()}`,
    name: customizations.name || `${template.name} (Custom)`,
    category: 'custom',
    transitions: template.transitions.map((t, i) => ({
      ...t,
      ...(customizations.transitions?.[i] || {}),
    })),
    rules: template.rules.map((r, i) => ({
      ...r,
      ...(customizations.rules?.[i] || {}),
    })),
    settings: {
      ...template.settings,
      ...customizations.settings,
    },
  };
}

/**
 * Validate workflow template
 */
export function validateWorkflow(workflow: WorkflowTemplate): {
  valid: boolean;
  errors: string[];
  warnings: string[];
} {
  const errors: string[] = [];
  const warnings: string[] = [];
  
  // Check for transition loops
  const stages = new Set<string>();
  workflow.transitions.forEach(t => {
    stages.add(t.from);
    stages.add(t.to);
  });
  
  // Check for unreachable stages
  const reachableStages = new Set(['discovered']);
  let changed = true;
  while (changed) {
    changed = false;
    workflow.transitions.forEach(t => {
      if (reachableStages.has(t.from) && !reachableStages.has(t.to)) {
        reachableStages.add(t.to);
        changed = true;
      }
    });
  }
  
  stages.forEach(stage => {
    if (!reachableStages.has(stage) && stage !== 'discovered') {
      warnings.push(`Stage '${stage}' may be unreachable`);
    }
  });
  
  // Check for conflicting rules
  const rulesByStage = new Map<string, AutomationRule[]>();
  workflow.rules.forEach(rule => {
    const stage = rule.stage || 'any';
    const existing = rulesByStage.get(stage) || [];
    existing.push(rule);
    rulesByStage.set(stage, existing);
  });
  
  rulesByStage.forEach((rules, stage) => {
    if (rules.length > 5) {
      warnings.push(`Stage '${stage}' has many rules (${rules.length}) - may cause conflicts`);
    }
  });
  
  return {
    valid: errors.length === 0,
    errors,
    warnings,
  };
}