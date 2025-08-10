/**
 * Routes Page
 * Plan multi-stop pickup routes with optimization
 */

import React, { useState, useEffect } from 'react';
import { Map, Navigation, DollarSign, Clock, MapPin, Calendar } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import { db } from '@/lib/db';
import { createRouteIcs } from '@/lib/calendar';
import { planRoute, findNearestSafeSpot } from '@/lib/routes';
import { formatCurrency } from '@/core';
import type { Deal } from '@/core';

interface RouteStop {
  dealId: string;
  title: string;
  price: number;
  address: string;
  coord: { lat: number; lng: number };
  safeSpotId?: string;
  safeSpotName?: string;
  safeSpotAddress?: string;
}

export function Routes() {
  const { toast } = useToast();
  const [pendingDeals, setPendingDeals] = useState<Deal[]>([]);
  const [selectedDealIds, setSelectedDealIds] = useState<Set<string>>(new Set());
  const [route, setRoute] = useState<{
    stops: RouteStop[];
    totalMiles: number;
    totalTime: number;
    fuelCost: number;
    mapsUrl: string;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadPendingDeals();
  }, []);

  const loadPendingDeals = async () => {
    try {
      const deals = await db.deals
        .where('stage')
        .equals('pending_pickup')
        .toArray();
      setPendingDeals(deals as Deal[]);
    } catch (error) {
      console.error('Failed to load deals:', error);
    }
  };

  const toggleDealSelection = (dealId: string) => {
    const newSelection = new Set(selectedDealIds);
    if (newSelection.has(dealId)) {
      newSelection.delete(dealId);
    } else {
      newSelection.add(dealId);
    }
    setSelectedDealIds(newSelection);
  };

  const handlePlanRoute = async () => {
    if (selectedDealIds.size < 2) {
      toast({
        title: 'Select more deals',
        description: 'Please select at least 2 deals to plan a route',
        variant: 'destructive',
      });
      return;
    }

    if (selectedDealIds.size > 10) {
      toast({
        title: 'Too many stops',
        description: 'Please select 10 or fewer deals for optimal routing',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);
    try {
      const selectedDeals = pendingDeals.filter(d => selectedDealIds.has(d.id));
      const routeResult = await planRoute(selectedDeals);
      setRoute(routeResult);
    } catch (error) {
      toast({
        title: 'Route planning failed',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenInMaps = () => {
    if (route?.mapsUrl) {
      window.open(route.mapsUrl, '_blank');
    }
  };

  const handleCreateICS = async () => {
    if (!route) return;

    try {
      const dealIds = route.stops.map(s => s.dealId);
      await createRouteIcs(dealIds);
      toast({
        title: 'Calendar events created',
        description: 'Route calendar file has been downloaded',
      });
    } catch (error) {
      toast({
        title: 'Failed to create calendar',
        description: String(error),
        variant: 'destructive',
      });
    }
  };

  const handleCopyRoute = () => {
    if (!route) return;

    const routeText = route.stops
      .map((stop, idx) => `${idx + 1}. ${stop.title} - ${stop.safeSpotName || stop.address}`)
      .join('\n');

    navigator.clipboard.writeText(routeText);
    toast({
      title: 'Route copied',
      description: 'Route details copied to clipboard',
    });
  };

  const totalValue = Array.from(selectedDealIds).reduce((sum, id) => {
    const deal = pendingDeals.find(d => d.id === id);
    return sum + (deal?.listing.price || 0);
  }, 0);

  return (
    <div className="h-full overflow-auto">
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Map className="h-6 w-6" />
              Route Planning
            </h1>
            <p className="text-muted-foreground">
              Plan efficient pickup routes for pending deals
            </p>
          </div>
          {selectedDealIds.size > 0 && (
            <div className="text-right">
              <div className="text-sm text-muted-foreground">
                {selectedDealIds.size} stops selected
              </div>
              <div className="font-semibold">
                Total value: {formatCurrency(totalValue)}
              </div>
            </div>
          )}
        </div>

        {/* Deal Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Select Deals</CardTitle>
            <CardDescription>
              Choose 2-10 pending pickup deals to include in your route
            </CardDescription>
          </CardHeader>
          <CardContent>
            {pendingDeals.length === 0 ? (
              <p className="text-muted-foreground">No pending pickup deals</p>
            ) : (
              <div className="space-y-2">
                {pendingDeals.map(deal => (
                  <div
                    key={deal.id}
                    className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-muted/50"
                  >
                    <Checkbox
                      id={deal.id}
                      checked={selectedDealIds.has(deal.id)}
                      onCheckedChange={() => toggleDealSelection(deal.id)}
                    />
                    <Label
                      htmlFor={deal.id}
                      className="flex-1 cursor-pointer font-normal"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-medium">{deal.listing.title}</div>
                          <div className="text-sm text-muted-foreground">
                            {deal.listing.location?.city}, {deal.listing.location?.state} • 
                            {formatCurrency(deal.listing.price)}
                          </div>
                        </div>
                        <div className="text-sm text-right">
                          <div className="text-muted-foreground">
                            Est. profit: {formatCurrency(deal.metrics?.estimatedProfit || 0)}
                          </div>
                        </div>
                      </div>
                    </Label>
                  </div>
                ))}
              </div>
            )}

            {pendingDeals.length > 0 && (
              <div className="mt-4">
                <Button
                  onClick={handlePlanRoute}
                  disabled={selectedDealIds.size < 2 || isLoading}
                  className="w-full"
                >
                  <Navigation className="h-4 w-4 mr-2" />
                  {isLoading ? 'Planning route...' : 'Plan Route'}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Route Results */}
        {route && (
          <>
            <Card>
              <CardHeader>
                <CardTitle>Route Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div>
                    <div className="text-sm text-muted-foreground">Total Distance</div>
                    <div className="text-2xl font-bold">{route.totalMiles.toFixed(1)} mi</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Est. Time</div>
                    <div className="text-2xl font-bold">{Math.ceil(route.totalTime)} min</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Fuel Cost</div>
                    <div className="text-2xl font-bold">{formatCurrency(route.fuelCost)}</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Cost per Stop</div>
                    <div className="text-2xl font-bold">
                      {formatCurrency(route.fuelCost / route.stops.length)}
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button onClick={handleOpenInMaps}>
                    <Map className="h-4 w-4 mr-2" />
                    Open in Google Maps
                  </Button>
                  <Button variant="outline" onClick={handleCreateICS}>
                    <Calendar className="h-4 w-4 mr-2" />
                    Create Calendar Events
                  </Button>
                  <Button variant="outline" onClick={handleCopyRoute}>
                    Copy Route
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Route Details</CardTitle>
                <CardDescription>
                  Optimized order with safe meetup locations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {route.stops.map((stop, idx) => (
                    <div key={stop.dealId} className="flex gap-3">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-medium">
                        {idx + 1}
                      </div>
                      <div className="flex-1 space-y-1">
                        <div className="font-medium">{stop.title}</div>
                        <div className="text-sm text-muted-foreground">
                          {formatCurrency(stop.price)}
                        </div>
                        {stop.safeSpotName ? (
                          <div className="text-sm">
                            <MapPin className="h-3 w-3 inline mr-1" />
                            Meet at: {stop.safeSpotName}
                            <div className="text-xs text-muted-foreground ml-4">
                              {stop.safeSpotAddress}
                            </div>
                          </div>
                        ) : (
                          <div className="text-sm text-muted-foreground">
                            <MapPin className="h-3 w-3 inline mr-1" />
                            {stop.address}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                <Alert className="mt-4">
                  <AlertDescription>
                    <strong>Safety Tips:</strong>
                    <ul className="list-disc list-inside mt-1 text-sm">
                      <li>Always meet in public, well-lit areas</li>
                      <li>Bring a friend if possible</li>
                      <li>Test all equipment before payment</li>
                      <li>Use cash in envelopes labeled by deal</li>
                    </ul>
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}