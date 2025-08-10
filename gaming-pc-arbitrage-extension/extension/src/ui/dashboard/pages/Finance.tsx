/**
 * Finance Page
 * P&L dashboard with charts and export
 */

import React, { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, Download, Calendar } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { db } from '@/lib/db';
import { 
  rollupPnL, 
  generatePnLTimeSeries,
  exportPnLCsv,
  type PnLSummary,
  type PnLTimeSeries 
} from '@/core/finance/pnl';
import { formatCurrency, formatPercentage } from '@/core';
import type { Deal } from '@/core';

export function Finance() {
  const { toast } = useToast();
  const [deals, setDeals] = useState<Deal[]>([]);
  const [summary, setSummary] = useState<PnLSummary | null>(null);
  const [timeSeries, setTimeSeries] = useState<PnLTimeSeries[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [dateRange, setDateRange] = useState<'all' | '30d' | '90d' | 'ytd'>('90d');
  const [granularity, setGranularity] = useState<'daily' | 'weekly' | 'monthly'>('monthly');

  useEffect(() => {
    loadData();
  }, [dateRange]);

  useEffect(() => {
    if (deals.length > 0) {
      const series = generatePnLTimeSeries(deals, granularity);
      setTimeSeries(series);
    }
  }, [deals, granularity]);

  const loadData = async () => {
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
      
      // Apply date filter
      const now = new Date();
      let filteredDeals = typedDeals;
      let range: { start: Date; end: Date } | undefined;
      
      if (dateRange === '30d') {
        range = {
          start: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000),
          end: now,
        };
      } else if (dateRange === '90d') {
        range = {
          start: new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000),
          end: now,
        };
      } else if (dateRange === 'ytd') {
        range = {
          start: new Date(now.getFullYear(), 0, 1),
          end: now,
        };
      }
      
      const pnlSummary = rollupPnL(typedDeals, range);
      setSummary(pnlSummary);
      
      // Set deals for time series
      if (range) {
        filteredDeals = typedDeals.filter(d => {
          const soldDate = d.soldAt ? new Date(d.soldAt) : null;
          return soldDate && soldDate >= range.start && soldDate <= range.end;
        });
      }
      
      setDeals(filteredDeals);
    } catch (error) {
      console.error('Failed to load finance data:', error);
      toast({
        title: 'Failed to load data',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = () => {
    try {
      const csv = exportPnLCsv(deals);
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `pnl-${dateRange}-${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      
      toast({
        title: 'Export complete',
        description: `Exported ${deals.filter(d => d.stage === 'sold').length} deals`,
      });
    } catch (error) {
      toast({
        title: 'Export failed',
        description: String(error),
        variant: 'destructive',
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <DollarSign className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h2 className="text-xl font-semibold mb-2">No Financial Data</h2>
          <p className="text-muted-foreground">Complete some deals to see P&L</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto">
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <DollarSign className="h-6 w-6" />
              Finance Dashboard
            </h1>
            <p className="text-muted-foreground">
              Profit & Loss Analysis
            </p>
          </div>
          
          <div className="flex gap-2">
            <Select value={dateRange} onValueChange={(v: any) => setDateRange(v)}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="30d">Last 30 Days</SelectItem>
                <SelectItem value="90d">Last 90 Days</SelectItem>
                <SelectItem value="ytd">Year to Date</SelectItem>
                <SelectItem value="all">All Time</SelectItem>
              </SelectContent>
            </Select>
            
            <Button variant="outline" onClick={handleExport}>
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(summary.totalRevenue)}</div>
              <p className="text-xs text-muted-foreground">
                {summary.dealCount} deals @ {formatCurrency(summary.avgDealSize)} avg
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Net Profit</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {formatCurrency(summary.netProfit)}
              </div>
              <p className="text-xs text-muted-foreground">
                After all expenses & taxes
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Margin %</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.avgMarginPct}%</div>
              <p className="text-xs text-muted-foreground">
                Average net margin
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Expenses</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {formatCurrency(summary.totalExpenses)}
              </div>
              <p className="text-xs text-muted-foreground">
                Fees: {formatCurrency(summary.totalFees)}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        {timeSeries.length > 0 && (
          <>
            {/* Net Profit Trend */}
            <Card>
              <CardHeader>
                <CardTitle>Net Profit Trend</CardTitle>
                <div className="flex justify-between items-center">
                  <CardDescription>
                    Monthly net profit after all expenses
                  </CardDescription>
                  <Select value={granularity} onValueChange={(v: any) => setGranularity(v)}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="daily">Daily</SelectItem>
                      <SelectItem value="weekly">Weekly</SelectItem>
                      <SelectItem value="monthly">Monthly</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={timeSeries}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis tickFormatter={(v) => `$${v}`} />
                    <Tooltip formatter={(v: any) => formatCurrency(v)} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="netProfit"
                      stroke="#10b981"
                      strokeWidth={2}
                      name="Net Profit"
                    />
                    <Line
                      type="monotone"
                      dataKey="revenue"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      name="Revenue"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Cost Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>Cost Breakdown</CardTitle>
                <CardDescription>
                  Revenue vs costs by period
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={timeSeries}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis tickFormatter={(v) => `$${v}`} />
                    <Tooltip formatter={(v: any) => formatCurrency(v)} />
                    <Legend />
                    <Bar dataKey="revenue" fill="#3b82f6" name="Revenue" />
                    <Bar dataKey="cogs" fill="#ef4444" name="COGS" />
                    <Bar dataKey="fees" fill="#f59e0b" name="Fees" />
                    <Bar dataKey="expenses" fill="#8b5cf6" name="Other Expenses" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </>
        )}

        {/* Summary Table */}
        <Card>
          <CardHeader>
            <CardTitle>P&L Summary</CardTitle>
            <CardDescription>
              Detailed breakdown for {dateRange}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between py-2 border-b">
                <span className="font-medium">Revenue</span>
                <span>{formatCurrency(summary.totalRevenue)}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-muted-foreground pl-4">- Cost of Goods Sold</span>
                <span className="text-red-600">({formatCurrency(summary.totalCogs)})</span>
              </div>
              <div className="flex justify-between py-2 border-b font-medium">
                <span>Gross Profit</span>
                <span>{formatCurrency(summary.grossProfit)}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-muted-foreground pl-4">- Platform Fees</span>
                <span className="text-red-600">({formatCurrency(summary.totalFees)})</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-muted-foreground pl-4">- Other Expenses</span>
                <span className="text-red-600">
                  ({formatCurrency(summary.totalExpenses - summary.totalFees)})
                </span>
              </div>
              <div className="flex justify-between py-2 border-t font-bold text-lg">
                <span>Net Profit</span>
                <span className="text-green-600">{formatCurrency(summary.netProfit)}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}