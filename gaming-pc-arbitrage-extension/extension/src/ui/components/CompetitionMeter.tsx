/**
 * Competition Meter Component
 * Visual competition indicator with tips
 */

import React from 'react';
import { Users, TrendingUp, Info } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import type { CompetitionScore } from '@/core/competition/signals';

interface CompetitionMeterProps {
  competition: CompetitionScore;
  className?: string;
}

export function CompetitionMeter({ competition, className }: CompetitionMeterProps) {
  const getColor = () => {
    if (competition.score >= 70) return 'text-red-500';
    if (competition.score >= 40) return 'text-yellow-500';
    return 'text-green-500';
  };

  const getProgressColor = () => {
    if (competition.score >= 70) return 'bg-red-500';
    if (competition.score >= 40) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getLevel = () => {
    if (competition.score >= 70) return 'HIGH';
    if (competition.score >= 40) return 'MODERATE';
    return 'LOW';
  };

  const getLevelVariant = () => {
    if (competition.score >= 70) return 'destructive';
    if (competition.score >= 40) return 'warning';
    return 'success';
  };

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Competition Level
          </span>
          <Badge variant={getLevelVariant()}>
            {getLevel()}
          </Badge>
        </CardTitle>
        <CardDescription>
          Buyer competition signals
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium">Competition Score</span>
            <span className={`text-2xl font-bold ${getColor()}`}>
              {competition.score}
            </span>
          </div>
          <Progress 
            value={competition.score} 
            className="h-3"
            indicatorClassName={getProgressColor()}
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>Low</span>
            <span>Moderate</span>
            <span>High</span>
          </div>
        </div>

        {/* Reasons */}
        {competition.reasons.length > 0 && (
          <div className="space-y-1">
            <div className="text-sm font-medium mb-2">Signals:</div>
            {competition.reasons.map((reason, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <TrendingUp className="h-3 w-3 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">{reason}</span>
              </div>
            ))}
          </div>
        )}

        {/* Tips */}
        {competition.tips.length > 0 && (
          <div className="bg-muted/50 rounded-lg p-3 space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Info className="h-4 w-4" />
              Strategy Tips
            </div>
            {competition.tips.map((tip, idx) => (
              <div key={idx} className="text-sm text-muted-foreground pl-6">
                • {tip}
              </div>
            ))}
          </div>
        )}

        {/* Quick Actions Based on Competition */}
        <div className="pt-2 border-t">
          <TooltipProvider>
            <div className="flex gap-2">
              {competition.score >= 70 && (
                <Tooltip>
                  <TooltipTrigger>
                    <Badge variant="outline" className="cursor-help">
                      Act Fast
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent>
                    High competition - make your best offer quickly
                  </TooltipContent>
                </Tooltip>
              )}
              
              {competition.score < 40 && (
                <Tooltip>
                  <TooltipTrigger>
                    <Badge variant="outline" className="cursor-help">
                      Negotiate Hard
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent>
                    Low competition - you have leverage
                  </TooltipContent>
                </Tooltip>
              )}
              
              {competition.reasons.some(r => r.includes('relisted')) && (
                <Tooltip>
                  <TooltipTrigger>
                    <Badge variant="outline" className="cursor-help">
                      Previous Deals Fell Through
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent>
                    Seller has had buyers back out - be reliable
                  </TooltipContent>
                </Tooltip>
              )}
            </div>
          </TooltipProvider>
        </div>
      </CardContent>
    </Card>
  );
}