/**
 * Negotiation Message Templates
 * Implements templates from the blueprint with variable substitution
 */

export interface MessageTemplate {
  id: string;
  category: 'opening' | 'negotiation' | 'followup' | 'closing' | 'logistics';
  tone: 'friendly' | 'direct' | 'professional';
  name: string;
  content: string;
  variables: string[];
  description?: string;
}

// Opening Messages
export const OPENING_MESSAGES: MessageTemplate[] = [
  {
    id: 'opening-friendly',
    category: 'opening',
    tone: 'friendly',
    name: 'Friendly Opener',
    content: "Hi! I'm interested in your {ITEM}. I'm a local buyer with cash ready for pickup today. Based on similar systems, would you consider ${OFFER}? Happy to work something out!",
    variables: ['ITEM', 'OFFER'],
    description: 'Warm, friendly approach emphasizing local and cash',
  },
  {
    id: 'opening-direct',
    category: 'opening',
    tone: 'direct',
    name: 'Direct Opener',
    content: "Hello - I can offer ${OFFER} cash for your {ITEM} and pick up within 24 hours. This accounts for current market prices and immediate payment. Let me know if this works.",
    variables: ['OFFER', 'ITEM'],
    description: 'Straightforward offer with quick pickup',
  },
  {
    id: 'opening-bundle',
    category: 'opening',
    tone: 'friendly',
    name: 'Bundle Opener',
    content: "Hi there! I see you also have {OTHER_ITEM} listed. Would you take ${BUNDLE_OFFER} for both? I can pick up this week with cash.",
    variables: ['OTHER_ITEM', 'BUNDLE_OFFER'],
    description: 'For sellers with multiple relevant listings',
  },
  {
    id: 'opening-enthusiast',
    category: 'opening',
    tone: 'friendly',
    name: 'Enthusiast Opener',
    content: "Hey! Nice {ITEM}! I'm building a system and this would be perfect. I can offer ${OFFER} cash and pick up at your convenience. I know the {KEY_COMPONENT} in this is solid.",
    variables: ['ITEM', 'OFFER', 'KEY_COMPONENT'],
    description: 'Shows knowledge and genuine interest',
  },
  {
    id: 'opening-flexible',
    category: 'opening',
    tone: 'professional',
    name: 'Flexible Opener',
    content: "Good {TIME_OF_DAY}! I'm interested in your {ITEM}. I have ${OFFER} in cash ready, but I'm flexible on price if we can work out a quick pickup. What works best for you?",
    variables: ['TIME_OF_DAY', 'ITEM', 'OFFER'],
    description: 'Professional with room for negotiation',
  },
];

// Negotiation Objection Handlers
export const OBJECTION_HANDLERS: MessageTemplate[] = [
  {
    id: 'objection-why-low',
    category: 'negotiation',
    tone: 'professional',
    name: 'Why So Low?',
    content: "I appreciate you asking! I based my offer on recent sales of similar systems (${COMP_PRICES}) and factored in the {MISSING_COMPONENT_OR_ISSUE}. I'm happy to explain my thinking or meet in the middle at ${COUNTER}.",
    variables: ['COMP_PRICES', 'MISSING_COMPONENT_OR_ISSUE', 'COUNTER'],
    description: 'Responds to price questioning with data',
  },
  {
    id: 'objection-paid-more',
    category: 'negotiation',
    tone: 'professional',
    name: 'I Paid More',
    content: "I understand - PC components depreciate quickly unfortunately. Current market value for your specs is around ${FMV}. I'm offering ${OFFER} for a quick cash sale today.",
    variables: ['FMV', 'OFFER'],
    description: 'Addresses sunk cost fallacy gently',
  },
  {
    id: 'objection-other-offers',
    category: 'negotiation',
    tone: 'friendly',
    name: 'Other Offers',
    content: "That's great! If those fall through, my offer stands. I have cash ready and flexible pickup times. Just let me know!",
    variables: [],
    description: 'Stays positive when competing',
  },
  {
    id: 'objection-firm-price',
    category: 'negotiation',
    tone: 'professional',
    name: 'Price Is Firm',
    content: "I respect that. If you change your mind or need a quick sale, I can do ${OFFER} cash today. The {COMPONENT} alone is worth ${COMPONENT_VALUE} to me. Thanks for considering!",
    variables: ['OFFER', 'COMPONENT', 'COMPONENT_VALUE'],
    description: 'Leaves door open while showing value knowledge',
  },
  {
    id: 'objection-need-more',
    category: 'negotiation',
    tone: 'direct',
    name: 'Need More Money',
    content: "I understand you need ${ASKING}. The highest I can go is ${MAX_OFFER} based on the {LIMITING_FACTOR}. That's still a fair price that lets us both win. What do you think?",
    variables: ['ASKING', 'MAX_OFFER', 'LIMITING_FACTOR'],
    description: 'Sets ceiling while explaining reasoning',
  },
];

