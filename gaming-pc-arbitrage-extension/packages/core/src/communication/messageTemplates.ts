/**
 * Message Templates
 * Pre-written templates for common communications
 */

export interface MessageTemplate {
  id: string;
  name: string;
  category: 'initial' | 'negotiation' | 'scheduling' | 'followup' | 'closing';
  tone: 'friendly' | 'professional' | 'casual' | 'urgent';
  variables: TemplateVariable[];
  template: string;
  followUp?: {
    delayHours: number;
    templateId: string;
  };
}

export interface TemplateVariable {
  name: string;
  type: 'text' | 'number' | 'date' | 'select';
  required: boolean;
  default?: any;
  options?: string[]; // For select type
}

export interface CompiledMessage {
  subject?: string;
  body: string;
  tone: string;
  estimatedResponseTime: number; // hours
}

// Message Templates
export const MESSAGE_TEMPLATES: MessageTemplate[] = [
  // Initial Contact
  {
    id: 'initial-friendly',
    name: 'Initial Contact - Friendly',
    category: 'initial',
    tone: 'friendly',
    variables: [
      { name: 'itemName', type: 'text', required: true },
      { name: 'myName', type: 'text', required: true, default: 'interested buyer' },
    ],
    template: `Hi! I saw your listing for the {{itemName}} and I'm very interested. Is it still available? If so, I'd love to know more about it. Thanks!

- {{myName}}`,
    followUp: {
      delayHours: 24,
      templateId: 'followup-gentle',
    },
  },
  
  {
    id: 'initial-professional',
    name: 'Initial Contact - Professional',
    category: 'initial',
    tone: 'professional',
    variables: [
      { name: 'itemName', type: 'text', required: true },
      { name: 'myName', type: 'text', required: true },
      { name: 'specificQuestions', type: 'text', required: false },
    ],
    template: `Good day,

I am writing regarding your listing for the {{itemName}}. I am seriously interested in purchasing this item if it is still available.

{{#if specificQuestions}}
I have a few specific questions:
{{specificQuestions}}
{{/if}}

I am prepared to move forward quickly with a fair offer. Please let me know your availability to discuss.

Best regards,
{{myName}}`,
  },
  
  // Negotiation
  {
    id: 'offer-standard',
    name: 'Make Offer - Standard',
    category: 'negotiation',
    tone: 'friendly',
    variables: [
      { name: 'offerAmount', type: 'number', required: true },
      { name: 'askingPrice', type: 'number', required: true },
      { name: 'reasoning', type: 'text', required: false },
      { name: 'cashReady', type: 'select', required: true, options: ['yes', 'no'], default: 'yes' },
    ],
    template: `Thanks for the quick response! I've had a chance to look at the details, and I'd like to offer ${{offerAmount}} for it.

{{#if reasoning}}
{{reasoning}}
{{/if}}

{{#if cashReady === 'yes'}}
I have cash ready and can pick up at your convenience.
{{/if}}

Let me know what you think!`,
  },
  
  {
    id: 'counter-offer',
    name: 'Counter Offer',
    category: 'negotiation',
    tone: 'professional',
    variables: [
      { name: 'theirOffer', type: 'number', required: true },
      { name: 'myCounter', type: 'number', required: true },
      { name: 'compromise', type: 'text', required: false },
    ],
    template: `I appreciate your offer of ${{theirOffer}}. I'm looking to get closer to ${{myCounter}} for this.

{{#if compromise}}
{{compromise}}
{{/if}}

Would you be able to meet me at ${{myCounter}}? I think that's a fair price given the condition and current market value.`,
  },
  
  // Scheduling
  {
    id: 'schedule-pickup',
    name: 'Schedule Pickup',
    category: 'scheduling',
    tone: 'friendly',
    variables: [
      { name: 'proposedDay', type: 'text', required: true },
      { name: 'timeOptions', type: 'text', required: true },
      { name: 'location', type: 'select', required: true, options: ['your place', 'public location', 'either'], default: 'either' },
    ],
    template: `Great! Let's set up a time to meet. I'm available {{proposedDay}} {{timeOptions}}.

{{#if location === 'public location'}}
Would you prefer to meet at a public location? I'm flexible on the spot - police station, busy parking lot, wherever you're comfortable.
{{else if location === 'your place'}}
I can come to your location if that works best for you.
{{else}}
I'm flexible on location - your place or a public spot, whatever you prefer.
{{/if}}

Just let me know what works for you!`,
  },
  
  {
    id: 'confirm-meeting',
    name: 'Confirm Meeting',
    category: 'scheduling',
    tone: 'professional',
    variables: [
      { name: 'meetingTime', type: 'text', required: true },
      { name: 'meetingPlace', type: 'text', required: true },
      { name: 'myPhone', type: 'text', required: false },
    ],
    template: `Perfect! I'll see you {{meetingTime}} at {{meetingPlace}}.

{{#if myPhone}}
My phone number is {{myPhone}} in case you need to reach me.
{{/if}}

I'll bring cash as agreed. Looking forward to it!`,
  },
  
  // Follow-ups
  {
    id: 'followup-gentle',
    name: 'Gentle Follow-up',
    category: 'followup',
    tone: 'casual',
    variables: [
      { name: 'daysSince', type: 'number', required: true, default: 1 },
    ],
    template: `Hey! Just following up on my message from {{daysSince}} day(s) ago. Still very interested if this is available. Let me know! 😊`,
  },
  
  {
    id: 'followup-urgent',
    name: 'Urgent Follow-up',
    category: 'followup',
    tone: 'urgent',
    variables: [
      { name: 'offerAmount', type: 'number', required: true },
      { name: 'deadline', type: 'text', required: false },
    ],
    template: `Hi - I'm ready to buy this today for ${{offerAmount}} cash. 

{{#if deadline}}
I need to make a decision by {{deadline}}, so please let me know ASAP if you're interested.
{{else}}
I have other options I'm considering, but yours is my first choice. Can we make this happen?
{{/if}}

Thanks!`,
  },
  
  // Closing
  {
    id: 'deal-closed',
    name: 'Deal Closed - Thank You',
    category: 'closing',
    tone: 'friendly',
    variables: [
      { name: 'sellerName', type: 'text', required: false, default: 'there' },
    ],
    template: `Thanks so much, {{sellerName}}! Everything looks great and works perfectly. Really smooth transaction - appreciate you being so easy to work with.

All the best!`,
  },
  
  {
    id: 'deal-cancelled',
    name: 'Deal Cancelled - Polite',
    category: 'closing',
    tone: 'professional',
    variables: [
      { name: 'reason', type: 'select', required: true, options: ['found another', 'changed mind', 'too far', 'other'] },
      { name: 'customReason', type: 'text', required: false },
    ],
    template: `Hi, thanks for your time on this. 

{{#if reason === 'found another'}}
I ended up finding another option that better fits my needs.
{{else if reason === 'changed mind'}}
After further consideration, I've decided to hold off for now.
{{else if reason === 'too far'}}
Unfortunately, the distance is more than I can manage right now.
{{else}}
{{customReason || 'My situation has changed and I need to pass on this.'}}
{{/if}}

Best of luck with the sale!`,
  },
];

