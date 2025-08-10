/**
 * Comps Store
 * Persist and manage market comp records
 */

import { db } from './db';
import { 
  CompRecord, 
  CompStats,
  mergeComps, 
  computeCompStats 
} from '@/core/comps';

const COMP_TTL_DAYS = 90; // Keep comps for 90 days

export interface DBComp extends CompRecord {
  _id?: number;
  expiresAt: Date;
}

/**
 * Save comps to database
 */
export async function saveComps(comps: CompRecord[]): Promise<void> {
  const expiresAt = new Date();
  expiresAt.setDate(expiresAt.getDate() + COMP_TTL_DAYS);
  
  const dbComps: DBComp[] = comps.map(comp => ({
    ...comp,
    expiresAt,
    timestamp: comp.timestamp instanceof Date ? comp.timestamp : new Date(comp.timestamp),
  }));
  
  // Get existing comps
  const existing = await db.comps.toArray();
  
  // Merge with deduplication
  const merged = mergeComps(
    existing.map(stripDbFields),
    comps,
    'url'
  );
  
  // Clear and re-insert (simpler than upsert logic)
  await db.transaction('rw', db.comps, async () => {
    await db.comps.clear();
    await db.comps.bulkAdd(merged.map(c => ({
      ...c,
      expiresAt,
      timestamp: c.timestamp instanceof Date ? c.timestamp : new Date(c.timestamp),
    })));
  });
  
  // Clean up expired
  await cleanupExpiredComps();
}

/**
 * Get comp stats for a query
 */
export async function getCompStats(
  query: Partial<Pick<CompRecord, 'cpu' | 'gpu' | 'ram' | 'storage'>>
): Promise<CompStats | null> {
  const comps = await db.comps.toArray();
  return computeCompStats(query, comps.map(stripDbFields));
}

/**
 * Get all comps
 */
export async function getAllComps(): Promise<CompRecord[]> {
  const comps = await db.comps.toArray();
  return comps.map(stripDbFields);
}

/**
 * Import comps from CSV
 */
export async function importCompsFromCsv(csvText: string): Promise<number> {
  const lines = csvText.trim().split('\n');
  if (lines.length < 2) return 0;
  
  const headers = lines[0].toLowerCase().split(',').map(h => h.trim());
  const comps: CompRecord[] = [];
  
  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map(v => v.trim());
    const record: any = {};
    
    headers.forEach((header, idx) => {
      record[header] = values[idx];
    });
    
    // Map CSV columns to CompRecord
    const comp: CompRecord = {
      id: record.id || `csv-${Date.now()}-${i}`,
      source: 'csv',
      title: record.title || record.name || '',
      price: parseFloat(record.price) || 0,
      currency: record.currency || 'USD',
      timestamp: record.date ? new Date(record.date) : new Date(),
      cpu: record.cpu,
      gpu: record.gpu,
      ram: record.ram ? parseInt(record.ram) : undefined,
      storage: record.storage ? parseInt(record.storage) : undefined,
      condition: record.condition as any,
      url: record.url,
    };
    
    if (record.city || record.state) {
      comp.location = {
        city: record.city,
        state: record.state,
      };
    }
    
    if (comp.title && comp.price > 0) {
      comps.push(comp);
    }
  }
  
  await saveComps(comps);
  return comps.length;
}

/**
 * Export comps to CSV
 */
export function exportCompsToCsv(comps: CompRecord[]): string {
  const headers = [
    'id', 'source', 'title', 'price', 'currency', 'date',
    'cpu', 'gpu', 'ram', 'storage', 'condition',
    'city', 'state', 'url'
  ];
  
  const rows = comps.map(comp => [
    comp.id,
    comp.source,
    `"${comp.title.replace(/"/g, '""')}"`,
    comp.price,
    comp.currency,
    comp.timestamp.toISOString(),
    comp.cpu || '',
    comp.gpu || '',
    comp.ram || '',
    comp.storage || '',
    comp.condition || '',
    comp.location?.city || '',
    comp.location?.state || '',
    comp.url || '',
  ]);
  
  return [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n');
}

/**
 * Clear comp cache
 */
export async function clearComps(): Promise<void> {
  await db.comps.clear();
}

/**
 * Clean up expired comps
 */
async function cleanupExpiredComps(): Promise<void> {
  const now = new Date();
  await db.comps.where('expiresAt').below(now).delete();
}

/**
 * Strip DB fields from comp record
 */
function stripDbFields(comp: DBComp): CompRecord {
  const { _id, expiresAt, ...record } = comp;
  return record;
}