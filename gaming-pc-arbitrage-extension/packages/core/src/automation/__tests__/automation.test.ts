/**
 * Tests for Automation Modules
 */

import { describe, it, expect } from 'vitest';
import {
  canTransition,
  executeTransition,
  evaluateAutomationRules,
  getNextStages,
  getStageMetadata,
  DEFAULT_TRANSITIONS,
  DEFAULT_AUTOMATION_RULES,
  type DealStage,
} from '../dealFlow';
import {
  getWorkflowTemplate,
  getWorkflowsByCategory,
  customizeWorkflow,
  validateWorkflow,
} from '../workflowTemplates';
import type { Deal } from '../../types';

describe('Deal Flow', () => {
  const mockDeal: Deal = {
    id: '123',
    listingId: '456',
    stage: 'evaluating',
    roi: 25,
    risk: { score: 50, flags: [], recommendation: 'proceed' },
    estimatedProfit: 300,
    metadata: {
      createdAt: new Date(),
      updatedAt: new Date(),
      source: 'manual',
      version: 1,
      lastActivityDays: 2,
    },
  };

  it('should check if transition is allowed', () => {
    // Valid transition with met conditions
    const result1 = canTransition(mockDeal, 'evaluating', 'negotiating');
    expect(result1.allowed).toBe(true);
    
    // Invalid transition (no path)
    const result2 = canTransition(mockDeal, 'evaluating', 'sold');
    expect(result2.allowed).toBe(false);
    expect(result2.reason).toContain('No transition path');
    
    // Valid path but conditions not met
    const lowROIDeal = { ...mockDeal, roi: 10 };
    const result3 = canTransition(lowROIDeal, 'evaluating', 'negotiating');
    expect(result3.allowed).toBe(false);
    expect(result3.reason).toContain('roi');
  });

  it('should execute stage transition', () => {
    const result = executeTransition(mockDeal, 'negotiating');
    
    expect(result.success).toBe(true);
    expect(result.actions).toHaveLength(2);
    expect(result.actions[0].type).toBe('notify');
    expect(result.actions[1].type).toBe('followup');
  });

  it('should evaluate automation rules', () => {
    // High-value deal
    const highValueDeal = { ...mockDeal, estimatedProfit: 600 };
    const rules1 = evaluateAutomationRules(highValueDeal);
    
    expect(rules1).toHaveLength(1);
    expect(rules1[0].id).toBe('high-value-alert');
    
    // Low ROI deal in evaluating stage
    const lowROIDeal = { ...mockDeal, roi: 8 };
    const rules2 = evaluateAutomationRules(lowROIDeal);
    
    expect(rules2).toHaveLength(1);
    expect(rules2[0].id).toBe('auto-reject-low-roi');
  });

  it('should get next possible stages', () => {
    const nextStages = getNextStages('evaluating');
    
    expect(nextStages).toContain('negotiating');
    expect(nextStages).not.toContain('sold');
  });

  it('should get stage metadata', () => {
    const metadata = getStageMetadata('negotiating');
    
    expect(metadata.label).toBe('Negotiating');
    expect(metadata.color).toBe('yellow');
    expect(metadata.icon).toBe('💬');
    expect(metadata.description).toContain('negotiation');
  });

  it('should handle complex conditions', () => {
    const complexDeal = {
      ...mockDeal,
      testResults: { passed: true },
      stage: 'testing',
    };
    
    const result = canTransition(complexDeal as any, 'testing', 'listing');
    expect(result.allowed).toBe(true);
  });

  it('should prioritize automation rules', () => {
    const multiRuleDeal = {
      ...mockDeal,
      roi: 5, // Triggers auto-reject
      estimatedProfit: 600, // Triggers high-value
    };
    
    const rules = evaluateAutomationRules(multiRuleDeal);
    
    // Auto-reject should come first (priority 100)
    expect(rules[0].id).toBe('auto-reject-low-roi');
    expect(rules[1].id).toBe('high-value-alert');
  });
});

describe('Workflow Templates', () => {
  it('should get workflow template by ID', () => {
    const template = getWorkflowTemplate('quick-flip');
    
    expect(template).toBeDefined();
    expect(template?.name).toBe('Quick Flip (Same Day)');
    expect(template?.category).toBe('fulfillment');
  });

  it('should get workflows by category', () => {
    const negotiationWorkflows = getWorkflowsByCategory('negotiation');
    
    expect(negotiationWorkflows.length).toBeGreaterThan(0);
    expect(negotiationWorkflows.every(w => w.category === 'negotiation')).toBe(true);
  });

  it('should customize workflow template', () => {
    const customized = customizeWorkflow('quick-flip', {
      name: 'My Quick Flip',
      settings: {
        maxHoldTime: 48,
        minROI: 20,
      },
    });
    
    expect(customized).toBeDefined();
    expect(customized?.name).toBe('My Quick Flip');
    expect(customized?.category).toBe('custom');
    expect(customized?.settings.maxHoldTime).toBe(48);
    expect(customized?.settings.minROI).toBe(20);
    expect(customized?.settings.autoPrice).toBe(true); // Original setting preserved
  });

  it('should validate workflow template', () => {
    const quickFlip = getWorkflowTemplate('quick-flip');
    const validation = validateWorkflow(quickFlip!);
    
    expect(validation.valid).toBe(true);
    expect(validation.errors).toHaveLength(0);
  });

  it('should detect unreachable stages in validation', () => {
    const brokenWorkflow = {
      id: 'broken',
      name: 'Broken Workflow',
      description: 'Has unreachable stages',
      category: 'custom' as const,
      transitions: [
        {
          from: 'discovered' as DealStage,
          to: 'evaluating' as DealStage,
          trigger: { type: 'manual' as const },
          actions: [],
          automatic: false,
        },
        // Missing path to 'negotiating'
        {
          from: 'negotiating' as DealStage,
          to: 'scheduled' as DealStage,
          trigger: { type: 'manual' as const },
          actions: [],
          automatic: false,
        },
      ],
      rules: [],
      settings: {},
    };
    
    const validation = validateWorkflow(brokenWorkflow);
    
    expect(validation.warnings).toContain("Stage 'negotiating' may be unreachable");
  });

  it('should have proper settings for each template', () => {
    const highValue = getWorkflowTemplate('high-value');
    
    expect(highValue?.settings.requirePhotos).toBe(true);
    expect(highValue?.settings.minSellerRating).toBe(4.0);
    
    const beginner = getWorkflowTemplate('beginner');
    
    expect(beginner?.settings.maxDealValue).toBe(500);
    expect(beginner?.settings.maxActiveDeals).toBe(3);
  });
});