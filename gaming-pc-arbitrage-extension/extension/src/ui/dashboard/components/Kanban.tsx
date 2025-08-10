/**
 * Kanban Component - Drag and drop deal management
 */

import React from 'react';
import { Card } from '../components/Card';
import type { Deal } from '@/core';

interface KanbanProps {
  deals: Deal[];
  onStageChange: (dealId: string, newStage: Deal['stage']) => void;
}

const STAGES: Array<{
  id: Deal['stage'];
  label: string;
  color: string;
}> = [
  { id: 'discovered', label: 'Discovered', color: 'bg-gray-100' },
  { id: 'contacted', label: 'Contacted', color: 'bg-blue-100' },
  { id: 'negotiating', label: 'Negotiating', color: 'bg-yellow-100' },
  { id: 'pending_pickup', label: 'Pending Pickup', color: 'bg-purple-100' },
  { id: 'acquired', label: 'Acquired', color: 'bg-green-100' },
  { id: 'refurbishing', label: 'Refurbishing', color: 'bg-orange-100' },
  { id: 'listed', label: 'Listed', color: 'bg-indigo-100' },
  { id: 'sold', label: 'Sold', color: 'bg-green-200' },
];

export function Kanban({ deals, onStageChange }: KanbanProps) {
  const handleDragStart = (e: React.DragEvent, dealId: string) => {
    e.dataTransfer.setData('dealId', dealId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent, stage: Deal['stage']) => {
    e.preventDefault();
    const dealId = e.dataTransfer.getData('dealId');
    if (dealId) {
      onStageChange(dealId, stage);
    }
  };

  const dealsByStage = STAGES.reduce((acc, stage) => {
    acc[stage.id] = deals.filter(deal => deal.stage === stage.id);
    return acc;
  }, {} as Record<Deal['stage'], Deal[]>);

  return (
    <div className="flex gap-4 h-full overflow-x-auto pb-4">
      {STAGES.map((stage) => (
        <div
          key={stage.id}
          className={`flex-shrink-0 w-80 ${stage.color} rounded-lg p-4`}
          onDragOver={handleDragOver}
          onDrop={(e) => handleDrop(e, stage.id)}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">{stage.label}</h3>
            <span className="text-sm text-muted-foreground">
              {dealsByStage[stage.id].length}
            </span>
          </div>

          <div className="space-y-3 max-h-[calc(100vh-300px)] overflow-y-auto">
            {dealsByStage[stage.id].map((deal) => (
              <div
                key={deal.id}
                draggable
                onDragStart={(e) => handleDragStart(e, deal.id)}
                className="cursor-move"
              >
                <Card deal={deal} />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}