/**
 * Compile template with variables
 */
export function compileTemplate(
  templateId: string,
  variables: Record<string, any>
): CompiledMessage | null {
  const template = MESSAGE_TEMPLATES.find(t => t.id === templateId);
  if (!template) return null;
  
  // Validate required variables
  for (const variable of template.variables) {
    if (variable.required && !variables[variable.name]) {
      console.warn(`Missing required variable: ${variable.name}`);
      return null;
    }
  }
  
  // Simple template compilation (replace with proper template engine)
  let body = template.template;
  
  // Handle conditionals (simplified)
  body = body.replace(/\{\{#if (.+?)\}\}([\s\S]*?)\{\{\/if\}\}/g, (match, condition, content) => {
    const evalCondition = evaluateCondition(condition, variables);
    return evalCondition ? content.trim() : '';
  });
  
  // Handle variables
  body = body.replace(/\{\{(\w+)\}\}/g, (match, varName) => {
    return variables[varName] || '';
  });
  
  // Clean up extra newlines
  body = body.replace(/\n{3,}/g, '\n\n');
  
  return {
    body: body.trim(),
    tone: template.tone,
    estimatedResponseTime: estimateResponseTime(template),
  };
}

/**
 * Get suggested templates for stage
 */
export function getSuggestedTemplates(context: {
  stage: 'initial' | 'negotiating' | 'scheduling' | 'closing';
  tone?: MessageTemplate['tone'];
  hasResponded: boolean;
  lastMessageHours?: number;
}): MessageTemplate[] {
  let templates = MESSAGE_TEMPLATES;
  
  // Filter by stage
  if (context.stage === 'initial') {
    templates = templates.filter(t => t.category === 'initial');
  } else if (context.stage === 'negotiating') {
    templates = templates.filter(t => t.category === 'negotiation');
  } else if (context.stage === 'scheduling') {
    templates = templates.filter(t => t.category === 'scheduling');
  } else if (context.stage === 'closing') {
    templates = templates.filter(t => t.category === 'closing');
  }
  
  // Add follow-ups if no response
  if (!context.hasResponded && context.lastMessageHours && context.lastMessageHours > 12) {
    const followups = MESSAGE_TEMPLATES.filter(t => t.category === 'followup');
    templates = [...templates, ...followups];
  }
  
  // Filter by tone preference
  if (context.tone) {
    templates = templates.filter(t => t.tone === context.tone);
  }
  
  return templates;
}

/**
 * Generate smart reply
 */
export function generateSmartReply(
  theirMessage: string,
  context: {
    stage: string;
    dealValue: number;
    myBudget: number;
  }
): CompiledMessage {
  const lower = theirMessage.toLowerCase();
  
  // Detect intent
  if (lower.includes('still available') || lower.includes('still for sale')) {
    return {
      body: 'Yes, still available! When would you like to take a look?',
      tone: 'friendly',
      estimatedResponseTime: 2,
    };
  }
  
  if (lower.includes('lowest price') || lower.includes('best price')) {
    const discount = context.dealValue * 0.9;
    return {
      body: `I'm fairly firm on the price, but I could do $${Math.round(discount)} for a quick sale today.`,
      tone: 'professional',
      estimatedResponseTime: 4,
    };
  }
  
  if (lower.includes('when can') || lower.includes('meet today')) {
    return {
      body: 'I can meet today after 5 PM or anytime tomorrow. What works best for you?',
      tone: 'friendly',
      estimatedResponseTime: 1,
    };
  }
  
  // Default
  return {
    body: 'Thanks for your message! Let me know if you have any questions.',
    tone: 'friendly',
    estimatedResponseTime: 4,
  };
}

// Helper functions
function evaluateCondition(condition: string, variables: Record<string, any>): boolean {
  // Simple condition evaluation
  if (condition.includes('===')) {
    const [left, right] = condition.split('===').map(s => s.trim());
    const leftValue = variables[left] || left.replace(/['"]/g, '');
    const rightValue = variables[right] || right.replace(/['"]/g, '');
    return leftValue === rightValue;
  }
  
  return !!variables[condition];
}

function estimateResponseTime(template: MessageTemplate): number {
  // Estimate based on tone and category
  if (template.tone === 'urgent') return 2;
  if (template.category === 'initial') return 6;
  if (template.category === 'negotiation') return 4;
  if (template.category === 'scheduling') return 2;
  return 4;
}