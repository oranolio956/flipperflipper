/**
 * Model Page
 * ML price prediction model management
 */

import React, { useState, useEffect } from 'react';
import { Brain, TrendingUp, Download, Upload, Play } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import { db } from '@/lib/db';
import { 
  trainModel,
  type ModelWeights 
} from '@/core/ml/priceModel';
import { formatCurrency } from '@/core';
import type { Deal } from '@/core';

export function Model() {
  const { toast } = useToast();
  const [model, setModel] = useState<ModelWeights | null>(null);
  const [isTraining, setIsTraining] = useState(false);
  const [modelBlend, setModelBlend] = useState(0.3);
  const [useModel, setUseModel] = useState(false);
  const [dealCount, setDealCount] = useState(0);

  useEffect(() => {
    loadModel();
    checkDealCount();
  }, []);

  const loadModel = async () => {
    try {
      const stored = await chrome.storage.local.get('mlModel');
      if (stored.mlModel) {
        setModel(stored.mlModel);
        
        const settings = await chrome.storage.local.get('mlSettings');
        if (settings.mlSettings) {
          setModelBlend(settings.mlSettings.blend || 0.3);
          setUseModel(settings.mlSettings.enabled || false);
        }
      }
    } catch (error) {
      console.error('Failed to load model:', error);
    }
  };

  const checkDealCount = async () => {
    const deals = await db.deals.toArray();
    const soldDeals = deals.filter(d => d.stage === 'sold' && d.sellPrice);
    setDealCount(soldDeals.length);
  };

  const handleTrain = async () => {
    setIsTraining(true);
    try {
      const allDeals = await db.deals.toArray();
      
      // Convert DB deals to Deal type
      const typedDeals: Deal[] = await Promise.all(
        allDeals.map(async (dbDeal) => {
          const listing = await db.listings
            .where('id')
            .equals(dbDeal.listingId)
            .first();
          
          return {
            ...dbDeal,
            listing: listing || {
              id: dbDeal.listingId,
              title: 'Unknown Listing',
              description: '',
              price: { amount: 0, currency: 'USD', formatted: '$0' },
              platform: 'facebook',
              url: '',
              seller: { id: '', name: '', profileUrl: '' },
              location: { city: '', state: '' },
              metadata: { createdAt: new Date(), updatedAt: new Date(), status: 'active' },
            },
          } as Deal;
        })
      );
      
      const weights = trainModel(typedDeals);
      setModel(weights);
      
      // Save model
      await chrome.storage.local.set({ mlModel: weights });
      
      toast({
        title: 'Model trained successfully',
        description: `Trained on ${weights.metrics?.trainSamples} deals with R² = ${weights.metrics?.r2.toFixed(3)}`,
      });
    } catch (error) {
      toast({
        title: 'Training failed',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsTraining(false);
    }
  };

  const handleBlendChange = async (value: number[]) => {
    const blend = value[0];
    setModelBlend(blend);
    
    await chrome.storage.local.set({
      mlSettings: { blend, enabled: useModel },
    });
  };

  const handleToggleModel = async (enabled: boolean) => {
    setUseModel(enabled);
    
    await chrome.storage.local.set({
      mlSettings: { blend: modelBlend, enabled },
    });
    
    toast({
      title: enabled ? 'Model enabled' : 'Model disabled',
      description: enabled 
        ? `Using ${Math.round(modelBlend * 100)}% model predictions`
        : 'Using only comp-based pricing',
    });
  };

  const handleExport = () => {
    if (!model) return;
    
    const data = JSON.stringify(model, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `price-model-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    toast({
      title: 'Model exported',
      description: 'Model weights saved to file',
    });
  };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      
      try {
        const text = await file.text();
        const weights = JSON.parse(text) as ModelWeights;
        
        // Validate structure
        if (!weights.bias || !weights.weights || !weights.featureNames) {
          throw new Error('Invalid model format');
        }
        
        setModel(weights);
        await chrome.storage.local.set({ mlModel: weights });
        
        toast({
          title: 'Model imported',
          description: 'Model weights loaded successfully',
        });
      } catch (error) {
        toast({
          title: 'Import failed',
          description: String(error),
          variant: 'destructive',
        });
      }
    };
    
    input.click();
  };

  const canTrain = dealCount >= 10;

  return (
    <div className="h-full overflow-auto">
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Brain className="h-6 w-6" />
              ML Price Predictor
            </h1>
            <p className="text-muted-foreground">
              Train a price prediction model on your historical deals
            </p>
          </div>
        </div>

        {/* Model Status */}
        <Card>
          <CardHeader>
            <CardTitle>Model Status</CardTitle>
            <CardDescription>
              Current model performance and settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {model ? (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-sm text-muted-foreground">Training Samples</div>
                    <div className="text-2xl font-bold">
                      {model.metrics?.trainSamples || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">R² Score</div>
                    <div className="text-2xl font-bold">
                      {model.metrics?.r2.toFixed(3) || '0.000'}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Mean Error</div>
                    <div className="text-2xl font-bold">
                      {formatCurrency(model.metrics?.mae || 0)}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Features</div>
                    <div className="text-2xl font-bold">
                      {model.featureNames.length}
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <div className="flex items-center justify-between mb-4">
                    <Label htmlFor="use-model">Use ML predictions in pricing</Label>
                    <Switch
                      id="use-model"
                      checked={useModel}
                      onCheckedChange={handleToggleModel}
                    />
                  </div>

                  {useModel && (
                    <div className="space-y-2">
                      <Label>Model Blend Factor</Label>
                      <Slider
                        value={[modelBlend]}
                        onValueChange={handleBlendChange}
                        min={0}
                        max={1}
                        step={0.1}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>100% Comps</span>
                        <span className="font-medium">
                          {Math.round((1 - modelBlend) * 100)}% Comps / {Math.round(modelBlend * 100)}% Model
                        </span>
                        <span>100% Model</span>
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <Brain className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-muted-foreground">No model trained yet</p>
                <p className="text-sm text-muted-foreground mt-2">
                  Train a model on your sold deals to enable predictions
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Training */}
        <Card>
          <CardHeader>
            <CardTitle>Model Training</CardTitle>
            <CardDescription>
              Train or update the price prediction model
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <TrendingUp className="h-4 w-4" />
              <AlertDescription>
                You have {dealCount} sold deals. {canTrain 
                  ? 'You can train a model.' 
                  : `Need ${10 - dealCount} more sold deals to train.`}
              </AlertDescription>
            </Alert>

            <div className="flex gap-2">
              <Button 
                onClick={handleTrain}
                disabled={!canTrain || isTraining}
              >
                <Play className="h-4 w-4 mr-2" />
                {isTraining ? 'Training...' : 'Train Model'}
              </Button>

              {model && (
                <>
                  <Button variant="outline" onClick={handleExport}>
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                  <Button variant="outline" onClick={handleImport}>
                    <Upload className="h-4 w-4 mr-2" />
                    Import
                  </Button>
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Feature Importance */}
        {model && (
          <Card>
            <CardHeader>
              <CardTitle>Feature Importance</CardTitle>
              <CardDescription>
                Which features have the most impact on price
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {model.featureNames.map((name, idx) => {
                  const weight = Math.abs(model.weights[idx]);
                  const maxWeight = Math.max(...model.weights.map(Math.abs));
                  const percentage = (weight / maxWeight) * 100;
                  
                  return (
                    <div key={name}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium">{name}</span>
                        <span className="text-muted-foreground">
                          {model.weights[idx] > 0 ? '+' : ''}{model.weights[idx].toFixed(2)}
                        </span>
                      </div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary transition-all"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}