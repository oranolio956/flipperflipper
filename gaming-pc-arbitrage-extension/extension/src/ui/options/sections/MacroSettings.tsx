/**
 * Macro Settings Section
 * Configure one-click action preferences
 */

import React from 'react';
import { Zap, Info } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { Settings } from '@/core';

interface MacroSettingsProps {
  settings: Settings;
  onUpdate: (updates: Partial<Settings>) => void;
}

export function MacroSettings({ settings, onUpdate }: MacroSettingsProps) {
  const macroConfig = settings.macros || {
    enabled: true,
    showHotkeys: true,
    buttons: {
      draftOpener: true,
      followUp24h: true,
      priceCalculator: true,
      addCalendar: true,
      markAcquired: true,
      createInvoice: false,
    },
    customHotkeys: {},
  };

  const updateMacros = (updates: Partial<typeof macroConfig>) => {
    onUpdate({
      macros: { ...macroConfig, ...updates },
    });
  };

  const updateButton = (buttonId: string, enabled: boolean) => {
    updateMacros({
      buttons: { ...macroConfig.buttons, [buttonId]: enabled },
    });
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions Bar</CardTitle>
          <CardDescription>
            Configure one-click workflow shortcuts
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="macros-enabled" className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Enable Quick Actions Bar
            </Label>
            <Switch
              id="macros-enabled"
              checked={macroConfig.enabled}
              onCheckedChange={(checked) => updateMacros({ enabled: checked })}
            />
          </div>

          <div className="flex items-center justify-between">
            <Label htmlFor="show-hotkeys">
              Show Keyboard Shortcuts
            </Label>
            <Switch
              id="show-hotkeys"
              checked={macroConfig.showHotkeys}
              onCheckedChange={(checked) => updateMacros({ showHotkeys: checked })}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Available Actions</CardTitle>
          <CardDescription>
            Choose which quick actions to show
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="btn-draft">Draft Opener Message</Label>
                <p className="text-sm text-muted-foreground">
                  Generate opening message (Cmd+O)
                </p>
              </div>
              <Switch
                id="btn-draft"
                checked={macroConfig.buttons.draftOpener}
                onCheckedChange={(checked) => updateButton('draftOpener', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="btn-followup">Schedule Follow-up</Label>
                <p className="text-sm text-muted-foreground">
                  Set 24h reminder (Cmd+F)
                </p>
              </div>
              <Switch
                id="btn-followup"
                checked={macroConfig.buttons.followUp24h}
                onCheckedChange={(checked) => updateButton('followUp24h', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="btn-price">Price Calculator</Label>
                <p className="text-sm text-muted-foreground">
                  Quick price anchors (Cmd+P)
                </p>
              </div>
              <Switch
                id="btn-price"
                checked={macroConfig.buttons.priceCalculator}
                onCheckedChange={(checked) => updateButton('priceCalculator', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="btn-calendar">Add to Calendar</Label>
                <p className="text-sm text-muted-foreground">
                  Export pickup event (Cmd+K)
                </p>
              </div>
              <Switch
                id="btn-calendar"
                checked={macroConfig.buttons.addCalendar}
                onCheckedChange={(checked) => updateButton('addCalendar', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="btn-acquired">Mark as Acquired</Label>
                <p className="text-sm text-muted-foreground">
                  Move to inventory stage
                </p>
              </div>
              <Switch
                id="btn-acquired"
                checked={macroConfig.buttons.markAcquired}
                onCheckedChange={(checked) => updateButton('markAcquired', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="btn-invoice">Create Invoice</Label>
                <p className="text-sm text-muted-foreground">
                  Generate PDF receipt (Coming soon)
                </p>
              </div>
              <Switch
                id="btn-invoice"
                checked={macroConfig.buttons.createInvoice}
                onCheckedChange={(checked) => updateButton('createInvoice', checked)}
                disabled
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          Quick actions appear contextually based on the current deal stage.
          Keyboard shortcuts work on Windows (Ctrl) and Mac (Cmd).
        </AlertDescription>
      </Alert>
    </div>
  );
}