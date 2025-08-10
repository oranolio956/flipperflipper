/**
 * Advanced Analytics Page
 * Business metrics with filtering and export
 */

import React, { useState, useEffect, useMemo } from 'react';
import { TrendingUp, Download, Calendar, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { db } from '@/lib/db';
import {
  CohortChart,
  SeasonalityChart,
  ElasticityChart,
  DemandChart,
  MarginTrendChart,
} from '../components/AdvancedCharts';
import {
  cohortsByMonth,
  seasonalityFactors,
  priceElasticity,
  demandScoreByComponent,
  marginTrend,
} from '@/core/analytics';
import type { Deal } from '@/core';

export function Analytics() {
  const { toast } = useToast();
  const [deals, setDeals] = useState<Deal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Filters
  const [dateRange, setDateRange] = useState<'30d' | '90d' | '1y' | 'all'>('90d');
  const [source, setSource] = useState<'all' | 'facebook' | 'craigslist' | 'offerup'>('all');
  const [gpuTier, setGpuTier] = useState<'all' | 'rtx30' | 'rtx40' | 'amd' | 'other'>('all');

  useEffect(() => {
    loadDeals();
  }, []);

  const loadDeals = async () => {
    try {
      const allDeals = await db.deals.toArray();
      setDeals(allDeals as Deal[]);
    } catch (error) {
      console.error('Failed to load deals:', error);
      toast({
        title: 'Failed to load data',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Apply filters
  const filteredDeals = useMemo(() => {
    let filtered = [...deals];
    
    // Date range filter
    if (dateRange !== 'all') {
      const now = new Date();
      const days = dateRange === '30d' ? 30 : dateRange === '90d' ? 90 : 365;
      const cutoff = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
      filtered = filtered.filter(d => new Date(d.metadata.createdAt) >= cutoff);
    }
    
    // Source filter
    if (source !== 'all') {
      filtered = filtered.filter(d => d.listing.platform === source);
    }
    
    // GPU tier filter
    if (gpuTier !== 'all') {
      filtered = filtered.filter(d => {
        const gpu = d.listing.components.gpu?.model?.toLowerCase() || '';
        switch (gpuTier) {
          case 'rtx30':
            return gpu.includes('rtx 30') || gpu.includes('rtx30');
          case 'rtx40':
            return gpu.includes('rtx 40') || gpu.includes('rtx40');
          case 'amd':
            return gpu.includes('rx ') || gpu.includes('radeon');
          case 'other':
            return gpu && !gpu.includes('rtx') && !gpu.includes('rx') && !gpu.includes('radeon');
          default:
            return true;
        }
      });
    }
    
    return filtered;
  }, [deals, dateRange, source, gpuTier]);

  // Calculate analytics
  const analytics = useMemo(() => {
    if (filteredDeals.length === 0) return null;
    
    const cohorts = cohortsByMonth(filteredDeals);
    const seasonality = seasonalityFactors(filteredDeals);
    const elasticity = priceElasticity(filteredDeals);
    const demand = demandScoreByComponent(filteredDeals);
    const trend = marginTrend(filteredDeals);
    
    // Get elasticity data points
    const elasticityPoints = filteredDeals
      .filter(d => d.stage === 'sold' && d.soldAt && d.soldPrice)
      .map(d => ({
        x: (d.listing.price - d.soldPrice!) / d.listing.price,
        y: Math.ceil(
          (new Date(d.soldAt!).getTime() - new Date(d.metadata.createdAt).getTime()) / 
          (1000 * 60 * 60 * 24)
        ),
      }));
    
    return {
      cohorts,
      seasonality,
      elasticity: { points: elasticityPoints, result: elasticity },
      demand,
      trend,
    };
  }, [filteredDeals]);

  const handleExportCSV = () => {
    if (!analytics) return;
    
    // Prepare CSV data
    const rows: string[] = [];
    
    // Cohorts
    rows.push('Cohort Analysis');
    rows.push('Month,Acquired,Sold,Avg Margin %,Avg Turn Time (days)');
    analytics.cohorts.forEach(c => {
      rows.push(`${c.month},${c.acquired},${c.sold},${c.avgMarginPct.toFixed(1)},${c.avgTurnTime.toFixed(1)}`);
    });
    
    rows.push('');
    rows.push('Component Demand');
    rows.push('Component,Score,Velocity/mo,Avg Margin %');
    analytics.demand.slice(0, 20).forEach(d => {
      rows.push(`"${d.component}",${d.score.toFixed(0)},${d.velocity.toFixed(2)},${(d.avgMargin * 100).toFixed(1)}`);
    });
    
    // Create and download CSV
    const csv = rows.join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    
    toast({
      title: 'Analytics exported',
      description: 'CSV file downloaded successfully',
    });
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
              <TrendingUp className="h-6 w-6" />
              Advanced Analytics
            </h1>
            <p className="text-muted-foreground">
              Business intelligence and performance metrics
            </p>
          </div>
          <Button onClick={handleExportCSV} disabled={!analytics}>
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        </div>

        {/* Filters */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-4 w-4" />
              Filters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Date Range</Label>
                <Select value={dateRange} onValueChange={(v: any) => setDateRange(v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="30d">Last 30 days</SelectItem>
                    <SelectItem value="90d">Last 90 days</SelectItem>
                    <SelectItem value="1y">Last year</SelectItem>
                    <SelectItem value="all">All time</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>Source</Label>
                <Select value={source} onValueChange={(v: any) => setSource(v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All sources</SelectItem>
                    <SelectItem value="facebook">Facebook</SelectItem>
                    <SelectItem value="craigslist">Craigslist</SelectItem>
                    <SelectItem value="offerup">OfferUp</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>GPU Tier</Label>
                <Select value={gpuTier} onValueChange={(v: any) => setGpuTier(v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All GPUs</SelectItem>
                    <SelectItem value="rtx30">RTX 30 Series</SelectItem>
                    <SelectItem value="rtx40">RTX 40 Series</SelectItem>
                    <SelectItem value="amd">AMD</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="mt-4 text-sm text-muted-foreground">
              Analyzing {filteredDeals.length} deals
            </div>
          </CardContent>
        </Card>

        {/* Charts */}
        {analytics && filteredDeals.length > 0 ? (
          <div className="space-y-6">
            <CohortChart data={analytics.cohorts} />
            <SeasonalityChart data={analytics.seasonality} />
            <ElasticityChart data={analytics.elasticity} />
            <DemandChart data={analytics.demand} />
            <MarginTrendChart data={analytics.trend} />
          </div>
        ) : (
          <Card>
            <CardContent className="p-12 text-center">
              <p className="text-muted-foreground">
                No data available for the selected filters
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}