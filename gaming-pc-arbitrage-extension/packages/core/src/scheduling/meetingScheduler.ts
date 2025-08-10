/**
 * Meeting Scheduler
 * Schedule and manage pickup/dropoff meetings
 */

export interface Meeting {
  id: string;
  dealId: string;
  type: 'pickup' | 'dropoff' | 'inspection';
  status: 'proposed' | 'confirmed' | 'completed' | 'cancelled';
  
  // Time
  proposedTimes: TimeSlot[];
  confirmedTime?: Date;
  duration: number; // minutes
  
  // Location
  location: MeetingLocation;
  
  // Participants
  otherParty: {
    name?: string;
    phone?: string;
    responseTime?: number; // avg hours
  };
  
  // Logistics
  items: string[];
  cashAmount?: number;
  notes?: string;
  
  // Safety
  safetyScore: number; // 0-100
  safetyFlags: string[];
}

export interface TimeSlot {
  start: Date;
  end: Date;
  preferred: boolean;
}

export interface MeetingLocation {
  type: 'residence' | 'public' | 'business';
  address?: string;
  coordinates?: { lat: number; lng: number };
  name?: string;
  safetyRating?: number;
  distance?: number; // miles
}

export interface ScheduleConstraints {
  earliestTime: string; // "09:00"
  latestTime: string; // "20:00"
  preferredDays: number[]; // 0-6 (Sun-Sat)
  blackoutDates: Date[];
  minNoticeHours: number;
  maxDrivingDistance: number;
  bufferBetweenMeetings: number; // minutes
}

export interface ScheduleSuggestion {
  slots: TimeSlot[];
  reasoning: string;
  efficiency: number; // 0-100
}

// Default constraints
const DEFAULT_CONSTRAINTS: ScheduleConstraints = {
  earliestTime: '09:00',
  latestTime: '19:00',
  preferredDays: [1, 2, 3, 4, 5], // Weekdays
  blackoutDates: [],
  minNoticeHours: 2,
  maxDrivingDistance: 25,
  bufferBetweenMeetings: 30,
};

/**
 * Suggest meeting times
 */
export function suggestMeetingTimes(
  existingMeetings: Meeting[],
  constraints: ScheduleConstraints = DEFAULT_CONSTRAINTS,
  preferences?: {
    preferMornings?: boolean;
    preferAfternoons?: boolean;
    batchNearby?: boolean;
  }
): ScheduleSuggestion {
  const slots: TimeSlot[] = [];
  const now = new Date();
  const minStart = new Date(now.getTime() + constraints.minNoticeHours * 60 * 60 * 1000);
  
  // Generate potential slots for next 7 days
  for (let days = 0; days < 7; days++) {
    const date = new Date(minStart);
    date.setDate(date.getDate() + days);
    
    // Skip non-preferred days
    if (!constraints.preferredDays.includes(date.getDay())) continue;
    
    // Skip blackout dates
    if (constraints.blackoutDates.some(d => isSameDay(d, date))) continue;
    
    // Generate time slots for this day
    const daySlots = generateDaySlots(date, constraints, preferences);
    
    // Filter out conflicts with existing meetings
    const availableSlots = daySlots.filter(slot => 
      !hasConflict(slot, existingMeetings, constraints.bufferBetweenMeetings)
    );
    
    slots.push(...availableSlots.slice(0, 3)); // Max 3 per day
  }
  
  // Sort by preference
  slots.sort((a, b) => {
    // Prefer earlier dates
    const dateDiff = a.start.getTime() - b.start.getTime();
    if (Math.abs(dateDiff) > 24 * 60 * 60 * 1000) return dateDiff;
    
    // Then by preference
    if (a.preferred !== b.preferred) return a.preferred ? -1 : 1;
    
    return 0;
  });
  
  // Calculate efficiency
  const efficiency = calculateScheduleEfficiency(slots.slice(0, 5), existingMeetings);
  
  return {
    slots: slots.slice(0, 5), // Top 5 suggestions
    reasoning: generateScheduleReasoning(slots, preferences),
    efficiency,
  };
}

/**
 * Optimize route for multiple meetings
 */
