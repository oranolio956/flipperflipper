/**
 * Price Drop Button Component
 * Watch/unwatch listings for price drops
 */

import React, { useState, useEffect } from 'react';
import { Eye, EyeOff, TrendingDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import {
  watchListing,
  unwatchListing,
  isWatched,
  getPriceDropStats,
} from '@/lib/priceDropWatcher';
import { formatCurrency } from '@/core';
import type { Listing } from '@/core';

interface PriceDropButtonProps {
  listing: Listing;
  className?: string;
}

export function PriceDropButton({ listing, className }: PriceDropButtonProps) {
  const { toast } = useToast();
  const [watched, setWatched] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    checkWatchStatus();
  }, [listing.id]);

  const checkWatchStatus = async () => {
    const isListingWatched = await isWatched(listing.id);
    setWatched(isListingWatched);
    
    if (isListingWatched) {
      const dropStats = await getPriceDropStats(listing.id);
      setStats(dropStats);
    }
  };

  const handleToggleWatch = async () => {
    setIsLoading(true);
    try {
      if (watched) {
        await unwatchListing(listing.id);
        setWatched(false);
        setStats(null);
        
        toast({
          title: 'Stopped watching',
          description: 'You will no longer receive price drop alerts',
        });
      } else {
        await watchListing(listing);
        setWatched(true);
        
        toast({
          title: 'Watching for price drops',
          description: 'You\'ll be notified when the price drops 10% or more',
        });
      }
    } catch (error) {
      toast({
        title: 'Failed to update watch status',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <TooltipProvider>
      <div className={`flex items-center gap-2 ${className}`}>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant={watched ? 'default' : 'outline'}
              size="sm"
              onClick={handleToggleWatch}
              disabled={isLoading}
            >
              {watched ? (
                <EyeOff className="h-4 w-4 mr-2" />
              ) : (
                <Eye className="h-4 w-4 mr-2" />
              )}
              {watched ? 'Watching' : 'Watch'}
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            {watched 
              ? 'Click to stop watching for price drops' 
              : 'Watch this listing for price drops'
            }
          </TooltipContent>
        </Tooltip>

        {stats && stats.totalDrop > 0 && (
          <Tooltip>
            <TooltipTrigger>
              <Badge variant="success" className="cursor-help">
                <TrendingDown className="h-3 w-3 mr-1" />
                -{Math.round(stats.totalDropPct)}%
              </Badge>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-xs">
              <div className="space-y-2">
                <div className="font-semibold">Price Drop History</div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                  <div className="text-muted-foreground">Original:</div>
                  <div>{formatCurrency(stats.originalPrice)}</div>
                  
                  <div className="text-muted-foreground">Current:</div>
                  <div className="font-medium text-green-600">
                    {formatCurrency(stats.currentPrice)}
                  </div>
                  
                  <div className="text-muted-foreground">Lowest:</div>
                  <div>{formatCurrency(stats.lowestPrice)}</div>
                  
                  <div className="text-muted-foreground">Total Drop:</div>
                  <div>
                    {formatCurrency(stats.totalDrop)} ({Math.round(stats.totalDropPct)}%)
                  </div>
                  
                  <div className="text-muted-foreground">Days Watched:</div>
                  <div>{stats.daysWatched}</div>
                </div>
                
                {stats.priceHistory.length > 1 && (
                  <div className="pt-2 border-t">
                    <div className="text-xs text-muted-foreground">
                      {stats.priceHistory.length} price changes tracked
                    </div>
                  </div>
                )}
              </div>
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </TooltipProvider>
  );
}