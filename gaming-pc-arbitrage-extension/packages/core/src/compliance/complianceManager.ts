/**
 * Compliance Manager
 * Platform ToS compliance and legal requirements
 */

export interface ComplianceRule {
  id: string;
  platform: 'facebook' | 'craigslist' | 'offerup' | 'all';
  category: 'messaging' | 'automation' | 'data_collection' | 'listing';
  rule: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  automated: boolean;
  requiresConsent: boolean;
}

export interface ComplianceCheck {
  ruleId: string;
  passed: boolean;
  timestamp: Date;
  details?: string;
  remediation?: string;
}

export interface ComplianceReport {
  platform: string;
  timestamp: Date;
  checks: ComplianceCheck[];
  overallStatus: 'compliant' | 'warnings' | 'violations';
  riskScore: number;
  recommendations: string[];
}

// Platform-specific rules
const COMPLIANCE_RULES: ComplianceRule[] = [
  // Facebook Marketplace
  {
    id: 'fb-msg-automation',
    platform: 'facebook',
    category: 'messaging',
    rule: 'No fully automated messaging - requires user confirmation',
    severity: 'critical',
    automated: false,
    requiresConsent: true,
  },
  {
    id: 'fb-listing-frequency',
    platform: 'facebook',
    category: 'listing',
    rule: 'Limit listing frequency to avoid spam detection',
    severity: 'high',
    automated: true,
    requiresConsent: false,
  },
  {
    id: 'fb-data-scraping',
    platform: 'facebook',
    category: 'data_collection',
    rule: 'Only parse data from user-viewed pages',
    severity: 'critical',
    automated: true,
    requiresConsent: false,
  },
  
  // Craigslist
  {
    id: 'cl-contact-info',
    platform: 'craigslist',
    category: 'messaging',
    rule: 'Do not harvest contact info for unsolicited messages',
    severity: 'high',
    automated: true,
    requiresConsent: false,
  },
  {
    id: 'cl-posting-limit',
    platform: 'craigslist',
    category: 'listing',
    rule: 'Maximum 1 post per category per 48 hours',
    severity: 'critical',
    automated: true,
    requiresConsent: false,
  },
  
  // General
  {
    id: 'all-user-consent',
    platform: 'all',
    category: 'data_collection',
    rule: 'Obtain user consent before collecting personal data',
    severity: 'critical',
    automated: false,
    requiresConsent: true,
  },
  {
    id: 'all-data-security',
    platform: 'all',
    category: 'data_collection',
    rule: 'Encrypt sensitive data at rest and in transit',
    severity: 'high',
    automated: true,
    requiresConsent: false,
  },
];

/**
 * Check compliance for action
 */
export function checkCompliance(
  action: {
    type: 'message' | 'listing' | 'data_collection' | 'automation';
    platform: string;
    details: Record<string, any>;
  }
): ComplianceCheck[] {
  const checks: ComplianceCheck[] = [];
  
  const relevantRules = COMPLIANCE_RULES.filter(rule => 
    (rule.platform === action.platform || rule.platform === 'all') &&
    (rule.category === action.type || rule.category === 'automation')
  );
  
  for (const rule of relevantRules) {
    const check = performCheck(rule, action);
    checks.push(check);
  }
  
  return checks;
}

/**
 * Generate compliance report
 */
export function generateComplianceReport(
  platform: string,
  recentActions: Array<{
    type: string;
    timestamp: Date;
    details: Record<string, any>;
  }>
): ComplianceReport {
  const checks: ComplianceCheck[] = [];
  let violations = 0;
  let warnings = 0;
  
  // Check each action
  for (const action of recentActions) {
    const actionChecks = checkCompliance({
      type: action.type as any,
      platform,
      details: action.details,
    });
    
    for (const check of actionChecks) {
      checks.push(check);
      if (!check.passed) {
        const rule = COMPLIANCE_RULES.find(r => r.id === check.ruleId);
        if (rule?.severity === 'critical') violations++;
        else if (rule?.severity === 'high') warnings++;
      }
    }
  }
  
  // Calculate risk score
  const riskScore = calculateRiskScore(checks);
  
  // Determine overall status
  let overallStatus: ComplianceReport['overallStatus'] = 'compliant';
  if (violations > 0) overallStatus = 'violations';
  else if (warnings > 0) overallStatus = 'warnings';
  
  // Generate recommendations
  const recommendations = generateRecommendations(checks, platform);
  
  return {
    platform,
    timestamp: new Date(),
    checks,
    overallStatus,
    riskScore,
    recommendations,
  };
}

/**
 * Validate message automation
 */
export function validateMessageAutomation(
  message: {
    content: string;
    recipient: string;
    platform: string;
    automated: boolean;
    userConfirmed: boolean;
  }
): { valid: boolean; reason?: string } {
  // Check platform-specific rules
  if (message.platform === 'facebook') {
    if (message.automated && !message.userConfirmed) {
      return { 
        valid: false, 
        reason: 'Facebook requires user confirmation for all messages' 
      };
    }
  }
  
  // Check content
  if (containsSpamKeywords(message.content)) {
    return { 
      valid: false, 
      reason: 'Message contains spam-like content' 
    };
  }
  
  // Check recipient consent
  if (!hasMessagingConsent(message.recipient)) {
    return { 
      valid: false, 
      reason: 'Recipient has not consented to messages' 
    };
  }
  
  return { valid: true };
}

/**
 * Rate limiting check
 */
