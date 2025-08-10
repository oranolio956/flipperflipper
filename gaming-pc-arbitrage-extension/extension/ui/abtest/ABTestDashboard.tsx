import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { AlertCircle, BarChart3, Eye, Pause, Play, Plus, RefreshCw, Users } from 'lucide-react';
import { experimentManager } from '@arbitrage/core';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Experiment } from '@arbitrage/core/types';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';

interface ExperimentResult {
  experimentId: string;
  variant: string;
  metrics: {
    conversions: number;
    participants: number;
    conversionRate: number;
    averageValue: number;
    confidence: number;
  };
  timeSeriesData: Array<{
    date: string;
    conversions: number;
    participants: number;
  }>;
}

export const ABTestDashboard: React.FC = () => {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [results, setResults] = useState<Map<string, ExperimentResult[]>>(new Map());
  const [selectedExperiment, setSelectedExperiment] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [newExperiment, setNewExperiment] = useState({
    name: '',
    description: '',
    variants: ['control', 'variant_a'],
    trafficAllocation: 50
  });

  useEffect(() => {
    loadExperiments();
  }, []);

  const loadExperiments = async () => {
    setLoading(true);
    try {
      // Load experiments from storage
      const { experiments: stored } = await chrome.storage.local.get('experiments');
      if (stored) {
        setExperiments(stored);
        
        // Load results for each experiment
        const resultsMap = new Map<string, ExperimentResult[]>();
        for (const exp of stored) {
          const results = await loadExperimentResults(exp.id);
          resultsMap.set(exp.id, results);
        }
        setResults(resultsMap);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadExperimentResults = async (experimentId: string): Promise<ExperimentResult[]> => {
    // Simulate loading results - in production, this would query analytics
    const { experimentResults } = await chrome.storage.local.get('experimentResults');
    return experimentResults?.[experimentId] || generateMockResults(experimentId);
  };

  const generateMockResults = (experimentId: string): ExperimentResult[] => {
    const variants = ['control', 'variant_a'];
    return variants.map(variant => {
      const participants = Math.floor(Math.random() * 1000) + 500;
      const conversions = Math.floor(participants * (0.1 + Math.random() * 0.2));
      
      // Generate time series data
      const timeSeriesData = Array.from({ length: 7 }, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (6 - i));
        return {
          date: date.toLocaleDateString(),
          conversions: Math.floor(Math.random() * 20) + 5,
          participants: Math.floor(Math.random() * 100) + 50
        };
      });

      return {
        experimentId,
        variant,
        metrics: {
          conversions,
          participants,
          conversionRate: conversions / participants,
          averageValue: Math.random() * 100 + 50,
          confidence: Math.random() * 0.3 + 0.7
        },
        timeSeriesData
      };
    });
  };

  const createExperiment = async () => {
    const experiment = await experimentManager.createExperiment({
      name: newExperiment.name,
      description: newExperiment.description,
      variants: newExperiment.variants.map((name, index) => ({
        name,
        weight: index === 0 ? 100 - newExperiment.trafficAllocation : newExperiment.trafficAllocation
      }))
    });

    // Save to storage
    const updated = [...experiments, experiment];
    await chrome.storage.local.set({ experiments: updated });
    
    setExperiments(updated);
    setNewExperiment({
      name: '',
      description: '',
      variants: ['control', 'variant_a'],
      trafficAllocation: 50
    });
  };

  const toggleExperiment = async (experimentId: string) => {
    const experiment = experiments.find(e => e.id === experimentId);
    if (!experiment) return;

    experiment.active = !experiment.active;
    await chrome.storage.local.set({ experiments });
    setExperiments([...experiments]);
  };

  const calculateStatisticalSignificance = (results: ExperimentResult[]): string => {
    if (results.length < 2) return 'N/A';
    
    const control = results[0];
    const variant = results[1];
    
    // Simplified statistical significance calculation
    const difference = Math.abs(variant.metrics.conversionRate - control.metrics.conversionRate);
    const pooledRate = (control.metrics.conversions + variant.metrics.conversions) / 
                      (control.metrics.participants + variant.metrics.participants);
    const se = Math.sqrt(pooledRate * (1 - pooledRate) * 
                        (1/control.metrics.participants + 1/variant.metrics.participants));
    const zScore = difference / se;
    
    if (zScore > 2.58) return '99% significant';
    if (zScore > 1.96) return '95% significant';
    if (zScore > 1.645) return '90% significant';
    return 'Not significant';
  };

  const experiment = selectedExperiment ? experiments.find(e => e.id === selectedExperiment) : null;
  const experimentResults = selectedExperiment ? results.get(selectedExperiment) || [] : [];

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">A/B Testing Dashboard</h1>
        <Button onClick={loadExperiments} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      <Tabs defaultValue="experiments" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="experiments">Experiments</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
          <TabsTrigger value="create">Create New</TabsTrigger>
        </TabsList>

        <TabsContent value="experiments" className="space-y-4">
          {loading ? (
            <Card>
              <CardContent className="p-6">
                <p className="text-center text-muted-foreground">Loading experiments...</p>
              </CardContent>
            </Card>
          ) : experiments.length === 0 ? (
            <Card>
              <CardContent className="p-6">
                <p className="text-center text-muted-foreground">No experiments yet. Create your first A/B test!</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {experiments.map((exp) => (
                <Card key={exp.id} className="cursor-pointer hover:shadow-lg transition-shadow"
                      onClick={() => setSelectedExperiment(exp.id)}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          {exp.name}
                          <Badge variant={exp.active ? 'default' : 'secondary'}>
                            {exp.active ? 'Active' : 'Paused'}
                          </Badge>
                        </CardTitle>
                        <CardDescription>{exp.description}</CardDescription>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleExperiment(exp.id);
                        }}
                      >
                        {exp.active ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Variants</p>
                        <p className="font-medium">{exp.variants.length}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Started</p>
                        <p className="font-medium">{new Date(exp.createdAt).toLocaleDateString()}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Status</p>
                        <p className="font-medium">{calculateStatisticalSignificance(results.get(exp.id) || [])}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="results" className="space-y-4">
          {!experiment ? (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Select an experiment from the Experiments tab to view its results.
              </AlertDescription>
            </Alert>
          ) : (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>{experiment.name} Results</CardTitle>
                  <CardDescription>
                    Statistical significance: {calculateStatisticalSignificance(experimentResults)}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-6">
                    {experimentResults.map((result, index) => (
                      <div key={result.variant} className="space-y-4">
                        <div className="flex items-center justify-between">
                          <h3 className="text-lg font-semibold">
                            {result.variant === 'control' ? 'Control' : `Variant ${index}`}
                          </h3>
                          <Badge variant={index === 0 ? 'secondary' : 'default'}>
                            {result.metrics.participants} users
                          </Badge>
                        </div>
                        
                        <div className="grid grid-cols-4 gap-4">
                          <Card>
                            <CardContent className="p-4">
                              <p className="text-sm text-muted-foreground">Conversion Rate</p>
                              <p className="text-2xl font-bold">
                                {(result.metrics.conversionRate * 100).toFixed(2)}%
                              </p>
                            </CardContent>
                          </Card>
                          
                          <Card>
                            <CardContent className="p-4">
                              <p className="text-sm text-muted-foreground">Conversions</p>
                              <p className="text-2xl font-bold">{result.metrics.conversions}</p>
                            </CardContent>
                          </Card>
                          
                          <Card>
                            <CardContent className="p-4">
                              <p className="text-sm text-muted-foreground">Avg Value</p>
                              <p className="text-2xl font-bold">
                                ${result.metrics.averageValue.toFixed(2)}
                              </p>
                            </CardContent>
                          </Card>
                          
                          <Card>
                            <CardContent className="p-4">
                              <p className="text-sm text-muted-foreground">Confidence</p>
                              <Progress value={result.metrics.confidence * 100} className="mt-2" />
                            </CardContent>
                          </Card>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-6 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={experimentResults[0]?.timeSeriesData || []}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        {experimentResults.map((result, index) => (
                          <Line
                            key={result.variant}
                            type="monotone"
                            dataKey="conversions"
                            stroke={index === 0 ? '#8884d8' : '#82ca9d'}
                            name={result.variant}
                          />
                        ))}
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        <TabsContent value="create" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Create New A/B Test</CardTitle>
              <CardDescription>
                Set up a new experiment to test different features or experiences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Experiment Name</Label>
                <Input
                  id="name"
                  value={newExperiment.name}
                  onChange={(e) => setNewExperiment({ ...newExperiment, name: e.target.value })}
                  placeholder="e.g., New pricing display test"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  value={newExperiment.description}
                  onChange={(e) => setNewExperiment({ ...newExperiment, description: e.target.value })}
                  placeholder="What are you testing?"
                />
              </div>

              <div className="space-y-2">
                <Label>Traffic Allocation</Label>
                <div className="flex items-center space-x-4">
                  <span className="text-sm">Control: {100 - newExperiment.trafficAllocation}%</span>
                  <Input
                    type="range"
                    min="0"
                    max="100"
                    value={newExperiment.trafficAllocation}
                    onChange={(e) => setNewExperiment({ 
                      ...newExperiment, 
                      trafficAllocation: parseInt(e.target.value) 
                    })}
                    className="flex-1"
                  />
                  <span className="text-sm">Variant: {newExperiment.trafficAllocation}%</span>
                </div>
              </div>

              <Button 
                onClick={createExperiment} 
                className="w-full"
                disabled={!newExperiment.name || !newExperiment.description}
              >
                <Plus className="h-4 w-4 mr-2" />
                Create Experiment
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};