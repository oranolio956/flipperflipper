/**
 * Listing Detail Page
 * View full deal details with actions
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Calendar, 
  Clock, 
  DollarSign, 
  AlertCircle, 
  MessageSquare,
  Download,
  MapPin,
  Camera
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import { db } from '@/lib/db';
import { createPickupIcs, createFollowUpIcs } from '@/lib/calendar';
import { formatCurrency, formatPercentage, formatDaysAgo } from '@/core';
import type { Deal } from '@/core';

export function ListingDetail() {
  const { dealId } = useParams<{ dealId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [deal, setDeal] = useState<Deal | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadDeal();
  }, [dealId]);

  const loadDeal = async () => {
    if (!dealId) return;
    
    try {
      const dbDeal = await db.deals.where('id').equals(dealId).first();
      if (dbDeal) {
        setDeal(dbDeal as Deal);
      }
    } catch (error) {
      console.error('Failed to load deal:', error);
      toast({
        title: 'Error loading deal',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddPickupToCalendar = async () => {
    if (!deal) return;
    
    try {
      await createPickupIcs(deal.id);
      toast({
        title: 'Calendar event created',
        description: 'Pickup event has been downloaded',
      });
    } catch (error) {
      toast({
        title: 'Failed to create event',
        description: String(error),
        variant: 'destructive',
      });
    }
  };

  const handleAddFollowUpToCalendar = async () => {
    if (!deal) return;
    
    try {
      await createFollowUpIcs(deal.id);
      toast({
        title: 'Reminder created',
        description: 'Follow-up reminder has been downloaded',
      });
    } catch (error) {
      toast({
        title: 'Failed to create reminder',
        description: String(error),
        variant: 'destructive',
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!deal) {
    return (
      <div className="p-6">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Deal not found</AlertDescription>
        </Alert>
      </div>
    );
  }

  const { listing } = deal;
  const stageColors: Record<Deal['stage'], string> = {
    sourcing: 'bg-slate-100',
    contacted: 'bg-blue-100',
    negotiating: 'bg-yellow-100',
    pending_pickup: 'bg-orange-100',
    acquired: 'bg-green-100',
    refurbishing: 'bg-purple-100',
    listed: 'bg-indigo-100',
    sold: 'bg-emerald-100',
  };

  return (
    <div className="h-full overflow-auto">
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/pipeline')}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold">{listing.title}</h1>
              <p className="text-muted-foreground">
                Listed {formatDaysAgo(listing.metadata.createdAt)}
              </p>
            </div>
          </div>
          <Badge className={stageColors[deal.stage]}>
            {deal.stage.replace('_', ' ')}
          </Badge>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Asking Price</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(listing.price)}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Est. Profit</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatCurrency(deal.metrics?.estimatedProfit || 0)}
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">ROI</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatPercentage(deal.metrics?.roi || 0)}
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Deal Score</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {deal.metrics?.dealScore || 0}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              <Button onClick={handleAddPickupToCalendar}>
                <Calendar className="h-4 w-4 mr-2" />
                Add Pickup to Calendar
              </Button>
              
              <Button variant="outline" onClick={handleAddFollowUpToCalendar}>
                <Clock className="h-4 w-4 mr-2" />
                Add Follow-Up Reminder
              </Button>
              
              <Button
                variant="outline"
                onClick={() => window.open(listing.url, '_blank')}
              >
                <MessageSquare className="h-4 w-4 mr-2" />
                View Listing
              </Button>
              
              {listing.location && (
                <Button
                  variant="outline"
                  onClick={() => {
                    const query = encodeURIComponent(
                      listing.location?.address || 
                      `${listing.location.city}, ${listing.location.state}`
                    );
                    window.open(`https://maps.google.com/?q=${query}`, '_blank');
                  }}
                >
                  <MapPin className="h-4 w-4 mr-2" />
                  View on Map
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Tabs */}
        <Tabs defaultValue="details" className="space-y-4">
          <TabsList>
            <TabsTrigger value="details">Details</TabsTrigger>
            <TabsTrigger value="components">Components</TabsTrigger>
            <TabsTrigger value="risk">Risk Analysis</TabsTrigger>
            <TabsTrigger value="activity">Activity</TabsTrigger>
          </TabsList>

          <TabsContent value="details" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Listing Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-medium mb-1">Description</h4>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                    {listing.description}
                  </p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium mb-1">Location</h4>
                    <p className="text-sm text-muted-foreground">
                      {listing.location?.city}, {listing.location?.state} {listing.location?.zipCode}
                    </p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium mb-1">Seller</h4>
                    <p className="text-sm text-muted-foreground">
                      {listing.seller?.name || 'Unknown'}
                      {listing.seller?.rating && ` (${listing.seller.rating}★)`}
                    </p>
                  </div>
                </div>
                
                {listing.images.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Images</h4>
                    <div className="grid grid-cols-4 gap-2">
                      {listing.images.slice(0, 8).map((img, idx) => (
                        <div
                          key={idx}
                          className="aspect-square bg-muted rounded-lg overflow-hidden cursor-pointer hover:opacity-90"
                          onClick={() => window.open(img, '_blank')}
                        >
                          <img
                            src={img}
                            alt={`Image ${idx + 1}`}
                            className="w-full h-full object-cover"
                          />
                        </div>
                      ))}
                    </div>
                    {listing.images.length > 8 && (
                      <p className="text-sm text-muted-foreground mt-2">
                        +{listing.images.length - 8} more images
                      </p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="components" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Detected Components</CardTitle>
              </CardHeader>
              <CardContent>
                {Object.entries(listing.components).length > 0 ? (
                  <div className="space-y-3">
                    {listing.components.cpu && (
                      <div className="flex justify-between items-center p-3 border rounded-lg">
                        <div>
                          <div className="font-medium">CPU</div>
                          <div className="text-sm text-muted-foreground">
                            {listing.components.cpu.model}
                          </div>
                        </div>
                        <Badge>{listing.components.cpu.condition}</Badge>
                      </div>
                    )}
                    
                    {listing.components.gpu && (
                      <div className="flex justify-between items-center p-3 border rounded-lg">
                        <div>
                          <div className="font-medium">GPU</div>
                          <div className="text-sm text-muted-foreground">
                            {listing.components.gpu.model}
                            {listing.components.gpu.vram && ` (${listing.components.gpu.vram}GB)`}
                          </div>
                        </div>
                        <Badge>{listing.components.gpu.condition}</Badge>
                      </div>
                    )}
                    
                    {listing.components.ram && listing.components.ram.length > 0 && (
                      <div className="flex justify-between items-center p-3 border rounded-lg">
                        <div>
                          <div className="font-medium">RAM</div>
                          <div className="text-sm text-muted-foreground">
                            {listing.components.ram.map(r => 
                              `${r.capacity}GB ${r.type} ${r.speed || ''}`
                            ).join(', ')}
                          </div>
                        </div>
                        <Badge>{listing.components.ram[0].condition}</Badge>
                      </div>
                    )}
                    
                    {listing.components.storage && listing.components.storage.length > 0 && (
                      <div className="flex justify-between items-center p-3 border rounded-lg">
                        <div>
                          <div className="font-medium">Storage</div>
                          <div className="text-sm text-muted-foreground">
                            {listing.components.storage.map(s => 
                              `${s.capacity}GB ${s.type}`
                            ).join(', ')}
                          </div>
                        </div>
                        <Badge>{listing.components.storage[0].condition}</Badge>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-muted-foreground">No components detected</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="risk" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Risk Assessment</CardTitle>
              </CardHeader>
              <CardContent>
                {deal.riskAssessment ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Overall Risk Score</span>
                      <Badge
                        variant={
                          deal.riskAssessment.overallScore > 70 ? 'destructive' :
                          deal.riskAssessment.overallScore > 40 ? 'secondary' :
                          'default'
                        }
                      >
                        {deal.riskAssessment.overallScore}/100
                      </Badge>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2">Risk Flags</h4>
                      <div className="space-y-2">
                        {deal.riskAssessment.flags.map((flag, idx) => (
                          <Alert key={idx} variant={flag.severity === 'high' ? 'destructive' : 'default'}>
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription>
                              <span className="font-medium">{flag.type}:</span> {flag.description}
                            </AlertDescription>
                          </Alert>
                        ))}
                      </div>
                    </div>
                    
                    {deal.riskAssessment.suggestedQuestions.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2">Suggested Questions</h4>
                        <ul className="list-disc list-inside space-y-1">
                          {deal.riskAssessment.suggestedQuestions.map((q, idx) => (
                            <li key={idx} className="text-sm text-muted-foreground">{q}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-muted-foreground">No risk assessment available</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="activity" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Activity Timeline</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {deal.history.map((event, idx) => (
                    <div key={idx} className="flex gap-3">
                      <div className="w-2 h-2 mt-2 rounded-full bg-primary flex-shrink-0" />
                      <div className="flex-1">
                        <div className="text-sm font-medium">{event.action}</div>
                        <div className="text-xs text-muted-foreground">
                          {new Date(event.timestamp).toLocaleString()}
                          {event.reason && ` - ${event.reason}`}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}