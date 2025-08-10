/**
 * Voice Notes Module
 * Voice input and transcription for notes and listings
 */

export interface VoiceNote {
  id: string;
  timestamp: Date;
  duration: number; // seconds
  transcript: string;
  confidence: number;
  type: 'listing' | 'note' | 'followup' | 'specs';
  metadata?: {
    listingId?: string;
    dealId?: string;
    location?: string;
  };
}

export interface TranscriptionResult {
  transcript: string;
  confidence: number;
  segments: TranscriptionSegment[];
  language: string;
}

export interface TranscriptionSegment {
  text: string;
  startTime: number;
  endTime: number;
  confidence: number;
}

export interface VoiceCommand {
  command: string;
  parameters: Record<string, any>;
  confidence: number;
}

// Voice command patterns
const VOICE_COMMANDS = {
  // Listing commands
  'new listing': /^(?:create|add|new)\s+listing/i,
  'price': /price\s+(?:is\s+)?(\$?\d+)/i,
  'cpu': /cpu\s+(?:is\s+)?(.+?)(?:\s+and|\s*$)/i,
  'gpu': /gpu\s+(?:is\s+)?(.+?)(?:\s+and|\s*$)/i,
  'ram': /(\d+)\s*(?:gigs?|gb|gigabytes?)\s*(?:of\s+)?ram/i,
  
  // Note commands
  'add note': /^(?:add|create)\s+note/i,
  'follow up': /follow\s*up\s+(?:in\s+)?(\d+)\s*(hours?|days?|weeks?)/i,
  'reminder': /remind(?:er)?\s+(?:me\s+)?(?:to\s+)?(.+)/i,
  
  // Action commands
  'mark sold': /mark\s+(?:as\s+)?sold/i,
  'mark bought': /mark\s+(?:as\s+)?(?:bought|purchased)/i,
  'cancel': /cancel\s+(?:this\s+)?(?:deal|listing)/i,
};

/**
 * Parse voice transcript into structured data
 */
export function parseVoiceTranscript(transcript: string): {
  type: VoiceNote['type'];
  data: any;
  commands: VoiceCommand[];
} {
  const lower = transcript.toLowerCase();
  const commands: VoiceCommand[] = [];
  let type: VoiceNote['type'] = 'note';
  const data: any = {};
  
  // Check for listing creation
  if (VOICE_COMMANDS['new listing'].test(lower)) {
    type = 'listing';
    
    // Extract price
    const priceMatch = transcript.match(VOICE_COMMANDS.price);
    if (priceMatch) {
      data.price = parseInt(priceMatch[1].replace('$', ''));
      commands.push({
        command: 'set_price',
        parameters: { price: data.price },
        confidence: 0.9,
      });
    }
    
    // Extract CPU
    const cpuMatch = transcript.match(VOICE_COMMANDS.cpu);
    if (cpuMatch) {
      data.cpu = normalizeCpuFromVoice(cpuMatch[1]);
      commands.push({
        command: 'set_cpu',
        parameters: { cpu: data.cpu },
        confidence: 0.8,
      });
    }
    
    // Extract GPU
    const gpuMatch = transcript.match(VOICE_COMMANDS.gpu);
    if (gpuMatch) {
      data.gpu = normalizeGpuFromVoice(gpuMatch[1]);
      commands.push({
        command: 'set_gpu',
        parameters: { gpu: data.gpu },
        confidence: 0.8,
      });
    }
    
    // Extract RAM
    const ramMatch = transcript.match(VOICE_COMMANDS.ram);
    if (ramMatch) {
      data.ram = `${ramMatch[1]}GB`;
      commands.push({
        command: 'set_ram',
        parameters: { ram: data.ram },
        confidence: 0.9,
      });
    }
  }
  
  // Check for follow-up
  const followUpMatch = transcript.match(VOICE_COMMANDS['follow up']);
  if (followUpMatch) {
    type = 'followup';
    const amount = parseInt(followUpMatch[1]);
    const unit = followUpMatch[2].toLowerCase();
    
    let hours = amount;
    if (unit.includes('day')) hours *= 24;
    if (unit.includes('week')) hours *= 168;
    
    data.followUpHours = hours;
    commands.push({
      command: 'schedule_followup',
      parameters: { hours },
      confidence: 0.9,
    });
  }
  
  // Check for action commands
  if (VOICE_COMMANDS['mark sold'].test(lower)) {
    commands.push({
      command: 'mark_sold',
      parameters: {},
      confidence: 0.95,
    });
  }
  
  if (VOICE_COMMANDS['mark bought'].test(lower)) {
    commands.push({
      command: 'mark_bought',
      parameters: {},
      confidence: 0.95,
    });
  }
  
  // Extract location mentions
  const locationMatch = transcript.match(/(?:in|at|near)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)/);
  if (locationMatch) {
    data.location = locationMatch[1];
  }
  
  return { type, data, commands };
}

