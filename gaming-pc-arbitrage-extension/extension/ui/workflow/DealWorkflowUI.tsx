/**
 * Deal Workflow Management UI
 * Provides interface for managing deal workflows, tasks, and automation
 */

import React, { useState, useEffect } from 'react';
import { dealHandoffManager, WorkflowTask, WorkflowTemplate, HandoffMetrics } from '@arbitrage/core';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { ScrollArea } from '../components/ui/scroll-area';
import { Alert, AlertDescription } from '../components/ui/alert';
import { 
  CheckCircle2, 
  Circle, 
  Clock, 
  AlertCircle,
  PlayCircle,
  BarChart3,
  Workflow,
  Plus,
  Copy,
  Settings,
  ChevronRight,
  Users,
  Zap,
  TrendingUp,
  AlertTriangle
} from 'lucide-react';

export function DealWorkflowUI() {
  const [activeTab, setActiveTab] = useState('tasks');
  const [selectedDealId, setSelectedDealId] = useState<string>('demo-deal-1');
  const [tasks, setTasks] = useState<WorkflowTask[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowTemplate[]>([]);
  const [metrics, setMetrics] = useState<HandoffMetrics | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string>('standard-workflow');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, [selectedDealId]);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load tasks for selected deal
      const dealTasks = dealHandoffManager.getTasksForDeal(selectedDealId);
      setTasks(dealTasks);

      // Load workflows
      const allWorkflows = dealHandoffManager.getWorkflows();
      setWorkflows(allWorkflows);

      // Load metrics
      const workflowMetrics = await dealHandoffManager.getWorkflowMetrics();
      setMetrics(workflowMetrics);
    } catch (error) {
      console.error('Failed to load workflow data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAssignWorkflow = async () => {
    try {
      await dealHandoffManager.assignWorkflow(selectedDealId, selectedWorkflow);
      await loadData();
    } catch (error) {
      console.error('Failed to assign workflow:', error);
    }
  };

  const handleTaskStatusUpdate = async (taskId: string, status: WorkflowTask['status']) => {
    try {
      await dealHandoffManager.updateTaskStatus(taskId, status);
      await loadData();
    } catch (error) {
      console.error('Failed to update task status:', error);
    }
  };

  const getTaskIcon = (status: WorkflowTask['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'in_progress':
        return <PlayCircle className="h-5 w-5 text-blue-500" />;
      case 'blocked':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Circle className="h-5 w-5 text-gray-400" />;
    }
  };

  const getPriorityColor = (priority: WorkflowTask['priority']) => {
    switch (priority) {
      case 'urgent':
        return 'destructive';
      case 'high':
        return 'default';
      case 'medium':
        return 'secondary';
      case 'low':
        return 'outline';
    }
  };

  const getAutomationTypeIcon = (type?: WorkflowTask['automationType']) => {
    switch (type) {
      case 'full_auto':
        return <Zap className="h-4 w-4 text-green-500" />;
      case 'semi_auto':
        return <Zap className="h-4 w-4 text-yellow-500" />;
      default:
        return null;
    }
  };

  const renderTasksView = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Deal Tasks</h3>
        <div className="flex items-center gap-2">
          <Select value={selectedWorkflow} onValueChange={setSelectedWorkflow}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select workflow" />
            </SelectTrigger>
            <SelectContent>
              {workflows.map(workflow => (
                <SelectItem key={workflow.id} value={workflow.id}>
                  {workflow.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={handleAssignWorkflow} size="sm">
            <Plus className="h-4 w-4 mr-1" />
            Assign Workflow
          </Button>
        </div>
      </div>

      {tasks.length === 0 ? (
        <Card>
          <CardContent className="text-center py-8">
            <Workflow className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No workflow assigned to this deal</p>
            <p className="text-sm text-gray-400 mt-1">Select and assign a workflow to get started</p>
          </CardContent>
        </Card>
      ) : (
        <ScrollArea className="h-[500px]">
          <div className="space-y-3">
            {tasks.map(task => (
              <Card key={task.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      {getTaskIcon(task.status)}
                      <div className="flex-1">
                        <h4 className="font-medium flex items-center gap-2">
                          {task.title}
                          {getAutomationTypeIcon(task.automationType)}
                        </h4>
                        <p className="text-sm text-gray-600 mt-1">{task.description}</p>
                        
                        <div className="flex items-center gap-4 mt-2">
                          <Badge variant={getPriorityColor(task.priority)}>
                            {task.priority}
                          </Badge>
                          
                          {task.dueDate && (
                            <span className="text-xs text-gray-500 flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              Due: {new Date(task.dueDate).toLocaleDateString()}
                            </span>
                          )}
                          
                          {task.assignee && (
                            <span className="text-xs text-gray-500 flex items-center gap-1">
                              <Users className="h-3 w-3" />
                              {task.assignee}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <Select 
                      value={task.status} 
                      onValueChange={(value) => handleTaskStatusUpdate(task.id, value as WorkflowTask['status'])}
                    >
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pending">Pending</SelectItem>
                        <SelectItem value="in_progress">In Progress</SelectItem>
                        <SelectItem value="completed">Completed</SelectItem>
                        <SelectItem value="blocked">Blocked</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  );

  const renderWorkflowsView = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Workflow Templates</h3>
        <Button size="sm">
          <Plus className="h-4 w-4 mr-1" />
          Create Workflow
        </Button>
      </div>

      <div className="grid gap-4">
        {workflows.map(workflow => (
          <Card key={workflow.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base">{workflow.name}</CardTitle>
                  <CardDescription>{workflow.description}</CardDescription>
                </div>
                <Badge variant={workflow.isActive ? 'default' : 'secondary'}>
                  {workflow.category}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Stages:</span> {workflow.stages.length}
                </div>
                
                <div className="flex flex-wrap gap-2">
                  {workflow.stages.map((stage, idx) => (
                    <div key={idx} className="flex items-center">
                      <Badge variant="outline" className="text-xs">
                        {stage.stage}
                      </Badge>
                      {idx < workflow.stages.length - 1 && (
                        <ChevronRight className="h-4 w-4 text-gray-400 mx-1" />
                      )}
                    </div>
                  ))}
                </div>

                <div className="flex gap-2 mt-4">
                  <Button size="sm" variant="outline">
                    <Copy className="h-4 w-4 mr-1" />
                    Clone
                  </Button>
                  <Button size="sm" variant="outline">
                    <Settings className="h-4 w-4 mr-1" />
                    Configure
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderMetricsView = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold mb-4">Workflow Analytics</h3>

      {metrics && (
        <>
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Task Completion Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.taskCompletionRate.toFixed(1)}%</div>
                <Progress value={metrics.taskCompletionRate} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Automation Success</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.automationSuccessRate.toFixed(1)}%</div>
                <Progress value={metrics.automationSuccessRate} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">SLA Breach Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">{metrics.slaBreachRate.toFixed(1)}%</div>
                <Progress value={metrics.slaBreachRate} className="mt-2" variant="destructive" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Avg Time in Stage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {Object.values(metrics.averageTimePerStage).reduce((a, b) => a + b, 0).toFixed(1)}h
                </div>
                <div className="text-xs text-gray-500 mt-1">Total cycle time</div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Stage Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(metrics.averageTimePerStage)
                  .filter(([_, time]) => time > 0)
                  .map(([stage, time]) => (
                    <div key={stage} className="flex items-center justify-between">
                      <span className="text-sm font-medium capitalize">{stage}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-600">{time.toFixed(1)}h</span>
                        <Progress value={Math.min((time / 50) * 100, 100)} className="w-24" />
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-500" />
                Bottlenecks & Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {metrics.bottlenecks.map((bottleneck, idx) => (
                  <div key={idx} className="border-l-4 border-yellow-400 pl-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium capitalize">{bottleneck.stage} Stage</h4>
                      <Badge variant="outline" className="text-xs">
                        Avg delay: {bottleneck.averageDelay}h
                      </Badge>
                    </div>
                    
                    <div className="text-sm text-gray-600">
                      <p className="font-medium mb-1">Common Issues:</p>
                      <ul className="list-disc list-inside">
                        {bottleneck.commonIssues.map((issue, i) => (
                          <li key={i}>{issue}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="text-sm">
                      <p className="font-medium text-green-700 mb-1">Recommendations:</p>
                      <ul className="list-disc list-inside text-green-600">
                        {bottleneck.recommendations.map((rec, i) => (
                          <li key={i}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="text-sm text-gray-500 mt-2">Loading workflow data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <Workflow className="h-6 w-6" />
          Deal Workflow Management
        </h2>
        <p className="text-gray-600">
          Automate and track deal lifecycle with customizable workflows
        </p>
      </div>

      <Alert className="mb-6">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <strong>Selected Deal:</strong> {selectedDealId} - 
          {tasks.length > 0 ? ` ${tasks.filter(t => t.status === 'completed').length}/${tasks.length} tasks completed` : ' No workflow assigned'}
        </AlertDescription>
      </Alert>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="tasks">
            <CheckCircle2 className="h-4 w-4 mr-2" />
            Tasks
          </TabsTrigger>
          <TabsTrigger value="workflows">
            <Workflow className="h-4 w-4 mr-2" />
            Workflows
          </TabsTrigger>
          <TabsTrigger value="metrics">
            <BarChart3 className="h-4 w-4 mr-2" />
            Analytics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="tasks" className="mt-6">
          {renderTasksView()}
        </TabsContent>

        <TabsContent value="workflows" className="mt-6">
          {renderWorkflowsView()}
        </TabsContent>

        <TabsContent value="metrics" className="mt-6">
          {renderMetricsView()}
        </TabsContent>
      </Tabs>
    </div>
  );
}