// Counter Offers
export const COUNTER_OFFERS: MessageTemplate[] = [
  {
    id: 'counter-split-difference',
    category: 'negotiation',
    tone: 'friendly',
    name: 'Split the Difference',
    content: "How about we meet in the middle at ${MIDDLE_PRICE}? I can pick up today with cash, which saves you time and hassle. Deal?",
    variables: ['MIDDLE_PRICE'],
    description: 'Classic compromise approach',
  },
  {
    id: 'counter-final-offer',
    category: 'negotiation',
    tone: 'direct',
    name: 'Final Offer',
    content: "I can stretch to ${FINAL_OFFER} cash, but that's really my limit. I think it's fair given the {REASON}. If that works, I can pick up within {TIMEFRAME}.",
    variables: ['FINAL_OFFER', 'REASON', 'TIMEFRAME'],
    description: 'Clear ceiling with urgency',
  },
  {
    id: 'counter-add-value',
    category: 'negotiation',
    tone: 'professional',
    name: 'Value Addition',
    content: "I understand your position. How about ${OFFER} and I'll {VALUE_ADD}? This way you get what you need and I stay within budget.",
    variables: ['OFFER', 'VALUE_ADD'],
    description: 'Adds non-monetary value',
  },
];

// Follow-up Messages
export const FOLLOWUP_MESSAGES: MessageTemplate[] = [
  {
    id: 'followup-gentle',
    category: 'followup',
    tone: 'friendly',
    name: 'Gentle Reminder',
    content: "Hi again! Just following up on my offer for your {ITEM}. Still very interested! My ${OFFER} offer stands if you're interested. Thanks!",
    variables: ['ITEM', 'OFFER'],
    description: 'First follow-up after 24-48 hours',
  },
  {
    id: 'followup-final',
    category: 'followup',
    tone: 'direct',
    name: 'Final Check',
    content: "Last check - my ${OFFER} offer for your {ITEM} is still available if you're interested. If not, no worries and good luck with your sale!",
    variables: ['OFFER', 'ITEM'],
    description: 'Final follow-up before moving on',
  },
  {
    id: 'followup-increased',
    category: 'followup',
    tone: 'professional',
    name: 'Increased Offer',
    content: "Hi! I've been thinking about your {ITEM} and I can increase my offer to ${NEW_OFFER}. This is my best offer. Let me know if you're interested!",
    variables: ['ITEM', 'NEW_OFFER'],
    description: 'Strategic offer increase',
  },
  {
    id: 'followup-urgency',
    category: 'followup',
    tone: 'direct',
    name: 'Time-Sensitive',
    content: "Quick update - I need to make a decision by {DEADLINE}. My ${OFFER} offer for your {ITEM} stands until then. Cash ready for immediate pickup!",
    variables: ['DEADLINE', 'OFFER', 'ITEM'],
    description: 'Creates urgency for decision',
  },
];

