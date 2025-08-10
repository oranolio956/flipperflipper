import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Copy, 
  Edit, 
  Trash2, 
  TrendingUp, 
  TrendingDown,
  Target,
  AlertCircle,
  ChevronRight,
  MessageSquare,
  Zap,
  Search,
  Download,
  Upload
} from 'lucide-react';
import { 
  negotiationScriptManager, 
  NegotiationScript, 
  NegotiationContext,
  NegotiationRecommendation 
} from '@arbitrage/core/negotiation/negotiationScriptManager';
import { Listing } from '@arbitrage/core/types';

interface ScriptPreview {
  script: NegotiationScript;
  preview: string;
}

export const NegotiationScriptsUI: React.FC = () => {
  const [scripts, setScripts] = useState<NegotiationScript[]>([]);
  const [selectedScript, setSelectedScript] = useState<NegotiationScript | null>(null);
  const [recommendation, setRecommendation] = useState<NegotiationRecommendation | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [editingScript, setEditingScript] = useState<NegotiationScript | null>(null);
  
  // Mock context for testing
  const [mockContext, setMockContext] = useState<NegotiationContext>({
    listing: {
      id: 'test',
      externalId: '123',
      url: 'https://example.com',
      platform: 'facebook',
      title: 'Gaming PC - RTX 3070, i7-10700K',
      description: 'Great gaming PC',
      price: 1200,
      location: { city: 'Seattle', state: 'WA', zipCode: '98101' },
      seller: { id: '1', name: 'John Doe', responseRate: 0.9, memberSince: new Date() },
      images: [],
      condition: 'used',
      category: 'gaming-pc',
      subcategory: 'desktop',
      attributes: {},
      postedAt: new Date(),
      lastUpdated: new Date(),
      status: 'active',
      viewCount: 100,
      savedCount: 5,
      components: {
        cpu: { model: 'Intel i7-10700K', brand: 'Intel', specs: {} },
        gpu: { model: 'NVIDIA RTX 3070', brand: 'NVIDIA', vram: 8, vramType: 'GDDR6' },
        ram: [{ capacity: 16, speed: 3200, type: 'DDR4' }],
        storage: [{ capacity: 512, type: 'NVMe SSD', model: 'Samsung 970 EVO' }]
      }
    } as Listing,
    targetPrice: 900,
    marketAverage: 950,
    sellerBehavior: 'unknown'
  });

  useEffect(() => {
    loadScripts();
  }, []);

  const loadScripts = () => {
    const allScripts = negotiationScriptManager.getAllScripts();
    setScripts(allScripts);
  };

  const getRecommendation = () => {
    const rec = negotiationScriptManager.getRecommendation(mockContext);
    setRecommendation(rec);
    setSelectedScript(rec.script);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    chrome.notifications.create({
      type: 'basic',
      iconUrl: chrome.runtime.getURL('icons/icon-48.png'),
      title: 'Copied!',
      message: 'Script copied to clipboard'
    });
  };

  const renderScript = (script: NegotiationScript, variables?: Record<string, any>): string => {
    let rendered = script.script;
    const vars = variables || {};

    // Fill in variables
    script.variables.forEach(v => {
      const value = vars[v.name] || v.defaultValue || `[${v.description}]`;
      const regex = new RegExp(`{{${v.name}}}`, 'g');
      rendered = rendered.replace(regex, value);
    });

    return rendered;
  };

  const recordUsage = async (scriptId: string, success: boolean) => {
    await negotiationScriptManager.recordUsage(scriptId, success);
    loadScripts(); // Reload to show updated stats
  };

  const deleteScript = async (scriptId: string) => {
    if (confirm('Are you sure you want to delete this script?')) {
      await negotiationScriptManager.deleteScript(scriptId);
      loadScripts();
      if (selectedScript?.id === scriptId) {
        setSelectedScript(null);
      }
    }
  };

  const exportScripts = () => {
    const data = negotiationScriptManager.exportScripts();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'negotiation-scripts.json';
    link.click();
  };

  const importScripts = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      await negotiationScriptManager.importScripts(text);
      loadScripts();
    } catch (error) {
      alert('Failed to import scripts: ' + error);
    }
  };

  const filteredScripts = scripts.filter(script => {
    const matchesSearch = !searchTerm || 
      script.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      script.scenario.toLowerCase().includes(searchTerm.toLowerCase()) ||
      script.script.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCategory = selectedCategory === 'all' || script.category === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Negotiation Scripts</h1>
          <p className="text-muted-foreground">Battle-tested scripts for every negotiation scenario</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={exportScripts}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Label htmlFor="import" className="cursor-pointer">
            <Button variant="outline" as="span">
              <Upload className="h-4 w-4 mr-2" />
              Import
            </Button>
            <Input
              id="import"
              type="file"
              accept=".json"
              className="hidden"
              onChange={importScripts}
            />
          </Label>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Get AI Recommendation</CardTitle>
          <CardDescription>
            Get the best negotiation script based on your current context
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <Label>Target Price</Label>
              <Input
                type="number"
                value={mockContext.targetPrice}
                onChange={(e) => setMockContext({
                  ...mockContext,
                  targetPrice: parseInt(e.target.value)
                })}
              />
            </div>
            <div>
              <Label>Seller Behavior</Label>
              <Select 
                value={mockContext.sellerBehavior}
                onValueChange={(value: any) => setMockContext({
                  ...mockContext,
                  sellerBehavior: value
                })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="unknown">Unknown</SelectItem>
                  <SelectItem value="flexible">Flexible</SelectItem>
                  <SelectItem value="firm">Firm</SelectItem>
                  <SelectItem value="desperate">Desperate</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <Button onClick={getRecommendation} className="w-full">
            <Zap className="h-4 w-4 mr-2" />
            Get Recommendation
          </Button>

          {recommendation && (
            <Alert className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <strong>Recommended:</strong> {recommendation.script.name}
                <br />
                <strong>Confidence:</strong> {(recommendation.confidence * 100).toFixed(0)}%
                <br />
                <strong>Reasoning:</strong>
                <ul className="list-disc list-inside mt-2">
                  {recommendation.reasoning.map((r, i) => (
                    <li key={i} className="text-sm">{r}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      <div className="flex gap-4 items-center">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              placeholder="Search scripts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <Select value={selectedCategory} onValueChange={setSelectedCategory}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            <SelectItem value="opening">Opening</SelectItem>
            <SelectItem value="counter">Counter Offer</SelectItem>
            <SelectItem value="closing">Closing</SelectItem>
            <SelectItem value="objection">Objection Handling</SelectItem>
            <SelectItem value="walkaway">Walk Away</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Script Library</h2>
          <ScrollArea className="h-[600px]">
            <div className="space-y-3">
              {filteredScripts.map(script => (
                <Card 
                  key={script.id}
                  className={`cursor-pointer transition-colors ${
                    selectedScript?.id === script.id ? 'border-primary' : ''
                  }`}
                  onClick={() => setSelectedScript(script)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-base">{script.name}</CardTitle>
                        <CardDescription className="text-sm mt-1">
                          {script.scenario}
                        </CardDescription>
                      </div>
                      <Badge variant={
                        script.category === 'opening' ? 'default' :
                        script.category === 'counter' ? 'secondary' :
                        script.category === 'closing' ? 'outline' :
                        'destructive'
                      }>
                        {script.category}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-4 text-sm">
                      <div className="flex items-center gap-1">
                        <Target className="h-3 w-3" />
                        <span>{script.targetDiscount}% discount</span>
                      </div>
                      {script.successRate !== undefined && (
                        <div className="flex items-center gap-1">
                          {script.successRate > 0.7 ? (
                            <TrendingUp className="h-3 w-3 text-green-500" />
                          ) : (
                            <TrendingDown className="h-3 w-3 text-red-500" />
                          )}
                          <span>{(script.successRate * 100).toFixed(0)}% success</span>
                        </div>
                      )}
                      <div className="flex items-center gap-1">
                        <MessageSquare className="h-3 w-3" />
                        <span>{script.usageCount} uses</span>
                      </div>
                    </div>
                    
                    <div className="flex gap-1 mt-2 flex-wrap">
                      {script.tags.map(tag => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </div>

        <div className="space-y-4">
          {selectedScript ? (
            <>
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold">Script Details</h2>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => copyToClipboard(renderScript(selectedScript, recommendation?.variables))}
                  >
                    <Copy className="h-4 w-4 mr-2" />
                    Copy
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => deleteScript(selectedScript.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>{selectedScript.name}</CardTitle>
                  <CardDescription>{selectedScript.scenario}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label>Script Preview</Label>
                    <Card className="mt-2">
                      <CardContent className="p-4">
                        <pre className="whitespace-pre-wrap text-sm font-mono">
                          {renderScript(selectedScript, recommendation?.variables)}
                        </pre>
                      </CardContent>
                    </Card>
                  </div>

                  <div>
                    <Label>Variables</Label>
                    <div className="space-y-2 mt-2">
                      {selectedScript.variables.map(variable => (
                        <div key={variable.name} className="flex items-center justify-between text-sm">
                          <span className="font-mono">{{'{{'}{variable.name}{'}}'}}}</span>
                          <span className="text-muted-foreground">{variable.description}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <Label>Negotiation Tactics</Label>
                    <div className="space-y-3 mt-2">
                      {selectedScript.tactics.map((tactic, i) => (
                        <Card key={i}>
                          <CardContent className="p-3">
                            <div className="flex justify-between items-start mb-2">
                              <h4 className="font-medium">{tactic.name}</h4>
                              <Badge variant={
                                tactic.riskLevel === 'low' ? 'default' :
                                tactic.riskLevel === 'medium' ? 'secondary' :
                                'destructive'
                              }>
                                {tactic.riskLevel} risk
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground mb-1">
                              {tactic.description}
                            </p>
                            <p className="text-sm">
                              <strong>When to use:</strong> {tactic.whenToUse}
                            </p>
                            <p className="text-sm">
                              <strong>Example:</strong> {tactic.example}
                            </p>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-2 pt-4">
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => recordUsage(selectedScript.id, false)}
                    >
                      Mark as Failed
                    </Button>
                    <Button
                      className="flex-1"
                      onClick={() => recordUsage(selectedScript.id, true)}
                    >
                      Mark as Success
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="p-12 text-center">
                <MessageSquare className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">
                  Select a script to view details
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};