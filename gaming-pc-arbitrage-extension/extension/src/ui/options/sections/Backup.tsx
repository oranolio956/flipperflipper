/**
 * Backup Settings Section
 * Configure automated backups and restore
 */

import React, { useState } from 'react';
import { Download, Upload, Shield, AlertCircle, Check } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import { can } from '@/lib/authz';
import { db } from '@/lib/db';
import { getSettings } from '@/lib/settings';
import { importAll } from '@arbitrage/data/backup';
import { sendMessage, MessageType } from '@/lib/messages';
import type { Settings } from '@/core';
import type { DBUser } from '@/lib/db';

interface BackupProps {
  settings: Settings;
  onUpdate: (updates: Partial<Settings>) => void;
}

export function Backup({ settings, onUpdate }: BackupProps) {
  const { toast } = useToast();
  const [currentUser, setCurrentUser] = useState<DBUser | null>(null);
  const [passphrase, setPassphrase] = useState(settings.backup?.passphrase || '');
  const [confirmPassphrase, setConfirmPassphrase] = useState('');
  const [isBackingUp, setIsBackingUp] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);
  const [showPassphrase, setShowPassphrase] = useState(false);

  const backupConfig = settings.backup || {
    enabled: false,
    frequency: 'weekly',
    retention: 5,
    passphrase: '',
  };

  React.useEffect(() => {
    loadCurrentUser();
  }, []);

  const loadCurrentUser = async () => {
    try {
      const currentSettings = await getSettings();
      const users = await db.users.toArray();
      const user = users.find(u => u.id === currentSettings.team?.currentUserId);
      setCurrentUser(user || null);
    } catch (error) {
      console.error('Failed to load current user:', error);
    }
  };

  const handleBackupNow = async () => {
    if (!currentUser || !can(currentUser.role, 'backup')) {
      toast({
        title: 'Permission denied',
        description: 'You cannot create backups',
        variant: 'destructive',
      });
      return;
    }

    if (!passphrase) {
      toast({
        title: 'Passphrase required',
        description: 'Please set a backup passphrase first',
        variant: 'destructive',
      });
      return;
    }

    setIsBackingUp(true);
    try {
      // Save passphrase if changed
      if (passphrase !== backupConfig.passphrase) {
        onUpdate({
          backup: { ...backupConfig, passphrase },
        });
      }

      // Trigger backup
      const result = await sendMessage({ type: MessageType.BACKUP_NOW });
      
      if (result.success) {
        toast({
          title: 'Backup created',
          description: `File saved: ${result.filename}`,
        });
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      toast({
        title: 'Backup failed',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsBackingUp(false);
    }
  };

  const handleRestore = async () => {
    if (!currentUser || !can(currentUser.role, 'backup')) {
      toast({
        title: 'Permission denied',
        description: 'You cannot restore backups',
        variant: 'destructive',
      });
      return;
    }

    if (!confirmPassphrase) {
      toast({
        title: 'Passphrase required',
        description: 'Enter the backup passphrase to restore',
        variant: 'destructive',
      });
      return;
    }

    // Create file input
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.backup,.gpca.backup';
    
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      setIsRestoring(true);
      try {
        await importAll(db, file, {
          passphrase: confirmPassphrase,
          merge: 'overwrite',
        });

        toast({
          title: 'Restore complete',
          description: 'All data has been restored',
        });

        // Reload settings
        window.location.reload();
      } catch (error) {
        toast({
          title: 'Restore failed',
          description: String(error),
          variant: 'destructive',
        });
      } finally {
        setIsRestoring(false);
      }
    };

    input.click();
  };

  const handleToggleBackup = (enabled: boolean) => {
    if (!passphrase && enabled) {
      toast({
        title: 'Passphrase required',
        description: 'Set a passphrase before enabling backups',
        variant: 'destructive',
      });
      return;
    }

    onUpdate({
      backup: { ...backupConfig, enabled, passphrase },
    });
  };

  const handlePruneData = async () => {
    if (!currentUser || !can(currentUser.role, 'backup')) {
      toast({
        title: 'Permission denied',
        variant: 'destructive',
      });
      return;
    }

    if (!confirm('Remove data older than 90 days? This cannot be undone.')) {
      return;
    }

    try {
      const cutoff = Date.now() - (90 * 24 * 60 * 60 * 1000);
      
      // Delete old events
      await db.events.where('timestamp').below(cutoff).delete();
      
      // Delete old deals
      const oldDeals = await db.deals
        .where('stage')
        .equals('sold')
        .filter(d => new Date(d.soldAt || 0).getTime() < cutoff)
        .toArray();
      
      for (const deal of oldDeals) {
        await db.deals.delete(deal._id!);
        await db.listings.where('id').equals(deal.listingId).delete();
      }

      toast({
        title: 'Data pruned',
        description: `Removed ${oldDeals.length} old deals and events`,
      });
    } catch (error) {
      toast({
        title: 'Prune failed',
        description: String(error),
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Backup Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Backup Configuration</CardTitle>
          <CardDescription>
            Encrypt and backup your data automatically
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert>
            <Shield className="h-4 w-4" />
            <AlertDescription>
              Backups are encrypted using AES-256-GCM with your passphrase.
              Store your passphrase securely - it cannot be recovered!
            </AlertDescription>
          </Alert>

          <div className="space-y-2">
            <Label htmlFor="passphrase">
              Backup Passphrase
              <span className="text-red-500 ml-1">*</span>
            </Label>
            <div className="flex gap-2">
              <Input
                id="passphrase"
                type={showPassphrase ? 'text' : 'password'}
                value={passphrase}
                onChange={(e) => setPassphrase(e.target.value)}
                placeholder="Enter a strong passphrase"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowPassphrase(!showPassphrase)}
              >
                {showPassphrase ? 'Hide' : 'Show'}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Use a strong passphrase with 12+ characters
            </p>
          </div>

          <div className="flex items-center justify-between">
            <Label htmlFor="auto-backup">Enable automatic backups</Label>
            <Switch
              id="auto-backup"
              checked={backupConfig.enabled}
              onCheckedChange={handleToggleBackup}
              disabled={!currentUser || !can(currentUser.role, 'backup')}
            />
          </div>

          {backupConfig.enabled && (
            <>
              <div className="space-y-2">
                <Label>Frequency</Label>
                <Select
                  value={backupConfig.frequency}
                  onValueChange={(value) => onUpdate({
                    backup: { ...backupConfig, frequency: value as any },
                  })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="weekly">Weekly</SelectItem>
                    <SelectItem value="monthly">Monthly</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Keep last</Label>
                <Select
                  value={String(backupConfig.retention)}
                  onValueChange={(value) => onUpdate({
                    backup: { ...backupConfig, retention: parseInt(value) },
                  })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="3">3 backups</SelectItem>
                    <SelectItem value="5">5 backups</SelectItem>
                    <SelectItem value="10">10 backups</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </>
          )}

          <Button
            onClick={handleBackupNow}
            disabled={isBackingUp || !passphrase || !currentUser || !can(currentUser.role, 'backup')}
            className="w-full"
          >
            <Download className="h-4 w-4 mr-2" />
            {isBackingUp ? 'Creating backup...' : 'Backup Now'}
          </Button>
        </CardContent>
      </Card>

      {/* Restore */}
      <Card>
        <CardHeader>
          <CardTitle>Restore Data</CardTitle>
          <CardDescription>
            Restore from a backup file
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Restoring will overwrite all existing data. Create a backup first!
            </AlertDescription>
          </Alert>

          <div className="space-y-2">
            <Label htmlFor="confirm-passphrase">
              Backup Passphrase
            </Label>
            <Input
              id="confirm-passphrase"
              type="password"
              value={confirmPassphrase}
              onChange={(e) => setConfirmPassphrase(e.target.value)}
              placeholder="Enter the backup passphrase"
            />
          </div>

          <Button
            onClick={handleRestore}
            disabled={isRestoring || !confirmPassphrase || !currentUser || !can(currentUser.role, 'backup')}
            variant="outline"
            className="w-full"
          >
            <Upload className="h-4 w-4 mr-2" />
            {isRestoring ? 'Restoring...' : 'Restore from File'}
          </Button>
        </CardContent>
      </Card>

      {/* Data Management */}
      <Card>
        <CardHeader>
          <CardTitle>Data Management</CardTitle>
          <CardDescription>
            Clean up old data to save space
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            onClick={handlePruneData}
            variant="destructive"
            disabled={!currentUser || !can(currentUser.role, 'backup')}
          >
            Prune Old Data (90+ days)
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}