export function optimizeMeetingRoute(
  meetings: Meeting[],
  startLocation?: { lat: number; lng: number }
): {
  optimizedOrder: Meeting[];
  totalDistance: number;
  totalTime: number;
  savings: { distance: number; time: number };
} {
  if (meetings.length <= 1) {
    return {
      optimizedOrder: meetings,
      totalDistance: 0,
      totalTime: 0,
      savings: { distance: 0, time: 0 },
    };
  }
  
  // Simple nearest neighbor algorithm
  const unvisited = [...meetings];
  const optimized: Meeting[] = [];
  let currentLocation = startLocation || { lat: 0, lng: 0 };
  
  while (unvisited.length > 0) {
    // Find nearest unvisited meeting
    let nearestIndex = 0;
    let nearestDistance = Infinity;
    
    unvisited.forEach((meeting, index) => {
      if (meeting.location.coordinates) {
        const distance = calculateDistance(
          currentLocation,
          meeting.location.coordinates
        );
        if (distance < nearestDistance) {
          nearestDistance = distance;
          nearestIndex = index;
        }
      }
    });
    
    const nearest = unvisited.splice(nearestIndex, 1)[0];
    optimized.push(nearest);
    
    if (nearest.location.coordinates) {
      currentLocation = nearest.location.coordinates;
    }
  }
  
  // Calculate metrics
  const optimizedDistance = calculateTotalDistance(optimized);
  const originalDistance = calculateTotalDistance(meetings);
  const avgSpeed = 30; // mph
  
  return {
    optimizedOrder: optimized,
    totalDistance: optimizedDistance,
    totalTime: (optimizedDistance / avgSpeed) * 60, // minutes
    savings: {
      distance: originalDistance - optimizedDistance,
      time: ((originalDistance - optimizedDistance) / avgSpeed) * 60,
    },
  };
}

/**
 * Evaluate location safety
 */
export function evaluateLocationSafety(
  location: MeetingLocation,
  meeting: { time?: Date; cashAmount?: number }
): {
  score: number;
  flags: string[];
  recommendations: string[];
} {
  let score = 70; // Base score
  const flags: string[] = [];
  const recommendations: string[] = [];
  
  // Location type
  if (location.type === 'public') {
    score += 20;
  } else if (location.type === 'business') {
    score += 15;
  } else if (location.type === 'residence') {
    score -= 10;
    flags.push('Residential location');
    recommendations.push('Consider meeting at a public location instead');
  }
  
  // Time of day
  if (meeting.time) {
    const hour = meeting.time.getHours();
    if (hour < 8 || hour > 20) {
      score -= 15;
      flags.push('Outside normal hours');
      recommendations.push('Try to schedule during daylight hours');
    }
  }
  
  // Cash amount
  if (meeting.cashAmount && meeting.cashAmount > 1000) {
    score -= 10;
    flags.push('High cash amount');
    recommendations.push('Consider meeting at a police station or bank');
  }
  
  // Distance
  if (location.distance && location.distance > 30) {
    score -= 5;
    flags.push('Far distance');
    recommendations.push('Verify the listing is legitimate before traveling');
  }
  
  // Cap score
  score = Math.max(0, Math.min(100, score));
  
  return { score, flags, recommendations };
}

/**
 * Generate calendar event
 */
export function generateCalendarEvent(meeting: Meeting): {
  title: string;
  description: string;
  location: string;
  startTime: Date;
  endTime: Date;
  reminders: number[]; // minutes before
} {
  const title = `${meeting.type === 'pickup' ? '📦 Pickup' : '📍 Dropoff'}: ${meeting.items.join(', ')}`;
  
  const description = [
    `Deal ID: ${meeting.dealId}`,
    meeting.otherParty.name ? `Contact: ${meeting.otherParty.name}` : '',
    meeting.otherParty.phone ? `Phone: ${meeting.otherParty.phone}` : '',
    meeting.cashAmount ? `Cash: $${meeting.cashAmount}` : '',
    meeting.notes ? `Notes: ${meeting.notes}` : '',
    '',
    '⚠️ Safety Reminders:',
    '- Bring a friend if possible',
    '- Meet in a well-lit public area',
    '- Verify item condition before payment',
    '- Trust your instincts',
  ].filter(Boolean).join('\n');
  
  const location = meeting.location.name || meeting.location.address || 'TBD';
  
  const startTime = meeting.confirmedTime || meeting.proposedTimes[0]?.start || new Date();
  const endTime = new Date(startTime.getTime() + meeting.duration * 60 * 1000);
  
  // Reminders based on distance
  const travelTime = meeting.location.distance ? Math.ceil(meeting.location.distance / 30 * 60) : 30;
  const reminders = [
    travelTime + 15, // Leave time + buffer
    60, // 1 hour before
  ];
  
  return {
    title,
    description,
    location,
    startTime,
    endTime,
    reminders,
  };
}

/**
 * Export to ICS format
 */
export function exportToICS(events: ReturnType<typeof generateCalendarEvent>[]): string {
  const icsLines: string[] = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Gaming PC Arbitrage//Meeting Scheduler//EN',
    'CALSCALE:GREGORIAN',
  ];
  
  for (const event of events) {
    icsLines.push(
      'BEGIN:VEVENT',
      `UID:${generateUID()}`,
      `DTSTAMP:${formatICSDate(new Date())}`,
      `DTSTART:${formatICSDate(event.startTime)}`,
      `DTEND:${formatICSDate(event.endTime)}`,
      `SUMMARY:${event.title}`,
      `DESCRIPTION:${event.description.replace(/\n/g, '\\n')}`,
      `LOCATION:${event.location}`,
    );
    
    // Add alarms
    for (const reminder of event.reminders) {
      icsLines.push(
        'BEGIN:VALARM',
        'TRIGGER:-PT' + reminder + 'M',
        'ACTION:DISPLAY',
        `DESCRIPTION:Reminder: ${event.title}`,
        'END:VALARM',
      );
    }
    
    icsLines.push('END:VEVENT');
  }
  
  icsLines.push('END:VCALENDAR');
  
  return icsLines.join('\r\n');
}

