/**
 * Popup App - Quick ROI Calculator & Recent Pipeline Items
 */

import React, { useState, useEffect } from 'react';
import { Calculator, Search, ExternalLink, Clock, TrendingUp, AlertCircle, ScanLine } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { sendMessage, MessageType } from '@/lib/messages';
import { getSettings } from '@/lib/settings';
import { db, getActiveDeals } from '@/lib/db';
import { FMVCalculator, ROICalculator, formatCurrency, formatPercentage } from '@/core';
import type { Settings, Listing, Deal } from '@/core';

interface QuickCalcInputs {
  askingPrice: number;
  distance: number;
  cpu: string;
  gpu: string;
  ram: number;
  storage: number;
  estimatedResale: number;
}

export function App() {
  const [activeTab, setActiveTab] = useState('calculator');
  const [settings, setSettings] = useState<Settings | null>(null);
  const [recentDeals, setRecentDeals] = useState<Deal[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  // Quick calc state
  const [calcInputs, setCalcInputs] = useState<QuickCalcInputs>({
    askingPrice: 0,
    distance: 10,
    cpu: 'i5-10400',
    gpu: 'rtx-3060',
    ram: 16,
    storage: 512,
    estimatedResale: 0,
  });
  
  const [calcResults, setCalcResults] = useState<{
    fmv: number;
    profit: number;
    roi: number;
    margin: number;
    recommendation: string;
  } | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [loadedSettings, deals] = await Promise.all([
        getSettings(),
        getActiveDeals(),
      ]);
      
      setSettings(loadedSettings);
      setRecentDeals(deals.slice(0, 5)); // Top 5 recent
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  const calculateROI = () => {
    if (!settings) return;
    
    // Create a mock listing for calculation
    const mockListing: Partial<Listing> = {
      price: calcInputs.askingPrice,
      title: 'Quick Calc PC',
      location: {
        city: 'Local',
        state: 'CO',
        zip: '',
        lat: 0,
        lng: 0,
        distance: calcInputs.distance,
      },
      components: {
        cpu: {
          brand: calcInputs.cpu.includes('i5') || calcInputs.cpu.includes('i7') ? 'Intel' : 'AMD',
          model: calcInputs.cpu,
          generation: 10,
          cores: 6,
          threads: 12,
          speed: 3.0,
        },
        gpu: {
          brand: 'NVIDIA',
          model: calcInputs.gpu,
          vram: 12,
        },
        ram: [{
          size: calcInputs.ram,
          type: 'DDR4',
          speed: 3200,
          modules: 2,
        }],
        storage: [{
          type: 'SSD',
          capacity: calcInputs.storage,
          brand: 'Unknown',
          model: 'Unknown',
        }],
      },
    };
    
    // Calculate FMV
    const fmvCalc = new FMVCalculator(settings);
    const fmvResult = fmvCalc.calculate(mockListing as Listing);
    
    // Calculate ROI
    const roiCalc = new ROICalculator(settings);
    const roiResult = roiCalc.calculate(mockListing as Listing, fmvResult);
    
    // Update results
    setCalcResults({
      fmv: fmvResult.total,
      profit: roiResult.netProfit,
      roi: roiResult.roi,
      margin: roiResult.profitMargin,
      recommendation: roiResult.dealScore >= 70 ? 'Good Deal' : 
                      roiResult.dealScore >= 50 ? 'Fair Deal' : 'Pass',
    });
    
    // Update estimated resale if not manually set
    if (calcInputs.estimatedResale === 0) {
      setCalcInputs(prev => ({
        ...prev,
        estimatedResale: Math.round(fmvResult.total * 1.1),
      }));
    }
  };

  const handleParseCurrentPage = async () => {
    setIsLoading(true);
    try {
      // Get active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      if (!tab.id) {
        throw new Error('No active tab');
      }
      
      // Check if it's a supported marketplace
      const supportedUrls = [
        'facebook.com/marketplace',
        'craigslist.org',
        'offerup.com',
      ];
      
      const isSupported = supportedUrls.some(url => tab.url?.includes(url));
      
      if (!isSupported) {
        alert('Please navigate to a Facebook Marketplace, Craigslist, or OfferUp listing first.');
        return;
      }
      
      // Send message to content script
      await chrome.tabs.sendMessage(tab.id, { action: 'parse' });
      
      // Close popup to see overlay
      window.close();
    } catch (error) {
      console.error('Parse error:', error);
      alert('Failed to parse page. Make sure you\'re on a supported marketplace listing.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBulkScan = async () => {
    setIsLoading(true);
    try {
      // Get active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      if (!tab.id) {
        throw new Error('No active tab');
      }
      
      // Check if it's a search results page
      const isSearchPage = tab.url?.includes('marketplace/search') ||
                          tab.url?.includes('marketplace/category') ||
                          (tab.url?.includes('craigslist.org') && tab.url?.includes('/search/'));
      
      if (!isSearchPage) {
        alert('Please navigate to a marketplace search results page first.');
        return;
      }
      
      // Send message to content script
      await chrome.tabs.sendMessage(tab.id, { action: 'scanSearch' });
      
      // Close popup to see results panel
      window.close();
    } catch (error) {
      console.error('Scan error:', error);
      alert('Failed to scan page. Make sure you\'re on a search results page.');
    } finally {
      setIsLoading(false);
    }
  };

  const openDashboard = async (page?: string) => {
    await sendMessage({
      type: MessageType.OPEN_DASHBOARD,
      page: page as any,
    });
    window.close();
  };

  const getStageColor = (stage: Deal['stage']) => {
    const colors: Record<Deal['stage'], string> = {
      discovered: 'bg-gray-500',
      contacted: 'bg-blue-500',
      negotiating: 'bg-yellow-500',
      pending_pickup: 'bg-purple-500',
      acquired: 'bg-green-500',
      refurbishing: 'bg-orange-500',
      listed: 'bg-indigo-500',
      sold: 'bg-green-700',
      cancelled: 'bg-red-500',
      completed: 'bg-gray-700',
    };
    return colors[stage] || 'bg-gray-500';
  };

  return (
    <div className="p-4 bg-background min-h-[500px]">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">Arbitrage Pro</h1>
        <Button size="sm" variant="ghost" onClick={() => openDashboard()}>
          <ExternalLink className="h-4 w-4 mr-1" />
          Dashboard
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-4">
        <Button 
          onClick={handleParseCurrentPage}
          disabled={isLoading}
          size="sm"
        >
          <Search className="h-4 w-4 mr-2" />
          Parse Page
        </Button>
        <Button 
          onClick={handleBulkScan}
          disabled={isLoading}
          size="sm"
          variant="outline"
        >
          <ScanLine className="h-4 w-4 mr-2" />
          Scan Results
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="calculator">
            <Calculator className="h-4 w-4 mr-1" />
            Quick ROI
          </TabsTrigger>
          <TabsTrigger value="recent">
            <Clock className="h-4 w-4 mr-1" />
            Recent
          </TabsTrigger>
        </TabsList>

        <TabsContent value="calculator" className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Quick ROI Calculator</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label htmlFor="price">Asking Price</Label>
                  <Input
                    id="price"
                    type="number"
                    value={calcInputs.askingPrice || ''}
                    onChange={(e) => setCalcInputs(prev => ({
                      ...prev,
                      askingPrice: Number(e.target.value),
                    }))}
                    placeholder="0"
                  />
                </div>
                <div>
                  <Label htmlFor="distance">Distance (mi)</Label>
                  <Input
                    id="distance"
                    type="number"
                    value={calcInputs.distance}
                    onChange={(e) => setCalcInputs(prev => ({
                      ...prev,
                      distance: Number(e.target.value),
                    }))}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label htmlFor="cpu">CPU</Label>
                  <Select
                    value={calcInputs.cpu}
                    onValueChange={(value) => setCalcInputs(prev => ({
                      ...prev,
                      cpu: value,
                    }))}
                  >
                    <SelectTrigger id="cpu">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="i5-10400">i5-10400</SelectItem>
                      <SelectItem value="i5-11400">i5-11400</SelectItem>
                      <SelectItem value="i5-12400">i5-12400</SelectItem>
                      <SelectItem value="i7-10700">i7-10700</SelectItem>
                      <SelectItem value="i7-11700">i7-11700</SelectItem>
                      <SelectItem value="ryzen-5-3600">Ryzen 5 3600</SelectItem>
                      <SelectItem value="ryzen-5-5600x">Ryzen 5 5600X</SelectItem>
                      <SelectItem value="ryzen-7-3700x">Ryzen 7 3700X</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="gpu">GPU</Label>
                  <Select
                    value={calcInputs.gpu}
                    onValueChange={(value) => setCalcInputs(prev => ({
                      ...prev,
                      gpu: value,
                    }))}
                  >
                    <SelectTrigger id="gpu">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="rtx-3060">RTX 3060</SelectItem>
                      <SelectItem value="rtx-3060ti">RTX 3060 Ti</SelectItem>
                      <SelectItem value="rtx-3070">RTX 3070</SelectItem>
                      <SelectItem value="rtx-3080">RTX 3080</SelectItem>
                      <SelectItem value="rtx-4060">RTX 4060</SelectItem>
                      <SelectItem value="rx-6600">RX 6600</SelectItem>
                      <SelectItem value="rx-6700xt">RX 6700 XT</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label htmlFor="ram">RAM (GB)</Label>
                  <Select
                    value={String(calcInputs.ram)}
                    onValueChange={(value) => setCalcInputs(prev => ({
                      ...prev,
                      ram: Number(value),
                    }))}
                  >
                    <SelectTrigger id="ram">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="8">8 GB</SelectItem>
                      <SelectItem value="16">16 GB</SelectItem>
                      <SelectItem value="32">32 GB</SelectItem>
                      <SelectItem value="64">64 GB</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="storage">Storage (GB)</Label>
                  <Select
                    value={String(calcInputs.storage)}
                    onValueChange={(value) => setCalcInputs(prev => ({
                      ...prev,
                      storage: Number(value),
                    }))}
                  >
                    <SelectTrigger id="storage">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="256">256 GB</SelectItem>
                      <SelectItem value="512">512 GB</SelectItem>
                      <SelectItem value="1000">1 TB</SelectItem>
                      <SelectItem value="2000">2 TB</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label htmlFor="resale">Est. Resale Price</Label>
                <Input
                  id="resale"
                  type="number"
                  value={calcInputs.estimatedResale || ''}
                  onChange={(e) => setCalcInputs(prev => ({
                    ...prev,
                    estimatedResale: Number(e.target.value),
                  }))}
                  placeholder="Leave blank for auto"
                />
              </div>

              <Button 
                className="w-full" 
                onClick={calculateROI}
                disabled={!settings || calcInputs.askingPrice === 0}
              >
                <Calculator className="h-4 w-4 mr-2" />
                Calculate ROI
              </Button>
            </CardContent>
          </Card>

          {calcResults && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center justify-between">
                  Results
                  <Badge 
                    variant={
                      calcResults.recommendation === 'Good Deal' ? 'default' :
                      calcResults.recommendation === 'Fair Deal' ? 'secondary' :
                      'destructive'
                    }
                  >
                    {calcResults.recommendation}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Fair Market Value</span>
                    <span className="font-medium">{formatCurrency(calcResults.fmv)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Est. Profit</span>
                    <span className="font-medium text-green-600">
                      {formatCurrency(calcResults.profit)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">ROI</span>
                    <span className="font-medium">{formatPercentage(calcResults.roi)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Margin</span>
                    <span className="font-medium">{formatPercentage(calcResults.margin)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="recent" className="space-y-3">
          {recentDeals.length === 0 ? (
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-muted-foreground">No active deals yet</p>
                <Button 
                  variant="link" 
                  onClick={() => openDashboard()}
                  className="mt-2"
                >
                  Go to Dashboard
                </Button>
              </CardContent>
            </Card>
          ) : (
            recentDeals.map((deal) => (
              <Card 
                key={deal.id}
                className="cursor-pointer hover:bg-accent/50 transition-colors"
                onClick={() => openDashboard('pipeline')}
              >
                <CardContent className="p-3">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-medium text-sm line-clamp-1">
                      {deal.listing.title}
                    </h3>
                    <Badge 
                      className={`${getStageColor(deal.stage)} text-white text-xs`}
                    >
                      {deal.stage.replace('_', ' ')}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{formatCurrency(deal.listing.price)}</span>
                    <span className="flex items-center gap-1">
                      <TrendingUp className="h-3 w-3" />
                      {formatPercentage(deal.analytics.roi)}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}