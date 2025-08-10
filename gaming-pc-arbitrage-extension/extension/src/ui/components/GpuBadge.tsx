/**
 * GPU Badge Component
 * Display GPU tier and performance info
 */

import React from 'react';
import { Cpu } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { findGPU, type GPUInfo } from '@/core/data/gpuHierarchy';
import { formatCurrency } from '@/core';

interface GpuBadgeProps {
  gpu: string;
  price?: number;
  showTooltip?: boolean;
  className?: string;
}

export function GpuBadge({ 
  gpu, 
  price,
  showTooltip = true,
  className 
}: GpuBadgeProps) {
  const gpuInfo = findGPU(gpu);
  
  if (!gpuInfo) {
    return (
      <Badge variant="outline" className={className}>
        <Cpu className="h-3 w-3 mr-1" />
        {gpu}
      </Badge>
    );
  }
  
  const getTierColor = (tier: GPUInfo['tier']) => {
    switch (tier) {
      case 'S': return 'bg-purple-500 hover:bg-purple-600';
      case 'A': return 'bg-red-500 hover:bg-red-600';
      case 'B': return 'bg-orange-500 hover:bg-orange-600';
      case 'C': return 'bg-yellow-500 hover:bg-yellow-600';
      case 'D': return 'bg-green-500 hover:bg-green-600';
      case 'F': return 'bg-gray-500 hover:bg-gray-600';
      default: return 'bg-gray-500 hover:bg-gray-600';
    }
  };
  
  const getTierLabel = (tier: GPUInfo['tier']) => {
    switch (tier) {
      case 'S': return 'Flagship';
      case 'A': return 'High-End';
      case 'B': return 'Mid-High';
      case 'C': return 'Mainstream';
      case 'D': return 'Budget';
      case 'F': return 'Entry';
      default: return 'Unknown';
    }
  };
  
  const getValueLabel = (gpuInfo: GPUInfo, price?: number) => {
    if (!price) return '';
    
    const midpoint = (gpuInfo.resaleRange.min + gpuInfo.resaleRange.max) / 2;
    const percentOfValue = (price / midpoint) * 100;
    
    if (percentOfValue < 80) return 'Great Deal';
    if (percentOfValue < 95) return 'Good Price';
    if (percentOfValue < 105) return 'Fair Price';
    if (percentOfValue < 120) return 'High Price';
    return 'Overpriced';
  };
  
  const badge = (
    <Badge 
      className={`${getTierColor(gpuInfo.tier)} text-white border-0 ${className}`}
    >
      <Cpu className="h-3 w-3 mr-1" />
      {gpuInfo.tier}-Tier
    </Badge>
  );
  
  if (!showTooltip) {
    return badge;
  }
  
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          {badge}
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-sm">
          <div className="space-y-2">
            <div className="font-semibold">{gpuInfo.name}</div>
            
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
              <div className="text-muted-foreground">Tier:</div>
              <div>{gpuInfo.tier} - {getTierLabel(gpuInfo.tier)}</div>
              
              <div className="text-muted-foreground">Performance:</div>
              <div>{gpuInfo.perfIndex}/100</div>
              
              <div className="text-muted-foreground">VRAM:</div>
              <div>{gpuInfo.vram}GB</div>
              
              <div className="text-muted-foreground">TDP:</div>
              <div>{gpuInfo.tdp}W</div>
              
              <div className="text-muted-foreground">Resale Range:</div>
              <div>
                {formatCurrency(gpuInfo.resaleRange.min)} - {formatCurrency(gpuInfo.resaleRange.max)}
              </div>
              
              {price && (
                <>
                  <div className="text-muted-foreground">This Price:</div>
                  <div className="font-medium">{getValueLabel(gpuInfo, price)}</div>
                </>
              )}
            </div>
            
            {gpuInfo.msrp && (
              <div className="text-xs text-muted-foreground pt-1 border-t">
                Original MSRP: {formatCurrency(gpuInfo.msrp)}
              </div>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}