/**
 * Deal Handoff Workflow Automation Manager
 * Manages automated workflows for deal lifecycle including task assignments,
 * stage transitions, notifications, and process automation
 */

import { Deal, DealStage, User, Notification } from '../types';

export interface WorkflowTask {
  id: string;
  dealId: string;
  title: string;
  description: string;
  assignee?: string;
  dueDate?: Date;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  dependencies?: string[]; // Other task IDs
  automationType?: 'manual' | 'semi_auto' | 'full_auto';
  completionCriteria?: string[];
  attachments?: string[];
  notes?: string;
  createdAt: Date;
  updatedAt: Date;
  completedAt?: Date;
}

export interface WorkflowStage {
  stage: DealStage;
  requiredTasks: Partial<WorkflowTask>[];
  automations: WorkflowAutomation[];
  notifications: NotificationRule[];
  conditions: StageCondition[];
  sla?: number; // SLA in hours
}

export interface WorkflowAutomation {
  id: string;
  name: string;
  trigger: AutomationTrigger;
  actions: AutomationAction[];
  enabled: boolean;
}

export interface AutomationTrigger {
  type: 'stage_entry' | 'stage_exit' | 'time_based' | 'condition_met' | 'manual';
  conditions?: Record<string, any>;
}

export interface AutomationAction {
  type: 'create_task' | 'send_notification' | 'update_field' | 'call_webhook' | 'generate_document';
  config: Record<string, any>;
}

export interface NotificationRule {
  id: string;
  trigger: 'stage_change' | 'task_due' | 'sla_breach' | 'deal_update';
  recipients: NotificationRecipient[];
  template: string;
  channels: ('email' | 'sms' | 'push' | 'slack' | 'discord')[];
}

export interface NotificationRecipient {
  type: 'assignee' | 'team' | 'specific_user' | 'role';
  value?: string;
}

export interface StageCondition {
  type: 'all_tasks_complete' | 'approval_required' | 'payment_received' | 'custom';
  config?: Record<string, any>;
}

export interface HandoffMetrics {
  averageTimePerStage: Record<DealStage, number>;
  taskCompletionRate: number;
  slaBreachRate: number;
  automationSuccessRate: number;
  bottlenecks: BottleneckAnalysis[];
}

