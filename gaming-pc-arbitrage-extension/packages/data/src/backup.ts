/**
 * Backup Module
 * Export and import database with AES-GCM encryption
 */

import type { Dexie } from 'dexie';

export interface BackupEnvelope {
  version: number;
  timestamp: string;
  encrypted: boolean;
  salt?: string;
  iv?: string;
  data: string;
}

export interface BackupOptions {
  passphrase: string;
  includeLogs?: boolean;
}

export interface RestoreOptions {
  passphrase: string;
  merge: 'overwrite' | 'upsert';
}

/**
 * Export entire database to encrypted blob
 */
export async function exportAll(
  db: Dexie, 
  options: BackupOptions
): Promise<Blob> {
  try {
    // Collect all data
    const backup: Record<string, any[]> = {};
    const tables = db.tables.filter(table => {
      // Optionally exclude logs/events
      if (!options.includeLogs) {
        return !['events', 'migrations'].includes(table.name);
      }
      return true;
    });
    
    for (const table of tables) {
      backup[table.name] = await table.toArray();
    }
    
    // Create envelope
    const envelope: BackupEnvelope = {
      version: 1,
      timestamp: new Date().toISOString(),
      encrypted: true,
      data: '',
    };
    
    // Encrypt data
    const dataString = JSON.stringify(backup);
    const encrypted = await encryptData(dataString, options.passphrase);
    
    envelope.salt = encrypted.salt;
    envelope.iv = encrypted.iv;
    envelope.data = encrypted.data;
    
    // Create blob
    const jsonString = JSON.stringify(envelope, null, 2);
    return new Blob([jsonString], { type: 'application/json' });
  } catch (error) {
    throw new Error(`Backup failed: ${error}`);
  }
}

/**
 * Import database from encrypted blob
 */
export async function importAll(
  db: Dexie,
  file: Blob,
  options: RestoreOptions
): Promise<void> {
  try {
    // Read file
    const text = await file.text();
    const envelope: BackupEnvelope = JSON.parse(text);
    
    // Validate envelope
    if (envelope.version !== 1) {
      throw new Error(`Unsupported backup version: ${envelope.version}`);
    }
    
    if (!envelope.encrypted || !envelope.salt || !envelope.iv) {
      throw new Error('Invalid backup format');
    }
    
    // Decrypt data
    const decrypted = await decryptData(
      envelope.data,
      envelope.salt,
      envelope.iv,
      options.passphrase
    );
    
    const backup = JSON.parse(decrypted);
    
    // Restore data
    await db.transaction('rw', ...db.tables, async () => {
      for (const [tableName, records] of Object.entries(backup)) {
        const table = db.table(tableName);
        if (!table) continue;
        
        if (options.merge === 'overwrite') {
          // Clear existing data
          await table.clear();
        }
        
        // Restore records
        for (const record of records as any[]) {
          // Convert date strings back to Date objects
          restoreDates(record);
          
          if (options.merge === 'upsert') {
            // Update or insert
            const key = record.id || record._id;
            if (key) {
              const existing = await table.where('id').equals(key).or('_id').equals(key).first();
              if (existing) {
                await table.update(existing._id || key, record);
              } else {
                await table.add(record);
              }
            } else {
              await table.add(record);
            }
          } else {
            // Just add (table was cleared)
            await table.add(record);
          }
        }
      }
    });
  } catch (error) {
    throw new Error(`Restore failed: ${error}`);
  }
}

/**
 * Encrypt data using WebCrypto API
 */
async function encryptData(
  data: string,
  passphrase: string
): Promise<{ data: string; salt: string; iv: string }> {
  // Generate salt and IV
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  
  // Derive key from passphrase
  const key = await deriveKey(passphrase, salt);
  
  // Encrypt
  const encoder = new TextEncoder();
  const encrypted = await crypto.subtle.encrypt(
    {
      name: 'AES-GCM',
      iv,
    },
    key,
    encoder.encode(data)
  );
  
  return {
    data: btoa(String.fromCharCode(...new Uint8Array(encrypted))),
    salt: btoa(String.fromCharCode(...salt)),
    iv: btoa(String.fromCharCode(...iv)),
  };
}

/**
 * Decrypt data
 */
async function decryptData(
  encryptedData: string,
  salt: string,
  iv: string,
  passphrase: string
): Promise<string> {
  // Decode from base64
  const encryptedBytes = Uint8Array.from(atob(encryptedData), c => c.charCodeAt(0));
  const saltBytes = Uint8Array.from(atob(salt), c => c.charCodeAt(0));
  const ivBytes = Uint8Array.from(atob(iv), c => c.charCodeAt(0));
  
  // Derive key
  const key = await deriveKey(passphrase, saltBytes);
  
  // Decrypt
  const decrypted = await crypto.subtle.decrypt(
    {
      name: 'AES-GCM',
      iv: ivBytes,
    },
    key,
    encryptedBytes
  );
  
  const decoder = new TextDecoder();
  return decoder.decode(decrypted);
}

/**
 * Derive encryption key from passphrase
 */
async function deriveKey(
  passphrase: string,
  salt: Uint8Array
): Promise<CryptoKey> {
  const encoder = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    encoder.encode(passphrase),
    'PBKDF2',
    false,
    ['deriveBits', 'deriveKey']
  );
  
  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt,
      iterations: 100000,
      hash: 'SHA-256',
    },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  );
}

/**
 * Restore date strings to Date objects
 */
function restoreDates(obj: any): void {
  if (!obj || typeof obj !== 'object') return;
  
  const dateFields = ['createdAt', 'updatedAt', 'lastSeen', 'soldAt', 'appliedAt', 'timestamp'];
  
  for (const [key, value] of Object.entries(obj)) {
    if (dateFields.includes(key) && typeof value === 'string') {
      // Check if it's a valid date string
      const date = new Date(value);
      if (!isNaN(date.getTime())) {
        obj[key] = date;
      }
    } else if (typeof value === 'object') {
      // Recurse into nested objects
      restoreDates(value);
    }
  }
}