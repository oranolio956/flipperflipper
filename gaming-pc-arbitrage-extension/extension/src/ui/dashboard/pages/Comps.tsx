/**
 * Comps Page
 * View and manage market comparables
 */

import React, { useState, useEffect } from 'react';
import { BarChart3, Upload, Download, Trash2, Filter } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  getAllComps,
  getCompStats,
  importCompsFromCsv,
  exportCompsToCsv,
  clearComps,
} from '@/lib/comps.store';
import type { CompRecord, CompStats } from '@/core/comps';

export function Comps() {
  const { toast } = useToast();
  const [comps, setComps] = useState<CompRecord[]>([]);
  const [stats, setStats] = useState<CompStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState({ cpu: '', gpu: '' });

  useEffect(() => {
    loadComps();
  }, []);

  useEffect(() => {
    if (filter.cpu || filter.gpu) {
      loadStats();
    }
  }, [filter]);

  const loadComps = async () => {
    try {
      const data = await getAllComps();
      setComps(data);
    } catch (error) {
      console.error('Failed to load comps:', error);
      toast({
        title: 'Failed to load comparables',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const query: any = {};
      if (filter.cpu) query.cpu = filter.cpu;
      if (filter.gpu) query.gpu = filter.gpu;
      
      const stats = await getCompStats(query);
      setStats(stats);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv';
    
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      
      try {
        const text = await file.text();
        const count = await importCompsFromCsv(text);
        
        toast({
          title: 'Import complete',
          description: `Imported ${count} comparables`,
        });
        
        await loadComps();
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

  const handleExport = () => {
    try {
      const csv = exportCompsToCsv(comps);
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `comps-${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      
      toast({
        title: 'Export complete',
        description: `Exported ${comps.length} comparables`,
      });
    } catch (error) {
      toast({
        title: 'Export failed',
        description: String(error),
        variant: 'destructive',
      });
    }
  };

  const handleClear = async () => {
    if (!confirm('Clear all comparables? This cannot be undone.')) {
      return;
    }
    
    try {
      await clearComps();
      await loadComps();
      setStats(null);
      
      toast({
        title: 'Cleared',
        description: 'All comparables removed',
      });
    } catch (error) {
      toast({
        title: 'Clear failed',
        description: String(error),
        variant: 'destructive',
      });
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const formatDate = (date: Date) => {
    const d = date instanceof Date ? date : new Date(date);
    const days = Math.floor((Date.now() - d.getTime()) / (1000 * 60 * 60 * 24));
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return d.toLocaleDateString();
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
              <BarChart3 className="h-6 w-6" />
              Market Comparables
            </h1>
            <p className="text-muted-foreground">
              {comps.length} comparables from sold listings
            </p>
          </div>
          
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleImport}>
              <Upload className="h-4 w-4 mr-2" />
              Import CSV
            </Button>
            <Button variant="outline" onClick={handleExport}>
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
            <Button variant="outline" onClick={handleClear}>
              <Trash2 className="h-4 w-4 mr-2" />
              Clear All
            </Button>
          </div>
        </div>

        {/* Stats Card */}
        {stats && (
          <Card>
            <CardHeader>
              <CardTitle>Price Statistics</CardTitle>
              <CardDescription>
                Based on {stats.n} matching comparables (avg {stats.recencyDays} days old)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-sm text-muted-foreground">25th Percentile</div>
                  <div className="text-2xl font-bold">{formatPrice(stats.p25)}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Median</div>
                  <div className="text-3xl font-bold text-primary">{formatPrice(stats.median)}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">75th Percentile</div>
                  <div className="text-2xl font-bold">{formatPrice(stats.p75)}</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Filters */}
        <Card>
          <CardHeader>
            <CardTitle>Filters</CardTitle>
            <CardDescription>
              Filter comparables to get specific pricing
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="cpu-filter">CPU Model</Label>
                <Input
                  id="cpu-filter"
                  placeholder="e.g., i7-10700K"
                  value={filter.cpu}
                  onChange={(e) => setFilter({ ...filter, cpu: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="gpu-filter">GPU Model</Label>
                <Input
                  id="gpu-filter"
                  placeholder="e.g., RTX 3070"
                  value={filter.gpu}
                  onChange={(e) => setFilter({ ...filter, gpu: e.target.value })}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Comps Table */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Comparables</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Price</TableHead>
                  <TableHead>CPU</TableHead>
                  <TableHead>GPU</TableHead>
                  <TableHead>RAM</TableHead>
                  <TableHead>Storage</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {comps.slice(0, 50).map((comp) => (
                  <TableRow key={comp.id}>
                    <TableCell className="max-w-xs truncate">
                      {comp.url ? (
                        <a
                          href={comp.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:underline"
                        >
                          {comp.title}
                        </a>
                      ) : (
                        comp.title
                      )}
                    </TableCell>
                    <TableCell className="font-medium">
                      {formatPrice(comp.price)}
                    </TableCell>
                    <TableCell>
                      {comp.cpu && <Badge variant="outline">{comp.cpu}</Badge>}
                    </TableCell>
                    <TableCell>
                      {comp.gpu && <Badge variant="outline">{comp.gpu}</Badge>}
                    </TableCell>
                    <TableCell>{comp.ram ? `${comp.ram}GB` : '-'}</TableCell>
                    <TableCell>{comp.storage ? `${comp.storage}GB` : '-'}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{comp.source}</Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDate(comp.timestamp)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}