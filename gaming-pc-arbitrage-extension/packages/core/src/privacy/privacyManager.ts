/**
 * Privacy Manager
 * Handle PII, consent, and data protection
 */

export interface PrivacySettings {
  dataCollection: {
    analytics: boolean;
    errorReporting: boolean;
    usageMetrics: boolean;
  };
  dataRetention: {
    dealHistory: number; // days
    messages: number;
    analytics: number;
  };
  piiHandling: {
    encryptAtRest: boolean;
    maskInLogs: boolean;
    autoAnonymize: boolean;
  };
  consent: {
    version: string;
    acceptedAt?: Date;
    acceptedFeatures: string[];
  };
}

export interface PIIField {
  field: string;
  type: 'name' | 'email' | 'phone' | 'address' | 'financial' | 'identifier';
  sensitivity: 'high' | 'medium' | 'low';
  purpose: string;
  encrypted: boolean;
}

export interface DataExport {
  exportId: string;
  requestedAt: Date;
  completedAt?: Date;
  format: 'json' | 'csv' | 'pdf';
  includesPII: boolean;
  password?: string;
  expiresAt: Date;
}

export interface ConsentRecord {
  version: string;
  timestamp: Date;
  ip?: string;
  features: Array<{
    feature: string;
    consented: boolean;
    purpose: string;
  }>;
  withdrawable: boolean;
}

// PII detection patterns
const PII_PATTERNS: Record<string, RegExp> = {
  email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
  phone: /\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b/g,
  ssn: /\b\d{3}-\d{2}-\d{4}\b/g,
  creditCard: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g,
  ipAddress: /\b(?:\d{1,3}\.){3}\d{1,3}\b/g,
};

/**
 * Detect PII in text
 */
export function detectPII(text: string): Array<{
  type: string;
  value: string;
  position: { start: number; end: number };
}> {
  const detections: any[] = [];
  
  for (const [type, pattern] of Object.entries(PII_PATTERNS)) {
    const matches = Array.from(text.matchAll(pattern));
    for (const match of matches) {
      if (match.index !== undefined) {
        detections.push({
          type,
          value: match[0],
          position: {
            start: match.index,
            end: match.index + match[0].length,
          },
        });
      }
    }
  }
  
  return detections;
}

/**
 * Mask PII in text
 */
export function maskPII(text: string, maskChar: string = '*'): {
  masked: string;
  detections: number;
} {
  let masked = text;
  const detections = detectPII(text);
  
  // Sort by position (reverse) to maintain indices
  detections.sort((a, b) => b.position.start - a.position.start);
  
  for (const detection of detections) {
    const maskLength = detection.value.length;
    const mask = maskChar.repeat(maskLength);
    masked = 
      masked.slice(0, detection.position.start) + 
      mask + 
      masked.slice(detection.position.end);
  }
  
  return { masked, detections: detections.length };
}

/**
 * Anonymize data
 */
export function anonymizeData<T extends Record<string, any>>(
  data: T,
  fields: string[]
): T {
  const anonymized = { ...data };
  
  for (const field of fields) {
    if (field in anonymized) {
      const value = (anonymized as any)[field];
      if (typeof value === 'string') {
        // Hash the value for consistency
        (anonymized as any)[field] = hashString(value);
      } else if (typeof value === 'number') {
        // Round numbers to reduce precision
        (anonymized as any)[field] = Math.round(value / 10) * 10;
      } else if (value instanceof Date) {
        // Remove time component
        (anonymized as any)[field] = new Date(value.toDateString());
      }
    }
  }
  
  return anonymized;
}

/**
 * Check consent for feature
 */
export function hasConsent(
  settings: PrivacySettings,
  feature: string
): boolean {
  if (!settings.consent.acceptedAt) return false;
  return settings.consent.acceptedFeatures.includes(feature);
}

/**
 * Record consent
 */
export function recordConsent(
  features: Array<{ feature: string; consented: boolean; purpose: string }>
): ConsentRecord {
  return {
    version: '1.0',
    timestamp: new Date(),
    features,
    withdrawable: true,
  };
}

/**
 * Generate data export
 */
export async function generateDataExport(
  data: {
    deals: any[];
    inventory: any[];
    messages: any[];
    analytics: any[];
  },
  options: {
    format: 'json' | 'csv' | 'pdf';
    includePII: boolean;
    password?: string;
  }
): Promise<DataExport> {
  const exportId = generateExportId();
  
  // Filter data based on PII preference
  let exportData = data;
  if (!options.includePII) {
    exportData = {
      deals: data.deals.map(d => anonymizeData(d, ['sellerName', 'sellerPhone', 'buyerName', 'buyerPhone'])),
      inventory: data.inventory.map(i => anonymizeData(i, ['serial'])),
      messages: data.messages.map(m => ({ 
        ...m, 
        content: maskPII(m.content).masked 
      })),
      analytics: data.analytics,
    };
  }
  
  // Format data
  let formatted: any;
  switch (options.format) {
    case 'csv':
      formatted = convertToCSV(exportData);
      break;
    case 'pdf':
      formatted = await generatePDF(exportData);
      break;
    default:
      formatted = JSON.stringify(exportData, null, 2);
  }
  
  // Encrypt if password provided
  if (options.password) {
    formatted = await encryptData(formatted, options.password);
  }
  
  return {
    exportId,
    requestedAt: new Date(),
    completedAt: new Date(),
    format: options.format,
    includesPII: options.includePII,
    password: options.password ? '***' : undefined,
    expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 days
  };
}

