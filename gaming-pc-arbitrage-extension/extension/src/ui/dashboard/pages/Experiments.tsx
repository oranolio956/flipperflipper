/**
 * Experiments Page
 * View and manage A/B tests
 */

import React, { useState, useEffect } from 'react';
import { Flask, TrendingUp, Award, RotateCcw } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import { 
  getAllExperiments, 
  promoteVariant, 
  resetExperiment 
} from '@/lib/experiments';
import { twoProportionZTest, type Experiment } from '@/core/abtest';

export function Experiments() {
  const { toast } = useToast();
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadExperiments();
  }, []);

  const loadExperiments = async () => {
    try {
      const exps = await getAllExperiments();
      setExperiments(exps);
    } catch (error) {
      console.error('Failed to load experiments:', error);
      toast({
        title: 'Failed to load experiments',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handlePromoteVariant = async (experimentId: string, variantId: string) => {
    try {
      await promoteVariant(experimentId, variantId);
      await loadExperiments();
      
      toast({
        title: 'Variant promoted',
        description: 'This variant will now be used for all new messages',
      });
    } catch (error) {
      toast({
        title: 'Failed to promote variant',
        description: String(error),
        variant: 'destructive',
      });
    }
  };

  const handleResetExperiment = async (experimentId: string) => {
    if (!confirm('Reset experiment? This will resume A/B testing.')) {
      return;
    }

    try {
      await resetExperiment(experimentId);
      await loadExperiments();
      
      toast({
        title: 'Experiment reset',
        description: 'A/B testing has resumed',
      });
    } catch (error) {
      toast({
        title: 'Failed to reset experiment',
        description: String(error),
        variant: 'destructive',
      });
    }
  };

  const calculateSignificance = (exp: Experiment) => {
    if (exp.variants.length < 2) return null;
    
    const sorted = [...exp.variants].sort((a, b) => b.conversionRate - a.conversionRate);
    const best = sorted[0];
    const secondBest = sorted[1];
    
    if (best.impressions < 10 || secondBest.impressions < 10) {
      return null;
    }
    
    const { p } = twoProportionZTest(
      { s: best.successes, n: best.impressions },
      { s: secondBest.successes, n: secondBest.impressions }
    );
    
    return { best, secondBest, p };
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto">
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Flask className="h-6 w-6" />
              A/B Testing
            </h1>
            <p className="text-muted-foreground">
              Test and optimize negotiation templates
            </p>
          </div>
        </div>

        {experiments.map(exp => {
          const sig = calculateSignificance(exp);
          const totalImpressions = exp.variants.reduce((sum, v) => sum + v.impressions, 0);
          
          return (
            <Card key={exp.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>{exp.name}</CardTitle>
                    <CardDescription>{exp.description}</CardDescription>
                  </div>
                  {exp.promotedId && (
                    <Badge variant="default" className="gap-1">
                      <Award className="h-3 w-3" />
                      Winner Selected
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Overall stats */}
                  <div className="flex gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Total impressions:</span>{' '}
                      <span className="font-medium">{totalImpressions}</span>
                    </div>
                    {sig && (
                      <div>
                        <span className="text-muted-foreground">p-value:</span>{' '}
                        <span className={`font-medium ${sig.p < 0.05 ? 'text-green-600' : ''}`}>
                          {sig.p.toFixed(4)}
                        </span>
                        {sig.p < 0.05 && <span className="text-green-600 ml-1">✓ Significant</span>}
                      </div>
                    )}
                  </div>

                  {/* Variants */}
                  <div className="space-y-3">
                    {exp.variants.map(variant => {
                      const isPromoted = variant.id === exp.promotedId;
                      const isBest = sig?.best.id === variant.id;
                      const percentage = variant.impressions > 0 
                        ? (variant.conversionRate * 100).toFixed(1)
                        : '0.0';
                      
                      return (
                        <div 
                          key={variant.id}
                          className={`p-4 border rounded-lg ${isPromoted ? 'border-primary' : ''}`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{variant.id}</span>
                              {isPromoted && (
                                <Badge variant="default" size="sm">Promoted</Badge>
                              )}
                              {isBest && !isPromoted && (
                                <Badge variant="secondary" size="sm">
                                  <TrendingUp className="h-3 w-3 mr-1" />
                                  Leading
                                </Badge>
                              )}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {variant.impressions} impressions
                            </div>
                          </div>
                          
                          <div className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                              <span>Conversion rate</span>
                              <span className="font-medium">{percentage}%</span>
                            </div>
                            <Progress 
                              value={variant.conversionRate * 100} 
                              className="h-2"
                            />
                            <div className="text-xs text-muted-foreground">
                              {variant.successes} / {variant.impressions} successful
                            </div>
                          </div>

                          {/* Actions */}
                          {!isPromoted && variant.impressions >= 30 && (
                            <div className="mt-3">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handlePromoteVariant(exp.id, variant.id)}
                              >
                                Promote as Winner
                              </Button>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Reset button */}
                  {exp.promotedId && (
                    <div className="pt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleResetExperiment(exp.id)}
                      >
                        <RotateCcw className="h-4 w-4 mr-2" />
                        Reset Experiment
                      </Button>
                    </div>
                  )}

                  {/* Instructions */}
                  {totalImpressions < 50 && (
                    <Alert>
                      <AlertDescription>
                        Need at least 50 impressions per variant for reliable results.
                        Keep sending messages to gather more data.
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}