/**
 * Migration Manager
 * Handle data schema upgrades and version migrations
 */

import type { Settings } from '../settings/schema';

export interface Migration {
  version: string;
  description: string;
  up: (data: any) => Promise<any>;
  down?: (data: any) => Promise<any>;
}

export interface MigrationResult {
  success: boolean;
  fromVersion: string;
  toVersion: string;
  migratedData?: any;
  error?: string;
  backup?: any;
}

export interface DataBackup {
  version: string;
  timestamp: Date;
  data: Record<string, any>;
  compressed: boolean;
}

// Migration registry
const migrations: Migration[] = [
  {
    version: '1.0.0',
    description: 'Initial schema',
    up: async (data) => data,
  },
  {
    version: '1.1.0',
    description: 'Add ML settings and comp stats',
    up: async (data) => {
      return {
        ...data,
        settings: {
          ...data.settings,
          ml: {
            enabled: false,
            modelVersion: '1.0',
            updateFrequency: 'weekly',
            blend: 0.3,
          },
          compAnalysis: {
            enabled: true,
            maxAge: 30,
            minSamples: 5,
          },
        },
      };
    },
    down: async (data) => {
      const { ml, compAnalysis, ...settings } = data.settings;
      return { ...data, settings };
    },
  },
  {
    version: '1.2.0',
    description: 'Add pricing adjusters and operating costs',
    up: async (data) => {
      return {
        ...data,
        settings: {
          ...data.settings,
          pricingAdjusters: {
            enabled: true,
            seasonal: { enabled: true, multipliers: [] },
            regional: { enabled: true, multipliers: [] },
            brand: { enabled: true, premiums: [] },
          },
          operatingCosts: {
            enabled: true,
            electricity: { kwhRate: 0.12, defaultUsageHours: 8, includeInTCO: true },
            mining: { enabled: false, algorithm: 'ethash', revenuePerMhPerDay: 0.05, warnOnUsedGpu: true },
            warranty: { enabled: true, multipliers: {} },
            holdingCosts: { perDayAmount: 2, includeOpportunityCost: true, opportunityRate: 0.05 },
          },
        },
      };
    },
  },
  {
    version: '1.3.0',
    description: 'Add inventory and pipeline features',
    up: async (data) => {
      return {
        ...data,
        inventory: data.inventory || [],
        pipeline: data.pipeline || { stages: [], history: [] },
        settings: {
          ...data.settings,
          inventory: {
            lowStockAlert: true,
            reorderPoints: {},
            autoBundle: true,
          },
          pipeline: {
            autoProgress: true,
            stageTimeouts: {},
            notifications: true,
          },
        },
      };
    },
  },
];

/**
 * Migrate data to latest version
 */
export async function migrateData(
  currentData: any,
  fromVersion: string,
  toVersion?: string
): Promise<MigrationResult> {
  try {
    // Create backup
    const backup = await createBackup(currentData, fromVersion);
    
    // Find migrations to apply
    const targetVersion = toVersion || getLatestVersion();
    const migrationsToApply = getMigrationPath(fromVersion, targetVersion);
    
    if (migrationsToApply.length === 0) {
      return {
        success: true,
        fromVersion,
        toVersion: targetVersion,
        migratedData: currentData,
      };
    }
    
    // Apply migrations sequentially
    let data = currentData;
    for (const migration of migrationsToApply) {
      console.log(`Applying migration: ${migration.description}`);
      data = await migration.up(data);
    }
    
    // Validate migrated data
    const isValid = await validateMigratedData(data, targetVersion);
    if (!isValid) {
      throw new Error('Migrated data validation failed');
    }
    
    return {
      success: true,
      fromVersion,
      toVersion: targetVersion,
      migratedData: data,
      backup,
    };
  } catch (error) {
    return {
      success: false,
      fromVersion,
      toVersion: toVersion || getLatestVersion(),
      error: (error as Error).message,
    };
  }
}

/**
 * Rollback migration
 */
export async function rollbackMigration(
  currentData: any,
  fromVersion: string,
  toVersion: string
): Promise<MigrationResult> {
  try {
    const rollbackPath = getMigrationPath(fromVersion, toVersion).reverse();
    
    let data = currentData;
    for (const migration of rollbackPath) {
      if (migration.down) {
        console.log(`Rolling back: ${migration.description}`);
        data = await migration.down(data);
      } else {
        throw new Error(`No rollback defined for version ${migration.version}`);
      }
    }
    
    return {
      success: true,
      fromVersion,
      toVersion,
      migratedData: data,
    };
  } catch (error) {
    return {
      success: false,
      fromVersion,
      toVersion,
      error: (error as Error).message,
    };
  }
}

/**
 * Create data backup
 */
export async function createBackup(
  data: any,
  version: string
): Promise<DataBackup> {
  const backup: DataBackup = {
    version,
    timestamp: new Date(),
    data: JSON.parse(JSON.stringify(data)), // Deep clone
    compressed: false,
  };
  
  // Compress if large
  const dataSize = JSON.stringify(data).length;
  if (dataSize > 1024 * 1024) { // 1MB
    backup.data = await compressData(backup.data);
    backup.compressed = true;
  }
  
  return backup;
}