/**
 * Apply retention policy
 */
export function applyRetentionPolicy<T extends { createdAt: Date }>(
  data: T[],
  retentionDays: number
): T[] {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - retentionDays);
  
  return data.filter(item => item.createdAt > cutoffDate);
}

/**
 * Get privacy report
 */
export function generatePrivacyReport(
  data: {
    totalRecords: number;
    piiFields: PIIField[];
    retentionPolicies: Record<string, number>;
    encryptedFields: string[];
    consentRecords: ConsentRecord[];
  }
): {
  summary: string;
  compliance: {
    gdpr: boolean;
    ccpa: boolean;
    issues: string[];
  };
  recommendations: string[];
} {
  const issues: string[] = [];
  const recommendations: string[] = [];
  
  // Check PII handling
  const unencryptedPII = data.piiFields.filter(f => 
    f.sensitivity === 'high' && !f.encrypted
  );
  if (unencryptedPII.length > 0) {
    issues.push(`${unencryptedPII.length} high-sensitivity PII fields are not encrypted`);
    recommendations.push('Enable encryption for all high-sensitivity PII fields');
  }
  
  // Check retention
  const longRetention = Object.entries(data.retentionPolicies)
    .filter(([_, days]) => days > 365);
  if (longRetention.length > 0) {
    issues.push('Some data is retained for over 1 year');
    recommendations.push('Review retention policies for compliance');
  }
  
  // Check consent
  const recentConsent = data.consentRecords.filter(c => {
    const age = Date.now() - c.timestamp.getTime();
    return age < 365 * 24 * 60 * 60 * 1000; // 1 year
  });
  if (recentConsent.length === 0) {
    issues.push('No recent consent records found');
    recommendations.push('Implement consent renewal process');
  }
  
  const gdprCompliant = unencryptedPII.length === 0 && 
                       longRetention.length === 0 && 
                       recentConsent.length > 0;
  
  const ccpaCompliant = data.consentRecords.some(c => c.withdrawable);
  
  return {
    summary: `Managing ${data.totalRecords} records with ${data.piiFields.length} PII fields`,
    compliance: {
      gdpr: gdprCompliant,
      ccpa: ccpaCompliant,
      issues,
    },
    recommendations,
  };
}

// Helper functions
function hashString(str: string): string {
  // Simple hash for demo - use crypto in production
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return `ANON_${Math.abs(hash).toString(36)}`;
}

function generateExportId(): string {
  return `export_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function convertToCSV(data: any): string {
  // Simplified CSV conversion
  const csvData: string[] = [];
  
  for (const [key, items] of Object.entries(data)) {
    if (Array.isArray(items) && items.length > 0) {
      csvData.push(`\n${key.toUpperCase()}`);
      
      const headers = Object.keys(items[0]);
      csvData.push(headers.join(','));
      
      for (const item of items) {
        const row = headers.map(h => JSON.stringify(item[h] || ''));
        csvData.push(row.join(','));
      }
    }
  }
  
  return csvData.join('\n');
}

async function generatePDF(data: any): Promise<string> {
  // Placeholder - would use PDF library in production
  return `PDF Export\n\n${JSON.stringify(data, null, 2)}`;
}

async function encryptData(data: string, password: string): Promise<string> {
  // Placeholder - would use WebCrypto in production
  return Buffer.from(data).toString('base64');
}

/**
 * Sanitize user input
 */
export function sanitizeInput(input: string): string {
  // Remove potential XSS
  return input
    .replace(/[<>]/g, '')
    .replace(/javascript:/gi, '')
    .replace(/on\w+=/gi, '')
    .trim();
}

/**
 * Validate data access
 */
export function validateDataAccess(
  userId: string,
  resourceId: string,
  resourceType: string
): { allowed: boolean; reason?: string } {
  // Simplified access control
  // In production, would check against ACL
  
  if (!userId) {
    return { allowed: false, reason: 'User not authenticated' };
  }
  
  if (!resourceId || !resourceType) {
    return { allowed: false, reason: 'Invalid resource' };
  }
  
  // Check resource-specific rules
  if (resourceType === 'pii' && !hasRole(userId, 'admin')) {
    return { allowed: false, reason: 'Insufficient privileges for PII access' };
  }
  
  return { allowed: true };
}

function hasRole(userId: string, role: string): boolean {
  // Placeholder - would check actual roles
  return userId === 'admin';
}