/**
 * ICS Calendar Event Generator
 * Creates iCalendar format files for pickups and follow-ups
 */

export interface ICSEvent {
  uid: string;
  title: string;
  description?: string;
  location?: string;
  start: Date;
  end: Date;
  url?: string;
  organizer?: {
    name: string;
    email: string;
  };
  alarms?: {
    minutes: number;
    description?: string;
  }[];
}

/**
 * Build ICS event string
 */
export function buildIcsEvent(event: ICSEvent): string {
  const lines: string[] = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Gaming PC Arbitrage//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'BEGIN:VEVENT',
    `UID:${event.uid}`,
    `DTSTAMP:${toIcsDate(new Date())}`,
    `DTSTART:${toIcsDate(event.start)}`,
    `DTEND:${toIcsDate(event.end)}`,
    `SUMMARY:${sanitizeText(event.title)}`,
  ];

  if (event.description) {
    lines.push(`DESCRIPTION:${sanitizeText(event.description)}`);
  }

  if (event.location) {
    lines.push(`LOCATION:${sanitizeText(event.location)}`);
  }

  if (event.url) {
    lines.push(`URL:${event.url}`);
  }

  if (event.organizer) {
    lines.push(`ORGANIZER;CN=${sanitizeText(event.organizer.name)}:mailto:${event.organizer.email}`);
  }

  // Add alarms
  if (event.alarms) {
    for (const alarm of event.alarms) {
      lines.push(
        'BEGIN:VALARM',
        'TRIGGER:-PT' + alarm.minutes + 'M',
        'ACTION:DISPLAY',
        `DESCRIPTION:${sanitizeText(alarm.description || 'Reminder')}`,
        'END:VALARM'
      );
    }
  }

  lines.push('END:VEVENT', 'END:VCALENDAR');

  return lines.join('\r\n');
}

/**
 * Convert Date to ICS format (YYYYMMDDTHHMMSSZ)
 */
export function toIcsDate(date: Date): string {
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');
  const hours = String(date.getUTCHours()).padStart(2, '0');
  const minutes = String(date.getUTCMinutes()).padStart(2, '0');
  const seconds = String(date.getUTCSeconds()).padStart(2, '0');
  
  return `${year}${month}${day}T${hours}${minutes}${seconds}Z`;
}

/**
 * Sanitize text for ICS format
 * - Escape commas, semicolons, and backslashes
 * - Fold long lines
 */
export function sanitizeText(text: string): string {
  // Escape special characters
  let sanitized = text
    .replace(/\\/g, '\\\\')
    .replace(/;/g, '\\;')
    .replace(/,/g, '\\,')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '');

  // Fold long lines (75 chars max)
  const maxLineLength = 75;
  if (sanitized.length <= maxLineLength) {
    return sanitized;
  }

  const lines: string[] = [];
  let currentLine = '';

  for (let i = 0; i < sanitized.length; i++) {
    currentLine += sanitized[i];
    
    if (currentLine.length >= maxLineLength) {
      lines.push(currentLine);
      currentLine = ' '; // Continuation lines start with space
    }
  }

  if (currentLine.length > 1) {
    lines.push(currentLine);
  }

  return lines.join('\r\n');
}

/**
 * Create ICS file content for multiple events
 */
export function buildIcsCalendar(events: ICSEvent[]): string {
  const lines: string[] = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Gaming PC Arbitrage//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
  ];

  for (const event of events) {
    // Extract just the VEVENT portion
    const eventIcs = buildIcsEvent(event);
    const veventMatch = eventIcs.match(/BEGIN:VEVENT[\s\S]*END:VEVENT/);
    if (veventMatch) {
      lines.push(veventMatch[0]);
    }
  }

  lines.push('END:VCALENDAR');
  return lines.join('\r\n');
}

/**
 * Generate a unique UID for an event
 */
export function generateEventUid(dealId: string, type: 'pickup' | 'followup'): string {
  const timestamp = Date.now();
  return `${dealId}-${type}-${timestamp}@arbitrage.local`;
}