/**
 * Custom Pricing Formula UI
 * Provides interface for creating, editing, testing, and managing custom pricing formulas
 */

import React, { useState, useEffect } from 'react';
import { customPricingEngine, PricingFormula, EvaluationResult, TestCase } from '@arbitrage/core';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Alert, AlertDescription } from '../components/ui/alert';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
  Calculator,
  Code,
  Play,
  Plus,
  Save,
  Trash2,
  AlertCircle,
  CheckCircle,
  Copy,
  Download,
  Upload,
  FlaskConical,
  Zap,
  TrendingUp,
  AlertTriangle,
  Info
} from 'lucide-react';

export function CustomPricingUI() {
  const [activeTab, setActiveTab] = useState('formulas');
  const [formulas, setFormulas] = useState<PricingFormula[]>([]);
  const [selectedFormula, setSelectedFormula] = useState<PricingFormula | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState<EvaluationResult | null>(null);
  const [testResults, setTestResults] = useState<TestCase[]>([]);
  const [loading, setLoading] = useState(false);

  // Form state
  const [formulaName, setFormulaName] = useState('');
  const [formulaDescription, setFormulaDescription] = useState('');
  const [formulaCode, setFormulaCode] = useState('');
  const [formulaCategory, setFormulaCategory] = useState<'buying' | 'selling' | 'both'>('both');

  // Test input state
  const [testInputs, setTestInputs] = useState<Record<string, any>>({});

  useEffect(() => {
    loadFormulas();
  }, []);

  const loadFormulas = () => {
    const allFormulas = customPricingEngine.getFormulas();
    setFormulas(allFormulas);
  };

  const handleCreateFormula = () => {
    setIsEditing(true);
    setSelectedFormula(null);
    setFormulaName('New Formula');
    setFormulaDescription('');
    setFormulaCode('// Enter your formula here\nreturn 0;');
    setFormulaCategory('both');
  };

  const handleEditFormula = (formula: PricingFormula) => {
    setIsEditing(true);
    setSelectedFormula(formula);
    setFormulaName(formula.name);
    setFormulaDescription(formula.description);
    setFormulaCode(formula.formula);
    setFormulaCategory(formula.category);
  };

  const handleSaveFormula = async () => {
    setLoading(true);
    try {
      if (selectedFormula) {
        // Update existing
        await customPricingEngine.updateFormula(selectedFormula.id, {
          name: formulaName,
          description: formulaDescription,
          formula: formulaCode,
          category: formulaCategory
        });
      } else {
        // Create new
        await customPricingEngine.createFormula({
          name: formulaName,
          description: formulaDescription,
          formula: formulaCode,
          category: formulaCategory,
          variables: [], // Would be extracted from formula
          isActive: true
        });
      }
      
      setIsEditing(false);
      loadFormulas();
    } catch (error) {
      console.error('Failed to save formula:', error);
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteFormula = async (formulaId: string) => {
    if (confirm('Are you sure you want to delete this formula?')) {
      try {
        await customPricingEngine.deleteFormula(formulaId);
        loadFormulas();
        if (selectedFormula?.id === formulaId) {
          setSelectedFormula(null);
        }
      } catch (error) {
        console.error('Failed to delete formula:', error);
      }
    }
  };

  const handleTestFormula = async () => {
    if (!selectedFormula) return;
    
    setLoading(true);
    try {
      const result = await customPricingEngine.evaluateFormula(selectedFormula.id, {
        userVariables: testInputs,
        // Mock listing data
        listing: {
          id: 'test-listing',
          externalId: 'test-123',
          platform: 'facebook',
          title: 'Gaming PC - RTX 3070',
          price: 800,
          location: 'San Francisco, CA',
          url: '#',
          description: 'Great gaming PC',
          images: [],
          components: {
            cpu: { brand: 'Intel', model: 'i7-10700K', value: 300 },
            gpu: { brand: 'NVIDIA', model: 'RTX 3070', value: 500 },
            ram: { capacity: 16, speed: 3200, value: 80 },
            storage: { capacity: 1000, type: 'SSD', value: 100 }
          },
          condition: 'good',
          risks: [],
          createdAt: new Date(),
          updatedAt: new Date()
        }
      });
      
      setEvaluationResult(result);
    } catch (error) {
      console.error('Failed to test formula:', error);
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRunTestCases = async () => {
    if (!selectedFormula) return;
    
    setLoading(true);
    try {
      const results = await customPricingEngine.runTestCases(selectedFormula.id);
      setTestResults(results);
    } catch (error) {
      console.error('Failed to run test cases:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportFormula = (formulaId: string) => {
    try {
      const exported = customPricingEngine.exportFormula(formulaId);
      const blob = new Blob([exported], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `formula-${formulaId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export formula:', error);
    }
  };

  const handleImportFormula = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      await customPricingEngine.importFormula(text);
      loadFormulas();
    } catch (error) {
      console.error('Failed to import formula:', error);
      alert(`Import failed: ${error.message}`);
    }
  };

  const renderFormulasView = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Pricing Formulas</h3>
        <div className="flex gap-2">
          <Button onClick={handleCreateFormula} size="sm">
            <Plus className="h-4 w-4 mr-1" />
            Create Formula
          </Button>
          <label htmlFor="import-formula">
            <Button size="sm" variant="outline" as="div">
              <Upload className="h-4 w-4 mr-1" />
              Import
            </Button>
            <input
              id="import-formula"
              type="file"
              accept=".json"
              className="hidden"
              onChange={handleImportFormula}
            />
          </label>
        </div>
      </div>

      <div className="grid gap-4">
        {formulas.map(formula => (
          <Card key={formula.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <CardTitle className="text-base flex items-center gap-2">
                    {formula.name}
                    {formula.isActive && <Badge variant="default" className="text-xs">Active</Badge>}
                  </CardTitle>
                  <CardDescription>{formula.description}</CardDescription>
                </div>
                <Badge variant="outline">
                  {formula.category}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  Variables: {formula.variables.length} | 
                  Tests: {formula.testCases?.length || 0}
                </div>
                
                <div className="flex gap-2">
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleEditFormula(formula)}
                  >
                    <Code className="h-4 w-4 mr-1" />
                    Edit
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => {
                      setSelectedFormula(formula);
                      setActiveTab('test');
                    }}
                  >
                    <Play className="h-4 w-4 mr-1" />
                    Test
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleExportFormula(formula.id)}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleDeleteFormula(formula.id)}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderEditorView = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">
          {selectedFormula ? 'Edit Formula' : 'Create Formula'}
        </h3>
        <div className="flex gap-2">
          <Button 
            onClick={() => setIsEditing(false)} 
            variant="outline" 
            size="sm"
          >
            Cancel
          </Button>
          <Button 
            onClick={handleSaveFormula} 
            size="sm"
            disabled={loading}
          >
            <Save className="h-4 w-4 mr-1" />
            Save Formula
          </Button>
        </div>
      </div>

      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="formula-name">Name</Label>
            <Input
              id="formula-name"
              value={formulaName}
              onChange={(e) => setFormulaName(e.target.value)}
              placeholder="e.g., Component-Based Pricing"
            />
          </div>
          
          <div>
            <Label htmlFor="formula-category">Category</Label>
            <Select value={formulaCategory} onValueChange={(v: any) => setFormulaCategory(v)}>
              <SelectTrigger id="formula-category">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="buying">Buying</SelectItem>
                <SelectItem value="selling">Selling</SelectItem>
                <SelectItem value="both">Both</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div>
          <Label htmlFor="formula-description">Description</Label>
          <Textarea
            id="formula-description"
            value={formulaDescription}
            onChange={(e) => setFormulaDescription(e.target.value)}
            placeholder="Describe what this formula does..."
            rows={2}
          />
        </div>

        <div>
          <Label htmlFor="formula-code">Formula Code</Label>
          <Alert className="mb-2">
            <Info className="h-4 w-4" />
            <AlertDescription className="text-xs">
              Available functions: min, max, round, floor, ceil, abs, sqrt, pow, percentage, markup, discount, 
              clamp, componentValue, totalComponentValue, if, switch, marketAdjustment, competitionFactor
            </AlertDescription>
          </Alert>
          <Textarea
            id="formula-code"
            value={formulaCode}
            onChange={(e) => setFormulaCode(e.target.value)}
            placeholder="// Your formula code here"
            rows={10}
            className="font-mono text-sm"
          />
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Example Formulas</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-xs font-mono">
              <div>
                <p className="text-gray-600 mb-1">Simple markup:</p>
                <code className="bg-gray-100 p-1 rounded">return markup(listing.price, 30);</code>
              </div>
              <div>
                <p className="text-gray-600 mb-1">Component-based:</p>
                <code className="bg-gray-100 p-1 rounded">return totalComponentValue(components) * 0.85;</code>
              </div>
              <div>
                <p className="text-gray-600 mb-1">Conditional pricing:</p>
                <code className="bg-gray-100 p-1 rounded">
                  return if(market.demandScore > 70, listing.price * 1.2, listing.price);
                </code>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderTestView = () => (
    <div className="space-y-4">
      {selectedFormula ? (
        <>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Test Formula: {selectedFormula.name}</h3>
            <Button 
              onClick={handleTestFormula} 
              size="sm"
              disabled={loading}
            >
              <Play className="h-4 w-4 mr-1" />
              Run Test
            </Button>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Test Inputs</CardTitle>
              <CardDescription>
                Configure variables for testing the formula
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="test-roi">Target ROI (%)</Label>
                  <Input
                    id="test-roi"
                    type="number"
                    value={testInputs.targetROI || 30}
                    onChange={(e) => setTestInputs({
                      ...testInputs,
                      targetROI: parseInt(e.target.value)
                    })}
                  />
                </div>
                
                <div>
                  <Label htmlFor="test-urgency">Urgency Level (%)</Label>
                  <Input
                    id="test-urgency"
                    type="number"
                    value={testInputs.urgencyLevel || 10}
                    onChange={(e) => setTestInputs({
                      ...testInputs,
                      urgencyLevel: parseInt(e.target.value)
                    })}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {evaluationResult && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center justify-between">
                  Evaluation Result
                  <Badge variant={evaluationResult.confidence > 80 ? 'default' : 'secondary'}>
                    {evaluationResult.confidence}% Confidence
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-center p-4 bg-gray-50 rounded">
                    <div className="text-3xl font-bold text-green-600">
                      ${evaluationResult.price.toFixed(2)}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">Calculated Price</div>
                  </div>

                  {evaluationResult.warnings && evaluationResult.warnings.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium flex items-center gap-1">
                        <AlertTriangle className="h-4 w-4 text-yellow-500" />
                        Warnings
                      </h4>
                      {evaluationResult.warnings.map((warning, idx) => (
                        <Alert key={idx}>
                          <AlertDescription className="text-xs">
                            {warning}
                          </AlertDescription>
                        </Alert>
                      ))}
                    </div>
                  )}

                  {evaluationResult.suggestions && evaluationResult.suggestions.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium flex items-center gap-1">
                        <TrendingUp className="h-4 w-4 text-blue-500" />
                        Suggestions
                      </h4>
                      {evaluationResult.suggestions.map((suggestion, idx) => (
                        <div key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                          <span className="text-blue-500">•</span>
                          {suggestion}
                        </div>
                      ))}
                    </div>
                  )}

                  <div>
                    <h4 className="text-sm font-medium mb-2">Calculation Breakdown</h4>
                    <ScrollArea className="h-48 rounded border p-2">
                      <div className="space-y-1 font-mono text-xs">
                        {evaluationResult.breakdown.map((step, idx) => (
                          <div key={idx} className="flex justify-between">
                            <span className="text-gray-600">{step.step}</span>
                            <span className="font-medium">{step.value.toFixed(2)}</span>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center justify-between">
                Test Cases
                <Button 
                  onClick={handleRunTestCases} 
                  size="sm" 
                  variant="outline"
                  disabled={loading || !selectedFormula.testCases?.length}
                >
                  <FlaskConical className="h-4 w-4 mr-1" />
                  Run All Tests
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {testResults.length > 0 ? (
                <div className="space-y-2">
                  {testResults.map((test, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 border rounded">
                      <div className="flex items-center gap-2">
                        {test.passed ? (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-red-500" />
                        )}
                        <span className="text-sm">Test {idx + 1}</span>
                      </div>
                      <div className="text-sm text-gray-600">
                        Expected: ${test.expectedOutput} | 
                        Actual: ${test.actualOutput?.toFixed(2) || 'N/A'}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 text-center py-4">
                  No test cases defined for this formula
                </p>
              )}
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-8">
          <Calculator className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Select a formula to test</p>
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="text-sm text-gray-500 mt-2">Processing...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <Calculator className="h-6 w-6" />
          Custom Pricing Formulas
        </h2>
        <p className="text-gray-600">
          Create and test custom pricing formulas with variables, functions, and conditions
        </p>
      </div>

      {isEditing ? (
        renderEditorView()
      ) : (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="formulas">
              <Zap className="h-4 w-4 mr-2" />
              Formulas
            </TabsTrigger>
            <TabsTrigger value="test">
              <FlaskConical className="h-4 w-4 mr-2" />
              Test
            </TabsTrigger>
          </TabsList>

          <TabsContent value="formulas" className="mt-6">
            {renderFormulasView()}
          </TabsContent>

          <TabsContent value="test" className="mt-6">
            {renderTestView()}
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}