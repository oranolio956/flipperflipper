/**
 * Background Sync Job
 * Handles scheduled Google Sheets synchronization
 */

import { db } from '@/lib/db';
import { syncAll } from '@/lib/integrations/sheetsBridge';
import type { SyncDirection } from '@arbitrage/integrations/google/sheetsAdapter';

const SYNC_ALARM_NAME = 'sheets-sync';

/**
 * Initialize sync alarms
 */
export async function initializeSync(): Promise<void> {
  // Check if sync is enabled
  const settings = await db.settings.orderBy('_id').last();
  const syncConfig = settings?.integrations?.sheets?.sync;
  
  if (syncConfig?.enabled && syncConfig?.cadenceMin > 0) {
    // Create or update alarm
    await chrome.alarms.create(SYNC_ALARM_NAME, {
      periodInMinutes: syncConfig.cadenceMin,
    });
    console.log(`Sheets sync scheduled every ${syncConfig.cadenceMin} minutes`);
  } else {
    // Clear alarm if disabled
    await chrome.alarms.clear(SYNC_ALARM_NAME);
    console.log('Sheets sync disabled');
  }
}

/**
 * Handle sync alarm
 */
export async function handleSyncAlarm(): Promise<void> {
  console.log('Running scheduled sheets sync');
  
  try {
    const settings = await db.settings.orderBy('_id').last();
    const sheetsConfig = settings?.integrations?.sheets;
    
    if (!sheetsConfig?.sync?.enabled) {
      console.log('Sync disabled, skipping');
      return;
    }
    
    if (!sheetsConfig.spreadsheetId) {
      console.log('No spreadsheet configured');
      return;
    }
    
    const config = {
      spreadsheetId: sheetsConfig.spreadsheetId,
      mappings: sheetsConfig.mappings || {},
    };
    
    const direction: SyncDirection = sheetsConfig.sync.direction || 'both';
    const result = await syncAll(config, direction);
    
    if (result.success) {
      console.log(`Sync completed: pushed=${result.pushed}, pulled=${result.pulled}`);
      
      // Log sync event
      await db.events.add({
        timestamp: Date.now(),
        category: 'integration',
        name: 'sheets_sync',
        data: {
          direction,
          pushed: result.pushed,
          pulled: result.pulled,
        },
      });
    } else {
      console.error('Sync failed:', result.error);
      
      // Log error
      await db.events.add({
        timestamp: Date.now(),
        category: 'error',
        name: 'sheets_sync_failed',
        data: { error: result.error },
      });
    }
  } catch (error) {
    console.error('Sync job error:', error);
  }
}

/**
 * Manually trigger sync
 */
export async function triggerSync(direction?: SyncDirection): Promise<void> {
  console.log('Manual sync triggered');
  
  const settings = await db.settings.orderBy('_id').last();
  const sheetsConfig = settings?.integrations?.sheets;
  
  if (!sheetsConfig?.spreadsheetId) {
    throw new Error('No spreadsheet configured');
  }
  
  const config = {
    spreadsheetId: sheetsConfig.spreadsheetId,
    mappings: sheetsConfig.mappings || {},
  };
  
  const result = await syncAll(config, direction || 'both');
  
  if (!result.success) {
    throw new Error(result.error || 'Sync failed');
  }
  
  // Send notification
  await chrome.notifications.create({
    type: 'basic',
    iconUrl: '/icons/icon-128.png',
    title: 'Sheets Sync Complete',
    message: `Pushed: ${result.pushed || 0} items, Pulled: ${result.pulled || 0} items`,
  });
}