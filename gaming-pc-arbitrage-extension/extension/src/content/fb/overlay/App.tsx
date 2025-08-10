/**
 * Overlay App - Floating ROI/Risk Widget
 * Shows analysis results on Facebook Marketplace listings
 */

import React, { useState, useEffect } from 'react';
import { X, DollarSign, AlertCircle, Plus, MessageSquare, BarChart3, ExternalLink, Scan } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Progress } from '@/components/ui/progress';
import { formatCurrency, formatPercentage } from '@/core';
import { sendMessage, MessageType } from '@/lib/messages';
import { extractSpecsFromImages, setOCRProgressCallback } from '@/lib/ocr';
import type { Listing, FMVResult, ROIResult, RiskAssessment } from '@/core';

interface OverlayData {
  listing?: Listing;
  fmv?: FMVResult;
  roi?: ROIResult;
  risk?: RiskAssessment;
}

export function OverlayApp() {
  const [data, setData] = useState<OverlayData>({});
  const [isMinimized, setIsMinimized] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [ocrProgress, setOcrProgress] = useState(0);
  const [ocrSpecs, setOcrSpecs] = useState<{
    cpu?: string;
    gpu?: string;
    ram?: string;
    storage?: string;
    psu?: string;
  } | null>(null);

  useEffect(() => {
    // Listen for updates from content script
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'ARBITRAGE_UPDATE') {
        setData(event.data.data);
        setIsLoading(false);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  const handleAddToPipeline = async () => {
    if (!data.listing) return;
    
    setIsLoading(true);
    try {
      const response = await sendMessage({
        type: MessageType.SAVE_LISTING,
        listing: data.listing,
        autoCreateDeal: true,
      });
      
      if (response.success) {
        setIsSaved(true);
        // Show success notification
        setTimeout(() => setIsSaved(false), 3000);
      }
    } catch (error) {
      console.error('Save error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDraftMessage = async () => {
    if (!data.listing || !isSaved) {
      // Save first if not already saved
      await handleAddToPipeline();
    }
    
    // Open messenger with draft
    const response = await sendMessage({
      type: MessageType.GENERATE_DRAFT,
      dealId: data.listing?.id || '',
    });
    
    if (response.success && response.draft) {
      // Copy to clipboard
      await navigator.clipboard.writeText(response.draft);
      
      // Open messenger (FB specific)
      const sellerLink = document.querySelector('a[href*="/profile/"]');
      if (sellerLink instanceof HTMLAnchorElement) {
        window.open(sellerLink.href + '?message=1', '_blank');
      }
    }
  };

  const handleOpenDashboard = async () => {
    await sendMessage({
      type: MessageType.OPEN_DASHBOARD,
      dealId: data.listing?.id,
    });
  };

  const handleScanImages = async () => {
    if (!data.listing?.images || data.listing.images.length === 0) {
      alert('No images to scan');
      return;
    }

    setIsScanning(true);
    setOcrProgress(0);
    
    try {
      // Set up progress callback
      setOCRProgressCallback((progress) => {
        setOcrProgress(Math.round(progress * 100));
      });

      // Extract specs from images
      const specs = await extractSpecsFromImages(data.listing.images);
      setOcrSpecs(specs);

      // Update listing with OCR results
      if (specs.cpu || specs.gpu || specs.ram || specs.storage || specs.psu) {
        // Send update message to background
        await sendMessage({
          type: MessageType.SAVE_LISTING,
          listing: {
            ...data.listing,
            metadata: {
              ...data.listing.metadata,
              ocrExtracted: true,
              ocrSpecs: specs,
            },
          },
        });
      }
    } catch (error) {
      console.error('OCR scan failed:', error);
      alert('Failed to scan images. Please try again.');
    } finally {
      setIsScanning(false);
      setOcrProgress(0);
    }
  };

  if (!data.listing) return null;

  const { listing, fmv, roi, risk } = data;
  const dealScore = roi?.dealScore || 0;
  const riskScore = risk?.overallScore || 0;

  // Color coding based on scores
  const getDealScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRiskBadgeVariant = (score: number): "default" | "secondary" | "destructive" | "outline" => {
    if (score <= 3) return 'secondary';
    if (score <= 6) return 'default';
    return 'destructive';
  };

  if (isMinimized) {
    return (
      <div className="fixed bottom-4 right-4 z-[9999]">
        <Card className="shadow-lg cursor-pointer" onClick={() => setIsMinimized(false)}>
          <CardContent className="p-3 flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            <span className="font-semibold">
              {roi ? formatPercentage(roi.roi) : '...'} ROI
            </span>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="fixed bottom-4 right-4 z-[9999] w-96">
        <Card className="shadow-xl border-2">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                PC Arbitrage Analysis
              </CardTitle>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsMinimized(true)}
                className="h-8 w-8"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          
          <CardContent className="space-y-4">
            {/* Component Summary */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium">Detected Components:</div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleScanImages}
                  disabled={isScanning || !data.listing?.images?.length}
                >
                  <Scan className="h-3 w-3 mr-1" />
                  {isScanning ? 'Scanning...' : 'Scan Photos'}
                </Button>
              </div>
              
              {isScanning && (
                <div className="space-y-1">
                  <div className="text-xs text-muted-foreground">
                    Extracting text from images...
                  </div>
                  <Progress value={ocrProgress} className="h-1" />
                </div>
              )}
              
              {ocrSpecs && (
                <div className="p-2 bg-muted rounded-md space-y-1">
                  <div className="text-xs font-medium">OCR Results:</div>
                  {ocrSpecs.cpu && <div className="text-xs">CPU: {ocrSpecs.cpu}</div>}
                  {ocrSpecs.gpu && <div className="text-xs">GPU: {ocrSpecs.gpu}</div>}
                  {ocrSpecs.ram && <div className="text-xs">RAM: {ocrSpecs.ram}</div>}
                  {ocrSpecs.storage && <div className="text-xs">Storage: {ocrSpecs.storage}</div>}
                  {ocrSpecs.psu && <div className="text-xs">PSU: {ocrSpecs.psu}</div>}
                </div>
              )}
              
              <div className="flex flex-wrap gap-1">
                {listing.components.cpu && (
                  <Badge variant="outline" className="text-xs">
                    {listing.components.cpu.model}
                  </Badge>
                )}
                {listing.components.gpu && (
                  <Badge variant="outline" className="text-xs">
                    {listing.components.gpu.model}
                  </Badge>
                )}
                {listing.components.ram?.[0] && (
                  <Badge variant="outline" className="text-xs">
                    {listing.components.ram.reduce((sum, r) => sum + r.size, 0)}GB RAM
                  </Badge>
                )}
                {listing.components.storage?.[0] && (
                  <Badge variant="outline" className="text-xs">
                    {listing.components.storage[0].capacity}GB {listing.components.storage[0].type}
                  </Badge>
                )}
              </div>
            </div>

            {/* Valuation */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground">Fair Market Value</div>
                <div className="text-lg font-semibold">
                  {fmv ? formatCurrency(fmv.total) : '...'}
                </div>
                {fmv && (
                  <div className="text-xs text-muted-foreground">
                    {formatPercentage(fmv.confidence * 100)} confidence
                  </div>
                )}
              </div>
              
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground">Asking Price</div>
                <div className="text-lg font-semibold">
                  {formatCurrency(listing.price)}
                </div>
                {fmv && (
                  <div className="text-xs">
                    {listing.price < fmv.total * 0.8 ? (
                      <span className="text-green-600">Good deal</span>
                    ) : listing.price > fmv.total * 1.2 ? (
                      <span className="text-red-600">Overpriced</span>
                    ) : (
                      <span className="text-yellow-600">Fair price</span>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* ROI Metrics */}
            {roi && (
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Target Buy</span>
                  <span className="font-semibold">{formatCurrency(roi.recommendedOffer)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Walk Away</span>
                  <span className="font-semibold">{formatCurrency(roi.walkAwayPrice)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Est. Profit</span>
                  <span className="font-semibold text-green-600">
                    {formatCurrency(roi.netProfit)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">ROI</span>
                  <span className={`font-semibold ${getDealScoreColor(dealScore)}`}>
                    {formatPercentage(roi.roi)}
                  </span>
                </div>
              </div>
            )}

            {/* Deal Score */}
            {roi && (
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Deal Score</span>
                  <span className={`font-semibold ${getDealScoreColor(dealScore)}`}>
                    {Math.round(dealScore)}/100
                  </span>
                </div>
                <Progress value={dealScore} className="h-2" />
              </div>
            )}

            {/* Risk Assessment */}
            {risk && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium flex items-center gap-1">
                    <AlertCircle className="h-4 w-4" />
                    Risk Assessment
                  </span>
                  <Badge variant={getRiskBadgeVariant(riskScore)}>
                    Score: {riskScore}/10
                  </Badge>
                </div>
                {risk.flags.slice(0, 3).map((flag, i) => (
                  <div key={i} className="text-xs">
                    <Badge variant="outline" className="mb-1">
                      {flag.severity}
                    </Badge>
                    <div className="text-muted-foreground">{flag.description}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Actions */}
            <div className="grid grid-cols-2 gap-2 pt-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button 
                    onClick={handleAddToPipeline}
                    disabled={isLoading || isSaved}
                    className="w-full"
                    variant={isSaved ? "secondary" : "default"}
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    {isSaved ? 'Saved!' : 'Add to Pipeline'}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Save this listing and create a deal</p>
                </TooltipContent>
              </Tooltip>
              
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button 
                    onClick={handleDraftMessage}
                    disabled={isLoading}
                    variant="outline"
                    className="w-full"
                  >
                    <MessageSquare className="h-4 w-4 mr-1" />
                    Draft Message
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Generate negotiation message</p>
                </TooltipContent>
              </Tooltip>
            </div>
            
            <Button 
              onClick={handleOpenDashboard}
              variant="ghost"
              className="w-full"
            >
              <ExternalLink className="h-4 w-4 mr-1" />
              Open Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    </TooltipProvider>
  );
}