// Helper functions
function generateDaySlots(
  date: Date,
  constraints: ScheduleConstraints,
  preferences?: any
): TimeSlot[] {
  const slots: TimeSlot[] = [];
  const [startHour, startMin] = constraints.earliestTime.split(':').map(Number);
  const [endHour, endMin] = constraints.latestTime.split(':').map(Number);
  
  // Morning slots
  if (!preferences?.preferAfternoons) {
    slots.push(
      createSlot(date, 9, 0, 60, preferences?.preferMornings),
      createSlot(date, 10, 30, 60, preferences?.preferMornings),
    );
  }
  
  // Afternoon slots
  if (!preferences?.preferMornings) {
    slots.push(
      createSlot(date, 14, 0, 60, preferences?.preferAfternoons),
      createSlot(date, 16, 0, 60, preferences?.preferAfternoons),
    );
  }
  
  // Evening slot
  if (endHour >= 18) {
    slots.push(createSlot(date, 18, 0, 60, false));
  }
  
  return slots.filter(slot => 
    slot.start.getHours() >= startHour && 
    slot.end.getHours() <= endHour
  );
}

function createSlot(date: Date, hour: number, minute: number, duration: number, preferred: boolean): TimeSlot {
  const start = new Date(date);
  start.setHours(hour, minute, 0, 0);
  
  const end = new Date(start);
  end.setMinutes(end.getMinutes() + duration);
  
  return { start, end, preferred };
}

function hasConflict(slot: TimeSlot, meetings: Meeting[], buffer: number): boolean {
  return meetings.some(meeting => {
    if (!meeting.confirmedTime || meeting.status === 'cancelled') return false;
    
    const meetingStart = new Date(meeting.confirmedTime.getTime() - buffer * 60 * 1000);
    const meetingEnd = new Date(meeting.confirmedTime.getTime() + (meeting.duration + buffer) * 60 * 1000);
    
    return (
      (slot.start >= meetingStart && slot.start < meetingEnd) ||
      (slot.end > meetingStart && slot.end <= meetingEnd) ||
      (slot.start <= meetingStart && slot.end >= meetingEnd)
    );
  });
}

function calculateDistance(loc1: { lat: number; lng: number }, loc2: { lat: number; lng: number }): number {
  // Haversine formula
  const R = 3959; // Earth radius in miles
  const dLat = (loc2.lat - loc1.lat) * Math.PI / 180;
  const dLng = (loc2.lng - loc1.lng) * Math.PI / 180;
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(loc1.lat * Math.PI / 180) * Math.cos(loc2.lat * Math.PI / 180) *
    Math.sin(dLng / 2) * Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function calculateTotalDistance(meetings: Meeting[]): number {
  let total = 0;
  for (let i = 0; i < meetings.length - 1; i++) {
    const loc1 = meetings[i].location.coordinates;
    const loc2 = meetings[i + 1].location.coordinates;
    if (loc1 && loc2) {
      total += calculateDistance(loc1, loc2);
    }
  }
  return total;
}

function calculateScheduleEfficiency(slots: TimeSlot[], existingMeetings: Meeting[]): number {
  if (slots.length === 0) return 0;
  
  let efficiency = 80; // Base
  
  // Penalize spread out times
  const daySpread = new Set(slots.map(s => s.start.toDateString())).size;
  if (daySpread > 3) efficiency -= 10;
  
  // Bonus for batching on same day
  if (daySpread === 1 && slots.length > 1) efficiency += 10;
  
  // Consider existing meetings
  const hasNearbyMeetings = existingMeetings.some(m => {
    if (!m.confirmedTime) return false;
    return slots.some(s => 
      Math.abs(s.start.getTime() - m.confirmedTime!.getTime()) < 2 * 60 * 60 * 1000
    );
  });
  
  if (hasNearbyMeetings) efficiency += 5;
  
  return Math.max(0, Math.min(100, efficiency));
}

function generateScheduleReasoning(slots: TimeSlot[], preferences?: any): string {
  const reasons: string[] = [];
  
  if (slots.length === 0) {
    return 'No available time slots found. Consider adjusting your constraints.';
  }
  
  const days = new Set(slots.map(s => s.start.toDateString())).size;
  reasons.push(`Found ${slots.length} available slots across ${days} days`);
  
  if (preferences?.preferMornings) {
    reasons.push('Prioritized morning slots as requested');
  } else if (preferences?.preferAfternoons) {
    reasons.push('Prioritized afternoon slots as requested');
  }
  
  return reasons.join('. ');
}

function isSameDay(date1: Date, date2: Date): boolean {
  return date1.toDateString() === date2.toDateString();
}

function generateUID(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}@arbitrage`;
}

function formatICSDate(date: Date): string {
  return date.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
}