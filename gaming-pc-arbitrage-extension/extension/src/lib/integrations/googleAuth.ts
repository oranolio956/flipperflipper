/**
 * Google OAuth Authentication
 * Handles OAuth flow using chrome.identity API
 */

import { db } from '@/lib/db';
import type { SheetsAuthState } from '@arbitrage/integrations/google/sheetsAdapter';

// OAuth configuration
const OAUTH_CONFIG = {
  clientId: '', // Set via settings
  scopes: [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/userinfo.email',
  ],
  authUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
  tokenUrl: 'https://oauth2.googleapis.com/token',
};

interface TokenResponse {
  access_token: string;
  expires_in: number;
  token_type: string;
  scope: string;
  refresh_token?: string;
}

/**
 * Get current auth state
 */
export async function getAuthState(): Promise<SheetsAuthState> {
  try {
    const settings = await db.settings.orderBy('_id').last();
    const auth = settings?.integrations?.sheets?.auth;
    
    if (!auth || !auth.accessToken) {
      return { isAuthenticated: false };
    }
    
    // Check if token is expired
    if (auth.expiresAt && Date.now() > auth.expiresAt) {
      return { isAuthenticated: false };
    }
    
    return {
      isAuthenticated: true,
      email: auth.email,
      accessToken: auth.accessToken,
      expiresAt: auth.expiresAt,
    };
  } catch (error) {
    console.error('Failed to get auth state:', error);
    return { isAuthenticated: false };
  }
}

/**
 * Initiate OAuth flow
 */
export async function authenticate(): Promise<SheetsAuthState> {
  try {
    const settings = await db.settings.orderBy('_id').last();
    const clientId = settings?.integrations?.sheets?.clientId;
    
    if (!clientId) {
      throw new Error('Google OAuth Client ID not configured. Please set it in settings.');
    }
    
    // Get extension ID for redirect URL
    const redirectUrl = `https://${chrome.runtime.id}.chromiumapp.org/`;
    
    // Build auth URL
    const authParams = new URLSearchParams({
      client_id: clientId,
      response_type: 'token',
      redirect_uri: redirectUrl,
      scope: OAUTH_CONFIG.scopes.join(' '),
      access_type: 'online',
      prompt: 'consent',
    });
    
    const authUrl = `${OAUTH_CONFIG.authUrl}?${authParams}`;
    
    // Launch auth flow
    const responseUrl = await chrome.identity.launchWebAuthFlow({
      url: authUrl,
      interactive: true,
    });
    
    // Parse response
    const url = new URL(responseUrl);
    const params = new URLSearchParams(url.hash.substring(1)); // Remove #
    const accessToken = params.get('access_token');
    const expiresIn = parseInt(params.get('expires_in') || '3600', 10);
    
    if (!accessToken) {
      throw new Error('No access token received');
    }
    
    // Get user info
    const userInfo = await fetchUserInfo(accessToken);
    
    // Save auth state
    const authState: SheetsAuthState = {
      isAuthenticated: true,
      email: userInfo.email,
      accessToken,
      expiresAt: Date.now() + (expiresIn * 1000),
    };
    
    await saveAuthState(authState);
    
    return authState;
  } catch (error) {
    console.error('Authentication failed:', error);
    throw error;
  }
}

/**
 * Clear auth state (logout)
 */
export async function logout(): Promise<void> {
  try {
    const settings = await db.settings.orderBy('_id').last();
    if (settings?.integrations?.sheets) {
      await db.settings.update(settings._id!, {
        'integrations.sheets.auth': null,
      });
    }
  } catch (error) {
    console.error('Logout failed:', error);
    throw error;
  }
}

/**
 * Get access token, refreshing if needed
 */
