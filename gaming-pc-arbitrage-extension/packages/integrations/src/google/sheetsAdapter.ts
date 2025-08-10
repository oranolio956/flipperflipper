/**
 * Google Sheets Adapter
 * Pure functions for syncing deals with Google Sheets
 */

import type { Deal, Listing } from '@/core';
import { formatCurrency, formatPercentage, formatDaysAgo } from '@/core';

export interface SheetsAuthState {
  isAuthenticated: boolean;
  email?: string;
  accessToken?: string;
  expiresAt?: number;
}

export type SyncDirection = 'push' | 'pull' | 'both';

export interface SheetMapping {
  sheetName: string;
  columns: ColumnMapping[];
  keyColumn: string; // Usually 'dealId'
}

export interface ColumnMapping {
  sheetColumn: string; // A, B, C...
  fieldPath: string; // e.g., 'id', 'listing.title', 'metrics.roi'
  format?: 'currency' | 'percentage' | 'date' | 'number' | 'text';
}

export interface SyncResult {
  success: boolean;
  pushed?: number;
  pulled?: number;
  conflicts?: string[];
  error?: string;
}

/**
 * Build a spreadsheet row from a deal using the mapping
 */
export function buildRowFromDeal(deal: Deal, mapping: SheetMapping): any[] {
  const row: any[] = [];
  
  for (const col of mapping.columns) {
    const value = getNestedValue(deal, col.fieldPath);
    const formatted = formatValue(value, col.format);
    row.push(formatted);
  }
  
  return row;
}

/**
 * Parse a spreadsheet row into a partial deal update
 */
export function parseRowToDeal(row: any[], mapping: SheetMapping): Partial<Deal> {
  const update: any = {};
  
  mapping.columns.forEach((col, index) => {
    if (row[index] !== undefined && row[index] !== '') {
      setNestedValue(update, col.fieldPath, parseValue(row[index], col.format));
    }
  });
  
  return update as Partial<Deal>;
}

/**
 * Compare local vs remote data to find changes
 */
export function diffLocalVsRemote(
  localDeals: Deal[],
  remoteRows: any[][],
  mapping: SheetMapping
): {
  toCreate: Deal[];
  toUpdate: Array<{ local: Deal; remote: any[] }>;
  toDelete: any[][];
} {
  const keyColIndex = mapping.columns.findIndex(c => c.fieldPath === mapping.keyColumn);
  if (keyColIndex === -1) throw new Error('Key column not found in mapping');
  
  const localMap = new Map(localDeals.map(d => [d.id, d]));
  const remoteMap = new Map(remoteRows.map(r => [r[keyColIndex], r]));
  
  const toCreate: Deal[] = [];
  const toUpdate: Array<{ local: Deal; remote: any[] }> = [];
  const toDelete: any[][] = [];
  
  // Find items to create or update
  for (const deal of localDeals) {
    const remoteRow = remoteMap.get(deal.id);
    if (!remoteRow) {
      toCreate.push(deal);
    } else {
      // Check if update needed
      const localRow = buildRowFromDeal(deal, mapping);
      if (!arraysEqual(localRow, remoteRow)) {
        toUpdate.push({ local: deal, remote: remoteRow });
      }
    }
  }
  
  // Find items to delete (in remote but not local)
  for (const [id, row] of remoteMap) {
    if (!localMap.has(id)) {
      toDelete.push(row);
    }
  }
  
  return { toCreate, toUpdate, toDelete };
}

/**
 * Build header row from mapping
 */
