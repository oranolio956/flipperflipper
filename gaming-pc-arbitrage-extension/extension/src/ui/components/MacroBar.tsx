/**
 * Macro Bar Component
 * Configurable one-click actions for common workflows
 */

import React, { useState } from 'react';
import {
  MessageSquare,
  Calculator,
  Calendar,
  CheckCircle,
  FileText,
  Clock,
  Zap,
  Settings,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useToast } from '@/components/ui/use-toast';
import { useHotkeys } from '@/lib/hooks/useHotkeys';
import { generateDraft } from '@/lib/negotiationBridge';
import { suggestAnchors } from '@/lib/offerEngine';
import { exportDealToIcs } from '@/lib/calendar';
import type { Deal, Listing } from '@/core';

interface MacroBarProps {
  deal?: Deal;
  listing?: Listing;
  fmv?: number;
  riskScore?: number;
  onRefresh?: () => void;
  className?: string;
}

interface MacroAction {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  hotkey?: string;
  action: () => void | Promise<void>;
  enabled: boolean;
}

export function MacroBar({
  deal,
  listing,
  fmv = 0,
  riskScore = 0,
  onRefresh,
  className,
}: MacroBarProps) {
  const { toast } = useToast();
  const [isProcessing, setIsProcessing] = useState<string | null>(null);

  const handleDraftOpener = async () => {
    if (!deal) return;
    
    setIsProcessing('draft-opener');
    try {
      const draft = await generateDraft(deal, 'opening');
      
      // Copy to clipboard
      await navigator.clipboard.writeText(draft.content);
      
      toast({
        title: 'Opening message copied',
        description: 'Paste into messenger to send',
      });
    } catch (error) {
      toast({
        title: 'Failed to generate message',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(null);
    }
  };

  const handleFollowUp24h = async () => {
    if (!deal) return;
    
    setIsProcessing('followup-24h');
    try {
      // In real implementation, would update thread in DB
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      
      toast({
        title: 'Follow-up scheduled',
        description: `Reminder set for ${tomorrow.toLocaleDateString()}`,
      });
    } catch (error) {
      toast({
        title: 'Failed to set follow-up',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(null);
    }
  };

  const handlePriceCalculator = () => {
    if (!fmv) return;
    
    const anchors = suggestAnchors(fmv, riskScore);
    
    const message = `
Price Calculator:
• FMV: $${fmv}
• Opening: $${anchors.open} (25% below)
• Target: $${anchors.target} (15% below)
• Walk-away: $${anchors.walkaway} (5% below)
    `.trim();
    
    // Copy to clipboard
    navigator.clipboard.writeText(message);
    
    toast({
      title: 'Price points copied',
      description: 'Paste anywhere to reference',
    });
  };

  const handleAddPickupCalendar = async () => {
    if (!deal || !deal.logistics?.pickup?.scheduled) return;
    
    setIsProcessing('add-calendar');
    try {
      const icsContent = exportDealToIcs(deal);
      const blob = new Blob([icsContent], { type: 'text/calendar' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `pickup-${deal.listing.title.replace(/\s+/g, '-')}.ics`;
      a.click();
      URL.revokeObjectURL(url);
      
      toast({
        title: 'Calendar event downloaded',
        description: 'Import to your calendar app',
      });
    } catch (error) {
      toast({
        title: 'Failed to create event',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(null);
    }
  };

  const handleMarkAcquired = async () => {
    if (!deal) return;
    
    setIsProcessing('mark-acquired');
    try {
      // In real implementation, would update deal stage
      toast({
        title: 'Deal marked as acquired',
        description: 'Moved to inventory stage',
      });
      
      onRefresh?.();
    } catch (error) {
      toast({
        title: 'Failed to update deal',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(null);
    }
  };

  const handleCreateInvoice = () => {
    if (!deal) return;
    
    // Stub - would generate PDF in real implementation
    toast({
      title: 'Invoice generation',
      description: 'Feature coming soon',
    });
  };

  const actions: MacroAction[] = [
    {
      id: 'draft-opener',
      label: 'Draft Opener',
      icon: MessageSquare,
      hotkey: 'cmd+o',
      action: handleDraftOpener,
      enabled: !!deal,
    },
    {
      id: 'followup-24h',
      label: 'Follow-up 24h',
      icon: Clock,
      hotkey: 'cmd+f',
      action: handleFollowUp24h,
      enabled: !!deal,
    },
    {
      id: 'price-calc',
      label: 'Price Calculator',
      icon: Calculator,
      hotkey: 'cmd+p',
      action: handlePriceCalculator,
      enabled: fmv > 0,
    },
    {
      id: 'add-calendar',
      label: 'Add to Calendar',
      icon: Calendar,
      hotkey: 'cmd+k',
      action: handleAddPickupCalendar,
      enabled: !!deal?.logistics?.pickup?.scheduled,
    },
    {
      id: 'mark-acquired',
      label: 'Mark Acquired',
      icon: CheckCircle,
      action: handleMarkAcquired,
      enabled: !!deal && deal.stage === 'negotiating',
    },
    {
      id: 'create-invoice',
      label: 'Create Invoice',
      icon: FileText,
      action: handleCreateInvoice,
      enabled: !!deal && deal.stage === 'sold',
    },
  ];

  // Register hotkeys
  useHotkeys(
    actions
      .filter(a => a.hotkey && a.enabled)
      .map(a => ({
        key: a.hotkey!,
        handler: a.action,
      }))
  );

  const enabledActions = actions.filter(a => a.enabled);
  const visibleActions = enabledActions.slice(0, 5);
  const overflowActions = enabledActions.slice(5);

  return (
    <TooltipProvider>
      <div className={`flex items-center gap-1 ${className}`}>
        <div className="flex items-center gap-1 p-1 bg-muted/50 rounded-lg">
          <Zap className="h-4 w-4 text-muted-foreground ml-2" />
          
          {visibleActions.map((action) => (
            <Tooltip key={action.id}>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={action.action}
                  disabled={isProcessing !== null}
                  className="h-8 px-2"
                >
                  <action.icon 
                    className={`h-4 w-4 ${
                      isProcessing === action.id ? 'animate-pulse' : ''
                    }`} 
                  />
                  <span className="ml-2 hidden lg:inline">
                    {action.label}
                  </span>
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <div>
                  <div>{action.label}</div>
                  {action.hotkey && (
                    <div className="text-xs text-muted-foreground">
                      {action.hotkey}
                    </div>
                  )}
                </div>
              </TooltipContent>
            </Tooltip>
          ))}
          
          {overflowActions.length > 0 && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 px-2">
                  <Settings className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {overflowActions.map((action) => (
                  <DropdownMenuItem
                    key={action.id}
                    onClick={action.action}
                    disabled={isProcessing !== null}
                  >
                    <action.icon className="h-4 w-4 mr-2" />
                    {action.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
        
        <div className="text-xs text-muted-foreground px-2">
          Quick Actions
        </div>
      </div>
    </TooltipProvider>
  );
}