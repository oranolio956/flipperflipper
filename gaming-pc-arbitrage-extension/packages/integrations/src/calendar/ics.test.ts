/**
 * ICS Calendar Tests
 */

import { describe, it, expect } from 'vitest';
import {
  buildIcsEvent,
  toIcsDate,
  sanitizeText,
  generateEventUid,
  buildIcsCalendar,
} from './ics';

describe('toIcsDate', () => {
  it('should convert date to ICS format', () => {
    const date = new Date('2024-01-15T14:30:00Z');
    expect(toIcsDate(date)).toBe('20240115T143000Z');
  });

  it('should handle timezone correctly', () => {
    const date = new Date('2024-06-15T10:00:00-07:00'); // PDT
    const icsDate = toIcsDate(date);
    expect(icsDate).toBe('20240615T170000Z'); // UTC
  });
});

describe('sanitizeText', () => {
  it('should escape special characters', () => {
    expect(sanitizeText('Test; with, special\\ chars')).toBe('Test\\; with\\, special\\\\ chars');
  });

  it('should replace newlines', () => {
    expect(sanitizeText('Line 1\nLine 2')).toBe('Line 1\\nLine 2');
  });

  it('should fold long lines', () => {
    const longText = 'A'.repeat(100);
    const sanitized = sanitizeText(longText);
    const lines = sanitized.split('\r\n');
    expect(lines[0].length).toBe(75);
    expect(lines[1]).toStartWith(' '); // Continuation line
  });
});

describe('generateEventUid', () => {
  it('should generate unique UIDs', () => {
    const uid1 = generateEventUid('deal-123', 'pickup');
    const uid2 = generateEventUid('deal-123', 'pickup');
    expect(uid1).not.toBe(uid2);
  });

  it('should include deal ID and type', () => {
    const uid = generateEventUid('deal-456', 'followup');
    expect(uid).toContain('deal-456');
    expect(uid).toContain('followup');
    expect(uid).toContain('@arbitrage.local');
  });
});

describe('buildIcsEvent', () => {
  const baseEvent = {
    uid: 'test-123',
    title: 'Pickup: Gaming PC',
    start: new Date('2024-01-15T14:00:00Z'),
    end: new Date('2024-01-15T14:30:00Z'),
  };

  it('should build basic event', () => {
    const ics = buildIcsEvent(baseEvent);
    
    expect(ics).toContain('BEGIN:VCALENDAR');
    expect(ics).toContain('VERSION:2.0');
    expect(ics).toContain('BEGIN:VEVENT');
    expect(ics).toContain('UID:test-123');
    expect(ics).toContain('SUMMARY:Pickup: Gaming PC');
    expect(ics).toContain('DTSTART:20240115T140000Z');
    expect(ics).toContain('DTEND:20240115T143000Z');
    expect(ics).toContain('END:VEVENT');
    expect(ics).toContain('END:VCALENDAR');
  });

  it('should include optional fields', () => {
    const event = {
      ...baseEvent,
      description: 'Meet seller at Starbucks',
      location: '123 Main St, Denver, CO',
      url: 'https://example.com/listing',
      organizer: { name: 'John Doe', email: 'john@example.com' },
    };
    
    const ics = buildIcsEvent(event);
    
    expect(ics).toContain('DESCRIPTION:Meet seller at Starbucks');
    expect(ics).toContain('LOCATION:123 Main St\\, Denver\\, CO');
    expect(ics).toContain('URL:https://example.com/listing');
    expect(ics).toContain('ORGANIZER;CN=John Doe:mailto:john@example.com');
  });

  it('should add alarms', () => {
    const event = {
      ...baseEvent,
      alarms: [
        { minutes: 60, description: '1 hour reminder' },
        { minutes: 15 },
      ],
    };
    
    const ics = buildIcsEvent(event);
    
    expect(ics).toContain('BEGIN:VALARM');
    expect(ics).toContain('TRIGGER:-PT60M');
    expect(ics).toContain('DESCRIPTION:1 hour reminder');
    expect(ics).toContain('TRIGGER:-PT15M');
    expect(ics).toContain('DESCRIPTION:Reminder');
  });
});

describe('buildIcsCalendar', () => {
  it('should combine multiple events', () => {
    const events = [
      {
        uid: 'event-1',
        title: 'Pickup 1',
        start: new Date('2024-01-15T10:00:00Z'),
        end: new Date('2024-01-15T10:30:00Z'),
      },
      {
        uid: 'event-2',
        title: 'Pickup 2',
        start: new Date('2024-01-15T11:00:00Z'),
        end: new Date('2024-01-15T11:30:00Z'),
      },
    ];
    
    const ics = buildIcsCalendar(events);
    
    expect(ics).toContain('BEGIN:VCALENDAR');
    expect(ics).toContain('VERSION:2.0');
    expect(ics.match(/BEGIN:VEVENT/g)).toHaveLength(2);
    expect(ics).toContain('UID:event-1');
    expect(ics).toContain('UID:event-2');
    expect(ics).toContain('SUMMARY:Pickup 1');
    expect(ics).toContain('SUMMARY:Pickup 2');
    expect(ics.match(/END:VEVENT/g)).toHaveLength(2);
    expect(ics).toContain('END:VCALENDAR');
  });
});