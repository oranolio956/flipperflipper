/**
 * Tests for Communication & Scheduling
 */

import { describe, it, expect } from 'vitest';
import {
  compileTemplate,
  getSuggestedTemplates,
  generateSmartReply,
} from '../messageTemplates';
import {
  suggestMeetingTimes,
  optimizeMeetingRoute,
  evaluateLocationSafety,
  generateCalendarEvent,
  exportToICS,
  type Meeting,
} from '../../scheduling/meetingScheduler';

describe('Message Templates', () => {
  it('should compile template with variables', () => {
    const result = compileTemplate('initial-friendly', {
      itemName: 'RTX 3080 Gaming PC',
      myName: 'John',
    });
    
    expect(result).toBeDefined();
    expect(result?.body).toContain('RTX 3080 Gaming PC');
    expect(result?.body).toContain('John');
    expect(result?.tone).toBe('friendly');
  });

  it('should handle conditional logic', () => {
    const result1 = compileTemplate('offer-standard', {
      offerAmount: 800,
      askingPrice: 1000,
      cashReady: 'yes',
    });
    
    expect(result1?.body).toContain('$800');
    expect(result1?.body).toContain('cash ready');
    
    const result2 = compileTemplate('offer-standard', {
      offerAmount: 800,
      askingPrice: 1000,
      cashReady: 'no',
    });
    
    expect(result2?.body).not.toContain('cash ready');
  });

  it('should suggest templates by stage', () => {
    const initial = getSuggestedTemplates({
      stage: 'initial',
      hasResponded: false,
    });
    
    expect(initial.every(t => t.category === 'initial')).toBe(true);
    
    const negotiating = getSuggestedTemplates({
      stage: 'negotiating',
      hasResponded: true,
    });
    
    expect(negotiating.every(t => t.category === 'negotiation')).toBe(true);
  });

  it('should include follow-ups when no response', () => {
    const templates = getSuggestedTemplates({
      stage: 'initial',
      hasResponded: false,
      lastMessageHours: 24,
    });
    
    expect(templates.some(t => t.category === 'followup')).toBe(true);
  });

  it('should generate smart replies', () => {
    const reply1 = generateSmartReply('Is this still available?', {
      stage: 'initial',
      dealValue: 1000,
      myBudget: 900,
    });
    
    expect(reply1.body).toContain('still available');
    expect(reply1.tone).toBe('friendly');
    
    const reply2 = generateSmartReply('What\'s your lowest price?', {
      stage: 'negotiating',
      dealValue: 1000,
      myBudget: 900,
    });
    
    expect(reply2.body).toMatch(/\$\d+/); // Contains price
  });
});

describe('Meeting Scheduler', () => {
  const existingMeetings: Meeting[] = [
    {
      id: '1',
      dealId: 'deal1',
      type: 'pickup',
      status: 'confirmed',
      proposedTimes: [],
      confirmedTime: new Date('2024-01-15T14:00:00'),
      duration: 60,
      location: {
        type: 'public',
        coordinates: { lat: 40.7128, lng: -74.0060 },
      },
      otherParty: {},
      items: ['PC'],
      safetyScore: 85,
      safetyFlags: [],
    },
  ];

  it('should suggest meeting times', () => {
    const suggestions = suggestMeetingTimes(existingMeetings, {
      earliestTime: '09:00',
      latestTime: '18:00',
      preferredDays: [1, 2, 3, 4, 5],
      blackoutDates: [],
      minNoticeHours: 2,
      maxDrivingDistance: 20,
      bufferBetweenMeetings: 30,
    });
    
    expect(suggestions.slots.length).toBeGreaterThan(0);
    expect(suggestions.slots.length).toBeLessThanOrEqual(5);
    expect(suggestions.reasoning).toBeTruthy();
    expect(suggestions.efficiency).toBeGreaterThan(0);
  });

  it('should prefer morning/afternoon slots', () => {
    const morningSuggestions = suggestMeetingTimes([], undefined, {
      preferMornings: true,
    });
    
    const morningSlots = morningSuggestions.slots.filter(s => 
      s.start.getHours() < 12 && s.preferred
    );
    
    expect(morningSlots.length).toBeGreaterThan(0);
  });

  it('should avoid conflicts with existing meetings', () => {
    const suggestions = suggestMeetingTimes(existingMeetings);
    
    // Should not suggest times that conflict with existing meeting
    const hasConflict = suggestions.slots.some(slot => {
      const slotTime = slot.start.getTime();
      const existingTime = existingMeetings[0].confirmedTime!.getTime();
      return Math.abs(slotTime - existingTime) < 90 * 60 * 1000; // 90 min window
    });
    
    expect(hasConflict).toBe(false);
  });

  it('should optimize meeting route', () => {
    const meetings: Meeting[] = [
      {
        ...existingMeetings[0],
        id: '1',
        location: { type: 'public', coordinates: { lat: 40.7128, lng: -74.0060 } },
      },
      {
        ...existingMeetings[0],
        id: '2',
        location: { type: 'public', coordinates: { lat: 40.7580, lng: -73.9855 } },
      },
      {
        ...existingMeetings[0],
        id: '3',
        location: { type: 'public', coordinates: { lat: 40.7489, lng: -73.9680 } },
      },
    ];
    
    const result = optimizeMeetingRoute(meetings);
    
    expect(result.optimizedOrder.length).toBe(3);
    expect(result.totalDistance).toBeGreaterThan(0);
    expect(result.totalTime).toBeGreaterThan(0);
    expect(result.savings.distance).toBeGreaterThanOrEqual(0);
  });

  it('should evaluate location safety', () => {
    const publicLocation = evaluateLocationSafety(
      { type: 'public', distance: 10 },
      { time: new Date('2024-01-15T14:00:00'), cashAmount: 500 }
    );
    
    expect(publicLocation.score).toBeGreaterThan(80);
    expect(publicLocation.flags.length).toBe(0);
    
    const residentialNight = evaluateLocationSafety(
      { type: 'residence', distance: 5 },
      { time: new Date('2024-01-15T22:00:00'), cashAmount: 2000 }
    );
    
    expect(residentialNight.score).toBeLessThan(60);
    expect(residentialNight.flags).toContain('Residential location');
    expect(residentialNight.flags).toContain('Outside normal hours');
    expect(residentialNight.flags).toContain('High cash amount');
    expect(residentialNight.recommendations.length).toBeGreaterThan(0);
  });

  it('should generate calendar event', () => {
    const meeting: Meeting = {
      ...existingMeetings[0],
      otherParty: { name: 'John Doe', phone: '555-1234' },
      cashAmount: 800,
      notes: 'Bring test equipment',
    };
    
    const event = generateCalendarEvent(meeting);
    
    expect(event.title).toContain('Pickup');
    expect(event.title).toContain('PC');
    expect(event.description).toContain('John Doe');
    expect(event.description).toContain('555-1234');
    expect(event.description).toContain('$800');
    expect(event.description).toContain('Safety Reminders');
    expect(event.reminders.length).toBeGreaterThan(0);
  });

  it('should export to ICS format', () => {
    const events = [
      generateCalendarEvent(existingMeetings[0]),
    ];
    
    const ics = exportToICS(events);
    
    expect(ics).toContain('BEGIN:VCALENDAR');
    expect(ics).toContain('END:VCALENDAR');
    expect(ics).toContain('BEGIN:VEVENT');
    expect(ics).toContain('END:VEVENT');
    expect(ics).toContain('SUMMARY:');
    expect(ics).toContain('DTSTART:');
    expect(ics).toContain('DTEND:');
    expect(ics).toContain('BEGIN:VALARM');
  });
});