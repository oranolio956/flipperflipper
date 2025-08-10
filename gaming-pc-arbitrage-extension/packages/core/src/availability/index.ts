/**
 * Availability Check Module
 * Draft messages and track response timers
 */

export interface AvailabilityPing {
  id: string;
  listingId: string;
  platform: string;
  message: string;
  variant: 'polite' | 'urgent' | 'casual';
  sentAt?: Date;
  responseDeadline: Date;
  status: 'draft' | 'sent' | 'responded' | 'stale';
}

export interface AvailabilityTemplate {
  variant: AvailabilityPing['variant'];
  template: string;
  followUpHours: number;
}

// Message templates
export const AVAILABILITY_TEMPLATES: AvailabilityTemplate[] = [
  {
    variant: 'polite',
    template: 'Hi! Is this still available? I\'m very interested and can pick up today with cash in hand. Thanks!',
    followUpHours: 24,
  },
  {
    variant: 'urgent',
    template: 'Hello - still available? Ready to buy NOW if you can meet today. Cash ready.',
    followUpHours: 12,
  },
  {
    variant: 'casual',
    template: 'Hey, is this still for sale? Interested if it\'s still around.',
    followUpHours: 48,
  },
];

/**
 * Generate availability ping message
 */
export function generateAvailabilityPing(
  listingId: string,
  platform: string,
  variant: AvailabilityPing['variant'] = 'polite'
): AvailabilityPing {
  const template = AVAILABILITY_TEMPLATES.find(t => t.variant === variant) || AVAILABILITY_TEMPLATES[0];
  
  const responseDeadline = new Date();
  responseDeadline.setHours(responseDeadline.getHours() + template.followUpHours);
  
  return {
    id: `ping-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    listingId,
    platform,
    message: template.template,
    variant,
    responseDeadline,
    status: 'draft',
  };
}

/**
 * Mark ping as sent
 */
export function markPingSent(ping: AvailabilityPing): AvailabilityPing {
  return {
    ...ping,
    sentAt: new Date(),
    status: 'sent',
  };
}

/**
 * Check if ping is stale
 */
export function isPingStale(ping: AvailabilityPing): boolean {
  if (ping.status !== 'sent') return false;
  return new Date() > ping.responseDeadline;
}

/**
 * Calculate response time
 */
export function calculateResponseTime(ping: AvailabilityPing, responseAt: Date): number | null {
  if (!ping.sentAt) return null;
  return Math.round((responseAt.getTime() - ping.sentAt.getTime()) / (1000 * 60)); // minutes
}

/**
 * Generate follow-up message
 */
export function generateFollowUp(originalPing: AvailabilityPing): string {
  const templates = [
    'Hi again - just following up. Is this still available?',
    'Following up on my earlier message. Still selling?',
    'Hey, didn\'t hear back - is this sold already?',
  ];
  
  return templates[Math.floor(Math.random() * templates.length)];
}

/**
 * Batch availability check workflow
 */
export interface BatchAvailabilityCheck {
  listingIds: string[];
  platform: string;
  variant: AvailabilityPing['variant'];
  staggerMinutes: number; // Delay between messages
}

/**
 * Create batch ping plan
 */
export function createBatchPingPlan(config: BatchAvailabilityCheck): AvailabilityPing[] {
  const pings: AvailabilityPing[] = [];
  let currentTime = new Date();
  
  config.listingIds.forEach((listingId, index) => {
    const ping = generateAvailabilityPing(listingId, config.platform, config.variant);
    
    // Stagger send times
    if (index > 0) {
      currentTime = new Date(currentTime.getTime() + config.staggerMinutes * 60 * 1000);
    }
    
    pings.push({
      ...ping,
      sentAt: currentTime,
    });
  });
  
  return pings;
}

/**
 * Get ping status summary
 */
export function getPingStatusSummary(pings: AvailabilityPing[]): {
  total: number;
  draft: number;
  sent: number;
  responded: number;
  stale: number;
  responseRate: number;
} {
  const summary = {
    total: pings.length,
    draft: 0,
    sent: 0,
    responded: 0,
    stale: 0,
    responseRate: 0,
  };
  
  pings.forEach(ping => {
    summary[ping.status]++;
    
    // Update stale count
    if (isPingStale(ping)) {
      summary.stale++;
    }
  });
  
  // Calculate response rate
  const totalSent = summary.sent + summary.responded + summary.stale;
  if (totalSent > 0) {
    summary.responseRate = (summary.responded / totalSent) * 100;
  }
  
  return summary;
}