export interface BottleneckAnalysis {
  stage: DealStage;
  averageDelay: number;
  commonIssues: string[];
  recommendations: string[];
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  stages: WorkflowStage[];
  category: 'standard' | 'express' | 'premium' | 'custom';
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export class DealHandoffManager {
  private tasks: Map<string, WorkflowTask> = new Map();
  private workflows: Map<string, WorkflowTemplate> = new Map();
  private activeAutomations: Map<string, WorkflowAutomation> = new Map();
  private dealWorkflows: Map<string, string> = new Map(); // dealId -> workflowId

  constructor() {
    this.initializeDefaultWorkflows();
    this.loadData();
  }

  private initializeDefaultWorkflows(): void {
    const standardWorkflow: WorkflowTemplate = {
      id: 'standard-workflow',
      name: 'Standard Deal Workflow',
      description: 'Default workflow for standard PC deals',
      stages: [
        {
          stage: 'new',
          requiredTasks: [
            {
              title: 'Initial Assessment',
              description: 'Review listing details and verify components',
              priority: 'high',
              automationType: 'semi_auto'
            },
            {
              title: 'Price Validation',
              description: 'Confirm pricing and calculate ROI',
              priority: 'high',
              automationType: 'full_auto'
            }
          ],
          automations: [
            {
              id: 'auto-price-check',
              name: 'Automated Price Check',
              trigger: { type: 'stage_entry' },
              actions: [
                {
                  type: 'update_field',
                  config: { field: 'priceAnalysis', method: 'runPriceAnalysis' }
                }
              ],
              enabled: true
            }
          ],
          notifications: [
            {
              id: 'new-deal-notification',
              trigger: 'stage_change',
              recipients: [{ type: 'team' }],
              template: 'New deal requires assessment: {{dealTitle}}',
              channels: ['push', 'slack']
            }
          ],
          conditions: [
            { type: 'all_tasks_complete' }
          ],
          sla: 2 // 2 hours
        },
        {
          stage: 'contacting',
          requiredTasks: [
            {
              title: 'Send Initial Message',
              description: 'Contact seller with initial inquiry',
              priority: 'high',
              automationType: 'semi_auto'
            },
            {
              title: 'Schedule Viewing',
              description: 'Arrange time to inspect the PC',
              priority: 'medium',
              automationType: 'manual'
            }
          ],
          automations: [
            {
              id: 'message-template',
              name: 'Generate Message Template',
              trigger: { type: 'stage_entry' },
              actions: [
                {
                  type: 'generate_document',
                  config: { template: 'initial_inquiry', autoFill: true }
                }
              ],
              enabled: true
            }
          ],
          notifications: [],
          conditions: [
            { type: 'custom', config: { check: 'sellerResponded' } }
          ],
          sla: 24 // 24 hours
        },
        {
          stage: 'negotiating',
          requiredTasks: [
            {
              title: 'Price Negotiation',
              description: 'Negotiate final price with seller',
              priority: 'high',
              automationType: 'manual'
            },
            {
              title: 'Verify Condition',
              description: 'Confirm PC condition matches listing',
              priority: 'high',
              automationType: 'manual'
            }
          ],
          automations: [
            {
              id: 'negotiation-tips',
              name: 'Provide Negotiation Scripts',
              trigger: { type: 'stage_entry' },
              actions: [
                {
                  type: 'send_notification',
                  config: { 
                    template: 'negotiation_tips',
                    includeScripts: true
                  }
                }
              ],
              enabled: true
            }
          ],
          notifications: [],
          conditions: [
            { type: 'custom', config: { check: 'priceAgreed' } }
          ],
          sla: 48 // 48 hours
        },
        {
          stage: 'pickup',
          requiredTasks: [
            {
              title: 'Arrange Pickup',
              description: 'Finalize pickup time and location',
              priority: 'high',
              automationType: 'manual'
            },
            {
              title: 'Prepare Payment',
              description: 'Ensure payment method is ready',
              priority: 'high',
              automationType: 'manual'
            },
            {
              title: 'Final Inspection Checklist',
              description: 'Review inspection checklist before pickup',
              priority: 'medium',
              automationType: 'semi_auto'
            }
          ],
          automations: [
            {
              id: 'pickup-reminder',
              name: 'Send Pickup Reminder',
              trigger: { 
                type: 'time_based',
                conditions: { hoursBefore: 2 }
              },
              actions: [
                {
                  type: 'send_notification',
                  config: { 
                    template: 'pickup_reminder',
                    urgent: true
                  }
                }
              ],
              enabled: true
            }
          ],
          notifications: [
            {
              id: 'pickup-scheduled',
              trigger: 'deal_update',
              recipients: [{ type: 'assignee' }],
              template: 'Pickup scheduled for {{pickupTime}} at {{location}}',
              channels: ['push', 'sms']
            }
          ],
          conditions: [
            { type: 'custom', config: { check: 'pickupCompleted' } }
          ],
          sla: 72 // 72 hours
        },
        {
          stage: 'testing',
          requiredTasks: [
            {
              title: 'Hardware Testing',
              description: 'Run comprehensive hardware tests',
              priority: 'high',
              automationType: 'semi_auto'
            },
            {
              title: 'Performance Benchmarks',
              description: 'Run and record benchmark results',
              priority: 'medium',
              automationType: 'semi_auto'
            },
            {
              title: 'Clean and Refurbish',
              description: 'Clean PC and perform any necessary refurbishment',
              priority: 'medium',
              automationType: 'manual'
            }
          ],
          automations: [
            {
              id: 'test-checklist',
              name: 'Generate Test Checklist',
              trigger: { type: 'stage_entry' },
              actions: [
                {
                  type: 'generate_document',
                  config: { 
                    template: 'hardware_test_checklist',
                    includeComponents: true
                  }
                }
              ],
              enabled: true
            }
          ],
          notifications: [],
          conditions: [
            { type: 'all_tasks_complete' },
            { type: 'custom', config: { check: 'allTestsPassed' } }
          ],
          sla: 24 // 24 hours
        },
        {
          stage: 'listing',
          requiredTasks: [
            {
              title: 'Take Photos',
              description: 'Take high-quality photos for listing',
              priority: 'high',
              automationType: 'manual'
            },
            {
              title: 'Write Listing',
              description: 'Create compelling listing description',
              priority: 'high',
              automationType: 'semi_auto'
            },
            {
              title: 'Post Listing',
              description: 'Post to selected marketplaces',
              priority: 'high',
              automationType: 'semi_auto'
            }
          ],
          automations: [
            {
              id: 'listing-generator',
              name: 'Generate Listing Content',
              trigger: { type: 'stage_entry' },
              actions: [
                {
                  type: 'generate_document',
                  config: { 
                    template: 'optimized_listing',
                    includeSpecs: true,
                    includeBenchmarks: true
                  }
                }
              ],
              enabled: true
            }
          ],
          notifications: [],
          conditions: [
            { type: 'custom', config: { check: 'listingActive' } }
          ],
          sla: 12 // 12 hours
        },
        {
          stage: 'selling',
          requiredTasks: [
            {
              title: 'Respond to Inquiries',
              description: 'Manage buyer inquiries',
              priority: 'high',
              automationType: 'semi_auto'
            },
            {
              title: 'Schedule Viewings',
              description: 'Arrange buyer viewings',
              priority: 'medium',
              automationType: 'manual'
            },
            {
              title: 'Negotiate Sale',
              description: 'Handle price negotiations',
              priority: 'high',
              automationType: 'manual'
            }
          ],
          automations: [
            {
              id: 'inquiry-autoresponder',
              name: 'Auto-respond to Common Questions',
              trigger: { type: 'condition_met' },
              actions: [
                {
                  type: 'send_notification',
                  config: { 
                    template: 'auto_response',
                    filterCommonQuestions: true
                  }
                }
              ],
              enabled: true
            }
          ],
          notifications: [
            {
              id: 'new-inquiry',
              trigger: 'deal_update',
              recipients: [{ type: 'assignee' }],
              template: 'New inquiry from {{buyerName}}',
              channels: ['push']
            }
          ],
          conditions: [
            { type: 'custom', config: { check: 'buyerCommitted' } }
          ]
        },
        {
          stage: 'sold',
          requiredTasks: [
            {
              title: 'Complete Sale',
              description: 'Finalize transaction with buyer',
              priority: 'high',
              automationType: 'manual'
            },
            {
              title: 'Record Profit',
              description: 'Update financial records',
              priority: 'high',
              automationType: 'full_auto'
            },
            {
              title: 'Archive Deal',
              description: 'Archive deal data for analytics',
              priority: 'low',
              automationType: 'full_auto'
            }
          ],
          automations: [
            {
              id: 'profit-calculator',
              name: 'Calculate Final Profit',
              trigger: { type: 'stage_entry' },
              actions: [
                {
                  type: 'update_field',
                  config: { 
                    field: 'finalProfit',
                    calculateFrom: ['sellPrice', 'purchasePrice', 'expenses']
                  }
                }
              ],
              enabled: true
            }
          ],
          notifications: [
            {
              id: 'deal-completed',
              trigger: 'stage_change',
              recipients: [{ type: 'team' }],
              template: 'Deal completed! Profit: ${{profit}}',
              channels: ['push', 'slack']
            }
          ],
          conditions: [],
          sla: 4 // 4 hours
        }
      ],
      category: 'standard',
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    this.workflows.set(standardWorkflow.id, standardWorkflow);
  }

  // Assign workflow to deal
  async assignWorkflow(dealId: string, workflowId: string): Promise<void> {
    const workflow = this.workflows.get(workflowId);
    if (!workflow) {
      throw new Error('Workflow not found');
    }

    this.dealWorkflows.set(dealId, workflowId);
    
    // Create initial tasks for the first stage
    const firstStage = workflow.stages.find(s => s.stage === 'new');
    if (firstStage) {
      await this.createTasksForStage(dealId, firstStage);
      await this.executeStageAutomations(dealId, firstStage);
    }

    await this.saveData();
  }

  // Transition deal to next stage
  async transitionStage(dealId: string, fromStage: DealStage, toStage: DealStage): Promise<void> {
    const workflowId = this.dealWorkflows.get(dealId);
    if (!workflowId) {
      throw new Error('No workflow assigned to deal');
    }

    const workflow = this.workflows.get(workflowId);
    if (!workflow) {
      throw new Error('Workflow not found');
    }

    // Check stage conditions
    const currentStageConfig = workflow.stages.find(s => s.stage === fromStage);
    if (currentStageConfig && !await this.checkStageConditions(dealId, currentStageConfig)) {
      throw new Error('Stage transition conditions not met');
    }

    // Complete current stage tasks
    await this.completeStageCleanup(dealId, fromStage);

    // Setup new stage
    const newStageConfig = workflow.stages.find(s => s.stage === toStage);
    if (newStageConfig) {
      await this.createTasksForStage(dealId, newStageConfig);
      await this.executeStageAutomations(dealId, newStageConfig);
      await this.sendStageNotifications(dealId, newStageConfig, 'stage_change');
    }

    await this.saveData();
  }

  // Create tasks for a stage
  private async createTasksForStage(dealId: string, stage: WorkflowStage): Promise<void> {
    for (const taskTemplate of stage.requiredTasks) {
      const task: WorkflowTask = {
        id: `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        dealId,
        title: taskTemplate.title || '',
        description: taskTemplate.description || '',
        priority: taskTemplate.priority || 'medium',
        status: 'pending',
        automationType: taskTemplate.automationType || 'manual',
        createdAt: new Date(),
        updatedAt: new Date(),
        ...taskTemplate
      };

      this.tasks.set(task.id, task);
    }
  }

  // Execute stage automations
  private async executeStageAutomations(dealId: string, stage: WorkflowStage): Promise<void> {
    for (const automation of stage.automations) {
      if (!automation.enabled) continue;

      if (automation.trigger.type === 'stage_entry') {
        await this.executeAutomationActions(dealId, automation.actions);
      }
    }
  }

  // Execute automation actions
  private async executeAutomationActions(dealId: string, actions: AutomationAction[]): Promise<void> {
    for (const action of actions) {
      switch (action.type) {
        case 'create_task':
          // Create additional task
          const task: WorkflowTask = {
            id: `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            dealId,
            ...action.config,
            createdAt: new Date(),
            updatedAt: new Date()
          };
          this.tasks.set(task.id, task);
          break;

        case 'send_notification':
          // Send notification (mock)
          console.log('Sending notification:', action.config);
          break;

        case 'update_field':
          // Update deal field (would integrate with deal manager)
          console.log('Updating field:', action.config);
          break;

        case 'generate_document':
          // Generate document from template
          console.log('Generating document:', action.config);
          break;

        case 'call_webhook':
          // Call external webhook (mock)
          console.log('Calling webhook:', action.config);
          break;
      }
    }
  }

  // Check stage transition conditions
  private async checkStageConditions(dealId: string, stage: WorkflowStage): Promise<boolean> {
    for (const condition of stage.conditions) {
      switch (condition.type) {
        case 'all_tasks_complete':
          const stageTasks = Array.from(this.tasks.values())
            .filter(t => t.dealId === dealId && t.status !== 'completed');
          if (stageTasks.length > 0) return false;
          break;

        case 'approval_required':
          // Check if approval is granted (mock)
          console.log('Checking approval:', condition.config);
          break;

        case 'payment_received':
          // Check payment status (mock)
          console.log('Checking payment:', condition.config);
          break;

        case 'custom':
          // Custom condition check (mock)
          console.log('Checking custom condition:', condition.config);
          break;
      }
    }
    return true;
  }

  // Send stage notifications
  private async sendStageNotifications(
    dealId: string, 
    stage: WorkflowStage, 
    trigger: NotificationRule['trigger']
  ): Promise<void> {
    const notifications = stage.notifications.filter(n => n.trigger === trigger);
    
    for (const notification of notifications) {
      // Send to each recipient through specified channels (mock)
      console.log('Sending notification:', {
        dealId,
        trigger,
        template: notification.template,
        channels: notification.channels,
        recipients: notification.recipients
      });
    }
  }

  // Complete stage cleanup
  private async completeStageCleanup(dealId: string, stage: DealStage): Promise<void> {
    // Mark remaining tasks as completed or cancelled
    const stageTasks = Array.from(this.tasks.values())
      .filter(t => t.dealId === dealId && t.status !== 'completed');
    
    for (const task of stageTasks) {
      task.status = task.status === 'in_progress' ? 'completed' : 'completed';
      task.completedAt = new Date();
      task.updatedAt = new Date();
    }
  }

  // Get tasks for deal
  getTasksForDeal(dealId: string): WorkflowTask[] {
    return Array.from(this.tasks.values())
      .filter(task => task.dealId === dealId)
      .sort((a, b) => {
        const priorityOrder = { urgent: 0, high: 1, medium: 2, low: 3 };
        return priorityOrder[a.priority] - priorityOrder[b.priority];
      });
  }

  // Update task status
  async updateTaskStatus(taskId: string, status: WorkflowTask['status']): Promise<void> {
    const task = this.tasks.get(taskId);
    if (!task) {
      throw new Error('Task not found');
    }

    task.status = status;
    task.updatedAt = new Date();
    
    if (status === 'completed') {
      task.completedAt = new Date();
    }

    await this.saveData();
  }

  // Get workflow metrics
  async getWorkflowMetrics(): Promise<HandoffMetrics> {
    const tasks = Array.from(this.tasks.values());
    const completedTasks = tasks.filter(t => t.status === 'completed');
    
    // Calculate average time per stage (mock data)
    const averageTimePerStage: Record<DealStage, number> = {
      new: 2.5,
      analyzing: 1.8,
      contacting: 24.3,
      negotiating: 36.2,
      purchasing: 0,
      pickup: 48.1,
      testing: 18.5,
      listing: 8.2,
      selling: 72.4,
      sold: 2.1,
      archived: 0
    };

    // Calculate metrics
    const taskCompletionRate = tasks.length > 0 
      ? (completedTasks.length / tasks.length) * 100 
      : 0;

    // Mock bottleneck analysis
    const bottlenecks: BottleneckAnalysis[] = [
      {
        stage: 'negotiating',
        averageDelay: 12.5,
        commonIssues: ['Seller slow to respond', 'Price disagreements'],
        recommendations: ['Use urgency tactics', 'Have backup deals ready']
      },
      {
        stage: 'selling',
        averageDelay: 24.8,
        commonIssues: ['Low buyer interest', 'Price too high'],
        recommendations: ['Improve listing photos', 'Adjust pricing strategy']
      }
    ];

    return {
      averageTimePerStage,
      taskCompletionRate,
      slaBreachRate: 8.3, // Mock
      automationSuccessRate: 94.2, // Mock
      bottlenecks
    };
  }

  // Create custom workflow
  async createWorkflow(workflow: Omit<WorkflowTemplate, 'id' | 'createdAt' | 'updatedAt'>): Promise<string> {
    const id = `workflow-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newWorkflow: WorkflowTemplate = {
      ...workflow,
      id,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    this.workflows.set(id, newWorkflow);
    await this.saveData();
    
    return id;
  }

  // Get all workflows
  getWorkflows(): WorkflowTemplate[] {
    return Array.from(this.workflows.values());
  }

  // Clone workflow
  async cloneWorkflow(workflowId: string, newName: string): Promise<string> {
    const original = this.workflows.get(workflowId);
    if (!original) {
      throw new Error('Workflow not found');
    }

    const cloned = {
      ...original,
      name: newName,
      description: `Cloned from ${original.name}`
    };

    delete (cloned as any).id;
    return this.createWorkflow(cloned);
  }

  // Get upcoming tasks
  getUpcomingTasks(assignee?: string): WorkflowTask[] {
    let tasks = Array.from(this.tasks.values())
      .filter(t => t.status === 'pending' || t.status === 'in_progress');

    if (assignee) {
      tasks = tasks.filter(t => t.assignee === assignee);
    }

    return tasks.sort((a, b) => {
      if (a.dueDate && b.dueDate) {
        return a.dueDate.getTime() - b.dueDate.getTime();
      }
      const priorityOrder = { urgent: 0, high: 1, medium: 2, low: 3 };
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    });
  }

  // Check SLA breaches
  async checkSLABreaches(): Promise<Array<{ dealId: string; stage: DealStage; hoursOverdue: number }>> {
    const breaches: Array<{ dealId: string; stage: DealStage; hoursOverdue: number }> = [];
    
    // This would integrate with deal manager to check actual stage times
    // Mock implementation
    console.log('Checking SLA breaches...');
    
    return breaches;
  }

  // Save data
  private async saveData(): Promise<void> {
    try {
      await chrome.storage.local.set({
        'dealHandoff:tasks': Array.from(this.tasks.entries()),
        'dealHandoff:workflows': Array.from(this.workflows.entries()),
        'dealHandoff:activeAutomations': Array.from(this.activeAutomations.entries()),
        'dealHandoff:dealWorkflows': Array.from(this.dealWorkflows.entries())
      });
    } catch (error) {
      console.error('Failed to save deal handoff data:', error);
    }
  }

  // Load data
  private async loadData(): Promise<void> {
    try {
      const data = await chrome.storage.local.get([
        'dealHandoff:tasks',
        'dealHandoff:workflows',
        'dealHandoff:activeAutomations',
        'dealHandoff:dealWorkflows'
      ]);

      if (data['dealHandoff:tasks']) {
        this.tasks = new Map(data['dealHandoff:tasks']);
      }
      if (data['dealHandoff:workflows']) {
        this.workflows = new Map(data['dealHandoff:workflows']);
      }
      if (data['dealHandoff:activeAutomations']) {
        this.activeAutomations = new Map(data['dealHandoff:activeAutomations']);
      }
      if (data['dealHandoff:dealWorkflows']) {
        this.dealWorkflows = new Map(data['dealHandoff:dealWorkflows']);
      }
    } catch (error) {
      console.error('Failed to load deal handoff data:', error);
    }
  }
}

// Export singleton instance
export const dealHandoffManager = new DealHandoffManager();