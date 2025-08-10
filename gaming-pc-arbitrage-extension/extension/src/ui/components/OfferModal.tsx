/**
 * Offer Modal Component
 * Create and manage offers with smart anchoring
 */

import React, { useState, useEffect } from 'react';
import { DollarSign, TrendingDown, Target, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { useToast } from '@/components/ui/use-toast';
import { formatCurrency } from '@/core';
import { 
  createOffer, 
  suggestAnchors,
  type OfferAnchors 
} from '@/lib/offerEngine';
import { generateDraft } from '@/lib/negotiationBridge';
import type { Listing, Deal } from '@/core';

interface OfferModalProps {
  open: boolean;
  onClose: () => void;
  listing: Listing;
  deal?: Deal;
  fmv: number;
  riskScore: number;
}

export function OfferModal({
  open,
  onClose,
  listing,
  deal,
  fmv,
  riskScore,
}: OfferModalProps) {
  const { toast } = useToast();
  const [anchors, setAnchors] = useState<OfferAnchors | null>(null);
  const [amount, setAmount] = useState(0);
  const [message, setMessage] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (open && fmv > 0) {
      const suggested = suggestAnchors(fmv, riskScore);
      setAnchors(suggested);
      setAmount(suggested.open);
    }
  }, [open, fmv, riskScore]);

  const handleGenerateMessage = async () => {
    if (!deal) return;
    
    setIsGenerating(true);
    try {
      const draft = await generateDraft(deal, 'opening');
      setMessage(draft.content);
    } catch (error) {
      console.error('Failed to generate message:', error);
      toast({
        title: 'Failed to generate message',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await createOffer(listing.id, amount, message);
      
      toast({
        title: 'Offer created',
        description: `Opening offer of ${formatCurrency(amount)} saved`,
      });
      
      onClose();
    } catch (error) {
      toast({
        title: 'Failed to create offer',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const getOfferLevel = () => {
    if (!anchors) return 'custom';
    if (amount <= anchors.open) return 'aggressive';
    if (amount <= anchors.target) return 'target';
    if (amount <= anchors.walkaway) return 'conservative';
    return 'high';
  };

  const getOfferColor = () => {
    const level = getOfferLevel();
    switch (level) {
      case 'aggressive':
        return 'text-green-600';
      case 'target':
        return 'text-blue-600';
      case 'conservative':
        return 'text-yellow-600';
      case 'high':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  if (!anchors) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Create Offer</DialogTitle>
          <DialogDescription>
            {listing.title}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Anchor Points */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <TrendingDown className="h-5 w-5 mx-auto mb-2 text-green-600" />
              <div className="text-sm text-muted-foreground">Opening</div>
              <div className="font-bold text-lg">{formatCurrency(anchors.open)}</div>
              <div className="text-xs text-muted-foreground">25% below FMV</div>
            </div>
            <div className="text-center">
              <Target className="h-5 w-5 mx-auto mb-2 text-blue-600" />
              <div className="text-sm text-muted-foreground">Target</div>
              <div className="font-bold text-lg">{formatCurrency(anchors.target)}</div>
              <div className="text-xs text-muted-foreground">15% below FMV</div>
            </div>
            <div className="text-center">
              <X className="h-5 w-5 mx-auto mb-2 text-yellow-600" />
              <div className="text-sm text-muted-foreground">Walk Away</div>
              <div className="font-bold text-lg">{formatCurrency(anchors.walkaway)}</div>
              <div className="text-xs text-muted-foreground">5% below FMV</div>
            </div>
          </div>

          {/* Offer Amount */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label>Offer Amount</Label>
              <div className="flex items-center gap-2">
                <span className={`text-2xl font-bold ${getOfferColor()}`}>
                  {formatCurrency(amount)}
                </span>
                <Badge variant="outline" className={getOfferColor()}>
                  {getOfferLevel()}
                </Badge>
              </div>
            </div>
            
            <Slider
              value={[amount]}
              onValueChange={([v]) => setAmount(v)}
              min={Math.round(anchors.open * 0.8)}
              max={Math.round(anchors.walkaway * 1.1)}
              step={10}
              className="w-full"
            />
            
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{formatCurrency(anchors.open * 0.8)}</span>
              <span>FMV: {formatCurrency(fmv)}</span>
              <span>{formatCurrency(anchors.walkaway * 1.1)}</span>
            </div>
          </div>

          {/* Message */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="message">Opening Message</Label>
              <Button
                variant="outline"
                size="sm"
                onClick={handleGenerateMessage}
                disabled={!deal || isGenerating}
              >
                {isGenerating ? 'Generating...' : 'Generate Message'}
              </Button>
            </div>
            <Textarea
              id="message"
              placeholder="Hi, I'm interested in your gaming PC..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={6}
            />
          </div>

          {/* Quick Presets */}
          <div>
            <Label>Quick Presets</Label>
            <div className="flex gap-2 mt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAmount(anchors.open)}
              >
                Aggressive ({formatCurrency(anchors.open)})
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAmount(anchors.target)}
              >
                Target ({formatCurrency(anchors.target)})
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAmount(anchors.walkaway)}
              >
                Conservative ({formatCurrency(anchors.walkaway)})
              </Button>
            </div>
          </div>

          {/* Risk Warning */}
          {riskScore > 50 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <div className="text-sm text-yellow-800">
                <strong>High Risk Listing:</strong> Consider starting with a lower offer
                due to elevated risk score ({riskScore}/100).
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving || amount === 0}>
            <DollarSign className="h-4 w-4 mr-2" />
            {isSaving ? 'Creating...' : 'Create Offer'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}