export function checkRateLimit(
  action: string,
  platform: string,
  history: Array<{ timestamp: Date }>
): { allowed: boolean; waitTime?: number } {
  const limits: Record<string, { count: number; window: number }> = {
    'facebook:message': { count: 20, window: 3600000 }, // 20 per hour
    'facebook:listing': { count: 5, window: 86400000 }, // 5 per day
    'craigslist:listing': { count: 1, window: 172800000 }, // 1 per 48 hours
    'data:parse': { count: 100, window: 3600000 }, // 100 per hour
  };
  
  const key = `${platform}:${action}`;
  const limit = limits[key];
  
  if (!limit) return { allowed: true };
  
  const now = Date.now();
  const recentActions = history.filter(h => 
    now - h.timestamp.getTime() < limit.window
  );
  
  if (recentActions.length >= limit.count) {
    const oldestAction = recentActions[0];
    const waitTime = limit.window - (now - oldestAction.timestamp.getTime());
    return { allowed: false, waitTime };
  }
  
  return { allowed: true };
}

/**
 * Audit log entry
 */
export interface AuditLog {
  id: string;
  timestamp: Date;
  userId: string;
  action: string;
  resource: string;
  details: Record<string, any>;
  compliance: {
    checked: boolean;
    passed: boolean;
    violations: string[];
  };
}

/**
 * Create audit log
 */
export function createAuditLog(
  userId: string,
  action: string,
  resource: string,
  details: Record<string, any>,
  complianceChecks?: ComplianceCheck[]
): AuditLog {
  const violations = complianceChecks
    ?.filter(c => !c.passed)
    .map(c => c.ruleId) || [];
  
  return {
    id: generateAuditId(),
    timestamp: new Date(),
    userId,
    action,
    resource,
    details,
    compliance: {
      checked: !!complianceChecks,
      passed: violations.length === 0,
      violations,
    },
  };
}

/**
 * Legal disclaimer generator
 */
export function generateLegalDisclaimer(
  context: 'listing' | 'message' | 'data_export'
): string {
  const disclaimers: Record<string, string> = {
    listing: 'This tool assists with listing creation. Users are responsible for compliance with all platform terms of service and local laws.',
    message: 'Messages are drafted for your review. You must personally send all communications. Automated messaging may violate platform policies.',
    data_export: 'Exported data may contain personal information. Handle in accordance with applicable privacy laws.',
  };
  
  return disclaimers[context] || 'Use this tool in compliance with all applicable laws and platform policies.';
}

// Helper functions
function performCheck(
  rule: ComplianceRule,
  action: any
): ComplianceCheck {
  let passed = true;
  let details = '';
  let remediation = '';
  
  switch (rule.id) {
    case 'fb-msg-automation':
      if (action.type === 'message' && action.details.automated) {
        passed = action.details.userConfirmed === true;
        if (!passed) {
          details = 'Automated message without user confirmation';
          remediation = 'Enable user confirmation for all messages';
        }
      }
      break;
      
    case 'fb-data-scraping':
      if (action.type === 'data_collection') {
        passed = action.details.userViewed === true;
        if (!passed) {
          details = 'Attempted to collect data from non-viewed page';
          remediation = 'Only parse data from actively viewed pages';
        }
      }
      break;
      
    case 'cl-posting-limit':
      if (action.type === 'listing' && action.platform === 'craigslist') {
        const recentPosts = action.details.recentPosts || 0;
        passed = recentPosts === 0;
        if (!passed) {
          details = `${recentPosts} posts in last 48 hours`;
          remediation = 'Wait 48 hours between posts in same category';
        }
      }
      break;
  }
  
  return {
    ruleId: rule.id,
    passed,
    timestamp: new Date(),
    details,
    remediation,
  };
}

function calculateRiskScore(checks: ComplianceCheck[]): number {
  let score = 0;
  
  for (const check of checks) {
    if (!check.passed) {
      const rule = COMPLIANCE_RULES.find(r => r.id === check.ruleId);
      if (rule) {
        switch (rule.severity) {
          case 'critical': score += 40; break;
          case 'high': score += 25; break;
          case 'medium': score += 15; break;
          case 'low': score += 5; break;
        }
      }
    }
  }
  
  return Math.min(100, score);
}

function generateRecommendations(
  checks: ComplianceCheck[],
  platform: string
): string[] {
  const recommendations: string[] = [];
  const failedChecks = checks.filter(c => !c.passed);
  
  if (failedChecks.length === 0) {
    recommendations.push('All compliance checks passed - maintain current practices');
    return recommendations;
  }
  
  // Group by category
  const byCategory: Record<string, ComplianceCheck[]> = {};
  for (const check of failedChecks) {
    const rule = COMPLIANCE_RULES.find(r => r.id === check.ruleId);
    if (rule) {
      byCategory[rule.category] = byCategory[rule.category] || [];
      byCategory[rule.category].push(check);
    }
  }
  
  // Generate category-specific recommendations
  if (byCategory.messaging) {
    recommendations.push('Review messaging practices - ensure all messages are user-initiated');
  }
  
  if (byCategory.data_collection) {
    recommendations.push('Audit data collection practices - verify user consent and encryption');
  }
  
  if (byCategory.listing) {
    recommendations.push('Implement rate limiting for listing creation');
  }
  
  // Platform-specific
  if (platform === 'facebook' && failedChecks.length > 2) {
    recommendations.push('Consider reducing automation level to avoid account restrictions');
  }
  
  return recommendations;
}

function containsSpamKeywords(content: string): boolean {
  const spamKeywords = [
    'guarantee', 'act now', 'limited time', 'risk free',
    'double your', 'earn money', 'work from home'
  ];
  
  const lowerContent = content.toLowerCase();
  return spamKeywords.some(keyword => lowerContent.includes(keyword));
}

function hasMessagingConsent(recipient: string): boolean {
  // Placeholder - would check consent database
  return true;
}

function generateAuditId(): string {
  return `audit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}