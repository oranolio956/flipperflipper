/**
 * Options App - Complete Settings Management UI
 */

import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Save, Download, Upload, RotateCcw, AlertCircle } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/ui/use-toast';
import { Toaster } from '@/components/ui/toaster';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Section } from './components/Section';
import { Field } from './components/Field';
import { Sheets } from './sections/Sheets';
import { Team } from './sections/Team';
import { Backup } from './sections/Backup';
import { 
  getSettings, 
  setSettings, 
  resetToDefaults,
  exportSettings,
  importSettings
} from '@/lib/settings';
import { Settings, validateSettings } from '@/core';
import { sendMessage, MessageType } from '@/lib/messages';

export function App() {
  const [settings, setLocalSettings] = useState<Settings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const { toast } = useToast();

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  // Track changes
  useEffect(() => {
    if (settings) {
      setHasChanges(true);
    }
  }, [settings]);

  const loadSettings = async () => {
    try {
      const loaded = await getSettings();
      setLocalSettings(loaded);
      setHasChanges(false);
    } catch (error) {
      toast({
        title: 'Error loading settings',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings) return;
    
    setIsSaving(true);
    try {
      // Validate before saving
      const validated = validateSettings(settings);
      await setSettings(validated);
      
      // Notify background of changes
      await sendMessage({
        type: MessageType.SET_SETTINGS,
        settings: validated,
        partial: false,
      });
      
      setHasChanges(false);
      toast({
        title: 'Settings saved',
        description: 'Your preferences have been updated.',
      });
    } catch (error) {
      toast({
        title: 'Error saving settings',
        description: error instanceof Error ? error.message : 'Invalid settings',
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = async () => {
    if (confirm('Reset all settings to defaults? This cannot be undone.')) {
      try {
        const defaults = await resetToDefaults();
        setLocalSettings(defaults);
        setHasChanges(false);
        toast({
          title: 'Settings reset',
          description: 'All settings have been restored to defaults.',
        });
      } catch (error) {
        toast({
          title: 'Error resetting settings',
          description: error instanceof Error ? error.message : 'Unknown error',
          variant: 'destructive',
        });
      }
    }
  };

  const handleExport = async () => {
    try {
      const json = await exportSettings();
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `arbitrage-settings-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
      
      toast({
        title: 'Settings exported',
        description: 'Your settings have been downloaded.',
      });
    } catch (error) {
      toast({
        title: 'Export failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    try {
      const text = await file.text();
      const imported = await importSettings(text);
      setLocalSettings(imported);
      setHasChanges(false);
      toast({
        title: 'Settings imported',
        description: 'Your settings have been updated from the file.',
      });
    } catch (error) {
      toast({
        title: 'Import failed',
        description: error instanceof Error ? error.message : 'Invalid settings file',
        variant: 'destructive',
      });
    }
    
    // Reset input
    event.target.value = '';
  };

  const updateSetting = <K extends keyof Settings>(key: K, value: Settings[K]) => {
    if (!settings) return;
    setLocalSettings({ ...settings, [key]: value });
  };

  const updateNestedSetting = <
    K extends keyof Settings,
    NK extends keyof Settings[K]
  >(
    key: K,
    nestedKey: NK,
    value: Settings[K][NK]
  ) => {
    if (!settings) return;
    setLocalSettings({
      ...settings,
      [key]: {
        ...settings[key],
        [nestedKey]: value,
      },
    });
  };

  if (isLoading || !settings) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container max-w-4xl mx-auto py-8 px-4">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <SettingsIcon className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold">Settings</h1>
          </div>
          
          <div className="flex gap-2">
            <input
              type="file"
              id="import-file"
              accept=".json"
              className="hidden"
              onChange={handleImport}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => document.getElementById('import-file')?.click()}
            >
              <Upload className="h-4 w-4 mr-2" />
              Import
            </Button>
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button variant="outline" size="sm" onClick={handleReset}>
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset
            </Button>
            <Button 
              onClick={handleSave} 
              disabled={!hasChanges || isSaving}
            >
              <Save className="h-4 w-4 mr-2" />
              {isSaving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </div>

        {hasChanges && (
          <Alert className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              You have unsaved changes. Click "Save Changes" to apply them.
            </AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="geography" className="space-y-6">
          <TabsList className="grid grid-cols-6 w-full">
            <TabsTrigger value="geography">Geography</TabsTrigger>
            <TabsTrigger value="financial">Financial</TabsTrigger>
            <TabsTrigger value="operations">Operations</TabsTrigger>
            <TabsTrigger value="risk">Risk</TabsTrigger>
            <TabsTrigger value="automation">Automation</TabsTrigger>
            <TabsTrigger value="features">Features</TabsTrigger>
            <TabsTrigger value="sheets">Google Sheets</TabsTrigger>
            <TabsTrigger value="team">Team</TabsTrigger>
            <TabsTrigger value="backup">Backup</TabsTrigger>
          </TabsList>

          <TabsContent value="geography">
            <Section title="Geography Settings" description="Configure your operating area and location preferences">
              <Field
                label="Home Base (City, State)"
                value={settings.geography.home_base}
                onChange={(value) => updateNestedSetting('geography', 'home_base', value)}
                placeholder="Denver, CO"
              />
              <Field
                label="Max Distance (miles)"
                type="number"
                value={settings.geography.max_distance_miles}
                onChange={(value) => updateNestedSetting('geography', 'max_distance_miles', Number(value))}
                min={1}
                max={100}
              />
              <Field
                label="Preferred Meetup Spots"
                value={settings.geography.preferred_meetup_spots.join(', ')}
                onChange={(value) => updateNestedSetting('geography', 'preferred_meetup_spots', value.split(',').map(s => s.trim()))}
                placeholder="Police station, Bank, Coffee shop"
                helperText="Comma-separated list of safe public locations"
              />
              <Field
                label="Timezone"
                value={settings.geography.timezone}
                onChange={(value) => updateNestedSetting('geography', 'timezone', value)}
                placeholder="America/Denver"
              />
            </Section>
          </TabsContent>

          <TabsContent value="financial">
            <Section title="Financial Settings" description="Configure costs, fees, and profit targets">
              <Field
                label="Fuel Cost per Mile ($)"
                type="number"
                value={settings.financial.fuel_cost_per_mile}
                onChange={(value) => updateNestedSetting('financial', 'fuel_cost_per_mile', Number(value))}
                step={0.01}
                min={0}
              />
              <Field
                label="Platform Fees (%)"
                type="number"
                value={settings.financial.platform_fees_percent}
                onChange={(value) => updateNestedSetting('financial', 'platform_fees_percent', Number(value))}
                min={0}
                max={20}
              />
              <Field
                label="Tax Rate (%)"
                type="number"
                value={settings.financial.tax_rate}
                onChange={(value) => updateNestedSetting('financial', 'tax_rate', Number(value))}
                min={0}
                max={20}
              />
              <Field
                label="Minimum Profit Target ($)"
                type="number"
                value={settings.financial.min_profit_target}
                onChange={(value) => updateNestedSetting('financial', 'min_profit_target', Number(value))}
                min={0}
              />
              <Field
                label="Minimum ROI (%)"
                type="number"
                value={settings.financial.min_roi_percent}
                onChange={(value) => updateNestedSetting('financial', 'min_roi_percent', Number(value))}
                min={0}
              />
              <Field
                label="Cash Reserve ($)"
                type="number"
                value={settings.financial.cash_reserve}
                onChange={(value) => updateNestedSetting('financial', 'cash_reserve', Number(value))}
                min={0}
                helperText="Amount to keep liquid for opportunities"
              />
            </Section>
          </TabsContent>

          <TabsContent value="operations">
            <Section title="Operations" description="Configure time targets and labor settings">
              <Field
                label="Target Days to Sell"
                type="number"
                value={settings.operations.target_days_to_sell}
                onChange={(value) => updateNestedSetting('operations', 'target_days_to_sell', Number(value))}
                min={1}
                max={90}
              />
              <Field
                label="Labor Rate per Hour ($)"
                type="number"
                value={settings.operations.labor_rate_per_hour}
                onChange={(value) => updateNestedSetting('operations', 'labor_rate_per_hour', Number(value))}
                min={0}
              />
              <Field
                label="Max Active Deals"
                type="number"
                value={settings.operations.max_active_deals}
                onChange={(value) => updateNestedSetting('operations', 'max_active_deals', Number(value))}
                min={1}
                max={50}
              />
              <Field
                label="Business Hours"
                value={settings.operations.business_hours}
                onChange={(value) => updateNestedSetting('operations', 'business_hours', value)}
                placeholder="9am-7pm"
              />
              <Field
                label="Max Messages per Day"
                type="number"
                value={settings.operations.max_messages_per_day}
                onChange={(value) => updateNestedSetting('operations', 'max_messages_per_day', Number(value))}
                min={1}
                max={100}
                helperText="Platform rate limiting protection"
              />
            </Section>
          </TabsContent>

          <TabsContent value="risk">
            <Section title="Risk Tolerance" description="Configure safety thresholds and risk weights">
              <Field
                label="Max Risk Score (1-10)"
                type="number"
                value={settings.risk_tolerance.max_risk_score}
                onChange={(value) => updateNestedSetting('risk_tolerance', 'max_risk_score', Number(value))}
                min={1}
                max={10}
              />
              <Field
                label="Require Photos"
                type="switch"
                value={settings.risk_tolerance.require_photos}
                onChange={(value) => updateNestedSetting('risk_tolerance', 'require_photos', value === 'true')}
              />
              <Field
                label="Require Serial Verification"
                type="switch"
                value={settings.risk_tolerance.require_serial_verification}
                onChange={(value) => updateNestedSetting('risk_tolerance', 'require_serial_verification', value === 'true')}
              />
              <Field
                label="Avoid Keywords"
                value={settings.risk_tolerance.avoid_keywords.join(', ')}
                onChange={(value) => updateNestedSetting('risk_tolerance', 'avoid_keywords', value.split(',').map(s => s.trim()))}
                placeholder="urgent, asap, cash only"
                helperText="Comma-separated red flag keywords"
              />
              <Field
                label="Min Seller Account Age (days)"
                type="number"
                value={settings.risk_tolerance.min_seller_account_age_days}
                onChange={(value) => updateNestedSetting('risk_tolerance', 'min_seller_account_age_days', Number(value))}
                min={0}
              />
            </Section>
          </TabsContent>

          <TabsContent value="automation">
            <Section title="Automation" description="Configure automation level and behaviors">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="automation-mode">Automation Mode</Label>
                    <p className="text-sm text-muted-foreground">
                      Control how much the extension automates
                    </p>
                  </div>
                  <select
                    id="automation-mode"
                    value={settings.automation.mode}
                    onChange={(e) => updateNestedSetting('automation', 'mode', e.target.value as Settings['automation']['mode'])}
                    className="h-10 px-3 py-2 text-sm border rounded-md"
                  >
                    <option value="off">Off - Manual Only</option>
                    <option value="assist">Assist - Suggestions Only</option>
                    <option value="max_auto">Max Auto - One-Tap Confirm</option>
                  </select>
                </div>
              </div>
              
              <Field
                label="Auto-parse Listings"
                type="switch"
                value={settings.automation.auto_parse_listings}
                onChange={(value) => updateNestedSetting('automation', 'auto_parse_listings', value === 'true')}
              />
              <Field
                label="Auto-calculate ROI"
                type="switch"
                value={settings.automation.auto_calculate_roi}
                onChange={(value) => updateNestedSetting('automation', 'auto_calculate_roi', value === 'true')}
              />
              <Field
                label="Auto-generate Messages"
                type="switch"
                value={settings.automation.auto_generate_messages}
                onChange={(value) => updateNestedSetting('automation', 'auto_generate_messages', value === 'true')}
              />
              <Field
                label="Follow-up Cadence (hours)"
                value={settings.automation.followup_cadence_hours.join(', ')}
                onChange={(value) => updateNestedSetting('automation', 'followup_cadence_hours', value.split(',').map(s => Number(s.trim())))}
                placeholder="1, 24, 72"
                helperText="Hours after initial contact"
              />
            </Section>
          </TabsContent>

          <TabsContent value="features">
            <Section title="Feature Flags" description="Enable or disable specific features">
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(settings.features).map(([key, enabled]) => (
                  <div key={key} className="flex items-center justify-between p-3 border rounded-lg">
                    <Label htmlFor={`feature-${key}`} className="text-sm font-normal cursor-pointer">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </Label>
                    <Switch
                      id={`feature-${key}`}
                      checked={enabled}
                      onCheckedChange={(checked) => {
                        setLocalSettings({
                          ...settings,
                          features: { ...settings.features, [key]: checked },
                        });
                      }}
                    />
                  </div>
                ))}
              </div>
            </Section>
          </TabsContent>

          <TabsContent value="sheets">
            <Sheets 
              settings={settings} 
              onUpdate={(updates) => {
                const newSettings = { ...settings, ...updates };
                setLocalSettings(newSettings);
                setHasChanges(true);
              }}
            />
          </TabsContent>

          <TabsContent value="team">
            <Team
              settings={settings}
              onUpdate={(updates) => {
                const newSettings = { ...settings, ...updates };
                setLocalSettings(newSettings);
                setHasChanges(true);
              }}
            />
          </TabsContent>

          <TabsContent value="backup">
            <Backup
              settings={settings}
              onUpdate={(updates) => {
                const newSettings = { ...settings, ...updates };
                setLocalSettings(newSettings);
                setHasChanges(true);
              }}
            />
          </TabsContent>
        </Tabs>
      </div>
      <Toaster />
    </div>
  );
}