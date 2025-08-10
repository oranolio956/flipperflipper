/**
 * Google Sheets Bridge
 * High-level sync operations with rate limiting and error handling
 */

import { getAccessToken } from './googleAuth';
import { db } from '@/lib/db';
import { retry, sleep } from '@/lib/utils';
import type {
  SheetMapping,
  SyncDirection,
  SyncResult,
  buildRowFromDeal,
  parseRowToDeal,
  diffLocalVsRemote,
  buildHeaderRow,
  DEFAULT_DEAL_MAPPING,
} from '@arbitrage/integrations/google/sheetsAdapter';

const SHEETS_API_BASE = 'https://sheets.googleapis.com/v4/spreadsheets';

interface SheetsConfig {
  spreadsheetId: string;
  mappings: {
    deals?: SheetMapping;
    analytics?: SheetMapping;
    inventory?: SheetMapping;
  };
}

/**
 * Ensure spreadsheet exists or create new one
 */
export async function ensureSpreadsheet(config?: Partial<SheetsConfig>): Promise<string> {
  const accessToken = await getAccessToken();
  if (!accessToken) throw new Error('Not authenticated');
  
  if (config?.spreadsheetId) {
    // Verify access to existing spreadsheet
    try {
      await fetchWithAuth(
        `${SHEETS_API_BASE}/${config.spreadsheetId}`,
        { method: 'GET' },
        accessToken
      );
      return config.spreadsheetId;
    } catch (error) {
      console.warn('Cannot access spreadsheet, creating new one');
    }
  }
  
  // Create new spreadsheet
  const response = await fetchWithAuth(
    SHEETS_API_BASE,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        properties: {
          title: `Gaming PC Arbitrage - ${new Date().toLocaleDateString()}`,
        },
        sheets: [
          { properties: { title: 'Deals' } },
          { properties: { title: 'Analytics' } },
          { properties: { title: 'Inventory' } },
        ],
      }),
    },
    accessToken
  );
  
  const spreadsheet = await response.json();
  return spreadsheet.spreadsheetId;
}

/**
 * Ensure sheets exist with headers
 */
export async function ensureSheets(config: SheetsConfig): Promise<void> {
  const accessToken = await getAccessToken();
  if (!accessToken) throw new Error('Not authenticated');
  
  // Get current sheets
  const response = await fetchWithAuth(
    `${SHEETS_API_BASE}/${config.spreadsheetId}`,
    { method: 'GET' },
    accessToken
  );
  
  const spreadsheet = await response.json();
  const existingSheets = new Set(
    spreadsheet.sheets.map((s: any) => s.properties.title)
  );
  
  // Create missing sheets and add headers
  const requests: any[] = [];
  
  for (const [key, mapping] of Object.entries(config.mappings)) {
    if (!mapping) continue;
    
    if (!existingSheets.has(mapping.sheetName)) {
      // Create sheet
      requests.push({
        addSheet: {
          properties: { title: mapping.sheetName },
        },
      });
    }
    
    // Add headers
    const headers = buildHeaderRow(mapping);
    requests.push({
      updateCells: {
        range: {
          sheetId: getSheetId(spreadsheet, mapping.sheetName),
          startRowIndex: 0,
          endRowIndex: 1,
        },
        rows: [{
          values: headers.map(h => ({ userEnteredValue: { stringValue: h } })),
        }],
        fields: 'userEnteredValue',
      },
    });
  }
  
  if (requests.length > 0) {
    await fetchWithAuth(
      `${SHEETS_API_BASE}/${config.spreadsheetId}:batchUpdate`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requests }),
      },
      accessToken
    );
  }
}

/**
 * Pull all data from sheets
 */
export async function pullAll(config: SheetsConfig): Promise<SyncResult> {
  const accessToken = await getAccessToken();
  if (!accessToken) throw new Error('Not authenticated');
  
  try {
    let pulled = 0;
    
    // Pull deals
    if (config.mappings.deals) {
      const range = `${config.mappings.deals.sheetName}!A2:Z`;
      const response = await fetchWithAuth(
        `${SHEETS_API_BASE}/${config.spreadsheetId}/values/${range}`,
        { method: 'GET' },
        accessToken
      );
      
      const data = await response.json();
      const rows = data.values || [];
      
      // Update local deals
      for (const row of rows) {
        const update = parseRowToDeal(row, config.mappings.deals);
        if (update.id) {
          const existing = await db.deals.where('id').equals(update.id).first();
          if (existing) {
            await db.deals.update(existing._id!, update);
            pulled++;
          }
        }
      }
    }
    
    return { success: true, pulled };
  } catch (error) {
    console.error('Pull failed:', error);
    return { success: false, error: String(error) };
  }
}

/**
 * Push all data to sheets
 */
export async function pushAll(config: SheetsConfig): Promise<SyncResult> {
  const accessToken = await getAccessToken();
  if (!accessToken) throw new Error('Not authenticated');
  
  try {
    let pushed = 0;
    
    // Push deals
    if (config.mappings.deals) {
      const deals = await db.deals.toArray();
      const rows = deals.map(d => buildRowFromDeal(d, config.mappings.deals!));
      
      if (rows.length > 0) {
        const range = `${config.mappings.deals.sheetName}!A2:Z`;
        await fetchWithAuth(
          `${SHEETS_API_BASE}/${config.spreadsheetId}/values/${range}:clear`,
          { method: 'POST' },
          accessToken
        );
        
        await fetchWithAuth(
          `${SHEETS_API_BASE}/${config.spreadsheetId}/values/${range}?valueInputOption=USER_ENTERED`,
          {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              range,
              values: rows,
            }),
          },
          accessToken
        );
        
        pushed = rows.length;
      }
    }
    
    return { success: true, pushed };
  } catch (error) {
    console.error('Push failed:', error);
    return { success: false, error: String(error) };
  }
}

/**
 * Sync all data in specified direction
 */
export async function syncAll(
  config: SheetsConfig,
  direction: SyncDirection
): Promise<SyncResult> {
  switch (direction) {
    case 'pull':
      return pullAll(config);
    case 'push':
      return pushAll(config);
    case 'both':
      // Pull first to get latest, then push local changes
      const pullResult = await pullAll(config);
      if (!pullResult.success) return pullResult;
      
      const pushResult = await pushAll(config);
      return {
        success: pushResult.success,
        pulled: pullResult.pulled,
        pushed: pushResult.pushed,
        error: pushResult.error,
      };
  }
}

/**
 * Fetch with auth and rate limiting
 */
async function fetchWithAuth(
  url: string,
  options: RequestInit,
  accessToken: string
): Promise<Response> {
  return retry(
    async () => {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${accessToken}`,
        },
      });
      
      if (response.status === 429) {
        // Rate limited, wait and retry
        const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
        await sleep(retryAfter * 1000);
        throw new Error('Rate limited');
      }
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }
      
      return response;
    },
    {
      retries: 3,
      delay: 1000,
      factor: 2,
    }
  );
}

/**
 * Get sheet ID by name
 */
function getSheetId(spreadsheet: any, sheetName: string): number {
  const sheet = spreadsheet.sheets.find(
    (s: any) => s.properties.title === sheetName
  );
  return sheet?.properties?.sheetId || 0;
}

// Export for convenience
export { DEFAULT_DEAL_MAPPING } from '@arbitrage/integrations/google/sheetsAdapter';