/**
 * Normalize CPU from voice input
 */
function normalizeCpuFromVoice(input: string): string {
  const lower = input.toLowerCase();
  
  // Handle phonetic variations
  const replacements: Record<string, string> = {
    'eye': 'i',
    'core': '',
    'intel': 'Intel',
    'rise in': 'Ryzen',
    'rising': 'Ryzen',
    'rye zen': 'Ryzen',
  };
  
  let normalized = input;
  for (const [pattern, replacement] of Object.entries(replacements)) {
    normalized = normalized.replace(new RegExp(pattern, 'gi'), replacement);
  }
  
  // Fix common patterns
  normalized = normalized
    .replace(/i\s*(\d)/g, 'i$1') // "i 7" -> "i7"
    .replace(/(\d)\s*thousand/g, '$1000') // "12 thousand" -> "12000"
    .replace(/(\d)\s*hundred/g, '$100') // "47 hundred" -> "4700"
    .trim();
  
  return normalized;
}

/**
 * Normalize GPU from voice input
 */
function normalizeGpuFromVoice(input: string): string {
  const lower = input.toLowerCase();
  
  // Handle phonetic variations
  const replacements: Record<string, string> = {
    'are tx': 'RTX',
    'g tx': 'GTX',
    'artex': 'RTX',
    'thirty': '30',
    'twenty': '20',
    'forty': '40',
    'fifty': '50',
    'sixty': '60',
    'seventy': '70',
    'eighty': '80',
    'ninety': '90',
    'ti': 'Ti',
    'tea eye': 'Ti',
  };
  
  let normalized = input;
  for (const [pattern, replacement] of Object.entries(replacements)) {
    normalized = normalized.replace(new RegExp(pattern, 'gi'), replacement);
  }
  
  // Clean up spacing
  normalized = normalized
    .replace(/\s+/g, ' ')
    .toUpperCase()
    .trim();
  
  return normalized;
}

/**
 * Generate voice prompt suggestions
 */
export function generateVoicePrompts(context: {
  stage?: 'listing' | 'negotiation' | 'followup';
  hasPrice?: boolean;
  hasSpecs?: boolean;
}): string[] {
  const prompts: string[] = [];
  
  if (context.stage === 'listing') {
    if (!context.hasPrice) {
      prompts.push('Say the price, like "Price is 800 dollars"');
    }
    if (!context.hasSpecs) {
      prompts.push('Describe the specs, like "CPU is i7 12700, GPU is RTX 3070"');
    }
    prompts.push('Add any notes about condition or included items');
  } else if (context.stage === 'negotiation') {
    prompts.push('Record offer details, like "Buyer offered 750"');
    prompts.push('Set a follow-up reminder, like "Follow up in 2 days"');
  } else if (context.stage === 'followup') {
    prompts.push('Update status, like "Mark as sold" or "Buyer not responding"');
    prompts.push('Schedule next action, like "Follow up tomorrow at 5 PM"');
  } else {
    prompts.push('Create new listing, add note, or set reminder');
  }
  
  return prompts;
}

/**
 * Format voice note for display
 */
export function formatVoiceNote(note: VoiceNote): string {
  const timeAgo = getTimeAgo(note.timestamp);
  const duration = formatDuration(note.duration);
  
  let formatted = `${timeAgo} (${duration})`;
  
  if (note.type === 'listing') {
    formatted = `📦 Listing: ${note.transcript.substring(0, 50)}...`;
  } else if (note.type === 'followup') {
    formatted = `⏰ Follow-up: ${note.transcript.substring(0, 50)}...`;
  } else if (note.type === 'specs') {
    formatted = `🔧 Specs: ${note.transcript.substring(0, 50)}...`;
  } else {
    formatted = `📝 Note: ${note.transcript.substring(0, 50)}...`;
  }
  
  return formatted;
}

// Helper functions
function getTimeAgo(date: Date): string {
  const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
  
  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

/**
 * Mock transcription function
 * In production, this would use Web Speech API or cloud service
 */
export async function transcribeAudio(audioBlob: Blob): Promise<TranscriptionResult> {
  // Mock implementation
  return {
    transcript: "New listing price is 850 dollars CPU is i7 12700K GPU is RTX 3070",
    confidence: 0.92,
    segments: [
      {
        text: "New listing",
        startTime: 0,
        endTime: 1.2,
        confidence: 0.95,
      },
      {
        text: "price is 850 dollars",
        startTime: 1.3,
        endTime: 3.0,
        confidence: 0.90,
      },
    ],
    language: 'en-US',
  };
}