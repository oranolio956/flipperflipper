/**
 * Crypto Utilities
 * ID generation and hashing functions
 */

/**
 * Generate a unique ID
 */
export function generateId(prefix?: string): string {
  const timestamp = Date.now().toString(36);
  const randomStr = Math.random().toString(36).substring(2, 9);
  const id = `${timestamp}-${randomStr}`;
  
  return prefix ? `${prefix}_${id}` : id;
}

/**
 * Simple hash function for strings (non-cryptographic)
 */
export function hashString(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash).toString(36);
}

/**
 * Generate a short ID (6 characters)
 */
export function generateShortId(): string {
  return Math.random().toString(36).substring(2, 8).toUpperCase();
}

/**
 * Create a deterministic ID from multiple inputs
 */
export function createDeterministicId(...parts: string[]): string {
  const combined = parts.join('-');
  return hashString(combined);
}

/**
 * Encode data for safe storage (base64)
 */
export function encodeData(data: string): string {
  return btoa(encodeURIComponent(data));
}

/**
 * Decode data from safe storage
 */
export function decodeData(encoded: string): string {
  try {
    return decodeURIComponent(atob(encoded));
  } catch {
    return '';
  }
}