// Logistics Messages
export const LOGISTICS_MESSAGES: MessageTemplate[] = [
  {
    id: 'logistics-pickup-confirm',
    category: 'logistics',
    tone: 'professional',
    name: 'Pickup Confirmation',
    content: "Great! I can pick up at {TIME} on {DATE}. I'll have ${AMOUNT} in cash. My number is {PHONE} if anything changes. Looking forward to it!",
    variables: ['TIME', 'DATE', 'AMOUNT', 'PHONE'],
    description: 'Confirms pickup details',
  },
  {
    id: 'logistics-location-suggest',
    category: 'logistics',
    tone: 'friendly',
    name: 'Safe Location',
    content: "For both our safety, how about meeting at {SAFE_LOCATION}? It's public and convenient. I'm flexible on time - what works for you?",
    variables: ['SAFE_LOCATION'],
    description: 'Suggests safe meetup spot',
  },
  {
    id: 'logistics-test-request',
    category: 'logistics',
    tone: 'professional',
    name: 'Test Request',
    content: "Sounds good! When we meet, would it be possible to see it power on briefly? Just want to make sure everything's working. I'll bring cash and we can complete the sale right there.",
    variables: [],
    description: 'Requests functionality test',
  },
  {
    id: 'logistics-cash-ready',
    category: 'logistics',
    tone: 'direct',
    name: 'Cash Confirmation',
    content: "Confirming I have ${AMOUNT} cash ready for our {TIME} meetup at {LOCATION}. See you there!",
    variables: ['AMOUNT', 'TIME', 'LOCATION'],
    description: 'Final confirmation with cash ready',
  },
];

// All templates combined
export const ALL_TEMPLATES: MessageTemplate[] = [
  ...OPENING_MESSAGES,
  ...OBJECTION_HANDLERS,
  ...COUNTER_OFFERS,
  ...FOLLOWUP_MESSAGES,
  ...LOGISTICS_MESSAGES,
];

// Template helper functions
export function fillTemplate(template: MessageTemplate, values: Record<string, string>): string {
  let filled = template.content;
  
  // Replace all variables with their values
  for (const variable of template.variables) {
    const value = values[variable];
    if (!value) {
      console.warn(`Missing value for variable ${variable} in template ${template.id}`);
      continue;
    }
    
    // Use global replace to handle multiple occurrences
    const regex = new RegExp(`{${variable}}`, 'g');
    filled = filled.replace(regex, value);
  }
  
  return filled;
}

export function getTemplatesByCategory(category: MessageTemplate['category']): MessageTemplate[] {
  return ALL_TEMPLATES.filter(t => t.category === category);
}

export function getTemplatesByTone(tone: MessageTemplate['tone']): MessageTemplate[] {
  return ALL_TEMPLATES.filter(t => t.tone === tone);
}

export function getTemplateById(id: string): MessageTemplate | undefined {
  return ALL_TEMPLATES.find(t => t.id === id);
}

// Smart template suggester based on context
export function suggestTemplate(context: {
  stage: 'initial' | 'negotiating' | 'following-up' | 'closing';
  priceGap?: number;
  tone?: MessageTemplate['tone'];
  hasOtherListings?: boolean;
  sellerMood?: 'receptive' | 'firm' | 'unresponsive';
}): MessageTemplate | undefined {
  const { stage, priceGap, tone = 'friendly', hasOtherListings, sellerMood } = context;
  
  // Initial contact
  if (stage === 'initial') {
    if (hasOtherListings) {
      return getTemplateById('opening-bundle');
    }
    return getTemplatesByTone(tone)[0];
  }
  
  // Negotiation phase
  if (stage === 'negotiating') {
    if (sellerMood === 'firm' && priceGap && priceGap > 0.2) {
      return getTemplateById('objection-firm-price');
    }
    if (priceGap && priceGap < 0.1) {
      return getTemplateById('counter-split-difference');
    }
    return getTemplateById('counter-final-offer');
  }
  
  // Follow-up phase
  if (stage === 'following-up') {
    if (sellerMood === 'unresponsive') {
      return getTemplateById('followup-final');
    }
    return getTemplateById('followup-gentle');
  }
  
  // Closing phase
  if (stage === 'closing') {
    return getTemplateById('logistics-pickup-confirm');
  }
  
  return undefined;
}