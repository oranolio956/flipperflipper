/**
 * Negotiation Bridge
 * Connects message templates with A/B testing
 */

import { getTemplateById, OPENING_MESSAGES } from '@/core';
import { selectVariant, recordTemplateOutcome } from './experiments';
import type { Deal, MessageTemplate } from '@/core';

export interface GeneratedDraft {
  content: string;
  template: MessageTemplate;
  variantId?: string;
  experimentId?: string;
}

/**
 * Generate message draft with A/B testing
 */
export async function generateDraft(
  deal: Deal,
  messageType: 'opening' | 'objection' | 'counter' | 'followup' | 'logistics'
): Promise<GeneratedDraft> {
  let template: MessageTemplate | null = null;
  let variantId: string | undefined;
  let experimentId: string | undefined;
  
  if (messageType === 'opening') {
    // Use A/B testing for opening messages
    experimentId = 'negotiation_openers';
    const variant = await selectVariant(experimentId);
    
    if (variant) {
      variantId = variant.variantId;
      template = getTemplateById(variant.templateId);
    }
  }
  
  // Fallback to default template
  if (!template) {
    const templates = messageType === 'opening' ? OPENING_MESSAGES : [];
    template = templates[0] || {
      id: 'default',
      category: messageType,
      tone: 'professional',
      template: 'Hi, I\'m interested in your {title}. Is it still available?',
      variables: ['title'],
      successRate: 0.5,
    };
  }
  
  // Fill template with deal data
  const variables: Record<string, string> = {
    title: deal.listing.title,
    price: `$${deal.listing.price}`,
    sellerName: deal.listing.seller?.name || 'there',
  };
  
  let content = template.template;
  for (const [key, value] of Object.entries(variables)) {
    content = content.replace(new RegExp(`\\{${key}\\}`, 'g'), value);
  }
  
  return {
    content,
    template,
    variantId,
    experimentId,
  };
}

/**
 * Mark draft as sent (impression recorded)
 */
export function markDraftSent(draft: GeneratedDraft): void {
  // Impression already recorded in generateDraft
  console.log('Draft sent:', draft.template.id);
}

/**
 * Record outcome of negotiation
 */
export async function recordNegotiationOutcome(
  draft: GeneratedDraft,
  outcome: 'accepted' | 'rejected' | 'no_response'
): Promise<void> {
  if (!draft.experimentId || !draft.variantId) {
    return;
  }
  
  // Map outcome to success
  const success = outcome === 'accepted';
  
  await recordTemplateOutcome(
    draft.experimentId,
    draft.variantId,
    success
  );
}