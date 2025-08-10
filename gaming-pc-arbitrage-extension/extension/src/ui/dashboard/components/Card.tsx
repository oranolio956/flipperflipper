/**
 * Card Component - Deal card for Kanban board
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, DollarSign, TrendingUp, AlertCircle, MessageSquare } from 'lucide-react';
import { Card as UICard, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatCurrency, formatPercentage, formatDaysAgo } from '@/core';
import type { Deal } from '@/core';

interface CardProps {
  deal: Deal;
}

export function Card({ deal }: CardProps) {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/pipeline/${deal.id}`);
  };

  const getRiskColor = (score: number) => {
    if (score <= 3) return 'text-green-600';
    if (score <= 6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <UICard 
      className="hover:shadow-md transition-shadow cursor-pointer"
      onClick={handleClick}
    >
      <CardContent className="p-4">
        {/* Title and price */}
        <div className="mb-3">
          <h4 className="font-medium text-sm line-clamp-2 mb-1">
            {deal.listing.title}
          </h4>
          <div className="flex items-center justify-between">
            <span className="text-lg font-semibold">
              {formatCurrency(deal.listing.price)}
            </span>
            {deal.listing.risks && (
              <span className={`text-sm ${getRiskColor(deal.listing.risks.score)}`}>
                <AlertCircle className="h-4 w-4 inline mr-1" />
                {deal.listing.risks.score}/10
              </span>
            )}
          </div>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
          <div className="flex items-center gap-1">
            <TrendingUp className="h-3 w-3 text-muted-foreground" />
            <span>ROI: {formatPercentage(deal.analytics.roi)}</span>
          </div>
          <div className="flex items-center gap-1">
            <DollarSign className="h-3 w-3 text-muted-foreground" />
            <span>+{formatCurrency(deal.financials.estimatedProfit)}</span>
          </div>
        </div>

        {/* Components */}
        <div className="flex flex-wrap gap-1 mb-3">
          {deal.listing.components.cpu && (
            <Badge variant="outline" className="text-xs">
              {deal.listing.components.cpu.model}
            </Badge>
          )}
          {deal.listing.components.gpu && (
            <Badge variant="outline" className="text-xs">
              {deal.listing.components.gpu.model}
            </Badge>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatDaysAgo(deal.metadata.createdAt)}
          </span>
          {deal.communication.messages.length > 0 && (
            <span className="flex items-center gap-1">
              <MessageSquare className="h-3 w-3" />
              {deal.communication.messages.length}
            </span>
          )}
        </div>

        {/* Priority indicator */}
        {deal.metadata.priority === 'high' && (
          <div className="absolute top-2 right-2">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
          </div>
        )}
      </CardContent>
    </UICard>
  );
}