export async function getAccessToken(): Promise<string | null> {
  const authState = await getAuthState();
  
  if (!authState.isAuthenticated) {
    return null;
  }
  
  // Check if token needs refresh (5 minutes buffer)
  if (authState.expiresAt && Date.now() > authState.expiresAt - 300000) {
    // For implicit flow, we need to re-authenticate
    // In production, use authorization code flow with refresh tokens
    try {
      const newAuth = await authenticate();
      return newAuth.accessToken || null;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return null;
    }
  }
  
  return authState.accessToken || null;
}

/**
 * Save auth state to encrypted storage
 */
async function saveAuthState(authState: SheetsAuthState): Promise<void> {
  const settings = await db.settings.orderBy('_id').last();
  
  if (!settings) {
    // Create initial settings
    await db.settings.add({
      version: 1,
      integrations: {
        sheets: {
          auth: {
            email: authState.email,
            accessToken: await encryptToken(authState.accessToken!),
            expiresAt: authState.expiresAt,
          },
        },
      },
    } as any);
  } else {
    // Update existing settings
    await db.settings.update(settings._id!, {
      'integrations.sheets.auth': {
        email: authState.email,
        accessToken: await encryptToken(authState.accessToken!),
        expiresAt: authState.expiresAt,
      },
    });
  }
}

/**
 * Fetch user info from Google
 */
async function fetchUserInfo(accessToken: string): Promise<{ email: string }> {
  const response = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch user info');
  }
  
  return await response.json();
}

/**
 * Encrypt token using WebCrypto
 */
async function encryptToken(token: string): Promise<string> {
  // Get or create encryption key
  const key = await getOrCreateEncryptionKey();
  
  // Encrypt
  const encoder = new TextEncoder();
  const data = encoder.encode(token);
  
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encrypted = await crypto.subtle.encrypt(
    {
      name: 'AES-GCM',
      iv,
    },
    key,
    data
  );
  
  // Combine IV and encrypted data
  const combined = new Uint8Array(iv.length + encrypted.byteLength);
  combined.set(iv, 0);
  combined.set(new Uint8Array(encrypted), iv.length);
  
  // Base64 encode
  return btoa(String.fromCharCode(...combined));
}

/**
 * Decrypt token
 */
async function decryptToken(encryptedToken: string): Promise<string> {
  const key = await getOrCreateEncryptionKey();
  
  // Base64 decode
  const combined = Uint8Array.from(atob(encryptedToken), c => c.charCodeAt(0));
  
  // Extract IV and data
  const iv = combined.slice(0, 12);
  const data = combined.slice(12);
  
  // Decrypt
  const decrypted = await crypto.subtle.decrypt(
    {
      name: 'AES-GCM',
      iv,
    },
    key,
    data
  );
  
  const decoder = new TextDecoder();
  return decoder.decode(decrypted);
}

/**
 * Get or create encryption key
 */
async function getOrCreateEncryptionKey(): Promise<CryptoKey> {
  const keyName = 'arbitrage-oauth-key';
  
  // Try to get existing key from IndexedDB
  const existing = await db.transaction('r', db.settings, async () => {
    const settings = await db.settings.orderBy('_id').last();
    return settings?.encryptionKey;
  });
  
  if (existing) {
    return await crypto.subtle.importKey(
      'raw',
      Uint8Array.from(atob(existing), c => c.charCodeAt(0)),
      { name: 'AES-GCM' },
      false,
      ['encrypt', 'decrypt']
    );
  }
  
  // Generate new key
  const key = await crypto.subtle.generateKey(
    {
      name: 'AES-GCM',
      length: 256,
    },
    true,
    ['encrypt', 'decrypt']
  );
  
  // Export and save
  const exported = await crypto.subtle.exportKey('raw', key);
  const keyString = btoa(String.fromCharCode(...new Uint8Array(exported)));
  
  await db.transaction('rw', db.settings, async () => {
    const settings = await db.settings.orderBy('_id').last();
    if (settings) {
      await db.settings.update(settings._id!, { encryptionKey: keyString });
    } else {
      await db.settings.add({ encryptionKey: keyString } as any);
    }
  });
  
  return key;
}