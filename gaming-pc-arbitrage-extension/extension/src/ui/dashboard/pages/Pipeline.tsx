/**
 * Pipeline Page - Kanban view of deals
 */

import React, { useState, useEffect } from 'react';
import { Plus, Filter, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Kanban } from '../components/Kanban';
import { Charts } from '../components/Charts';
import { db, dealsByStage } from '@/lib/db';
import { exportJson } from '@/lib/db';
import type { Deal } from '@/core';

export function Pipeline() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCharts, setShowCharts] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadDeals();
  }, []);

  const loadDeals = async () => {
    try {
      const allDeals = await dealsByStage();
      setDeals(allDeals as Deal[]);
    } catch (error) {
      console.error('Failed to load deals:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStageChange = async (dealId: string, newStage: Deal['stage']) => {
    // Update in DB
    await db.deals
      .where('id')
      .equals(dealId)
      .modify({ stage: newStage });
    
    // Reload deals
    await loadDeals();
  };

  const handleExport = async () => {
    try {
      const data = await exportJson();
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `arbitrage-pipeline-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const filteredDeals = deals.filter((deal) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      deal.listing.title.toLowerCase().includes(query) ||
      deal.listing.seller?.name?.toLowerCase().includes(query) ||
      deal.id.toLowerCase().includes(query)
    );
  });

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b bg-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Deal Pipeline</h2>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => setShowCharts(!showCharts)}
            >
              {showCharts ? 'Hide Charts' : 'Show Charts'}
            </Button>
            <Button variant="outline" onClick={handleExport}>
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        <div className="flex gap-4">
          <div className="flex-1">
            <Input
              placeholder="Search deals..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="max-w-sm"
            />
          </div>
          <Button variant="outline">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden p-6">
        {showCharts && (
          <div className="mb-6">
            <Charts deals={deals} />
          </div>
        )}
        
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          <Kanban
            deals={filteredDeals}
            onStageChange={handleStageChange}
          />
        )}
      </div>
    </div>
  );
}