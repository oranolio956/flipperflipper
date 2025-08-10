/**
 * Saved Searches Page
 * Manage and run saved search monitors
 */

import React, { useState, useEffect } from 'react';
import { Search, Plus, Play, Edit2, Trash2, Clock, ExternalLink } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import {
  getSavedSearches,
  addSavedSearch,
  updateSavedSearch,
  deleteSavedSearch,
  runSavedSearch,
  type SavedSearch,
} from '@/lib/watches';
import { formatDistanceToNow } from 'date-fns';

export function SavedSearches() {
  const { toast } = useToast();
  const [searches, setSearches] = useState<SavedSearch[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [editingSearch, setEditingSearch] = useState<SavedSearch | null>(null);
  const [showDialog, setShowDialog] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    cadenceMin: 0,
    enabled: true,
    filters: {
      minPrice: undefined as number | undefined,
      maxPrice: undefined as number | undefined,
      distance: undefined as number | undefined,
      gpuTier: '',
      cpuTier: '',
      keywords: [] as string[],
    },
  });

  useEffect(() => {
    loadSearches();
  }, []);

  const loadSearches = async () => {
    setIsLoading(true);
    try {
      const data = await getSavedSearches();
      setSearches(data);
    } catch (error) {
      toast({
        title: 'Failed to load searches',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingSearch(null);
    setFormData({
      name: '',
      url: '',
      cadenceMin: 0,
      enabled: true,
      filters: {
        minPrice: undefined,
        maxPrice: undefined,
        distance: undefined,
        gpuTier: '',
        cpuTier: '',
        keywords: [],
      },
    });
    setShowDialog(true);
  };

  const handleEdit = (search: SavedSearch) => {
    setEditingSearch(search);
    setFormData({
      name: search.name,
      url: search.url,
      cadenceMin: search.cadenceMin,
      enabled: search.enabled,
      filters: search.filters,
    });
    setShowDialog(true);
  };

  const handleSave = async () => {
    try {
      if (editingSearch) {
        await updateSavedSearch(editingSearch.id, formData);
        toast({ title: 'Search updated' });
      } else {
        await addSavedSearch(formData);
        toast({ title: 'Search added' });
      }
      
      setShowDialog(false);
      await loadSearches();
    } catch (error) {
      toast({
        title: 'Failed to save search',
        description: String(error),
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this saved search?')) return;
    
    try {
      await deleteSavedSearch(id);
      toast({ title: 'Search deleted' });
      await loadSearches();
    } catch (error) {
      toast({
        title: 'Failed to delete search',
        description: String(error),
        variant: 'destructive',
      });
    }
  };

  const handleRun = async (id: string) => {
    try {
      await runSavedSearch(id);
      // Will navigate away
    } catch (error) {
      toast({
        title: 'Failed to run search',
        description: String(error),
        variant: 'destructive',
      });
    }
  };

  const handleToggleEnabled = async (search: SavedSearch) => {
    try {
      await updateSavedSearch(search.id, { enabled: !search.enabled });
      await loadSearches();
    } catch (error) {
      toast({
        title: 'Failed to update search',
        description: String(error),
        variant: 'destructive',
      });
    }
  };

  const getCadenceLabel = (minutes: number) => {
    if (minutes === 0) return 'Manual';
    if (minutes < 60) return `Every ${minutes}m`;
    if (minutes < 1440) return `Every ${Math.round(minutes / 60)}h`;
    return `Every ${Math.round(minutes / 1440)}d`;
  };

  return (
    <div className="h-full overflow-auto">
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Search className="h-6 w-6" />
              Saved Searches
            </h1>
            <p className="text-muted-foreground">
              Monitor search results and get notified of new deals
            </p>
          </div>
          
          <Button onClick={handleAdd}>
            <Plus className="h-4 w-4 mr-2" />
            Add Search
          </Button>
        </div>

        {/* Search List */}
        <div className="grid gap-4">
          {searches.length === 0 ? (
            <Card>
              <CardContent className="text-center py-12">
                <Search className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-muted-foreground mb-4">No saved searches yet</p>
                <Button onClick={handleAdd}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Your First Search
                </Button>
              </CardContent>
            </Card>
          ) : (
            searches.map(search => (
              <Card key={search.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg flex items-center gap-2">
                        {search.name}
                        {search.enabled ? (
                          <Badge variant="default">Active</Badge>
                        ) : (
                          <Badge variant="secondary">Paused</Badge>
                        )}
                      </CardTitle>
                      <CardDescription>
                        <a 
                          href={search.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-xs hover:underline flex items-center gap-1"
                        >
                          {search.url.substring(0, 60)}...
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </CardDescription>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={search.enabled}
                        onCheckedChange={() => handleToggleEnabled(search)}
                      />
                    </div>
                  </div>
                </CardHeader>
                
                <CardContent className="space-y-4">
                  <div className="flex flex-wrap gap-2">
                    {search.filters.minPrice && (
                      <Badge variant="outline">
                        Min: ${search.filters.minPrice}
                      </Badge>
                    )}
                    {search.filters.maxPrice && (
                      <Badge variant="outline">
                        Max: ${search.filters.maxPrice}
                      </Badge>
                    )}
                    {search.filters.distance && (
                      <Badge variant="outline">
                        {search.filters.distance}mi
                      </Badge>
                    )}
                    {search.filters.gpuTier && (
                      <Badge variant="outline">
                        GPU: {search.filters.gpuTier}
                      </Badge>
                    )}
                    {search.filters.cpuTier && (
                      <Badge variant="outline">
                        CPU: {search.filters.cpuTier}
                      </Badge>
                    )}
                    {search.filters.keywords?.map(kw => (
                      <Badge key={kw} variant="outline">
                        {kw}
                      </Badge>
                    ))}
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4" />
                        <span>
                          {getCadenceLabel(search.cadenceMin)}
                          {search.lastRunAt && (
                            <> • Last run {formatDistanceToNow(new Date(search.lastRunAt))} ago</>
                          )}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="default"
                        onClick={() => handleRun(search.id)}
                      >
                        <Play className="h-3 w-3 mr-1" />
                        Run Now
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleEdit(search)}
                      >
                        <Edit2 className="h-3 w-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDelete(search.id)}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Add/Edit Dialog */}
        <Dialog open={showDialog} onOpenChange={setShowDialog}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>
                {editingSearch ? 'Edit Search' : 'Add Saved Search'}
              </DialogTitle>
              <DialogDescription>
                Create a search monitor to track new listings
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Gaming PCs under $800"
                />
              </div>
              
              <div>
                <Label htmlFor="url">Search URL</Label>
                <Input
                  id="url"
                  value={formData.url}
                  onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                  placeholder="https://www.facebook.com/marketplace/search/?query=gaming%20pc"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Copy the full URL from your marketplace search
                </p>
              </div>
              
              <div>
                <Label htmlFor="cadence">Check Frequency</Label>
                <Select
                  value={String(formData.cadenceMin)}
                  onValueChange={(value) => setFormData({ 
                    ...formData, 
                    cadenceMin: parseInt(value) 
                  })}
                >
                  <SelectTrigger id="cadence">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">Manual Only</SelectItem>
                    <SelectItem value="60">Every Hour</SelectItem>
                    <SelectItem value="120">Every 2 Hours</SelectItem>
                    <SelectItem value="240">Every 4 Hours</SelectItem>
                    <SelectItem value="720">Every 12 Hours</SelectItem>
                    <SelectItem value="1440">Daily</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label>Filters (Optional)</Label>
                <div className="grid grid-cols-2 gap-3 mt-2">
                  <div>
                    <Label htmlFor="minPrice" className="text-xs">Min Price</Label>
                    <Input
                      id="minPrice"
                      type="number"
                      value={formData.filters.minPrice || ''}
                      onChange={(e) => setFormData({
                        ...formData,
                        filters: {
                          ...formData.filters,
                          minPrice: e.target.value ? parseInt(e.target.value) : undefined,
                        },
                      })}
                      placeholder="0"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="maxPrice" className="text-xs">Max Price</Label>
                    <Input
                      id="maxPrice"
                      type="number"
                      value={formData.filters.maxPrice || ''}
                      onChange={(e) => setFormData({
                        ...formData,
                        filters: {
                          ...formData.filters,
                          maxPrice: e.target.value ? parseInt(e.target.value) : undefined,
                        },
                      })}
                      placeholder="1000"
                    />
                  </div>
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleSave}>
                {editingSearch ? 'Update' : 'Create'} Search
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}