export function buildHeaderRow(mapping: SheetMapping): string[] {
  return mapping.columns.map(col => {
    // Convert fieldPath to readable header
    return col.fieldPath
      .split('.')
      .map(part => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  });
}

// Helper functions

function getNestedValue(obj: any, path: string): any {
  const parts = path.split('.');
  let current = obj;
  
  for (const part of parts) {
    if (current === null || current === undefined) return undefined;
    current = current[part];
  }
  
  return current;
}

function setNestedValue(obj: any, path: string, value: any): void {
  const parts = path.split('.');
  let current = obj;
  
  for (let i = 0; i < parts.length - 1; i++) {
    const part = parts[i];
    if (!(part in current)) {
      current[part] = {};
    }
    current = current[part];
  }
  
  current[parts[parts.length - 1]] = value;
}

function formatValue(value: any, format?: string): any {
  if (value === null || value === undefined) return '';
  
  switch (format) {
    case 'currency':
      return typeof value === 'number' ? formatCurrency(value) : value;
    case 'percentage':
      return typeof value === 'number' ? formatPercentage(value) : value;
    case 'date':
      return value instanceof Date ? value.toLocaleDateString() : value;
    case 'number':
      return typeof value === 'number' ? value : parseFloat(value) || 0;
    default:
      return String(value);
  }
}

function parseValue(value: any, format?: string): any {
  if (value === '' || value === null) return undefined;
  
  switch (format) {
    case 'currency':
      return parseFloat(String(value).replace(/[^0-9.-]/g, '')) || 0;
    case 'percentage':
      return parseFloat(String(value).replace('%', '')) / 100 || 0;
    case 'date':
      return new Date(value);
    case 'number':
      return parseFloat(value) || 0;
    default:
      return value;
  }
}

function arraysEqual(a: any[], b: any[]): boolean {
  if (a.length !== b.length) return false;
  return a.every((val, index) => val === b[index]);
}

// Default mappings

export const DEFAULT_DEAL_MAPPING: SheetMapping = {
  sheetName: 'Deals',
  keyColumn: 'id',
  columns: [
    { sheetColumn: 'A', fieldPath: 'id', format: 'text' },
    { sheetColumn: 'B', fieldPath: 'listing.title', format: 'text' },
    { sheetColumn: 'C', fieldPath: 'stage', format: 'text' },
    { sheetColumn: 'D', fieldPath: 'listing.price', format: 'currency' },
    { sheetColumn: 'E', fieldPath: 'metrics.estimatedProfit', format: 'currency' },
    { sheetColumn: 'F', fieldPath: 'metrics.roi', format: 'percentage' },
    { sheetColumn: 'G', fieldPath: 'listing.seller.name', format: 'text' },
    { sheetColumn: 'H', fieldPath: 'listing.location.city', format: 'text' },
    { sheetColumn: 'I', fieldPath: 'metadata.createdAt', format: 'date' },
    { sheetColumn: 'J', fieldPath: 'notes', format: 'text' },
  ],
};

export const DEFAULT_ANALYTICS_MAPPING: SheetMapping = {
  sheetName: 'Analytics',
  keyColumn: 'month',
  columns: [
    { sheetColumn: 'A', fieldPath: 'month', format: 'text' },
    { sheetColumn: 'B', fieldPath: 'dealsCount', format: 'number' },
    { sheetColumn: 'C', fieldPath: 'totalRevenue', format: 'currency' },
    { sheetColumn: 'D', fieldPath: 'totalProfit', format: 'currency' },
    { sheetColumn: 'E', fieldPath: 'avgROI', format: 'percentage' },
    { sheetColumn: 'F', fieldPath: 'avgTurnTime', format: 'number' },
  ],
};

export const DEFAULT_INVENTORY_MAPPING: SheetMapping = {
  sheetName: 'Inventory',
  keyColumn: 'id',
  columns: [
    { sheetColumn: 'A', fieldPath: 'id', format: 'text' },
    { sheetColumn: 'B', fieldPath: 'name', format: 'text' },
    { sheetColumn: 'C', fieldPath: 'category', format: 'text' },
    { sheetColumn: 'D', fieldPath: 'quantity', format: 'number' },
    { sheetColumn: 'E', fieldPath: 'cost', format: 'currency' },
    { sheetColumn: 'F', fieldPath: 'location', format: 'text' },
  ],
};