/**
 * Restore from backup
 */
export async function restoreBackup(backup: DataBackup): Promise<any> {
  let data = backup.data;
  
  if (backup.compressed) {
    data = await decompressData(data);
  }
  
  return data;
}

/**
 * Get migration path between versions
 */
function getMigrationPath(fromVersion: string, toVersion: string): Migration[] {
  const fromIndex = migrations.findIndex(m => m.version === fromVersion);
  const toIndex = migrations.findIndex(m => m.version === toVersion);
  
  if (fromIndex === -1 || toIndex === -1) {
    throw new Error(`Invalid version range: ${fromVersion} to ${toVersion}`);
  }
  
  if (fromIndex >= toIndex) {
    return []; // No migration needed or downgrade
  }
  
  return migrations.slice(fromIndex + 1, toIndex + 1);
}

/**
 * Get latest version
 */
export function getLatestVersion(): string {
  return migrations[migrations.length - 1].version;
}

/**
 * Check if migration is needed
 */
export function isMigrationNeeded(currentVersion: string): boolean {
  const latest = getLatestVersion();
  return compareVersions(currentVersion, latest) < 0;
}

/**
 * Compare version strings
 */
function compareVersions(v1: string, v2: string): number {
  const parts1 = v1.split('.').map(Number);
  const parts2 = v2.split('.').map(Number);
  
  for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
    const p1 = parts1[i] || 0;
    const p2 = parts2[i] || 0;
    
    if (p1 < p2) return -1;
    if (p1 > p2) return 1;
  }
  
  return 0;
}

/**
 * Validate migrated data
 */
async function validateMigratedData(data: any, version: string): Promise<boolean> {
  // Basic validation
  if (!data || typeof data !== 'object') {
    return false;
  }
  
  // Check required fields based on version
  switch (version) {
    case '1.3.0':
      return !!(
        data.settings &&
        data.inventory &&
        data.pipeline &&
        data.settings.inventory &&
        data.settings.pipeline
      );
    case '1.2.0':
      return !!(
        data.settings &&
        data.settings.pricingAdjusters &&
        data.settings.operatingCosts
      );
    case '1.1.0':
      return !!(
        data.settings &&
        data.settings.ml &&
        data.settings.compAnalysis
      );
    default:
      return true;
  }
}

/**
 * Compress data (placeholder)
 */
async function compressData(data: any): Promise<any> {
  // In production, use proper compression library
  return {
    compressed: true,
    data: JSON.stringify(data),
  };
}

/**
 * Decompress data (placeholder)
 */
async function decompressData(compressed: any): Promise<any> {
  // In production, use proper compression library
  if (compressed.compressed && compressed.data) {
    return JSON.parse(compressed.data);
  }
  return compressed;
}

/**
 * Export all data for backup
 */
export async function exportAllData(
  format: 'json' | 'encrypted' = 'json',
  password?: string
): Promise<Blob> {
  // Gather all data
  const data = {
    version: getLatestVersion(),
    exportDate: new Date().toISOString(),
    settings: await getSettings(),
    deals: await getDeals(),
    inventory: await getInventory(),
    messages: await getMessages(),
    analytics: await getAnalytics(),
  };
  
  let output: string;
  if (format === 'encrypted' && password) {
    output = await encryptData(JSON.stringify(data), password);
  } else {
    output = JSON.stringify(data, null, 2);
  }
  
  return new Blob([output], { type: 'application/json' });
}

/**
 * Import data from backup
 */
export async function importData(
  file: File,
  password?: string
): Promise<{ success: boolean; error?: string }> {
  try {
    const text = await file.text();
    let data: any;
    
    // Try to decrypt if needed
    if (text.startsWith('ENCRYPTED:')) {
      if (!password) {
        throw new Error('Password required for encrypted backup');
      }
      const decrypted = await decryptData(text, password);
      data = JSON.parse(decrypted);
    } else {
      data = JSON.parse(text);
    }
    
    // Validate and migrate if needed
    if (!data.version) {
      throw new Error('Invalid backup file: missing version');
    }
    
    if (isMigrationNeeded(data.version)) {
      const result = await migrateData(data, data.version);
      if (!result.success) {
        throw new Error(result.error || 'Migration failed');
      }
      data = result.migratedData;
    }
    
    // Restore data
    await restoreAllData(data);
    
    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: (error as Error).message,
    };
  }
}

// Placeholder functions for data access
async function getSettings(): Promise<any> {
  // Would fetch from storage
  return {};
}

async function getDeals(): Promise<any[]> {
  return [];
}

async function getInventory(): Promise<any[]> {
  return [];
}

async function getMessages(): Promise<any[]> {
  return [];
}

async function getAnalytics(): Promise<any[]> {
  return [];
}

async function restoreAllData(data: any): Promise<void> {
  // Would restore to storage
}

async function encryptData(data: string, password: string): Promise<string> {
  // Placeholder - use WebCrypto in production
  return 'ENCRYPTED:' + Buffer.from(data).toString('base64');
}

async function decryptData(encrypted: string, password: string): Promise<string> {
  // Placeholder - use WebCrypto in production
  const base64 = encrypted.replace('ENCRYPTED:', '');
  return Buffer.from(base64, 'base64').toString();
}