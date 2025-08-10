/**
 * Google Sheets Settings Section
 * Configure authentication, sync, and mappings
 */

import React, { useState, useEffect } from 'react';
import { Check, Cloud, CloudOff, RefreshCw, Settings, FileSpreadsheet } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import { Field } from '../components/Field';
import { 
  authenticate, 
  logout, 
  getAuthState 
} from '@/lib/integrations/googleAuth';
import { 
  ensureSpreadsheet, 
  ensureSheets,
  DEFAULT_DEAL_MAPPING 
} from '@/lib/integrations/sheetsBridge';
import { sendMessage, MessageType } from '@/lib/messages';
import type { Settings } from '@/core';
import type { SheetsAuthState } from '@arbitrage/integrations/google/sheetsAdapter';

interface SheetsProps {
  settings: Settings;
  onUpdate: (updates: Partial<Settings>) => void;
}

export function Sheets({ settings, onUpdate }: SheetsProps) {
  const [authState, setAuthState] = useState<SheetsAuthState>({ isAuthenticated: false });
  const [isConnecting, setIsConnecting] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const { toast } = useToast();

  const sheetsConfig = settings.integrations?.sheets || {};

  useEffect(() => {
    loadAuthState();
  }, []);

  const loadAuthState = async () => {
    try {
      const state = await getAuthState();
      setAuthState(state);
    } catch (error) {
      console.error('Failed to load auth state:', error);
    }
  };

  const handleConnect = async () => {
    setIsConnecting(true);
    try {
      const state = await authenticate();
      setAuthState(state);
      toast({
        title: 'Connected to Google',
        description: `Signed in as ${state.email}`,
      });
    } catch (error) {
      toast({
        title: 'Connection failed',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await logout();
      setAuthState({ isAuthenticated: false });
      toast({
        title: 'Disconnected',
        description: 'Signed out of Google',
      });
    } catch (error) {
      toast({
        title: 'Disconnect failed',
        description: String(error),
        variant: 'destructive',
      });
    }
  };

  const handleCreateSpreadsheet = async () => {
    setIsCreating(true);
    try {
      const spreadsheetId = await ensureSpreadsheet();
      
      // Update settings
      onUpdate({
        integrations: {
          ...settings.integrations,
          sheets: {
            ...sheetsConfig,
            spreadsheetId,
            mappings: {
              deals: DEFAULT_DEAL_MAPPING,
            },
          },
        },
      });

      // Ensure sheets exist
      await ensureSheets({
        spreadsheetId,
        mappings: {
          deals: DEFAULT_DEAL_MAPPING,
        },
      });

      toast({
        title: 'Spreadsheet created',
        description: 'Your new spreadsheet is ready',
      });

      // Open in new tab
      window.open(`https://docs.google.com/spreadsheets/d/${spreadsheetId}`, '_blank');
    } catch (error) {
      toast({
        title: 'Creation failed',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsCreating(false);
    }
  };

  const handleSyncNow = async () => {
    setIsSyncing(true);
    try {
      await sendMessage({
        type: MessageType.SHEETS_SYNC,
        direction: sheetsConfig.sync?.direction || 'both',
      });
      
      toast({
        title: 'Sync complete',
        description: 'Your data has been synchronized',
      });
    } catch (error) {
      toast({
        title: 'Sync failed',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Authentication */}
      <Card>
        <CardHeader>
          <CardTitle>Google Account</CardTitle>
          <CardDescription>
            Connect your Google account to sync data with Google Sheets
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!sheetsConfig.clientId && (
            <Alert>
              <AlertDescription>
                To use Google Sheets sync, you need to set up a Google OAuth client:
                <ol className="mt-2 ml-4 list-decimal">
                  <li>Go to <a href="https://console.cloud.google.com" target="_blank" className="underline">Google Cloud Console</a></li>
                  <li>Create a new project or select existing</li>
                  <li>Enable Google Sheets API</li>
                  <li>Create OAuth 2.0 credentials (Web application)</li>
                  <li>Add redirect URI: <code className="text-xs">https://{chrome.runtime.id}.chromiumapp.org/</code></li>
                  <li>Copy the Client ID below</li>
                </ol>
              </AlertDescription>
            </Alert>
          )}

          <Field
            label="OAuth Client ID"
            type="text"
            value={sheetsConfig.clientId || ''}
            onChange={(value) => onUpdate({
              integrations: {
                ...settings.integrations,
                sheets: {
                  ...sheetsConfig,
                  clientId: value,
                },
              },
            })}
            placeholder="1234567890-abc.apps.googleusercontent.com"
            helper="Get this from Google Cloud Console"
          />

          {sheetsConfig.clientId && (
            <div className="flex items-center justify-between p-4 border rounded-lg">
              {authState.isAuthenticated ? (
                <>
                  <div className="flex items-center gap-2">
                    <Cloud className="h-5 w-5 text-green-500" />
                    <div>
                      <div className="font-medium">Connected</div>
                      <div className="text-sm text-muted-foreground">{authState.email}</div>
                    </div>
                  </div>
                  <Button variant="outline" onClick={handleDisconnect}>
                    Disconnect
                  </Button>
                </>
              ) : (
                <>
                  <div className="flex items-center gap-2">
                    <CloudOff className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <div className="font-medium">Not connected</div>
                      <div className="text-sm text-muted-foreground">Sign in to sync data</div>
                    </div>
                  </div>
                  <Button onClick={handleConnect} disabled={isConnecting}>
                    {isConnecting ? 'Connecting...' : 'Connect'}
                  </Button>
                </>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Spreadsheet Configuration */}
      {authState.isAuthenticated && (
        <Card>
          <CardHeader>
            <CardTitle>Spreadsheet</CardTitle>
            <CardDescription>
              Configure which spreadsheet to sync with
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Field
              label="Spreadsheet ID"
              type="text"
              value={sheetsConfig.spreadsheetId || ''}
              onChange={(value) => onUpdate({
                integrations: {
                  ...settings.integrations,
                  sheets: {
                    ...sheetsConfig,
                    spreadsheetId: value,
                  },
                },
              })}
              placeholder="1a2b3c4d5e6f..."
              helper="Find this in the spreadsheet URL"
            />

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handleCreateSpreadsheet}
                disabled={isCreating}
              >
                <FileSpreadsheet className="h-4 w-4 mr-2" />
                {isCreating ? 'Creating...' : 'Create New Spreadsheet'}
              </Button>
              
              {sheetsConfig.spreadsheetId && (
                <Button
                  variant="outline"
                  onClick={() => window.open(`https://docs.google.com/spreadsheets/d/${sheetsConfig.spreadsheetId}`, '_blank')}
                >
                  Open Spreadsheet
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sync Settings */}
      {authState.isAuthenticated && sheetsConfig.spreadsheetId && (
        <Card>
          <CardHeader>
            <CardTitle>Sync Settings</CardTitle>
            <CardDescription>
              Configure automatic synchronization
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="sync-enabled">Enable automatic sync</Label>
              <Switch
                id="sync-enabled"
                checked={sheetsConfig.sync?.enabled || false}
                onCheckedChange={(checked) => onUpdate({
                  integrations: {
                    ...settings.integrations,
                    sheets: {
                      ...sheetsConfig,
                      sync: {
                        ...sheetsConfig.sync,
                        enabled: checked,
                      },
                    },
                  },
                })}
              />
            </div>

            {sheetsConfig.sync?.enabled && (
              <>
                <div className="space-y-2">
                  <Label>Sync direction</Label>
                  <Select
                    value={sheetsConfig.sync?.direction || 'both'}
                    onValueChange={(value) => onUpdate({
                      integrations: {
                        ...settings.integrations,
                        sheets: {
                          ...sheetsConfig,
                          sync: {
                            ...sheetsConfig.sync,
                            direction: value as any,
                          },
                        },
                      },
                    })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="push">Push only (Local → Sheets)</SelectItem>
                      <SelectItem value="pull">Pull only (Sheets → Local)</SelectItem>
                      <SelectItem value="both">Two-way sync</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Field
                  label="Sync frequency (minutes)"
                  type="number"
                  value={sheetsConfig.sync?.cadenceMin || 60}
                  onChange={(value) => onUpdate({
                    integrations: {
                      ...settings.integrations,
                      sheets: {
                        ...sheetsConfig,
                        sync: {
                          ...sheetsConfig.sync,
                          cadenceMin: parseInt(value) || 60,
                        },
                      },
                    },
                  })}
                  min={5}
                  max={1440}
                  helper="How often to sync data automatically"
                />
              </>
            )}

            <Button
              onClick={handleSyncNow}
              disabled={isSyncing}
              className="w-full"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isSyncing ? 'animate-spin' : ''}`} />
              {isSyncing ? 'Syncing...' : 'Sync Now'}
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}